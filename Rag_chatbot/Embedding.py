import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

# ── 1. Load your CSV ──────────────────────────────────────────
df = pd.read_csv(
    "../data/text1.csv",
    quotechar='"',        # fields wrapped in quotes are treated as one
    quoting=0,            # QUOTE_MINIMAL
    engine="python",
    on_bad_lines="warn"   # shows which lines are bad instead of crashing
)

# Assumes columns are named 'context' and 'response'
# If named differently, change these strings to match exactly
contexts  = df["context"].astype(str).tolist()
responses = df["response"].astype(str).tolist()

print(f"Loaded {len(contexts)} rows")

# ── 2. Generate embeddings for context only ───────────────────
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding contexts...")
embeddings = model.encode(
    contexts,
    batch_size=64,
    show_progress_bar=True,
)
embeddings = embeddings.tolist()
# ── 3. Store in ChromaDB ──────────────────────────────────────
client     = chromadb.PersistentClient(path="../../chroma_db")
collection = client.get_or_create_collection(
    name="text1",
    metadata={"hnsw:space": "cosine"}   # cosine similarity works best here
)

collection.add(
    ids        = [f"doc_{i}" for i in range(len(contexts))],
    documents  = contexts,               # searchable text
    embeddings = embeddings,
    metadatas  = [{"response": r} for r in responses]  # payload returned at query time
)

print(f"✅ Stored {collection.count()} embeddings in ./chroma_db")