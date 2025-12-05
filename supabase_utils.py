from supabase import create_client
import os

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Get RAG context from Supabase vector DB
def fetch_rag_context(question_embedding):
    response = supabase.rpc(
        "match_vectors",
        {
            "query_embedding": question_embedding,
            "match_count": 3
        }
    ).execute()

    chunks = [row["content"] for row in response.data]
    return "\n\n".join(chunks)