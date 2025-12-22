# **Deep Insights Copilot**

AI Copilot
ระบบช่วยตอบคำถามจากข้อมูล (SQL + Docs) ด้วยภาษาธรรมชาติ
พร้อมระบบ Guardrail ปลอดภัย และรองรับการเรียกใช้งานผ่าน MCP Tools

ระบบนี้สามารถ:

- ตอบคำถามเชิงข้อมูลจาก Knowledge Base (markdown docs)
- รันคำสั่ง SQL หรือ KPI Aggregation ได้อย่างปลอดภัย
- วิเคราะห์คำถามและเลือกว่าใช้ Tool ไหนอัตโนมัติผ่าน `router.py`

## Key Features

**Natural Language Q&A** ถามคำถามเป็นภาษาอังกฤษ เช่น “What are the known issues in version 1.2?”  
**KPI & Trend Analytics** แสดง top root causes ของ ticket ล่าสุด  
**MCP Tool Routing** แยกอัตโนมัติระหว่าง `sql.query`, `kb.search`, `kpi.top_root_causes`  
**Knowledge Search (RAG)** ดึงข้อมูลจากไฟล์ markdown ใน `knowledge_base`  
**Safe SQL Guardrail** บล็อก DROP / UPDATE / DELETE / TRUNCATE  
**LLM Model** ใช้ `Ollama (Llama3:8b)` ประมวลผลภาษาธรรมชาติ  
**Vector Database** ใช้ `Chroma` + `HuggingFaceEmbeddings` (MiniLM-L6-v2)  
**Streamlit UI (Pro)** มี 3 แท็บ: Ask Copilot / SQL Playground / KB Upload  
**Docker-ready** ตั้งค่าผ่าน `.env` ได้ รองรับ containerization

## MCP Tools

**sql.query run SQL** (read-only)  
**kb.search QA** ผ่าน VectorDB  
**kpi.top_root_causes** วิเคราะห์ KPI

PostgreSQL + Chroma (Structured + Docs DB)

## โครงสร้างไฟล์

**deep_insights_copilot**  
**app.py** Main Streamlit App  
**router.py** Route query ไปยัง MCP tools  
**guardrail.py** ป้องกัน SQL ที่ไม่ปลอดภัย  
**build_vector_db.py** สร้าง Chroma จาก knowledge base  
**knowledge_base** Markdown files เช่น known_issues.md, policies.md  
**chroma_db** VectorDB ที่สร้างจาก build_vector_db.py  
**init.sql** สร้างตารางจำลอง (customers, tickets, products)  
**requirements.txt** Python dependencies  
**README.md**

## MCP Tools

**Tool** หน้าที่ ตัวอย่างคำถาม  
**sql.query** รันคำสั่ง SQL แบบอ่านอย่างเดียว “Show open tickets by product”  
**kpi.top_root_causes** รวม top issue ตาม category “Top 5 root causes of product issues last month”  
**kb.search** ดึงข้อมูลจาก Knowledge Base “What are the known issues in version 1.2?”

## AI Guardrails

**SQL Safety** บล็อก DROP, DELETE, UPDATE, ALTER, TRUNCATE  
**Read-only DB** ใช้ psycopg2 แบบไม่แก้ไขข้อมูล  
**PII Masking (optional)** สามารถเพิ่มการ mask email / phone  
**Execution Wrapper** ทุกคำสั่งผ่าน safe_execute() เพื่อ log และ validate

## ตัวอย่าง guardrail.py

```
forbidden = ["drop", "delete", "alter", "insert", "update", "truncate"]
pattern = "|".join(fr"\b{w}\b" for w in forbidden)
if re.search(pattern, query.lower()):
    return "Unsafe SQL detected. Execution blocked."
```

## วิธีใช้งาน

ติดตั้ง Ollama และโมเดล

```
ollama pull llama3:8b
```

รันระบบ

```
docker-compose up --build
```

ติดตั้งแพ็กเกจ

```
pip install -r requirements.txt
```

สร้างฐานข้อมูล

```
psql -U postgres -f init.sql
```

สร้างฐานความรู้

```
python build_vector_db.py
```

รันแอป

```
streamlit run app.py
```

จากนั้นเปิดเบราว์เซอร์ที่ http://localhost:8501

## Known Issues - Virtual Bank App v1.2

- Login crash occurs on some Android 14 devices.
- OTP verification delay (up to 15 seconds).
- Dashboard display glitch after midnight transactions.

## Recommendations

- Patch 1.2.1 fixes the OTP delay issue.
- Patch 1.2.2 addresses UI glitches.

## Explain Mode

เปิด “Explain Mode” เพื่อดูว่าทำไมระบบถึงเลือก tool นั้น:  
Keyword match → documentation/policy query → route to kb.search.

## Tech Stack

UI = Streamlit  
LLM = Ollama (Llama3 8B)  
Vector DB = Chroma  
Embedding = all-MiniLM-L6-v2  
DB = PostgreSQL  
Routing = MCP tool abstraction  
Guardrail = Regex-based SQL protection

## Deliverables

- Streamlit UI พร้อม 3 Tabs (Ask / SQL / KB Upload)
- 3 MCP Tools: sql.query, kb.search, kpi.top_root_causes
- Guardrail ปลอดภัย (Read-only + Log)
- Chroma VectorDB จาก markdown docs
- Docker-ready, ใช้งานใน local ได้ทันที

## output

[here](output.pdf)
