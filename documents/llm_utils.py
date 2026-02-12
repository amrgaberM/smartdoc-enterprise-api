import os
from groq import Groq

# It's best to put this in your docker-compose.yml environment variables!
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")

client = Groq(api_key=GROQ_API_KEY)

def generate_answer(question, context_chunks):
    """
    Takes a question and retrieved chunks, then generates an answer using Groq.
    """
    # Combine the chunks into a structured context block
    context_text = "\n\n".join([
        f"--- Snapshot {i+1} ---\n{chunk.text_content}" 
        for i, chunk in enumerate(context_chunks)
    ])
    
    system_prompt = (
        "You are the SmartDoc AI. You provide answers based strictly on the provided document snapshots. "
        "If the answer isn't in the snapshots, politely tell the user. "
        "Keep your answers concise, professional, and well-structured."
    )
    
    user_prompt = f"""
    DOCUMENT CONTEXT:
    {context_text}

    USER QUESTION: 
    {question}
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.2, # Low temperature = more factual, less creative
    )
    
    return chat_completion.choices[0].message.content

# --- ADD THIS FUNCTION BELOW ---
def generate_beneficial_analysis(text):
    """
    Generates 3 bullet points + a summary. 
    Protects against Context Window limits by truncating input.
    """
    # SAFETY CLIP: Limit to first 15,000 chars to prevent API crash
    safe_text = text[:15000] 

    system_prompt = (
        "You are an expert Document Analyst. "
        "Analyze the provided text and output a text block containing two sections: "
        "1. A 2-sentence summary. "
        "2. Three short, punchy bullet points highlighting key insights. "
        "Do not use JSON or complex formatting. Just plain text."
    )

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this:\n\n{safe_text}"}
            ],
            model="llama-3.3-70b-versatile", # Very fast, good for summaries
            temperature=0.5,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Could not generate insights: {str(e)}"