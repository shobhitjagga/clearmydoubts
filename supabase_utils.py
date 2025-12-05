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

    # Some RPC definitions return different column names; fall back gracefully.
    chunks = []
    for row in response.data or []:
        if "content" in row:
            chunks.append(row["content"])
        elif "question_text" in row:
            chunks.append(row["question_text"])
        else:
            # Capture any other text-like fields
            for key in ("text", "body", "doc"):
                if key in row:
                    chunks.append(row[key])
                    break
    return "\n\n".join(chunks)