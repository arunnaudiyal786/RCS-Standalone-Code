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
    solution_step: ReasoningStep  # Single step instead of multiple steps
    complexity_level: str  # Simple, Moderate, Complex
    estimated_time: str
    confidence_score: float
    session_id: str
    timestamp: str



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


class SimilarTicket(BaseModel):
    """Similar ticket information retrieved from vector store"""
    ticket_id: str
    similarity_score: float
    description: str
    resolution: str
    

class TableSchema(BaseModel):
    """Database table schema information"""
    table_name: str
    columns: List[str]
    business_rules: List[str]
    relationships: List[str]


class InfoRetrieverOutput(BaseModel):
    """Output model for Information Retrieval agent"""
    similar_tickets: List[SimilarTicket]
    table_schemas: List[TableSchema]
    analysis_summary: str
    recommendations: List[str]
    confidence_score: float
    session_id: str
    timestamp: str


class ExecutionStep(BaseModel):
    """Individual execution step result"""
    step_number: int
    action_type: str
    description: str
    status: str  # SUCCESS, FAILED, PENDING
    result: str
    error_message: Optional[str] = None


class ExecutionOutput(BaseModel):
    """Output model for Execution agent"""
    executed_steps: List[ExecutionStep]
    overall_status: str  # SUCCESS, FAILED, PARTIAL
    success_count: int
    failure_count: int
    execution_summary: str
    session_id: str
    timestamp: str


class ValidationIssue(BaseModel):
    """Individual validation issue found"""
    issue_type: str
    description: str
    severity: str  # HIGH, MEDIUM, LOW
    recommendation: str


class ValidationOutput(BaseModel):
    """Output model for Validation agent"""
    is_resolution_successful: bool
    confidence_score: float
    issues_found: List[ValidationIssue]
    validation_summary: str
    recommendations: List[str]
    next_steps: List[str]
    session_id: str
    timestamp: str


class ReportOutput(BaseModel):
    """Output model for Report agent"""
    ticket_id: str
    resolution_status: str  # RESOLVED, PARTIALLY_RESOLVED, FAILED
    resolution_summary: str
    steps_taken: List[str]
    time_to_resolution: str
    confidence_score: float
    lessons_learned: List[str]
    follow_up_actions: List[str]
    session_id: str
    timestamp: str


class TaskAssignment(BaseModel):
    """Individual task assignment by supervisor"""
    assigned_agent: str
    task_description: str
    reasoning_steps: List[int]
    priority: str  # HIGH, MEDIUM, LOW
    

class SupervisorOutput(BaseModel):
    """Output model for Supervisor agent"""
    workflow_status: str  # IN_PROGRESS, COMPLETED, FAILED
    current_phase: str
    task_assignments: List[TaskAssignment]
    completed_agents: List[str]
    next_agent: Optional[str] = None
    coordination_summary: str
    session_id: str
    timestamp: str


class SolutionState(TypedDict, total=False):
    messages: List[HumanMessage | AIMessage | ToolMessage | SystemMessage]
    query_refinement_output: Optional[QueryRefinementOutput]
    input_ticket: Optional[InputTicket]
    ticket_refinement_output: Optional[TicketRefinementOutput]
    reasoning_output: Optional[ReasoningOutput]
    info_retriever_output: Optional[InfoRetrieverOutput]
    execution_output: Optional[ExecutionOutput]
    validation_output: Optional[ValidationOutput]
    report_output: Optional[ReportOutput]
    supervisor_output: Optional[SupervisorOutput]