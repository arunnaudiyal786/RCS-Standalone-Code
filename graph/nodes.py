import json
from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from models.data_models import MessagesState
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS


def pattern_analysis(state: MessagesState):
    return {"messages": [AIMessage(content="Analyzing pattern...")]}


def label_analysis(state: MessagesState):
    return {"messages": [AIMessage(content="Analyzing labels...")]}


def load_sample_ticket():
    """Load the sample ticket from JSON file"""
    try:
        with open('/Users/arunnaudiyal/Arun/Deloitte/Tejas/RCS-Standalone-Code/data/sample_ticket.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"ticket_description": "Error loading ticket: " + str(e)}


def query_refinement_check(state: MessagesState):
    """Query Refinement Check agent that analyzes ticket completeness"""
    # Load the sample ticket
    ticket_data = load_sample_ticket()
    ticket_description = ticket_data.get("ticket_description", "")
    
    # Load prompt from file
    with open('/Users/arunnaudiyal/Arun/Deloitte/Tejas/RCS-Standalone-Code/prompts/query_refinement_check.txt', 'r') as f:
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
    
    # Store the response in state
    return {"messages": state["messages"] + [AIMessage(content=response.content)]}


def query_refinement(state: MessagesState) -> Literal["Refine Query Step", "Label Analysis Step"]:
    """Router function that decides next step based on confidence score"""
    # Get the last message which should contain the analysis result
    last_message = state["messages"][-1] if state["messages"] else None
    
    if last_message and hasattr(last_message, 'content'):
        try:
            # Try to parse JSON from the response
            content = last_message.content
            # Extract JSON from the content if it's wrapped in other text
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                analysis = json.loads(json_str)
                confidence_score = analysis.get("confidence_score", 1.0)
                
                # Route based on confidence score
                if confidence_score < 0.50:
                    return "Refine Query Step"
        except (json.JSONDecodeError, ValueError):
            # If parsing fails, default to refinement
            return "Refine Query Step"
    
    return "Label Analysis Step"