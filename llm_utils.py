import os
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY)


def generate_answer(question, context_chunks):
    """Generate answer using Groq LLM"""
    
    context_parts = []
    for i, chunk in enumerate(context_chunks):
        page = chunk.chunk_index + 1
        context_parts.append(f"[Source {i+1}, Page {page}]\n{chunk.text_content}\n")
    
    context_text = "\n---\n".join(context_parts)
    
    system_prompt = """You are a helpful AI assistant that answers questions based on provided document excerpts.

Rules:
- Answer ONLY based on the provided sources
- If the answer isn't in the sources, say so clearly
- Be concise (2-4 sentences)
- Use natural language"""
    
    user_prompt = f"""Document excerpts:
{context_text}

Question: {question}

Answer based on the excerpts above:"""
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=800
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating answer: {str(e)}"


def generate_beneficial_analysis(text):
    """Generate document summary"""
    
    word_count = len(text.split())
    
    system_prompt = """You are a document analyst. Create a concise summary (3-4 sentences) of the document's main points."""
    
    user_prompt = f"""Summarize this document ({word_count} words):

{text}

Provide a clear 3-4 sentence summary:"""
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Document contains {word_count} words. Analysis failed: {str(e)}"