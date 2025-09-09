from typing import List, Dict
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config.settings import OPENAI_API_KEY


class TicketVectorStore:
    def __init__(self):
        # Initialize embeddings with environment variables
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            model="text-embedding-3-small"
        )
        
        # Create sample historical tickets
        sample_tickets = [
            "Login authentication failure - users unable to access system",
            "Database connection timeout errors in production environment",
            "Payment gateway integration returning 500 errors",
            "Email notification service not sending confirmations",
            "API rate limiting causing client timeouts",
            "SSL certificate expired causing HTTPS errors",
            "Memory leak in application server causing crashes",
            "Broken image uploads in user profile section",
            "Search functionality returning incorrect results",
            "Mobile app crashes on iOS devices during startup"
        ] * 100  # Simulate 1000 tickets
        
        # Create documents
        docs = [Document(page_content=ticket, metadata={"id": f"TICKET-{i+1}"}) 
                for i, ticket in enumerate(sample_tickets)]
        
        # Create FAISS vector store
        self.vectorstore = FAISS.from_documents(docs, self.embeddings)
    
    def search_similar_tickets(self, query: str, k: int = 10) -> List[Dict]:
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return [
            {
                "ticket_id": doc.metadata["id"],
                "content": doc.page_content,
                "similarity_score": float(score)
            }
            for doc, score in results
        ]


# Initialize vector store
vector_store = TicketVectorStore()