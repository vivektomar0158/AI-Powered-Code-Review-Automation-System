import logging
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
from app.services.embedding_service import embedding_service
from app.db.session import async_session_maker
from app.models.pattern import Pattern
from sqlalchemy import select

logger = logging.getLogger(__name__)

class PatternMatcher:
    def __init__(self):
        self.pc = None
        self.index = None
        if settings.PINECONE_API_KEY:
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            self._ensure_index()

    def _ensure_index(self):
        try:
            if settings.PINECONE_INDEX_NAME not in self.pc.list_indexes().names():
                # 768 dimensions for Gemini embeddings
                self.pc.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=768,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=settings.PINECONE_ENVIRONMENT
                    )
                )
            self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone index: {e}")

    async def find_similar(self, code_snippet: str, language: str, repo_id: int, top_k: int = 5) -> List[Dict[str, Any]]:
        """Find similar previously reviewed patterns."""
        if not self.index:
            return []

        embedding = await embedding_service.generate_embedding(code_snippet)
        if not embedding:
            return []

        try:
            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                filter={
                    "repo_id": repo_id,
                    "language": language
                }
            )
            
            patterns = []
            for match in results.matches:
                if match.score > 0.85:  # Similarity threshold
                    patterns.append(match.metadata)
                    
            return patterns
        except Exception as e:
            logger.error(f"Pinecone query failed: {e}")
            return []

    async def store_pattern(self, repo_id: int, pattern_type: str, code: str, description: str, language: str) -> str:
        """Store a new pattern in Pinecone and PostgreSQL."""
        if not self.index:
            return ""

        embedding = await embedding_service.generate_embedding(code)
        if not embedding:
            return ""

        vector_id = f"repo_{repo_id}_{hash(code)}"
        
        # 1. Store in Pinecone
        try:
            self.index.upsert(
                vectors=[
                    {
                        "id": vector_id,
                        "values": embedding,
                        "metadata": {
                            "repo_id": repo_id,
                            "pattern_type": pattern_type,
                            "description": description,
                            "language": language,
                            "positive_votes": 0,
                            "negative_votes": 0
                        }
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Pinecone upsert failed: {e}")
            return ""

        # 2. Store in PostgreSQL
        try:
            async with async_session_maker() as session:
                new_pattern = Pattern(
                    repository_id=repo_id,
                    pattern_type=pattern_type,
                    description=description,
                    example_code=code,
                    vector_id=vector_id,
                    language=language
                )
                session.add(new_pattern)
                await session.commit()
                return vector_id
        except Exception as e:
            logger.error(f"DB pattern insert failed: {e}")
            return ""

    async def update_votes(self, vector_id: str, accepted: bool):
        """Update the votes for a pattern when feedback is detected."""
        if not self.index:
            return

        try:
            # 1. Update DB
            async with async_session_maker() as session:
                stmt = select(Pattern).where(Pattern.vector_id == vector_id)
                result = await session.execute(stmt)
                pattern = result.scalar_one_or_none()
                
                if pattern:
                    if accepted:
                        pattern.positive_votes += 1
                    else:
                        pattern.negative_votes += 1
                    await session.commit()
                    
                    # 2. Sync to Pinecone
                    self.index.update(
                        id=vector_id,
                        set_metadata={
                            "positive_votes": pattern.positive_votes,
                            "negative_votes": pattern.negative_votes
                        }
                    )
        except Exception as e:
            logger.error(f"Failed to update votes for {vector_id}: {e}")

pattern_matcher = PatternMatcher()
