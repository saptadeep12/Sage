# 🌿 Sage — AI Therapy Chatbot

A warm, empathetic AI therapy assistant built with RAG (Retrieval Augmented Generation) 
that helps users navigate mental and emotional challenges in their day to day life.

---

## ✨ Features
- Empathetic AI therapist persona powered by Groq LLM
- RAG pipeline using ChromaDB for personalized, context-aware responses
- Real-time streaming responses (word by word, like ChatGPT)
- Conversation memory within a session
- Clean, minimal chat UI

---

## 🛠️ Tech Stack
| Layer | Technology |
|---|---|
| Backend | FastAPI |
| Vector DB | ChromaDB |
| Embeddings | SentenceTransformers (all-MiniLM-L6-v2) |
| LLM | Groq (openai/gpt-oss-120b) |
| Frontend | HTML, CSS, Vanilla JS |

# 📁 Project Structure

```text
Sage/
│
├── Rag_chatbot/
│   │
│   ├── templates/
│   │   └── chat_ui.html        # Chat interface
│   │
│   ├── backend.py              # FastAPI server + RAG logic
│   │
│   ├── Embedding.py            # Generates vector embeddings from CSV
│   │
│   ├── query.py                # Test retrieval from ChromaDB
│   │
│   ├── data/
│   │   └── text1.csv           # Dataset (context + response columns)
│   │
│   ├── chroma_db/              # Vector database
│   │   (auto-generated, not pushed)
│   │
│   ├── .env                    # API keys (not pushed)
│   │
│   ├── .gitignore
│   │
│   ├── requirements.txt
│   │
│   └── README.md

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/Sage.git
cd Sage
```

### 2. Create and activate virtual environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your API key
Create a `.env` file in the root:

Get a free key at [console.groq.com](https://console.groq.com)

### 5. Add your dataset
Place your CSV file in the `data/` folder. It must have two columns:

### 6. Generate embeddings (only needed once)
```bash
python Rag_chatbot/Embedding.py
```

### 7. Run the server
```bash
cd Rag_chatbot
python -m uvicorn backend:app --reload --port 5000
```

### 8. Open the chat UI
Visit **http://localhost:5000/ui** in your browser.

---

## ⚠️ Disclaimer
Sage is an AI assistant and is **not a replacement for professional mental health care**. 
If you are in crisis, please contact a mental health professional or crisis helpline immediately.

---

## 📄 License
MIT