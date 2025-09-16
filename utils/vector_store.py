import os
import glob
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


class TableSchemaVectorStore:
    def __init__(self):
        """Initialize ChromaDB vector store for table schema descriptions."""
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            model="text-embedding-3-small"
        )
        self.vectorstore = None
        self._initialize_schema_store()
    
    def _initialize_schema_store(self):
        """Load and vectorize all table description files."""
        try:
            # Path to table description files
            table_desc_path = "/Users/arunnaudiyal/Arun/Deloitte/Tejas/RCS-Standalone-Code/data/table_description"
            
            # Load all table description files
            description_files = glob.glob(os.path.join(table_desc_path, "*.txt"))
            
            if not description_files:
                print(f"Warning: No table description files found in {table_desc_path}")
                return
            
            documents = []
            for file_path in description_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Extract table name from filename
                    table_name = os.path.basename(file_path).replace('_description.txt', '')
                    
                    # Create document with metadata
                    doc = Document(
                        page_content=content,
                        metadata={
                            "table_name": table_name,
                            "file_path": file_path,
                            "doc_type": "table_schema"
                        }
                    )
                    documents.append(doc)
                    
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
                    continue
            
            if documents:
                # Create FAISS vector store (more reliable than ChromaDB for this use case)
                self.vectorstore = FAISS.from_documents(
                    documents=documents,
                    embedding=self.embeddings
                )
                print(f"Initialized table schema vector store with {len(documents)} table descriptions")
            else:
                print("Warning: No valid table description documents found")
                
        except Exception as e:
            print(f"Error initializing table schema vector store: {e}")
    
    def search_relevant_schemas(self, query: str, k: int = 3, target_tables: str = None) -> List[Dict]:
        """
        Search for relevant table schemas based on query.
        
        Args:
            query: Search query describing the operation or requirement
            k: Number of results to return
            target_tables: Optional comma-separated list of specific tables to focus on
        
        Returns:
            List of dictionaries containing relevant table information
        """
        if not self.vectorstore:
            return [{
                "error": "Table schema vector store not initialized",
                "tables": [],
                "confidence_score": 0.0
            }]
        
        try:
            # Perform similarity search (FAISS doesn't support metadata filtering like ChromaDB)
            all_results = self.vectorstore.similarity_search_with_score(query, k=k*2)  # Get more results to filter
            
            # If target tables specified, filter results manually
            if target_tables:
                table_list = [t.strip().lower() for t in target_tables.split(',')]
                filtered_results = []
                for doc, score in all_results:
                    if doc.metadata.get("table_name", "").lower() in table_list:
                        filtered_results.append((doc, score))
                        if len(filtered_results) >= k:  # Limit to requested number
                            break
                results = filtered_results
            else:
                results = all_results[:k]  # Take first k results
            
            formatted_results = []
            for doc, score in results:
                # Parse the document content to extract structured information
                content = doc.page_content
                table_info = self._parse_table_description(content, doc.metadata["table_name"])
                table_info.update({
                    "relevance_score": float(1 - score),  # Convert distance to similarity
                    "search_query": query
                })
                formatted_results.append(table_info)
            
            return formatted_results
            
        except Exception as e:
            return [{
                "error": f"Error searching table schemas: {str(e)}",
                "tables": [],
                "confidence_score": 0.0
            }]
    
    def _parse_table_description(self, content: str, table_name: str) -> Dict:
        """
        Parse table description content into structured format.
        
        Args:
            content: Raw table description content
            table_name: Name of the table
        
        Returns:
            Structured dictionary with table information
        """
        try:
            lines = content.split('\n')
            parsed_info = {
                "table_name": table_name,
                "description": "",
                "columns": [],
                "business_rules": [],
                "relationships": [],
                "usage": []
            }
            
            current_section = None
            current_column = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Identify sections
                if line.startswith("DESCRIPTION:"):
                    current_section = "description"
                    continue
                elif line.startswith("COLUMNS:"):
                    current_section = "columns"
                    continue
                elif line.startswith("BUSINESS RULES:"):
                    current_section = "business_rules"
                    continue
                elif line.startswith("DATA RELATIONSHIPS:"):
                    current_section = "relationships"
                    continue
                elif line.startswith("USAGE:"):
                    current_section = "usage"
                    continue
                
                # Parse content based on current section
                if current_section == "description" and not line.startswith(("COLUMNS:", "BUSINESS")):
                    parsed_info["description"] += line + " "
                elif current_section == "columns":
                    if line and line[0].isdigit() and "." in line:
                        # New column definition
                        current_column = {"definition": line, "details": []}
                        parsed_info["columns"].append(current_column)
                    elif current_column and line.startswith("-"):
                        # Column detail
                        current_column["details"].append(line)
                elif current_section == "business_rules" and line.startswith("-"):
                    parsed_info["business_rules"].append(line[1:].strip())
                elif current_section == "relationships" and line.startswith("-"):
                    parsed_info["relationships"].append(line[1:].strip())
                elif current_section == "usage" and line.startswith("-"):
                    parsed_info["usage"].append(line[1:].strip())
            
            # Clean up description
            parsed_info["description"] = parsed_info["description"].strip()
            
            return parsed_info
            
        except Exception as e:
            return {
                "table_name": table_name,
                "description": f"Error parsing table description: {str(e)}",
                "columns": [],
                "business_rules": [],
                "relationships": [],
                "usage": [],
                "raw_content": content
            }


# Initialize vector stores
vector_store = TicketVectorStore()
table_schema_store = TableSchemaVectorStore()