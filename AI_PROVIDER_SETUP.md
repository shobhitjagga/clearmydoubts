# AI Provider Setup Guide

## Overview

The application now supports **both** OpenAI GPT-4 and Google Gemini for AI processing. You can switch between them using an environment variable.

## AI Provider Selection

Set the `AI_PROVIDER` environment variable to choose which AI provider to use:
- `gpt` (default) - Uses OpenAI GPT-4o for text and vision
- `gemini` - Uses Google Gemini 2.0 Flash

## Environment Variables

### For OpenAI (GPT-4):
```bash
OPENAI_API_KEY=your_openai_api_key
AI_PROVIDER=gpt  # or omit (defaults to gpt)
```

### For Google Gemini:
```bash
GEMINI_API_KEY=your_gemini_api_key
AI_PROVIDER=gemini
```

## Models Used

### OpenAI (GPT-4):
- **Text Generation**: `gpt-4o-mini` (cost-optimized, excellent quality)
- **Image Processing**: `gpt-4o` (with vision capabilities, images compressed before sending)
- **Embeddings**: `text-embedding-3-small` (768 dimensions - matches Gemini, cost-optimized)

### Google Gemini:
- **Text Generation**: `gemini-2.0-flash`
- **Image Processing**: `gemini-2.0-flash-vision-preview`
- **Embeddings**: `text-embedding-004` (768 dimensions)

## Important Notes

### Embedding Dimensions

✅ **Standardized**: Both OpenAI and Gemini now use **768 dimensions** for embeddings:
- **OpenAI**: `text-embedding-3-large` with `dimensions=768` parameter
- **Gemini**: `text-embedding-004` (native 768 dimensions)

This ensures compatibility with your Supabase vector tables. You can switch between AI providers without changing your database schema.

### Supabase Configuration

Your Supabase `match_vectors` function should use **768 dimensions**:

```sql
CREATE OR REPLACE FUNCTION public.match_vectors(
  query_embedding vector(768),
  match_count int
)
RETURNS TABLE (
  id uuid,
  question_text text,
  embedding vector,
  similarity float
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT
    q.id,
    q.question_text,
    q.embedding,
    1 - (q.embedding <=> query_embedding) AS similarity
  FROM public.questions q
  ORDER BY q.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

**Note**: If you have existing embeddings created with a different dimension, you'll need to regenerate them after switching providers.

## Features

Both providers support:
- ✅ Text question processing
- ✅ Image question extraction (handwritten text from images)
- ✅ RAG-based answer generation
- ✅ Embedding generation for vector search

## Switching Providers

To switch between AI providers, simply change the `AI_PROVIDER` environment variable:

```bash
# Use OpenAI GPT-4 (default)
export AI_PROVIDER=gpt
# or just omit the variable

# Use Google Gemini
export AI_PROVIDER=gemini
```

## Health Check

Visit `/health` endpoint to see which AI providers are configured:
```bash
curl https://your-app.onrender.com/health
```

Response includes:
```json
{
  "ai_provider": "gpt",
  "providers_configured": {
    "ai": {
      "gpt": true,
      "gemini": true
    }
  }
}
```

## Cost Considerations

- **OpenAI GPT-4o**: Generally more expensive, but very high quality
- **Google Gemini**: More cost-effective, good quality

You can switch providers based on your usage and budget needs.

## Troubleshooting

### OpenAI Errors
- Verify `OPENAI_API_KEY` is set correctly
- Check OpenAI API quota/limits
- Ensure you have access to GPT-4o model

### Gemini Errors
- Verify `GEMINI_API_KEY` is set correctly
- Check Gemini API quota/limits
- Ensure you have access to the vision model

### Embedding Dimension Mismatch
Both providers now use 768 dimensions, so this should not be an issue. If you see dimension errors:
1. Verify your Supabase `match_vectors` function uses `vector(768)`
2. Ensure your existing embeddings in the database are 768 dimensions
3. If you have old embeddings with different dimensions, regenerate them

## Testing

Test with a simple curl:
```bash
# Test with GPT-4 (default)
curl -X POST https://your-app.onrender.com/twilio-webhook \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+919876543210" \
  -d "Body=What is photosynthesis?" \
  -d "NumMedia=0"

# Switch to Gemini and test
export AI_PROVIDER=gemini
# Restart server and test again
```

## Code Structure

- `openai_utils.py` - OpenAI GPT-4 integration
- `gemini_utils.py` - Google Gemini integration (preserved)
- `main.py` - Unified interface that switches between providers

Both implementations use the same function signatures, making switching seamless.

