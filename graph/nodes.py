import json
import os
import uuid
from datetime import datetime
from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from models.data_models import MessagesState, QueryRefinementOutput, InputTicket, TicketRefinementOutput, ReasoningOutput, ReasoningStep
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
from config.constants import REASONING_AGENT


def pattern_analysis(state: MessagesState):
    return {"messages": [AIMessage(content="Analyzing pattern...")]}


def label_analysis(state: MessagesState):
    # Get the refined query from state if available
    query_to_analyze = None
    
    if "query_refinement_output" in state and state["query_refinement_output"]:
        query_output = state["query_refinement_output"]
        # Use refined_query if available, otherwise use original ticket_description
        if query_output.refined_query:
            query_to_analyze = query_output.refined_query
        else:
            query_to_analyze = query_output.ticket_description
    else:
        # Fallback to loading from sample ticket
        ticket_data = load_sample_ticket()
        query_to_analyze = ticket_data.get("ticket_description", "No query available")
    
    analysis_result = f"Analyzing labels for query: {query_to_analyze}"
    return {"messages": state["messages"] + [AIMessage(content=analysis_result)]}


def load_sample_ticket():
    """Load the sample ticket from JSON file"""
    try:
        with open('/Users/arunnaudiyal/Arun/Deloitte/Tejas/RCS-Standalone-Code/data/sample_ticket.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"ticket_description": "Error loading ticket: " + str(e)}


def create_session_folder():
    """Create session folder with MMDDYYYY_HHMM_UUID format"""
    now = datetime.now()
    date_str = now.strftime("%m%d%Y_%H%M")
    uuid_str = str(uuid.uuid4())[:4]
    session_id = f"{date_str}_{uuid_str}"
    
    session_path = f"/Users/arunnaudiyal/Arun/Deloitte/Tejas/RCS-Standalone-Code/sessions/{session_id}"
    os.makedirs(session_path, exist_ok=True)
    
    return session_id, session_path


def query_refinement_check(state: MessagesState):
    """Query Refinement Check agent that analyzes ticket completeness"""
    # Create session folder
    session_id, session_path = create_session_folder()
    
    # Load the sample ticket
    ticket_data = load_sample_ticket()
    ticket_description = ticket_data.get("ticket_description", "")
    
    # Create immutable InputTicket at the beginning and store in state
    input_ticket = InputTicket(
        ticket_id=f"ticket_{session_id}",
        ticket_description=ticket_description,
        source="sample_data",
        timestamp=datetime.now().isoformat(),
        priority=ticket_data.get("priority"),
        category=ticket_data.get("category")
    )
    
    # Load prompt from file
    with open('/Users/arunnaudiyal/Arun/Deloitte/Tejas/RCS-Standalone-Code/prompts/query_refinement_check_with_refined.txt', 'r') as f:
        prompt_template = f.read()
    
    # Create the LLM
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        max_tokens=OPENAI_MAX_TOKENS
    )
    
    # Create the prompt with ticket data
    full_prompt = f"{prompt_template}\n\nTicket to analyze: {ticket_description}"
    
    # Get response from LLM
    response = llm.invoke([HumanMessage(content=full_prompt)])
    
    # Parse the JSON response
    try:
        content = response.content
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            json_str = content[start_idx:end_idx]
            analysis_data = json.loads(json_str)
            
            # Determine next step based on confidence score
            confidence_score = analysis_data.get("confidence_score", 1.0)
            next_step = "Refine Query Step" if confidence_score < 0.50 else "Label Analysis Step"
            
            # Create output model
            query_output = QueryRefinementOutput(
                ticket_description=analysis_data.get("ticket_description", ticket_description),
                incomplete_flag=analysis_data.get("incomplete_flag", False),
                reason=analysis_data.get("reason", ""),
                confidence_score=confidence_score,
                session_id=session_id,
                timestamp=datetime.now().isoformat(),
                refined_query=analysis_data.get("refined_query", None),
                next_step=next_step
            )
            
            # Save to session folder
            output_file = os.path.join(session_path, "query_refinement_output.json")
            with open(output_file, 'w') as f:
                json.dump(query_output.model_dump(), f, indent=2)
            
            # Store in state
            return {
                "messages": state["messages"] + [AIMessage(content=response.content)],
                "query_refinement_output": query_output,
                "input_ticket": input_ticket
            }
    except (json.JSONDecodeError, ValueError) as e:
        # Fallback if parsing fails - default to refinement
        query_output = QueryRefinementOutput(
            ticket_description=ticket_description,
            incomplete_flag=True,
            reason=f"Failed to parse response: {str(e)}",
            confidence_score=0.0,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            refined_query=None,
            next_step="Refine Query Step"
        )
        
        # Save to session folder
        output_file = os.path.join(session_path, "query_refinement_output.json")
        with open(output_file, 'w') as f:
            json.dump(query_output.model_dump(), f, indent=2)
    
    # Store the response in state
    return {
        "messages": state["messages"] + [AIMessage(content=response.content)],
        "query_refinement_output": query_output,
        "input_ticket": input_ticket
    }


def ticket_refinement_step(state: MessagesState):
    """Ticket Refinement agent that improves incomplete ticket descriptions"""
    # Get the input ticket from state
    if "input_ticket" not in state or not state["input_ticket"]:
        return {"messages": state["messages"] + [AIMessage(content="Error: No input ticket found in state")]}
    
    input_ticket = state["input_ticket"]
    session_id = state["query_refinement_output"]["session_id"] if "query_refinement_output" in state else "unknown"
    
    # Load refinement prompt
    with open('/Users/arunnaudiyal/Arun/Deloitte/Tejas/RCS-Standalone-Code/prompts/ticket_refinement.txt', 'r') as f:
        prompt_template = f.read()
    
    # Create the LLM
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        max_tokens=OPENAI_MAX_TOKENS
    )
    
    # Create the prompt with original ticket
    full_prompt = f"{prompt_template}\n\nOriginal ticket to refine: {input_ticket.ticket_description}"
    
    # Get response from LLM
    response = llm.invoke([HumanMessage(content=full_prompt)])
    
    # Parse the JSON response
    try:
        content = response.content
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            json_str = content[start_idx:end_idx]
            refinement_data = json.loads(json_str)
            
            # Create refinement output model
            refinement_output = TicketRefinementOutput(
                initial_ticket=input_ticket,
                refined_ticket=refinement_data.get("refined_ticket", input_ticket.ticket_description),
                refinement_reason=refinement_data.get("refinement_reason", ""),
                confidence_score=refinement_data.get("confidence_score", 0.5),
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )
            
            # Save to session folder if we have a session path
            try:
                session_path = f"/Users/arunnaudiyal/Arun/Deloitte/Tejas/RCS-Standalone-Code/sessions/{session_id}"
                output_file = os.path.join(session_path, "ticket_refinement_output.json")
                with open(output_file, 'w') as f:
                    json.dump(refinement_output.model_dump(), f, indent=2)
            except Exception as e:
                print(f"Warning: Could not save refinement output: {e}")
            
            return {
                "messages": state["messages"] + [AIMessage(content=response.content)],
                "ticket_refinement_output": refinement_output
            }
            
    except (json.JSONDecodeError, ValueError) as e:
        # Fallback if parsing fails
        refinement_output = TicketRefinementOutput(
            initial_ticket=input_ticket,
            refined_ticket=input_ticket.ticket_description,
            refinement_reason=f"Failed to parse refinement response: {str(e)}",
            confidence_score=0.0,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
    
    return {
        "messages": state["messages"] + [AIMessage(content=response.content)],
        "ticket_refinement_output": refinement_output
    }


def query_refinement(state: MessagesState) -> Literal["Ticket Refinement Step", "Reasoning_Agent"]:
    """Router function that reads routing decision from state"""
    # Check if we have query refinement output in state with routing decision
    if "query_refinement_output" in state and state["query_refinement_output"]:
        query_output = state["query_refinement_output"]
        next_step = query_output.next_step
        # Map the old steps to new workflow
        if next_step == "Refine Query Step":
            return "Ticket Refinement Step"
        elif next_step == "Label Analysis Step":
            return REASONING_AGENT  # Skip directly to reasoning since analysis steps are commented out
        return REASONING_AGENT  # Default to reasoning agent
    
    # Default fallback if no state available
    return REASONING_AGENT


def reasoning_agent_node(state: MessagesState):
    """Reasoning Agent node that creates step-by-step solution plans"""
    # Determine input ticket - priority: refined > original > sample
    ticket_to_analyze = None
    session_id = "unknown"
    
    # Check for refined ticket first
    if "ticket_refinement_output" in state and state["ticket_refinement_output"]:
        ticket_to_analyze = state["ticket_refinement_output"].refined_ticket
        session_id = state["ticket_refinement_output"].session_id
    # Check for original input ticket
    elif "input_ticket" in state and state["input_ticket"]:
        ticket_to_analyze = state["input_ticket"].ticket_description
        session_id = state["query_refinement_output"].session_id if "query_refinement_output" in state and state["query_refinement_output"] else "unknown"
    # Fallback to sample ticket
    else:
        ticket_data = load_sample_ticket()
        ticket_to_analyze = ticket_data.get("ticket_description", "No ticket available")
        session_id = f"fallback_{datetime.now().strftime('%m%d%Y_%H%M')}"
    
    # Load reasoning prompt
    with open('/Users/arunnaudiyal/Arun/Deloitte/Tejas/RCS-Standalone-Code/prompts/reasoning_agent.txt', 'r') as f:
        prompt_template = f.read()
    
    # Create the LLM
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        max_tokens=OPENAI_MAX_TOKENS
    )
    
    # Create the prompt with ticket
    full_prompt = f"{prompt_template}\n\nTicket to analyze: {ticket_to_analyze}"
    
    # Get response from LLM
    response = llm.invoke([HumanMessage(content=full_prompt)])
    
    # Parse the JSON response
    try:
        content = response.content
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            json_str = content[start_idx:end_idx]
            reasoning_data = json.loads(json_str)
            
            # Parse solution steps
            solution_steps = []
            for step_data in reasoning_data.get("solution_steps", []):
                step = ReasoningStep(
                    step_number=step_data.get("step_number", 1),
                    action_type=step_data.get("action_type", "VERIFY"),
                    description=step_data.get("description", ""),
                    target=step_data.get("target", ""),
                    details=step_data.get("details", "")
                )
                solution_steps.append(step)
            
            # Create reasoning output model
            reasoning_output = ReasoningOutput(
                ticket_summary=reasoning_data.get("ticket_summary", ticket_to_analyze),
                solution_steps=solution_steps,
                complexity_level=reasoning_data.get("complexity_level", "Moderate"),
                estimated_time=reasoning_data.get("estimated_time", "Unknown"),
                confidence_score=reasoning_data.get("confidence_score", 0.5),
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )
            
            # Create reasoning_agent folder in session path and save output
            try:
                session_path = f"/Users/arunnaudiyal/Arun/Deloitte/Tejas/RCS-Standalone-Code/sessions/{session_id}"
                reasoning_folder = os.path.join(session_path, "reasoning_agent")
                os.makedirs(reasoning_folder, exist_ok=True)
                
                output_file = os.path.join(reasoning_folder, "reasoning_output.json")
                with open(output_file, 'w') as f:
                    json.dump(reasoning_output.model_dump(), f, indent=2)
            except Exception as e:
                print(f"Warning: Could not save reasoning output: {e}")
            
            return {
                "messages": state["messages"] + [AIMessage(content=response.content)],
                "reasoning_output": reasoning_output
            }
            
    except (json.JSONDecodeError, ValueError) as e:
        # Fallback if parsing fails
        fallback_step = ReasoningStep(
            step_number=1,
            action_type="VERIFY",
            description=f"Analyze ticket issue: {ticket_to_analyze}",
            target="System",
            details=f"Failed to parse reasoning response: {str(e)}"
        )
        
        reasoning_output = ReasoningOutput(
            ticket_summary=ticket_to_analyze,
            solution_steps=[fallback_step],
            complexity_level="Moderate",
            estimated_time="Unknown",
            confidence_score=0.0,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
        # Save fallback output
        try:
            session_path = f"/Users/arunnaudiyal/Arun/Deloitte/Tejas/RCS-Standalone-Code/sessions/{session_id}"
            reasoning_folder = os.path.join(session_path, "reasoning_agent")
            os.makedirs(reasoning_folder, exist_ok=True)
            
            output_file = os.path.join(reasoning_folder, "reasoning_output.json")
            with open(output_file, 'w') as f:
                json.dump(reasoning_output.model_dump(), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save fallback reasoning output: {e}")
    
    return {
        "messages": state["messages"] + [AIMessage(content=response.content)],
        "reasoning_output": reasoning_output
    }