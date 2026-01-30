"""Qdrant vector store manager for knowledge base search."""
import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter


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
            return self._get_stub_results()
        
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )
            
            return [
                {
                    'id': hit.id,
                    'score': hit.score,
                    'payload': hit.payload,
                }
                for hit in results
            ]
        except Exception as e:
            print(f"Error searching Qdrant: {e}")
            return self._get_stub_results()
    
    def search_by_text(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using text query.
        
        Note: This is a stub that returns sample results. In production, you would:
        1. Generate embeddings for the query text using OpenAI embeddings API
        2. Call self.search() with the generated vector
        
        Args:
            query_text: Text query
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        # This is a stub implementation
        # In production, you would:
        # 1. from openai import OpenAI
        # 2. client = OpenAI()
        # 3. response = client.embeddings.create(input=query_text, model="text-embedding-ada-002")
        # 4. query_vector = response.data[0].embedding
        # 5. return self.search(query_vector, limit)
        
        return self._get_stub_results(query_text)
    
    def insert_documents(self, documents: List[Dict[str, Any]]):
        """Insert documents into the vector store.
        
        This is a stub for future implementation. In production, you would:
        1. Generate embeddings for each document
        2. Insert points into Qdrant with vectors and payloads
        
        Args:
            documents: List of documents with 'text' and metadata
        """
        if not self.client:
            print("Qdrant client not initialized. Cannot insert documents.")
            return
        
        # Stub implementation
        print(f"Stub: Would insert {len(documents)} documents into Qdrant")
        # In production:
        # 1. Generate embeddings for each document
        # 2. points = [PointStruct(id=idx, vector=vector, payload=doc) for idx, (vector, doc) in enumerate(embeddings_and_docs)]
        # 3. self.client.upsert(collection_name=self.collection_name, points=points)
    
    def _get_stub_results(self, query: str = "") -> List[Dict[str, Any]]:
        """Return stub/sample search results for testing.
        
        Args:
            query: Query text (used to customize stub results)
            
        Returns:
            List of sample documents
        """
        # Return sample knowledge base articles
        stub_results = [
            {
                'id': 1,
                'score': 0.92,
                'payload': {
                    'title': 'How to Track Your Order',
                    'content': 'You can track your order by using your order ID. Go to the order status page and enter your order number to see real-time tracking information.',
                    'category': 'shipping',
                    'url': '/help/track-order'
                }
            },
            {
                'id': 2,
                'score': 0.88,
                'payload': {
                    'title': 'Return Policy',
                    'content': 'We offer a 30-day return policy for all products. Items must be in original condition with tags attached. Shipping costs are non-refundable.',
                    'category': 'returns',
                    'url': '/help/return-policy'
                }
            },
            {
                'id': 3,
                'score': 0.85,
                'payload': {
                    'title': 'Shipping Options and Rates',
                    'content': 'We offer standard (5-7 days), express (2-3 days), and overnight shipping. Rates vary by weight and destination. Free shipping on orders over $50.',
                    'category': 'shipping',
                    'url': '/help/shipping-options'
                }
            },
            {
                'id': 4,
                'score': 0.82,
                'payload': {
                    'title': 'Payment Methods',
                    'content': 'We accept all major credit cards, PayPal, and Apple Pay. All transactions are secure and encrypted.',
                    'category': 'payment',
                    'url': '/help/payment-methods'
                }
            },
            {
                'id': 5,
                'score': 0.78,
                'payload': {
                    'title': 'Product Warranty Information',
                    'content': 'All products come with a 1-year manufacturer warranty. Extended warranties are available for purchase. Contact support for warranty claims.',
                    'category': 'warranty',
                    'url': '/help/warranty'
                }
            }
        ]
        
        # Filter results based on query keywords if provided
        if query:
            query_lower = query.lower()
            relevant_results = []
            for result in stub_results:
                content_lower = result['payload']['content'].lower()
                title_lower = result['payload']['title'].lower()
                if any(word in content_lower or word in title_lower for word in query_lower.split()):
                    relevant_results.append(result)
            
            if relevant_results:
                return relevant_results[:5]
        
        return stub_results[:5]
    
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

