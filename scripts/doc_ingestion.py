import os, glob
from supabase import create_client
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
load_dotenv()
def chunk_text(text, chunk_size = 1200, chunk_overlap =200):
    chunks = []
    step = chunk_size - chunk_overlap
    for i in range(0,len(text),step):
        chunk = text[i:i+chunk_size].strip()
        if chunk:
            chunks.append(chunk)
    return chunks

    # chunks = []
    # i = 0
    # chunks.append(text[i:i+chunk_size])
    # i+= chunk_size - chunk_overlap
    # chunks= []
    # for c in chunks:
    #     if c.strip():
    #         cleaned.append(c.strip())
    # return cleaned
    

def main():
    print("starting the ingestion")
    print("CWD:", os.getcwd())
    files = glob.glob("docs/*.txt")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if url is None or key is None:
        raise ValueError("Supabase credentialas are not found")
        

    print("SUPABASE_URL set:", bool(url))
    print("SUPABASE_SERVICE_KEY set:", bool(key))
    sb = create_client(url, key)
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    print("model loaded")
    for path in files:
        print("\nprocessing:", path)
        title = os.path.basename(path).replace(".txt", "")
        with open(path, "r") as f:
            text =f.read()
        print("Text length",len(text))
        doc_response = sb.table("documents").insert({
            "source": "local_docs",
            "title": title,
            "url": None
        }).execute()
        doc_id = doc_response.data[0]["id"]
        print("Inserted document ID:", doc_id)

        # Chunk text
        chunks = chunk_text(text)
        print("Number of chunks:", len(chunks))

        # Create embeddings
        embeddings = embedder.encode(chunks, normalize_embeddings=True)
        print("Embedding shape:", len(embeddings), "x", len(embeddings[0]))

        rows = []
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            rows.append({
                "document_id": doc_id,
                "chunk_text": chunk,
                "embedding": emb.tolist(),
                "metadata": {
                    "chunk_index": idx,
                    "path": path
                }
            })

        sb.table("chunks").insert(rows).execute()
        print(f"Inserted {len(rows)} chunks.")

    print("\nIngestion complete.")



if __name__ == "__main__":
    main()