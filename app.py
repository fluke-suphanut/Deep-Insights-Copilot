import os
import time
import streamlit as st
import psycopg2
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from router import choose_tool
from guardrail import safe_execute

# CONFIG
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "1234")
DB_NAME = os.getenv("DB_NAME", "dbank_demo")
KB_DIR = "knowledge_base"
DB_DIR = "chroma_db"
COLLECTION = "kb_docs"

# DB Helpers
def sql_query(query: str):
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute("SET search_path TO public;")
    cur.execute(query)
    try:
        rows = cur.fetchall()
    except psycopg2.ProgrammingError:
        rows = []
    cur.close()
    conn.close()
    return rows

def kpi_top_root_causes():
    query = """
        SELECT category, COUNT(*) AS issue_count
        FROM tickets
        WHERE status='open'
        GROUP BY category
        ORDER BY issue_count DESC
        LIMIT 5;
    """
    return sql_query(query)

# Vector DB (Chroma)
@st.cache_resource
def load_vector_db():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # rebuild เมื่อ KB ใหม่กว่า index เดิม
    latest_md = 0
    md_files = [f for f in os.listdir(KB_DIR) if f.endswith(".md")]
    if md_files:
        latest_md = max(os.path.getmtime(os.path.join(KB_DIR, f)) for f in md_files)

    need_build = (not os.path.exists(DB_DIR)) or (
        latest_md and os.path.getmtime(DB_DIR) < latest_md
    )

    if need_build:
        loader = DirectoryLoader(KB_DIR, glob="*.md", show_progress=True)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = splitter.split_documents(docs)
        db = Chroma.from_documents(
            chunks, embeddings, persist_directory=DB_DIR, collection_name=COLLECTION
        )
        db.persist()
    else:
        db = Chroma(
            persist_directory=DB_DIR,
            embedding_function=embeddings,
            collection_name=COLLECTION,
        )
    return db

def force_rebuild_vectordb():
    """เคลียร์ cache แล้วบังคับ rebuild จากไฟล์ใน KB_DIR"""
    st.cache_resource.clear()
    _ = load_vector_db()
    return True

# Knowledge Search (RAG)
def kb_search(question: str):
    llm = Ollama(model="llama3:8b")
    vectordb = load_vector_db()
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
    )
    out = qa({"query": question})
    sources = [d.metadata.get("source", "") for d in out.get("source_documents", [])]
    return out["result"], sources

# NL-SQL
def natural_to_sql(question: str) -> str:
    llm = Ollama(model="llama3:8b")
    prompt = f"""
You convert natural language to a SINGLE-LINE PostgreSQL SELECT.
Constraints:
- Use ONLY these tables & columns:
  customers(id, name, segment, joined_at);
  tickets(id, customer_id, product, category, issue, status, created_at);
  products(id, name, category, release_date).
- NO JOINs, NO subqueries, NO functions, NO CTEs.
- WHERE must use simple conditions (=, ILIKE '%...%', BETWEEN, AND/OR).
- LIMIT 100 if result could be large.
- Output SQL only (no prose, no code fences).

Question: {question}
""".strip()
    sql_text = llm(prompt).strip()
    sql_text = sql_text.strip("`").replace("```sql", "").replace("```", "").strip()
    return sql_text

# ตัวตรวจ SQL
ALLOWED_TABLES = {"customers", "tickets", "products"}
def lint_sql_select(sql_text: str) -> bool:
    s = sql_text.strip().lower()
    if not s.startswith("select"):
        return False
    if any(bad in s for bad in [" join ", " union ", " except ", " intersect ", ";", "--", "/*", "*/", " drop ", " delete "]):
        return False
    if " from " not in s:
        return False
    table = s.split(" from ", 1)[1].split()[0].strip().strip('"')
    return table in ALLOWED_TABLES

# Router Explain
def explain_routing(question: str, tool: str) -> str:
    q = question.lower()
    # rules เร็วและชัด
    if any(x in q for x in ["known issue", "version", "release", "policy", "document", "privacy", "patch", "fixes", "changelog"]):
        return "Keyword match → documentation/policy query → route to kb.search."
    if any(x in q for x in ["root cause", "trend", "top", "summary", "count", "kpi"]):
        return "Keyword match → aggregation insight → route to kpi.top_root_causes."
    if "select" in q or " from " in q or "sql" in q:
        return "Looks like SQL or data-retrieval → route to sql.query."

    # ถ้าไม่เข้า rules ให้ LLM อธิบาย
    llm = Ollama(model="llama3:8b")
    p = f"Question: {question}\nChosen tool: {tool}\nExplain briefly in one sentence why this tool fits."
    return llm(p).strip()

# Streamlit UI
st.set_page_config(page_title="Deep Insights Copilot", layout="wide")
st.title("Deep Insights Copilot")

tab_ask, tab_sql, tab_kb = st.tabs(["Ask Copilot", "SQL Playground", "Knowledge Upload"])

# Ask Copilot
with tab_ask:
    query = st.text_area(
    label="Ask a question",
    value="",
    placeholder="Ask anything",
    label_visibility="collapsed",
    height=120,
    key="ask_input",
)

    col1, col2 = st.columns([1,1])
    with col1:
        ask = st.button("Run", use_container_width=True)
    with col2:
        show_explain = st.toggle("Explain Mode", value=True)

    if ask:
        tool = choose_tool(query)
        st.write(f"Selected tool: **{tool}**")

        # อธิบายเหตุผล
        if show_explain:
            st.caption(explain_routing(query, tool))

        # รันตามเครื่องมือที่เลือก
        if tool == "sql.query":
            sql_text = query if query.lower().lstrip().startswith("select") else natural_to_sql(query)
            if not lint_sql_select(sql_text):
                st.warning("Generated SQL is not allowed (joins/functions/unknown table). Routing to kb.search instead.")
                answer, sources = kb_search(query)
                st.write(answer)
                st.caption("Sources: " + (", ".join(sources) if sources else "(none)"))
            else:
                st.code(sql_text, language="sql")
                result = safe_execute(sql_query, sql_text)
                try:
                    import pandas as pd
                    st.dataframe(pd.DataFrame(result), use_container_width=True)
                except Exception:
                    st.write(result)

        elif tool == "kpi.top_root_causes":
            import pandas as pd
            rows = kpi_top_root_causes()
            df = pd.DataFrame(rows, columns=["category", "issue_count"])
            st.dataframe(df, use_container_width=True)

        elif tool == "kb.search":
            import traceback
            with st.spinner("Searching knowledge base..."):
                try:
                    answer, sources = kb_search(query)
                    if not answer or answer.strip().lower() in {"i don't know", "idk"}:
                        st.warning("No confident answer from KB. Try rephrasing or rebuild the KB index.")
                    else:
                        st.write(answer)
                    st.caption("Sources: " + (", ".join(sources) if sources else "(none)"))
                except Exception as e:
                    st.error("kb.search failed. See details below.")
                    st.exception(e)
        else:
            st.warning("No valid tool matched.")

# SQL Playground
with tab_sql:
    st.subheader("Run read-only SQL")
    sql_text = st.text_area(
        label="SQL",
        value="",
        placeholder="Ask anything",
        height=150,
        key="sql_playground_input",
    )
    if st.button("Execute SQL", type="primary"):
        st.code(sql_text, language="sql")
        result = safe_execute(sql_query, sql_text)  # guardrail ป้องกัน DROP/DELETE
        try:
            import pandas as pd
            df = pd.DataFrame(result)
            st.dataframe(df, use_container_width=True)
        except Exception:
            st.write(result)


# Knowledge Upload
with tab_kb:
    st.subheader("Upload Markdown files to Knowledge Base")
    st.caption("รองรับไฟล์ .md เท่านั้น (หลีกเลี่ยง .pdf เพื่อไม่เพิ่ม dependencies)")
    uploaded = st.file_uploader("Upload .md files", type=["md"], accept_multiple_files=True)

    if uploaded:
        saved = []
        for f in uploaded:
            path = os.path.join(KB_DIR, f.name)
            with open(path, "wb") as out:
                out.write(f.read())
            saved.append(path)
        st.success(f"Saved {len(saved)} file(s): " + ", ".join(os.path.basename(p) for p in saved))
        if st.button("Rebuild Vector DB"):
            force_rebuild_vectordb()
            st.success("Rebuilt Vector DB from latest markdown files.")

# Sidebar info
with st.sidebar:
    st.header("Available MCP Tools")
    st.markdown("- `sql.query` — Read-only SQL / Data")
    st.markdown("- `kb.search` — Knowledge search (RAG)")
    st.markdown("- `kpi.top_root_causes` — KPI aggregation")
    if st.button("Clear KB Cache"):
        st.cache_resource.clear()
        st.success("Cache cleared. It will rebuild on next query.")
