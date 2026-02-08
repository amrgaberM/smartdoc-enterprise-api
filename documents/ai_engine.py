import os
from PyPDF2 import PdfReader
from django.conf import settings

class AIEngine:
    
    @staticmethod
    def extract_text(file_path):
        """
        Opens a PDF file from the hard drive and returns the text.
        """
        try:
            # 1. Open the file
            reader = PdfReader(file_path)
            text = ""
            
            # 2. Read every page
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    @staticmethod
    def analyze(text):
        """
        SIMULATED AI: In the future, we call OpenAI/DeepSeek here.
        For now, we use a simple rule-based mock to prove it works.
        """
        word_count = len(text.split())
        
        # Simple "Mock" Analysis Logic
        summary = f"This document contains {word_count} words."
        
        if "invoice" in text.lower():
            sentiment = "Financial"
            summary += " It appears to be a financial document."
        elif "contract" in text.lower():
            sentiment = "Legal"
            summary += " It appears to be a legal contract."
        else:
            sentiment = "General"
            summary += " It appears to be a general text."

        return {
            "summary": summary,
            "sentiment": sentiment,
            "confidence": 0.95
        }