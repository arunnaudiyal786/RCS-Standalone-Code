from pydantic import BaseModel, Field
from typing import List
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage


class MessagesState(TypedDict):
    messages: List[HumanMessage | AIMessage | ToolMessage | SystemMessage]


class ResolutionStep(BaseModel):
    step_number: int
    description: str
    estimated_time: str


class ResolutionPlan(BaseModel):
    steps: List[ResolutionStep]
    priority: str
    complexity: str


class TicketAnalysis(BaseModel):
    ticket_id: str
    similarity_score: float
    resolution_approach: str


class ValidationResult(BaseModel):
    is_valid: bool
    confidence_score: float
    issues_found: List[str]
    recommendations: List[str]