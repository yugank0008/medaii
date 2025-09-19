import requests
import json
from typing import Optional
import os
from fastapi import HTTPException

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    def call_gemini(self, prompt: str) -> str:
        try:
            headers = {
                "Content-Type": "application/json",
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")
        except (KeyError, IndexError) as e:
            raise HTTPException(status_code=500, detail=f"Invalid response from Gemini API: {str(e)}")

# Initialize Gemini client
gemini_client = GeminiClient()

