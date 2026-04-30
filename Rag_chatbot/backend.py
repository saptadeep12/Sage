from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from fastapi.responses import FileResponse, StreamingResponse
from sentence_transformers import SentenceTransformer
import requests
import json
from dotenv import load_dotenv
import os

app = FastAPI()

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load once at startup ──────────────────────────────────────
chroma_client = chromadb.PersistentClient(path="../../chroma_db")
collection     = chroma_client.get_collection("text1")
embed_model    = SentenceTransformer("all-MiniLM-L6-v2")

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")   # ← paste new key here
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
chat_history = []

class SourceItem(BaseModel):
    context: str
    response: str
    score: float

class ChatRequest(BaseModel):
    message: str
    top_k: int = 3

class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]

# ── Retrieval helper ──────────────────────────────────────────
def retrieve(query: str, top_k: int = 3) -> list[SourceItem]:
    query_embedding = embed_model.encode([query]).tolist()[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    hits = []
    for i in range(len(results["ids"][0])):
        hits.append(SourceItem(
            context=results["documents"][0][i],
            response=results["metadatas"][0][i]["response"],
            score=results["distances"][0][i]
        ))
    return hits

# ── Groq API call ─────────────────────────────────────────────
def call_groq(system_prompt: str, user_message: str) -> str:
    payload = json.dumps({
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ],
        "model": "openai/gpt-oss-120b",
        "temperature": 0.8,
        "max_completion_tokens": 600,
        "top_p": 1,
        "stream": True,
        "reasoning_effort": "medium",
        "stop": None
    })
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    response = requests.post(GROQ_URL, headers=headers, data=payload)
    data = response.json()

    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    else:
        raise HTTPException(status_code=500, detail=f"Groq API error: {data}")

# ── Routes ────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "RAG backend is running"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "documents_in_db": collection.count()
    }

@app.get("/ui")
def serve_ui():
    return FileResponse(os.path.join(BASE_DIR, "templates", "chat_ui.html"))

@app.post("/chat")
def chat(req: ChatRequest):
    global chat_history

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    hits = retrieve(req.message, top_k=req.top_k)
    context_block = "\n\n".join(
        [f"Context: {h.context}\nResponse: {h.response}" for h in hits]
    )

    system_prompt = (
        "You are Sage, a warm, empathetic and non-judgmental AI therapy assistant. "
        "Your role is to support users through the mental and emotional challenges "
        "they face in their day to day life. You listen deeply, validate feelings, "
        "and guide users with compassion and care"
        "You responses should be Warm, calm, and deeply empathetic.\n\n"

        "## How You Respond\n"
        "- Always acknowledge the user's feelings before offering advice\n"
        "- Keep your entire response to 5-6 sentences maximum\n"
        "- End every response with either a complete thought or a gentle question\n"
        "- Use the context provided to give personalized, relevant guidance\n"
        "- Keep responses concise — avoid overwhelming the user with long replies\n"
        "- Use simple, human language — never clinical or robotic\n\n"
        "- Never leave a sentence unfinished\n\n"
        "- Never force a question at the end just to fill space\n\n"
        
        # "## What You Help With\n"
        # "- Stress, anxiety, and overthinking\n"
        # "- Loneliness and relationship struggles\n"
        # "- Low motivation and self-doubt\n"
        # "- Grief, loss, and difficult life transitions\n"
        # "- Building healthy habits and emotional resilience\n\n"

        "## Hard Rules\n"
        "- Never diagnose any mental health condition\n"
        "- Never prescribe or recommend medication\n"
        "- If the user expresses thoughts of self-harm or suicide, "
        "immediately and compassionately encourage them to contact a "
        "crisis helpline or mental health professional\n"
        "- Always remind users you are an AI and not a replacement "
        "for professional therapy when the topic is serious\n\n"

        "## Context from Knowledge Base\n"
        "Use the context below to inform and personalize your responses. "
        "If the context is not relevant to what the user is saying, rely "
        "on your empathetic judgment instead.\n\n"
        f"{context_block}"




    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": req.message})


    def stream_response():
        global chat_history
        full_answer = ""

        with requests.post(
                GROQ_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GROQ_API_KEY}"
                },
                data=json.dumps({
                    "messages": messages,
                    "model": "openai/gpt-oss-120b",
                    "temperature": 0.6,
                    "max_completion_tokens": 300,
                    "top_p": 1,
                    "reasoning_effort": "medium",
                    "stream": True,  # ← enable streaming
                    "stop": None
                }),
                stream=True
        ) as r:
            for line in r.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                if line == "[DONE]":
                    break
                try:
                    chunk = json.loads(line)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        full_answer += delta
                        yield f"data: {json.dumps({'token': delta})}\n\n"
                except Exception:
                    continue

        # Save to history after streaming completes
        chat_history.append({"role": "user", "content": req.message})
        chat_history.append({"role": "assistant", "content": full_answer})
        chat_history = chat_history[-10:]

        # Signal done
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

    # answer = call_groq(system_prompt, req.message)
    #
    # return ChatResponse(answer=answer, sources=hits)

# python -m uvicorn backend:app --reload --port 5000