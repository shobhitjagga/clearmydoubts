"""
OpenAI GPT-4 integration for text and image processing
Optimized for cost efficiency
"""
import os
import base64
from io import BytesIO
from PIL import Image
from openai import OpenAI
from prompts import ANSWER_PROMPT

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def compress_image(img_bytes, max_size=(1024, 1024), quality=85):
    """
    Compress and resize image to reduce token usage.
    Reduces image size before sending to OpenAI API.
    """
    try:
        img = Image.open(BytesIO(img_bytes))
        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img
        # Resize if too large
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        # Compress
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"Image compression error: {e}, using original")
        return img_bytes


def create_embedding(text):
    """
    Generate OpenAI embedding for the input text.
    Uses text-embedding-3-small with 768 dimensions (cheaper than large).
    This ensures compatibility with Supabase vector tables.
    """
    response = client.embeddings.create(
        model="text-embedding-3-small",  # Cheaper than large, still high quality
        input=text,
        dimensions=768  # Match Gemini's embedding dimension
    )
    return response.data[0].embedding


def extract_question_from_image(img_bytes):
    """
    Extract handwritten question from image using GPT-4 Vision.
    Optimized: Compresses image before sending to reduce token usage.
    """
    # Compress image to reduce token usage
    compressed_img = compress_image(img_bytes, max_size=(1024, 1024), quality=85)
    
    # Convert image bytes to base64
    base64_image = base64.b64encode(compressed_img).decode('utf-8')
    
    response = client.chat.completions.create(
        model="gpt-4o",  # GPT-4 Omni supports vision (best for OCR)
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract the handwritten question from this image. Clean it up. Only return the question:"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "low"  # Use low detail to reduce tokens (sufficient for text extraction)
                        }
                    }
                ]
            }
        ],
        max_tokens=300  # Reduced from 500 - questions are usually short
    )
    
    return response.choices[0].message.content.strip()


def generate_answer(question, context):
    """
    Generate board-style answer using GPT-4o-mini (cheaper) with RAG context.
    GPT-4o-mini provides excellent quality at much lower cost.
    """
    filled_prompt = ANSWER_PROMPT.format(question=question, context=context)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Much cheaper than gpt-4o, still excellent quality
        messages=[
            {
                "role": "system",
                "content": "You are an expert CBSE board examiner for Class 10/12."
            },
            {
                "role": "user",
                "content": filled_prompt
            }
        ],
        temperature=0.7,
        max_tokens=1500  # Reduced from 2000 - sufficient for most answers
    )
    
    return response.choices[0].message.content.strip()

