"""Qdrant vector store manager for knowledge base search."""
import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter
from openai import OpenAI
from fastembed import TextEmbedding


QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
COLLECTION_NAME = "knowledge_base"

class VectorStore:
    """Manages Qdrant vector database for semantic search."""
    
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, 
                 collection_name: str = "knowledge_base"):
        """Initialize Qdrant client.
        
        Args:
            url: Qdrant cloud URL (defaults to QDRANT_URL env var)
            api_key: Qdrant API key (defaults to QDRANT_API_KEY env var)
            collection_name: Name of the collection to use
        """
        self.url = url or os.getenv("QDRANT_URL")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        self.collection_name = collection_name
        
        if not self.url or not self.api_key:
            print("Warning: Qdrant URL or API key not configured. Vector search won't work.")
            self.client = None
        else:
            try:
                self.client = QdrantClient(
                    url=self.url,
                    api_key=self.api_key,
                )
                self._initialize_collection()
                self.embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5") # fast + good demo choice
            except Exception as e:
                print(f"Error connecting to Qdrant: {e}")
                self.client = None
    
    def _initialize_collection(self):
        """Initialize collection if it doesn't exist."""
        if not self.client:
            return
        
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create collection with 1536 dimensions (OpenAI embedding size)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                )
                print(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            print(f"Error initializing collection: {e}")
    
    def search(self, query_vector: List[float], limit: int = 5, 
               score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity.
        
        Args:
            query_vector: Query embedding vector (1536 dimensions for OpenAI)
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of matching documents with scores
        """
        if not self.client:
            raise Exception("Qdrant client not initialized. Cannot search by vector.")
        
        try:
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )
            
            return [
                {
                    'id': point.id,
                    'score': point.score,
                    'payload': point.payload,
                }
                for point in results.points
            ]
        except Exception as e:
            print(f"Error searching Qdrant: {e}")
            raise Exception(f"Error searching Qdrant: {e}")
    
    def search_by_text(self, query_text: str, limit: int = 5, 
                       score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar documents using text query.
        
        Generates embeddings for the query text and performs vector similarity search.
        
        Args:
            query_text: Text query
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of matching documents
        """
        if not self.client:
            raise Exception("Qdrant client not initialized. Cannot search by text.")
        
        try:
            # Initialize OpenAI client
            openai_client = OpenAI()
            
            # Generate embeddings for the query text
            query_vector = next(self.embedder.embed([query_text]))
            
            # Perform vector search
            return self.search(query_vector, limit, score_threshold)
            
        except Exception as e:
            print(f"Error generating embeddings or searching: {e}")
            raise Exception(f"Error generating embeddings or searching: {e}")    
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection.
        
        Returns:
            Collection information dictionary
        """
        if not self.client:
            return {
                'status': 'disconnected',
                'message': 'Qdrant client not initialized'
            }
        
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'status': 'connected',
                'name': self.collection_name,
                'points_count': info.points_count,
                'vectors_count': info.vectors_count,
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

