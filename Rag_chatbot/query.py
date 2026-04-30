import chromadb
from sentence_transformers import SentenceTransformer

# Load existing DB — no re-embedding needed
client     = chromadb.PersistentClient(path="../../chroma_db")
collection = client.get_collection("text1")
model      = SentenceTransformer("all-MiniLM-L6-v2")

def retrieve(query, top_k=3):
    query_embedding = model.encode([query]).tolist()[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )   

    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "context":  results["documents"][0][i],
            "response": results["metadatas"][0][i]["response"],
            "score":    results["distances"][0][i]
        })
    return hits

# Test it
hits = retrieve("type your test question here")
for h in hits:
    print(f"Score   : {h['score']:.4f}")   # lower = more relevant
    print(f"Context : {h['context'][:100]}")
    print(f"Response: {h['response'][:100]}")
    print("---")