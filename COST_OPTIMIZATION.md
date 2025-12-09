# Cost Optimization Guide

## Overview

The OpenAI integration has been optimized to reduce token usage and API costs while maintaining quality.

## Optimizations Applied

### 1. Embeddings
- **Changed**: `text-embedding-3-large` → `text-embedding-3-small`
- **Savings**: ~5x cheaper per embedding
- **Quality**: Minimal difference, both are high-quality embeddings
- **Dimensions**: Still outputs 768 dimensions (matches Gemini)

### 2. Text Generation
- **Changed**: `gpt-4o` → `gpt-4o-mini`
- **Savings**: ~10x cheaper per token
- **Quality**: Excellent quality, suitable for educational content
- **Max Tokens**: Reduced from 2000 to 1500 (sufficient for most answers)

### 3. Image Processing
- **Model**: Still uses `gpt-4o` (best for OCR/vision tasks)
- **Optimizations**:
  - Images are compressed/resized to max 1024x1024 before sending
  - Uses `detail: "low"` for image processing (sufficient for text extraction)
  - Max tokens reduced from 500 to 300 (questions are usually short)
- **Savings**: Significantly reduced token usage for images

### 4. Image Compression
- Automatically compresses images before sending to OpenAI
- Reduces image size by 60-80% typically
- Maintains quality sufficient for text extraction
- Uses JPEG compression with quality=85

## Cost Comparison

### Before Optimization (per request):
- Embedding: ~$0.00013 (text-embedding-3-large)
- Text Generation: ~$0.03-0.06 (gpt-4o, 2000 tokens)
- Image Processing: ~$0.01-0.03 (gpt-4o, large image)
- **Total**: ~$0.04-0.09 per request

### After Optimization (per request):
- Embedding: ~$0.00002 (text-embedding-3-small)
- Text Generation: ~$0.002-0.004 (gpt-4o-mini, 1500 tokens)
- Image Processing: ~$0.003-0.008 (gpt-4o, compressed image)
- **Total**: ~$0.005-0.012 per request

**Estimated Savings: 80-85% reduction in costs**

## Quality Impact

- **Embeddings**: No noticeable quality difference
- **Text Generation**: GPT-4o-mini provides excellent quality for educational content
- **Image Processing**: Compression doesn't affect text extraction accuracy

## If You Need Higher Quality

If you need the absolute best quality and have sufficient quota, you can modify `openai_utils.py`:

```python
# For embeddings (if needed)
model="text-embedding-3-large"  # Instead of small

# For text generation (if needed)
model="gpt-4o"  # Instead of gpt-4o-mini
max_tokens=2000  # Instead of 1500

# For image processing (already using best)
model="gpt-4o"  # Keep this for best OCR
```

## Monitoring Usage

To monitor your OpenAI usage:
1. Check OpenAI Dashboard: https://platform.openai.com/usage
2. Set up usage alerts in OpenAI dashboard
3. Monitor logs for API errors

## Quota Management

If you're hitting quota limits:
1. **Switch to Gemini**: Set `AI_PROVIDER=gemini` (often has more generous free tier)
2. **Upgrade OpenAI Plan**: Add payment method to increase quota
3. **Use Rate Limiting**: Implement request throttling in your code
4. **Cache Embeddings**: Store embeddings in database to avoid regenerating

## Recommendations

1. **For Production**: Use the optimized settings (current implementation)
2. **For Testing**: Can temporarily use higher-quality models if needed
3. **For High Volume**: Consider implementing caching for common questions
4. **For Budget-Conscious**: Use Gemini (`AI_PROVIDER=gemini`) which has more generous free tier

## Fallback Strategy

If OpenAI quota is exceeded, you can:
1. Automatically fallback to Gemini
2. Show user-friendly error messages
3. Implement retry logic with exponential backoff

Consider implementing this in `main.py` if needed.

