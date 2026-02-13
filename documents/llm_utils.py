import os
from groq import Groq

# Read API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")

client = Groq(api_key=GROQ_API_KEY)

# ============================================================================
# ENHANCED ANSWER GENERATION (RAG)
# ============================================================================

def generate_answer(question, context_chunks):
    """
    Enhanced RAG answer generation with:
    - Better context structuring
    - Source awareness
    - Confidence indicators
    - Fallback handling
    """
    
    # Build enriched context with metadata
    context_parts = []
    for i, chunk in enumerate(context_chunks):
        # Extract metadata
        page = getattr(chunk, 'chunk_index', i) + 1
        similarity = 1 - float(getattr(chunk, 'distance', 0))
        
        context_parts.append(
            f"[SOURCE {i+1}] (Page {page}, Relevance: {similarity:.0%})\n"
            f"{chunk.text_content}\n"
        )
    
    context_text = "\n---\n".join(context_parts)
    
    # Enhanced system prompt
    system_prompt = """You are SmartDoc AI, an expert document analysis assistant.

YOUR CAPABILITIES:
- Provide accurate answers based strictly on the provided document excerpts
- Cite specific sources when making claims
- Acknowledge uncertainty when information is incomplete
- Explain complex concepts clearly and concisely

RESPONSE RULES:
1. Answer ONLY based on the provided sources
2. If the answer isn't in the sources, say "I don't have enough information in these excerpts to answer that question"
3. Use natural language - avoid robotic phrases like "according to the document"
4. Be concise but complete - aim for 2-4 sentences unless more detail is requested
5. When multiple sources agree, mention that for confidence
6. When sources conflict or are ambiguous, acknowledge this

CITATION STYLE:
- Reference sources naturally: "The text explains..." or "As mentioned in the excerpt..."
- Don't use formal citations like [1], [2] - keep it conversational
- For specific facts/numbers, briefly indicate which source (e.g., "The second excerpt mentions...")

TONE: Professional, helpful, and straightforward."""
    
    # User prompt with context
    user_prompt = f"""DOCUMENT EXCERPTS:
{context_text}

USER QUESTION:
{question}

Please provide a clear, accurate answer based on the excerpts above. If the information needed to answer isn't present, let me know."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,  # Low for factual accuracy
            max_tokens=800,   # Allow detailed answers
            top_p=0.9,        # Nucleus sampling for quality
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        return f"I encountered an error processing your question: {str(e)}. Please try again or rephrase your question."


# ============================================================================
# ENHANCED DOCUMENT ANALYSIS (SUMMARIZATION)
# ============================================================================

def generate_beneficial_analysis(text):
    """
    Enhanced document analysis with:
    - Specific, actionable insights
    - Document type identification
    - Key facts extraction
    - Concrete examples
    """
    
    # Safety clip to prevent API overload
    safe_text = text[:15000]
    
    # Word count for context
    word_count = len(safe_text.split())
    
    system_prompt = """You are an expert document analyst specializing in extracting actionable insights.

YOUR TASK:
Create a comprehensive analysis that helps users quickly understand:
1. What this document is about (specific, not generic)
2. What they can DO with this information (actionable insights)
3. What type of document this is

ANALYSIS STRUCTURE:

## Summary
Write 2-3 sentences that answer:
- What is this document? (Be specific - not just "a document about X")
- What's its purpose or main argument?
- Who is the target audience?

Include specific details: names, topics, techniques, frameworks mentioned.

## Key Insights
Provide 3-5 bullet points with:
- SPECIFIC, ACTIONABLE takeaways
- Concrete examples, numbers, or techniques when available
- Avoid generic statements like "important to understand"
- Each insight should teach something NEW

Good: "Temperature 0.2 produces consistent outputs for code generation; 0.8 enables creative variation"
Bad: "Temperature is an important parameter to consider"

## Document Type
Identify the document category:
- Technical Guide / Tutorial
- Research Paper / Study
- Business Report / Analysis
- Reference Manual / Documentation
- Policy Document / Legal Text
- Educational Material / Course Content
- Marketing / Sales Material
- Creative Writing / Literature
- Other: [specify]

QUALITY STANDARDS:
- Be SPECIFIC - avoid vague language
- Use CONCRETE details from the text
- Make insights ACTIONABLE
- Keep total length under 300 words
- Use clear, professional language"""

    user_prompt = f"""Analyze this document excerpt ({word_count} words):

{safe_text}

Provide a detailed analysis following the structure specified."""

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,      # Slightly higher for nuanced analysis
            max_tokens=1000,      # Allow detailed summaries
            top_p=0.95,
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"""## Summary
Analysis failed due to a technical error. The document contains {word_count} words of content.

## Key Insights
* Unable to generate insights due to: {str(e)}
* Please try re-analyzing the document
* If the error persists, the document may contain formatting issues

## Document Type
Unknown - Analysis incomplete"""


# ============================================================================
# UTILITY FUNCTION: VALIDATE CONTEXT QUALITY
# ============================================================================

def validate_context_quality(question, context_chunks):
    """
    Helper function to check if context is sufficient for answering.
    Returns (is_valid, reason) tuple.
    """
    if not context_chunks or len(context_chunks) == 0:
        return False, "No relevant content found in the document"
    
    # Check if chunks are too short
    total_chars = sum(len(chunk.text_content) for chunk in context_chunks)
    if total_chars < 50:
        return False, "Retrieved content is too brief to generate a meaningful answer"
    
    # Check similarity scores (distance should be < 0.5 for good matches)
    if hasattr(context_chunks[0], 'distance'):
        avg_distance = sum(float(chunk.distance) for chunk in context_chunks) / len(context_chunks)
        if avg_distance > 0.6:
            return False, "Retrieved content has low relevance to your question"
    
    return True, "Context is sufficient"


# ============================================================================
# OPTIONAL: MULTI-DOCUMENT ANSWER GENERATION
# ============================================================================

def generate_multi_document_answer(question, context_chunks):
    """
    Enhanced version for global_ask endpoint that handles multiple documents.
    Similar to generate_answer but optimized for cross-document queries.
    """
    
    # Group chunks by document
    docs_map = {}
    for chunk in context_chunks:
        doc_id = chunk.document.id
        doc_title = chunk.document.title
        
        if doc_id not in docs_map:
            docs_map[doc_id] = {
                'title': doc_title,
                'chunks': []
            }
        docs_map[doc_id]['chunks'].append(chunk)
    
    # Build context with document separation
    context_parts = []
    for doc_id, doc_data in docs_map.items():
        context_parts.append(f"\n{'='*60}\nDOCUMENT: {doc_data['title']}\n{'='*60}")
        
        for i, chunk in enumerate(doc_data['chunks']):
            page = chunk.chunk_index + 1
            similarity = 1 - float(chunk.distance)
            context_parts.append(
                f"\n[Excerpt {i+1}, Page {page}, Relevance: {similarity:.0%}]\n"
                f"{chunk.text_content}"
            )
    
    context_text = "\n".join(context_parts)
    
    system_prompt = """You are SmartDoc AI analyzing multiple documents simultaneously.

YOUR TASK:
Synthesize information from multiple document sources to provide comprehensive answers.

RESPONSE RULES:
1. Draw connections between documents when relevant
2. Mention which document(s) support each point
3. Highlight agreements or contradictions between sources
4. Maintain accuracy - only use information present in the excerpts
5. If documents don't contain the answer, clearly state this

CITATION STYLE:
- Reference documents by name: "According to [Document Name]..."
- Compare sources: "While Document A suggests X, Document B indicates Y..."
- Note consensus: "Multiple documents confirm that..."

TONE: Analytical, clear, and objective."""

    user_prompt = f"""DOCUMENTS ANALYZED: {len(docs_map)}

EXCERPTS FROM YOUR DOCUMENTS:
{context_text}

USER QUESTION:
{question}

Provide a comprehensive answer synthesizing information from these documents."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.25,
            max_tokens=1000,
            top_p=0.9,
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        return f"Error synthesizing answer from multiple documents: {str(e)}"