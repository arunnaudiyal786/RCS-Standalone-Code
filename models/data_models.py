from typing import List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from pydantic import BaseModel
from datetime import datetime


class QueryRefinementOutput(BaseModel):
    ticket_description: str
    incomplete_flag: bool
    reason: str
    confidence_score: float
    session_id: str
    timestamp: str
    refined_query: Optional[str] = None
    next_step: str

class InputTicket(BaseModel):
    """Immutable model for storing the original input ticket"""
    model_config = {"frozen": True}
    
    ticket_id: str
    ticket_description: str
    source: str = "user_input"
    timestamp: str
    priority: Optional[str] = None
    category: Optional[str] = None


class TicketRefinementOutput(BaseModel):
    """Output model for ticket refinement containing both original and refined tickets"""
    initial_ticket: InputTicket
    refined_ticket: str
    refinement_reason: str
    confidence_score: float
    session_id: str
    timestamp: str


class ReasoningStep(BaseModel):
    """Individual step in the reasoning solution plan"""
    step_number: int
    action_type: str  # INSERT, UPDATE, DELETE, VERIFY, CONFIGURE
    description: str
    target: str  # table/system/component to act on
    details: str  # specific parameters, values, conditions


class ReasoningOutput(BaseModel):
    """Output model for reasoning agent solution planning"""
    ticket_summary: str
    solution_steps: List[ReasoningStep]
    complexity_level: str  # Simple, Moderate, Complex
    estimated_time: str
    confidence_score: float
    session_id: str
    timestamp: str


class MessagesState(TypedDict):
    messages: List[HumanMessage | AIMessage | ToolMessage | SystemMessage]
    query_refinement_output: Optional[QueryRefinementOutput]
    input_ticket: Optional[InputTicket]
    ticket_refinement_output: Optional[TicketRefinementOutput]
    reasoning_output: Optional[ReasoningOutput]


class ResolutionStep(TypedDict):
    step_number: int
    description: str
    estimated_time: str


class ResolutionPlan(TypedDict):
    steps: List[ResolutionStep]
    priority: str
    complexity: str

     
class TicketAnalysis(TypedDict):
    ticket_id: str
    similarity_score: float
    resolution_approach: str


class ValidationResult(TypedDict):
    is_valid: bool
    confidence_score: float
    issues_found: List[str]
    recommendations: List[str]


class DomainSupervisorDecision(BaseModel):
    """Tracks domain supervisor task assignment decisions"""
    assigned_agent: str
    reasoning_step_numbers: List[int]
    assignment_reason: str
    session_id: str
    timestamp: str