import logging
from typing import List
from google import genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.client = None
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using Gemini text-embedding-004."""
        if not self.client:
            logger.error("Gemini API key not configured for embeddings.")
            return []
            
        try:
            response = await self.client.aio.models.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                contents=text,
            )
            return response.embeddings[0].values
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []

embedding_service = EmbeddingService()
