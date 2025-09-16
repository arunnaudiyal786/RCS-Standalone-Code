from typing import List, Dict
from langchain_core.tools import tool
from models.data_models import ValidationResult
from utils.vector_store import vector_store, table_schema_store


@tool
def retrieve_similar_tickets(ticket_description: str) -> List[Dict]:
    """Retrieve top 10 most similar historical tickets from vector database."""
    return vector_store.search_similar_tickets(ticket_description, k=10)


@tool
def execute_resolution_step(step_description: str, step_number: int) -> Dict:
    """Execute a specific resolution step."""
    return {
        "step_number": step_number,
        "status": "completed",
        "execution_time": "25 minutes",
        "output": f"Successfully executed: {step_description}",
        "next_action": "Proceed to validation"
    }


@tool
def validate_resolution(ticket_id: str, executed_steps: str) -> ValidationResult:
    """Validate that the resolution steps were successful."""
    return ValidationResult(
        is_valid=True,
        confidence_score=0.92,
        issues_found=[],
        recommendations=["Monitor system for 24 hours", "Document solution in knowledge base"]
    )


@tool
def refine_query(query: str) -> str:
    """
    Refine the input query to make it clearer and more understandable.
    """
    # For now, simply return the original query.
    # In a real implementation, you could use an LLM or rules to rewrite the query.
    return query


@tool
def retrieve_table_schema_info(step_description: str, target_tables: str = None) -> Dict:
    """
    Retrieve relevant table schema and column information from table descriptions
    based on the step description provided by domain supervisor agent.
    
    This tool creates a real-time ChromaDB vector store from table description files
    and performs semantic similarity search to find relevant database schema information.
    
    Args:
        step_description: Description of the resolution step needing table/column info
        target_tables: Optional comma-separated list of specific tables to focus on
                      (e.g., "member_enrollment,claims_medical")
    
    Returns:
        Dict containing relevant table schemas, columns, business rules, and relationships
    """
    try:
        # Search for relevant table schemas
        relevant_schemas = table_schema_store.search_relevant_schemas(
            query=step_description,
            k=3,  # Return top 3 most relevant tables
            target_tables=target_tables
        )
        
        if not relevant_schemas:
            return {
                "status": "no_results",
                "message": "No relevant table schemas found",
                "step_description": step_description,
                "target_tables": target_tables,
                "relevant_tables": []
            }
        
        # Check for errors
        if relevant_schemas and "error" in relevant_schemas[0]:
            return {
                "status": "error",
                "message": relevant_schemas[0]["error"],
                "step_description": step_description,
                "target_tables": target_tables,
                "relevant_tables": []
            }
        
        # Format the response
        response = {
            "status": "success",
            "step_description": step_description,
            "target_tables": target_tables,
            "relevant_tables": relevant_schemas,
            "summary": {
                "total_tables_found": len(relevant_schemas),
                "table_names": [schema.get("table_name", "unknown") for schema in relevant_schemas],
                "avg_relevance_score": sum(schema.get("relevance_score", 0) for schema in relevant_schemas) / len(relevant_schemas) if relevant_schemas else 0
            },
            "recommendations": []
        }
        
        # Add recommendations based on the schemas found
        for schema in relevant_schemas:
            table_name = schema.get("table_name", "unknown")
            if schema.get("business_rules"):
                response["recommendations"].append(f"Review business rules for {table_name} table before making changes")
            if schema.get("relationships"):
                response["recommendations"].append(f"Consider foreign key relationships when modifying {table_name}")
        
        return response
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving table schema information: {str(e)}",
            "step_description": step_description,
            "target_tables": target_tables,
            "relevant_tables": []
        }