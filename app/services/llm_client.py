import json
import logging
from typing import Optional, Dict, Any
import httpx
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Dual-provider LLM client with automatic failover.
    Primary: Gemini 2.0 Flash
    Fallback: OpenRouter free models
    """
    
    def __init__(self):
        self.gemini_client = None
        if settings.GEMINI_API_KEY:
            self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
        self.openrouter_api_key = settings.OPENROUTER_API_KEY
        self.openrouter_url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
        self.timeout = settings.AGENT_TIMEOUT_SECONDS

    async def analyze_code(self, prompt: str, system_prompt: str) -> Optional[Dict[str, Any]]:
        """Analyze code with fallback strategy."""
        
        # 1. Try Gemini first
        if self.gemini_client:
            try:
                result = await self._call_gemini(prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Gemini API failed: {e}. Falling back to OpenRouter.")
        
        # 2. Try OpenRouter fallback
        if self.openrouter_api_key:
            try:
                result = await self._call_openrouter(prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.error(f"OpenRouter API failed: {e}.")
                
        logger.error("All LLM providers failed for this request.")
        return None
        
    async def _call_gemini(self, prompt: str, system_prompt: str) -> Optional[Dict[str, Any]]:
        response = await self.gemini_client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        
        text = response.text
        if not text:
            return None
            
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Gemini JSON: {text[:100]}")
            return None

    async def _call_openrouter(self, prompt: str, system_prompt: str) -> Optional[Dict[str, Any]]:
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "AI Code Review Agent",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": settings.OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            # OpenRouter might not fully support response_format for all free models, 
            # but we can try enforcing it or instructing it in the prompt.
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.openrouter_url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse OpenRouter JSON: {content[:100]}")
                return None

llm_client = LLMClient()
