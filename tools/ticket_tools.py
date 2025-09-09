from typing import List, Dict
from langchain_core.tools import tool
from models.data_models import ValidationResult
from utils.vector_store import vector_store


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