import logging
import numpy as np
import faiss
from typing import List, Tuple
from .embeddings import EmbeddingModel

logger = logging.getLogger(__name__)


class RAGRetriever:
    """RAG retriever using FAISS for similarity search"""

    def __init__(self, data_file: str, chunk_size: int = 300):
        """
        Initialize RAG retriever

        Args:
            data_file: Path to text file with knowledge base
            chunk_size: Maximum characters per chunk
        """
        self.chunk_size = chunk_size
        self.embedding_model = EmbeddingModel()
        self.chunks = []
        self.index = None

        logger.info(f"Loading data from {data_file}")
        self._load_and_index(data_file)

    def _load_and_index(self, data_file: str):
        """Load data file, split into chunks, and create FAISS index"""
        with open(data_file, 'r', encoding='utf-8') as f:
            text = f.read()

        # Simple chunking by paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        # Split large paragraphs if needed
        for para in paragraphs:
            if len(para) <= self.chunk_size:
                self.chunks.append(para)
            else:
                # Split by sentences (simple approach)
                sentences = para.split('. ')
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= self.chunk_size:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            self.chunks.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                if current_chunk:
                    self.chunks.append(current_chunk.strip())

        logger.info(f"Created {len(self.chunks)} chunks from data file")

        # Create embeddings
        embeddings = self.embedding_model.encode(self.chunks)
        embeddings_array = np.array(embeddings).astype('float32')

        # Create FAISS index
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)
        logger.info(f"FAISS index created with {self.index.ntotal} vectors")

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Retrieve most relevant chunks for a query

        Args:
            query: User query
            top_k: Number of top chunks to return

        Returns:
            List of (chunk_text, distance) tuples
        """
        logger.info(f"Retrieving top {top_k} chunks for query: {query}")

        # Create query embedding
        query_embedding = np.array([self.embedding_model.encode_single(query)]).astype('float32')

        # Search in FAISS index
        distances, indices = self.index.search(query_embedding, top_k)

        # Return results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            chunk_text = self.chunks[idx]
            results.append((chunk_text, float(distance)))
            logger.info(f"Found chunk (distance={distance:.4f}): {chunk_text[:100]}...")

        logger.info(f"Retrieved {len(results)} chunks total")
        return results

    def get_context(self, query: str, top_k: int = 3) -> str:
        """
        Get context string for LLM from retrieved chunks

        Args:
            query: User query
            top_k: Number of top chunks to retrieve

        Returns:
            Context string formatted for LLM
        """
        results = self.retrieve(query, top_k)
        context_parts = [chunk for chunk, _ in results]
        context = "\n\n".join(context_parts)
        return context
