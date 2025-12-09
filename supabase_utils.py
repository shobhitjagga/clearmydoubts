from supabase import create_client
import os

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def fetch_rag_context(question_embedding):
    response = supabase.rpc(
        "match_cbse_context",
        {
            "query_embedding": question_embedding,
            "match_count": 3
        }
    ).execute()

    chunks = []
    for row in response.data or []:
        if "content" in row:
            chunks.append(row["content"])
        else:
            # fallback if structure changes
            for key in ("text", "body", "doc", "chunk", "context"):
                if key in row:
                    chunks.append(row[key])
                    break

    return "\n\n".join(chunks)