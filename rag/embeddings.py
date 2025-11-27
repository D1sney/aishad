import logging
from sentence_transformers import SentenceTransformer
from typing import List

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Wrapper for sentence-transformers embedding model"""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embedding model

        Args:
            model_name: Name of the sentence-transformers model
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully")

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for texts

        Args:
            texts: List of text strings

        Returns:
            List of embeddings
        """
        logger.debug(f"Encoding {len(texts)} texts")
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def encode_single(self, text: str) -> List[float]:
        """
        Create embedding for a single text

        Args:
            text: Text string

        Returns:
            Embedding vector
        """
        return self.encode([text])[0]
