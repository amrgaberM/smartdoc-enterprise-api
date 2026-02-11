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