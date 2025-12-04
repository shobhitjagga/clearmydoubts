import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Extract handwritten question from image
def extract_question_from_image(img_bytes):
    model = genai.GenerativeModel("gemini-2.0-flash-vision-preview")
    response = model.generate_content(
        ["Extract the handwritten question from this image. Clean it up. Only return the question:", img_bytes]
    )
    return response.text.strip()


# Generate board-style answer using RAG + prompt
def generate_answer(question, context):
    model = genai.GenerativeModel("gemini-2.0-flash")
    filled_prompt = ANSWER_PROMPT.format(question=question, context=context)
    response = model.generate_content(filled_prompt)
    return response.text.strip()
