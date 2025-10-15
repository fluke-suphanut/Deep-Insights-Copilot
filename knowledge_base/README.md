# Line Chatbot with LangChain & Ollama

โปรเจคนี้เป็น **LINE Chatbot** ที่สามารถตอบกลับข้อความผู้ใช้ได้ทั้งข้อความปกติและข้อความที่อิงกับความรู้จากไฟล์เอกสาร (Text File) โดยใช้ **LangChain**, **Chroma Vectorstore**, และ **Ollama LLM (LLaMA 3.2)**

## Features

* ตอบข้อความทั่วไป เช่น `"ประวัติ"`, `"สถานที่ตั้ง"` ด้วยข้อความหรือ Location
* ตอบคำถามเชิงความรู้โดยดึงข้อมูลจากเอกสาร (`text02new.txt`) ผ่าน **LangChain RetrievalQA**
* ใช้ **ChromaDB** สำหรับ Vector Store
* ใช้ **Ollama LLM** (LLaMA 3.2 3B) เป็นตัวประมวลผลภาษา
* รองรับภาษาไทย

## Requirements

ติดตั้ง dependencies ด้วย `pip`

```bash
pip install flask line-bot-sdk werkzeug langchain langchain-community langchain-ollama chromadb
```

> ต้องติดตั้ง Ollama และโมเดล `llama3.2:3b` ไว้ในเครื่องก่อน
> [Ollama Download](https://ollama.ai/download)

## Environment Variables

ในโค้ดมีการกำหนดค่าไว้ตรงๆ (hard-coded) แต่แนะนำให้ซ่อน key ไว้ใน `.env` เช่น:

```env
CHANNEL_SECRET=your_line_channel_secret
CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
```

แล้วเรียกใช้ด้วย `os.getenv()`

## Running

ใช้ **ngrok** หรือ server ที่รองรับ HTTPS

```bash
ngrok http 5000
```

แล้วนำ URL ที่ได้ไปตั้งค่า **Webhook URL** ใน LINE Developer Console

## การใช้งาน

* พิมพ์ `"ประวัติ"` → จะได้ข้อความอธิบาย
* พิมพ์ `"สถานที่ตั้ง"` → จะได้ Location
* พิมพ์คำถามทั่วไป → Bot จะใช้ LangChain + Ollama หาคำตอบจาก `text02new.txt`

## Example

**User:** `"ภาควิชานี้ก่อตั้งปีไหน"`
**Bot:** `"ภาควิชาวิศวกรรมไฟฟ้า ก่อตั้งตั้งแต่ปี พ.ศ. 2550"`
