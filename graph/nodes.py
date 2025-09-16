import json
import os
import uuid
from datetime import datetime
from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from models.data_models import MessagesState, QueryRefinementOutput, InputTicket, TicketRefinementOutput, ReasoningOutput, ReasoningStep, InfoRetrieverOutput, ExecutionOutput, ValidationOutput, ReportOutput, SupervisorOutput
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
from config.constants import REASONING_AGENT, INFO_RETRIEVER_AGENT, EXECUTION_AGENT, VALIDATION_AGENT, REPORT_AGENT, SUPERVISOR_AGENT
from agents.specialized_agents import create_reasoning_agent, create_info_retriever_agent, create_execution_agent, create_validation_agent, create_report_agent, create_supervisor_agent
from utils.helpers import get_data_path, get_prompts_path, get_sessions_path, ensure_directory_exists


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
        sample_ticket_path = get_data_path("sample_ticket.json")
        with open(sample_ticket_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"ticket_description": "Error loading ticket: " + str(e)}


def create_session_folder():
    """Create session folder with MMDDYYYY_HHMM_UUID format"""
    now = datetime.now()
    date_str = now.strftime("%m%d%Y_%H%M")
    uuid_str = str(uuid.uuid4())[:4]
    session_id = f"{date_str}_{uuid_str}"
    
    session_path = get_sessions_path(session_id)
    ensure_directory_exists(session_path)
    
    return session_id, str(session_path)


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
    prompt_path = get_prompts_path("query_refinement_check_with_refined.txt")
    with open(prompt_path, 'r') as f:
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
    prompt_path = get_prompts_path("ticket_refinement.txt")
    with open(prompt_path, 'r') as f:
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
                session_path = get_sessions_path(session_id)
                output_file = session_path / "ticket_refinement_output.json"
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
    
    # Create the reasoning react agent
    reasoning_agent = create_reasoning_agent()
    
    # Create the input message with ticket to analyze
    input_message = f"Ticket to analyze: {ticket_to_analyze}"
    
    # Get response from reasoning agent
    response = reasoning_agent.invoke({"messages": [HumanMessage(content=input_message)]})
    
    # Extract the latest AI message content for logging/display
    ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]
    agent_response_content = ai_messages[-1].content if ai_messages else "No response from reasoning agent"
    
    # Get the structured response from the agent
    try:
        if "structured_response" in response and response["structured_response"]:
            reasoning_output = response["structured_response"]
            
            # Update the session_id and timestamp in the structured response
            reasoning_output.session_id = session_id
            reasoning_output.timestamp = datetime.now().isoformat()
            
            # Create reasoning_agent folder in session path and save output
            try:
                session_path = get_sessions_path(session_id)
                reasoning_folder = session_path / "reasoning_agent"
                ensure_directory_exists(reasoning_folder)
                
                output_file = reasoning_folder / "reasoning_output.json"
                with open(output_file, 'w') as f:
                    json.dump(reasoning_output.model_dump(), f, indent=2)
            except Exception as e:
                print(f"Warning: Could not save reasoning output: {e}")
            
            return {
                "messages": state["messages"] + [AIMessage(content=agent_response_content)],
                "reasoning_output": reasoning_output
            }
        else:
            raise ValueError("No structured response found in agent output")
            
    except Exception as e:
        # Fallback if structured response is not available
        print(f"Warning: Could not get structured response from reasoning agent: {e}")
        fallback_step = ReasoningStep(
            step_number=1,
            action_type="VERIFY",
            description=f"Analyze ticket issue: {ticket_to_analyze}",
            target="System",
            details=f"Failed to get structured response: {str(e)}"
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
            session_path = get_sessions_path(session_id)
            reasoning_folder = session_path / "reasoning_agent"
            ensure_directory_exists(reasoning_folder)
            
            output_file = reasoning_folder / "reasoning_output.json"
            with open(output_file, 'w') as f:
                json.dump(reasoning_output.model_dump(), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save fallback reasoning output: {e}")
        
        return {
            "messages": state["messages"] + [AIMessage(content=agent_response_content)],
            "reasoning_output": reasoning_output
        }


def info_retriever_agent_node(state: MessagesState):
    """Information Retrieval Agent node that gathers historical tickets and schema info"""
    # Determine session_id from state
    session_id = "unknown"
    if "reasoning_output" in state and state["reasoning_output"]:
        session_id = state["reasoning_output"].session_id
    elif "query_refinement_output" in state and state["query_refinement_output"]:
        session_id = state["query_refinement_output"].session_id
    else:
        session_id = f"fallback_{datetime.now().strftime('%m%d%Y_%H%M')}"
    
    # Get task details from reasoning output
    task_details = "Retrieve relevant information for ticket resolution"
    if "reasoning_output" in state and state["reasoning_output"]:
        reasoning_output = state["reasoning_output"]
        task_details = f"Retrieve information for: {reasoning_output.ticket_summary}. Steps: {[step.description for step in reasoning_output.solution_steps]}"
    
    # Create the info retriever agent
    info_retriever_agent = create_info_retriever_agent()
    
    # Create input message
    input_message = f"Task: {task_details}"
    
    # Get response from agent
    response = info_retriever_agent.invoke({"messages": [HumanMessage(content=input_message)]})
    
    # Extract AI message content
    ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]
    agent_response_content = ai_messages[-1].content if ai_messages else "No response from info retriever agent"
    
    # Get structured response
    try:
        if "structured_response" in response and response["structured_response"]:
            info_output = response["structured_response"]
            info_output.session_id = session_id
            info_output.timestamp = datetime.now().isoformat()
            
            # Save to session folder
            try:
                session_path = get_sessions_path(session_id)
                agent_folder = session_path / "info_retriever_agent"
                ensure_directory_exists(agent_folder)
                
                output_file = agent_folder / "output.json"
                with open(output_file, 'w') as f:
                    json.dump(info_output.model_dump(), f, indent=2)
            except Exception as e:
                print(f"Warning: Could not save info retriever output: {e}")
            
            return {
                "messages": state["messages"] + [AIMessage(content=agent_response_content)],
                "info_retriever_output": info_output
            }
        else:
            raise ValueError("No structured response found in agent output")
            
    except Exception as e:
        print(f"Warning: Could not get structured response from info retriever agent: {e}")
        # Create fallback output
        fallback_output = InfoRetrieverOutput(
            similar_tickets=[],
            table_schemas=[],
            analysis_summary=f"Failed to process info retrieval: {str(e)}",
            recommendations=["Review agent configuration"],
            confidence_score=0.0,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
        return {
            "messages": state["messages"] + [AIMessage(content=agent_response_content)],
            "info_retriever_output": fallback_output
        }


def execution_agent_node(state: MessagesState):
    """Execution Agent node that implements resolution steps"""
    # Determine session_id from state
    session_id = "unknown"
    if "reasoning_output" in state and state["reasoning_output"]:
        session_id = state["reasoning_output"].session_id
    elif "query_refinement_output" in state and state["query_refinement_output"]:
        session_id = state["query_refinement_output"].session_id
    else:
        session_id = f"fallback_{datetime.now().strftime('%m%d%Y_%H%M')}"
    
    # Get execution steps from reasoning output
    execution_details = "Execute resolution steps"
    if "reasoning_output" in state and state["reasoning_output"]:
        reasoning_output = state["reasoning_output"]
        execution_steps = [step for step in reasoning_output.solution_steps if step.action_type in ["INSERT", "UPDATE", "DELETE", "CONFIGURE"]]
        execution_details = f"Execute steps: {[f'{step.step_number}: {step.description}' for step in execution_steps]}"
    
    # Create the execution agent
    execution_agent = create_execution_agent()
    
    # Create input message
    input_message = f"Execute the following: {execution_details}"
    
    # Get response from agent
    response = execution_agent.invoke({"messages": [HumanMessage(content=input_message)]})
    
    # Extract AI message content
    ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]
    agent_response_content = ai_messages[-1].content if ai_messages else "No response from execution agent"
    
    # Get structured response
    try:
        if "structured_response" in response and response["structured_response"]:
            execution_output = response["structured_response"]
            execution_output.session_id = session_id
            execution_output.timestamp = datetime.now().isoformat()
            
            # Save to session folder
            try:
                session_path = get_sessions_path(session_id)
                agent_folder = session_path / "execution_agent"
                ensure_directory_exists(agent_folder)
                
                output_file = agent_folder / "output.json"
                with open(output_file, 'w') as f:
                    json.dump(execution_output.model_dump(), f, indent=2)
            except Exception as e:
                print(f"Warning: Could not save execution output: {e}")
            
            return {
                "messages": state["messages"] + [AIMessage(content=agent_response_content)],
                "execution_output": execution_output
            }
        else:
            raise ValueError("No structured response found in agent output")
            
    except Exception as e:
        print(f"Warning: Could not get structured response from execution agent: {e}")
        # Create fallback output
        fallback_output = ExecutionOutput(
            executed_steps=[],
            overall_status="FAILED",
            success_count=0,
            failure_count=1,
            execution_summary=f"Failed to process execution: {str(e)}",
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
        return {
            "messages": state["messages"] + [AIMessage(content=agent_response_content)],
            "execution_output": fallback_output
        }


def validation_agent_node(state: MessagesState):
    """Validation Agent node that verifies resolution success"""
    # Determine session_id from state
    session_id = "unknown"
    if "reasoning_output" in state and state["reasoning_output"]:
        session_id = state["reasoning_output"].session_id
    elif "query_refinement_output" in state and state["query_refinement_output"]:
        session_id = state["query_refinement_output"].session_id
    else:
        session_id = f"fallback_{datetime.now().strftime('%m%d%Y_%H%M')}"
    
    # Get validation context from previous steps
    validation_context = "Validate resolution success"
    if "execution_output" in state and state["execution_output"]:
        execution_output = state["execution_output"]
        validation_context = f"Validate execution results: {execution_output.execution_summary}. Steps executed: {len(execution_output.executed_steps)}"
    elif "reasoning_output" in state and state["reasoning_output"]:
        reasoning_output = state["reasoning_output"]
        verify_steps = [step for step in reasoning_output.solution_steps if step.action_type == "VERIFY"]
        validation_context = f"Validate steps: {[f'{step.step_number}: {step.description}' for step in verify_steps]}"
    
    # Create the validation agent
    validation_agent = create_validation_agent()
    
    # Create input message
    input_message = f"Validate the following: {validation_context}"
    
    # Get response from agent
    response = validation_agent.invoke({"messages": [HumanMessage(content=input_message)]})
    
    # Extract AI message content
    ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]
    agent_response_content = ai_messages[-1].content if ai_messages else "No response from validation agent"
    
    # Get structured response
    try:
        if "structured_response" in response and response["structured_response"]:
            validation_output = response["structured_response"]
            validation_output.session_id = session_id
            validation_output.timestamp = datetime.now().isoformat()
            
            # Save to session folder
            try:
                session_path = get_sessions_path(session_id)
                agent_folder = session_path / "validation_agent"
                ensure_directory_exists(agent_folder)
                
                output_file = agent_folder / "output.json"
                with open(output_file, 'w') as f:
                    json.dump(validation_output.model_dump(), f, indent=2)
            except Exception as e:
                print(f"Warning: Could not save validation output: {e}")
            
            return {
                "messages": state["messages"] + [AIMessage(content=agent_response_content)],
                "validation_output": validation_output
            }
        else:
            raise ValueError("No structured response found in agent output")
            
    except Exception as e:
        print(f"Warning: Could not get structured response from validation agent: {e}")
        # Create fallback output
        fallback_output = ValidationOutput(
            is_resolution_successful=False,
            confidence_score=0.0,
            issues_found=[],
            validation_summary=f"Failed to process validation: {str(e)}",
            recommendations=["Review validation agent configuration"],
            next_steps=["Debug validation process"],
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
        return {
            "messages": state["messages"] + [AIMessage(content=agent_response_content)],
            "validation_output": fallback_output
        }


def report_agent_node(state: MessagesState):
    """Report Agent node that generates final resolution report"""
    # Determine session_id from state
    session_id = "unknown"
    if "reasoning_output" in state and state["reasoning_output"]:
        session_id = state["reasoning_output"].session_id
    elif "query_refinement_output" in state and state["query_refinement_output"]:
        session_id = state["query_refinement_output"].session_id
    else:
        session_id = f"fallback_{datetime.now().strftime('%m%d%Y_%H%M')}"
    
    # Gather information from all previous agents
    report_context = "Generate final resolution report"
    ticket_id = f"ticket_{session_id}"
    
    if "reasoning_output" in state and state["reasoning_output"]:
        reasoning_output = state["reasoning_output"]
        report_context += f". Ticket: {reasoning_output.ticket_summary}"
        
    if "execution_output" in state and state["execution_output"]:
        execution_output = state["execution_output"]
        report_context += f". Execution status: {execution_output.overall_status}"
        
    if "validation_output" in state and state["validation_output"]:
        validation_output = state["validation_output"]
        report_context += f". Validation result: {'SUCCESS' if validation_output.is_resolution_successful else 'FAILED'}"
    
    # Create the report agent
    report_agent = create_report_agent()
    
    # Create input message
    input_message = f"Generate report for: {report_context}"
    
    # Get response from agent
    response = report_agent.invoke({"messages": [HumanMessage(content=input_message)]})
    
    # Extract AI message content
    ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]
    agent_response_content = ai_messages[-1].content if ai_messages else "No response from report agent"
    
    # Get structured response
    try:
        if "structured_response" in response and response["structured_response"]:
            report_output = response["structured_response"]
            report_output.session_id = session_id
            report_output.timestamp = datetime.now().isoformat()
            report_output.ticket_id = ticket_id
            
            # Save to session folder
            try:
                session_path = get_sessions_path(session_id)
                agent_folder = session_path / "report_agent"
                ensure_directory_exists(agent_folder)
                
                output_file = agent_folder / "output.json"
                with open(output_file, 'w') as f:
                    json.dump(report_output.model_dump(), f, indent=2)
            except Exception as e:
                print(f"Warning: Could not save report output: {e}")
            
            return {
                "messages": state["messages"] + [AIMessage(content=agent_response_content)],
                "report_output": report_output
            }
        else:
            raise ValueError("No structured response found in agent output")
            
    except Exception as e:
        print(f"Warning: Could not get structured response from report agent: {e}")
        # Create fallback output
        fallback_output = ReportOutput(
            ticket_id=ticket_id,
            resolution_status="FAILED",
            resolution_summary=f"Failed to generate report: {str(e)}",
            steps_taken=["Report generation attempted"],
            time_to_resolution="Unknown",
            confidence_score=0.0,
            lessons_learned=["Report agent needs configuration review"],
            follow_up_actions=["Debug report generation process"],
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
        return {
            "messages": state["messages"] + [AIMessage(content=agent_response_content)],
            "report_output": fallback_output
        }


def supervisor_agent_node(state: MessagesState):
    """Supervisor Agent node that orchestrates workflow and task assignments"""
    # Determine session_id from state
    session_id = "unknown"
    if "reasoning_output" in state and state["reasoning_output"]:
        session_id = state["reasoning_output"].session_id
    elif "query_refinement_output" in state and state["query_refinement_output"]:
        session_id = state["query_refinement_output"].session_id
    else:
        session_id = f"fallback_{datetime.now().strftime('%m%d%Y_%H%M')}"
    
    # Gather workflow context
    workflow_context = "Orchestrate ticket resolution workflow"
    if "reasoning_output" in state and state["reasoning_output"]:
        reasoning_output = state["reasoning_output"]
        workflow_context = f"Coordinate resolution for: {reasoning_output.ticket_summary}. Available steps: {[f'{step.step_number}: {step.action_type}' for step in reasoning_output.solution_steps]}"
    
    # Create the supervisor agent
    supervisor_agent = create_supervisor_agent()
    
    # Create input message
    input_message = f"Coordinate workflow: {workflow_context}"
    
    # Get response from agent
    response = supervisor_agent.invoke({"messages": [HumanMessage(content=input_message)]})
    
    # Extract AI message content
    ai_messages = [msg for msg in response["messages"] if isinstance(msg, AIMessage)]
    agent_response_content = ai_messages[-1].content if ai_messages else "No response from supervisor agent"
    
    # Get structured response
    try:
        if "structured_response" in response and response["structured_response"]:
            supervisor_output = response["structured_response"]
            supervisor_output.session_id = session_id
            supervisor_output.timestamp = datetime.now().isoformat()
            
            # Save to session folder
            try:
                session_path = get_sessions_path(session_id)
                agent_folder = session_path / "supervisor_agent"
                ensure_directory_exists(agent_folder)
                
                output_file = agent_folder / "output.json"
                with open(output_file, 'w') as f:
                    json.dump(supervisor_output.model_dump(), f, indent=2)
            except Exception as e:
                print(f"Warning: Could not save supervisor output: {e}")
            
            return {
                "messages": state["messages"] + [AIMessage(content=agent_response_content)],
                "supervisor_output": supervisor_output
            }
        else:
            raise ValueError("No structured response found in agent output")
            
    except Exception as e:
        print(f"Warning: Could not get structured response from supervisor agent: {e}")
        # Create fallback output
        fallback_output = SupervisorOutput(
            workflow_status="FAILED",
            current_phase="Error",
            task_assignments=[],
            completed_agents=[],
            next_agent=None,
            coordination_summary=f"Failed to coordinate workflow: {str(e)}",
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
        return {
            "messages": state["messages"] + [AIMessage(content=agent_response_content)],
            "supervisor_output": fallback_output
        }