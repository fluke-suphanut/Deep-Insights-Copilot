from langchain_community.llms import Ollama

# Router Configuration
PATCH_KEYWORDS = [
    "patch", "fix", "fixed", "bugfix", "release notes", "changelog",
    "version", "v1.", "v2.", "hotfix"
]

DOC_KEYWORDS = [
    "known issue", "policy", "document", "privacy", "manual",
    "guide", "specification", "user guide", "instruction", "compliance"
]

KPI_KEYWORDS = [
    "root cause", "trend", "top", "summary", "count", "kpi",
    "statistic", "most common", "frequent"
]

SQL_KEYWORDS = [
    "select", " from ", "sql", "query", "where", "group by"
]

# Core Function
def choose_tool(question: str) -> str:
    """เลือกเครื่องมือที่เหมาะสมตามคำถามของผู้ใช้"""
    q = question.lower().strip()

    if any(k in q for k in PATCH_KEYWORDS + DOC_KEYWORDS):
        return "kb.search"
    if any(k in q for k in KPI_KEYWORDS):
        return "kpi.top_root_causes"
    if any(k in q for k in SQL_KEYWORDS):
        return "sql.query"

    llm = Ollama(model="llama3:8b")
    prompt = f"""
You are a tool router. 
Available tools:
- sql.query → When user wants to query or view data from the database.
- kpi.top_root_causes → When user wants insights, trends, or root causes.
- kb.search → When user asks about documents, patches, product info, or policies.

Reply with ONLY one of:
sql.query, kpi.top_root_causes, kb.search

Question: {question}
""".strip()

    try:
        tool = llm(prompt).strip().lower()
        for name in ["sql.query", "kpi.top_root_causes", "kb.search"]:
            if name in tool:
                return name
    except Exception:
        pass

    return "kb.search"

# Optional: Debug Explanation
def explain_rule_match(question: str) -> str:
    """คืนคำอธิบายว่าติด rule ไหน (ใช้ใน Explain Mode หรือ debug)"""
    q = question.lower()
    if any(k in q for k in PATCH_KEYWORDS):
        return "Keyword match → patch/release context → route to kb.search."
    if any(k in q for k in DOC_KEYWORDS):
        return "Keyword match → documentation/policy → route to kb.search."
    if any(k in q for k in KPI_KEYWORDS):
        return "Keyword match → KPI or trend → route to kpi.top_root_causes."
    if any(k in q for k in SQL_KEYWORDS):
        return "Keyword match → SQL or database query → route to sql.query."
    return "No explicit rule matched → fallback to LLM reasoning (llama3)."
