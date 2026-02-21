import os
from dotenv import load_dotenv
from supabase import create_client
from sentence_transformers import SentenceTransformer

load_dotenv()

def main():
    print("Starting retrieval test...")

    sb = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"]
    )

    print("Loading embedding model...")
    embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print("Model loaded.")

    ##########
    query = "why did china dominate the 2008 olympics?"

    print("\nQuery:", query)

    # Embed the question
    query_embedding = embedder.encode(
        [query],
        normalize_embeddings=True
    )[0].tolist()

    print("Query embedding dimension:", len(query_embedding))

    # Call Supabase RPC function
    response = sb.rpc(
        "match_chunks",
        {
            "query_embedding": query_embedding,
            "match_count": 5
        }
    ).execute()

    print("\nTop matches:\n")

    for i, row in enumerate(response.data, start=1):
        print(f"{i}. [{row['title']}] similarity={row['similarity']:.4f}")
        preview = row["chunk_text"][:250].replace("\n", " ")
        print(f"   {preview}...\n")

if __name__ == "__main__":
    main()