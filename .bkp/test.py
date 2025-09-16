"""
Multi-Agent Supervisor System with LangGraph
Using create_supervisor from langgraph-supervisor library
"""

import os
from typing import Annotated, TypedDict, Sequence
import pandas as pd
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from dotenv import load_dotenv

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

def setup_environment():
    """Set up API keys from .env file in the same directory."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(env_path)
    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY not found in .env file.")

# ============================================================================
# CREATE SAMPLE CSV DATA
# ============================================================================

def create_sample_csv():
    """Create a sample member management CSV file"""
    data = {
        'member_id': [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010],
        'name': ['Alice Johnson', 'Bob Smith', 'Charlie Brown', 'Diana Ross', 'Edward Norton',
                 'Fiona Apple', 'George Martin', 'Helen Troy', 'Isaac Newton', 'Julia Roberts'],
        'email': ['alice@email.com', 'bob@email.com', 'charlie@email.com', 'diana@email.com',
                  'edward@email.com', 'fiona@email.com', 'george@email.com', 'helen@email.com',
                  'isaac@email.com', 'julia@email.com'],
        'membership_type': ['Premium', 'Basic', 'Premium', 'Gold', 'Basic',
                            'Gold', 'Premium', 'Basic', 'Gold', 'Premium'],
        'join_date': ['2023-01-15', '2023-02-20', '2023-03-10', '2023-04-05', '2023-05-12',
                      '2023-06-18', '2023-07-22', '2023-08-30', '2023-09-14', '2023-10-25']
    }
    
    df = pd.DataFrame(data)
    df.to_csv('member_management.csv', index=False)
    print("✅ Created member_management.csv with 10 rows")
    print("\n📋 Sample data preview:")
    print(df.head())
    return df

# ============================================================================
# CSV TOOLS
# ============================================================================

@tool
def get_info_from_csv(member_id: int = None, name: str = None) -> str:
    """
    Check if a row is present in the CSV file.
    Can search by member_id or name.
    """
    try:
        df = pd.read_csv('member_management.csv')
        
        if member_id:
            result = df[df['member_id'] == member_id]
            if not result.empty:
                return f"✅ Found member: {result.to_dict('records')[0]}"
            else:
                return f"❌ Member with ID {member_id} not found"
        
        if name:
            result = df[df['name'].str.contains(name, case=False, na=False)]
            if not result.empty:
                return f"✅ Found member(s): {result.to_dict('records')}"
            else:
                return f"❌ Member with name '{name}' not found"
        
        return "Please provide either member_id or name to search"
    except Exception as e:
        return f"Error reading CSV: {str(e)}"

@tool
def insert_row_in_csv(member_id: int, name: str, email: str, 
                      membership_type: str, join_date: str) -> str:
    """
    Insert a new row into the CSV file.
    """
    try:
        df = pd.read_csv('member_management.csv')
        
        # Check if member_id already exists
        if member_id in df['member_id'].values:
            return f"❌ Member with ID {member_id} already exists"
        
        # Create new row
        new_row = {
            'member_id': member_id,
            'name': name,
            'email': email,
            'membership_type': membership_type,
            'join_date': join_date
        }
        
        # Append new row
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv('member_management.csv', index=False)
        
        return f"✅ Successfully added member: {new_row}"
    except Exception as e:
        return f"Error inserting row: {str(e)}"

@tool
def validate_row_in_csv(member_id: int) -> str:
    """
    Validate if a specific row exists in the CSV file.
    """
    try:
        df = pd.read_csv('member_management.csv')
        
        if member_id in df['member_id'].values:
            row = df[df['member_id'] == member_id].iloc[0]
            return f"✅ Validation successful! Member {member_id} exists: {row.to_dict()}"
        else:
            return f"❌ Validation failed! Member {member_id} does not exist"
    except Exception as e:
        return f"Error validating: {str(e)}"

# ============================================================================
# CREATE AGENTS AND SUPERVISOR GRAPH
# ============================================================================

def create_supervisor_graph():
    """Create all worker agents and supervisor using create_supervisor"""
    
    # Initialize LLM - Use gpt-4o-mini or gpt-3.5-turbo for better compatibility
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 1. Info Retriever Agent
    info_retriever_agent = create_react_agent(
        model=llm,
        tools=[get_info_from_csv],
        prompt=(
            "You are an Info Retriever Agent.\n"
            "Your job is to check if data exists in the CSV file.\n"
            "Use the get_info_from_csv tool to search for members.\n"
            "Report your findings clearly and concisely."
        ),
        name="info_retriever"
    )
    
    # 2. Execution Agent
    execution_agent = create_react_agent(
        model=llm,
        tools=[insert_row_in_csv],
        prompt=(
            "You are an Execution Agent.\n"
            "Your job is to add new rows to the CSV file.\n"
            "Use the insert_row_in_csv tool to add members.\n"
            "Ensure all required fields are provided."
        ),
        name="execution"
    )
    
    # 3. Validation Agent
    validation_agent = create_react_agent(
        model=llm,
        tools=[validate_row_in_csv],
        prompt=(
            "You are a Validation Agent.\n"
            "Your job is to verify that operations were successful.\n"
            "Use the validate_row_in_csv tool to confirm data integrity.\n"
            "Report validation results clearly."
        ),
        name="validation"
    )
    
    print("✅ All worker agents created")
    
    # Create supervisor using create_supervisor from langgraph-supervisor
    # Use a more robust model for supervisor
    supervisor_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    supervisor_workflow = create_supervisor(
        agents=[info_retriever_agent, execution_agent, validation_agent],
        model=supervisor_llm,
        prompt=(
            "You are a Supervisor Agent managing three specialized agents:\n"
            "1. info_retriever - checks if data exists in CSV\n"
            "2. execution - adds new rows to CSV\n"
            "3. validation - verifies operations were successful\n\n"
            "For adding a new member, follow this workflow:\n"
            "1. First, delegate to info_retriever to check if the member already exists\n"
            "2. If not exists, delegate to execution to add the member\n"
            "3. Finally, delegate to validation to confirm the addition\n\n"
            "Coordinate tasks sequentially and provide clear instructions to each agent.\n"
            "When delegating to agents, be specific about what they should do."
        ),
        # Add these parameters to improve compatibility
        parallel_tool_calls=False,  # Disable parallel tool calls
        output_mode="last_message"  # Use last_message mode
    )
    
    print("✅ Supervisor workflow created using create_supervisor")
    
    # Compile the graph
    compiled_graph = supervisor_workflow.compile()
    
    print("✅ Multi-agent graph compiled successfully")
    return compiled_graph

# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_add_member(graph, member_data):
    """Test adding a new member to the system"""
    
    # Format the message more clearly for the supervisor
    test_input = {
        "messages": [
            HumanMessage(
                content=(
                    f"Please add a new member to the CSV file. "
                    f"The member details are: "
                    f"Member ID: {member_data['member_id']}, "
                    f"Name: {member_data['name']}, "
                    f"Email: {member_data['email']}, "
                    f"Membership Type: {member_data['membership_type']}, "
                    f"Join Date: {member_data['join_date']}. "
                    f"First check if this member exists, then add if not exists, "
                    f"and finally validate the addition."
                )
            )
        ]
    }
    
    print("🔄 Processing request...")
    print("-" * 50)
    
    try:
        # Run the supervisor graph with error handling
        for chunk in graph.stream(test_input, {"recursion_limit": 50}):
            for node_name, node_output in chunk.items():
                if "messages" in node_output:
                    last_message = node_output["messages"][-1]
                    print(f"\n📍 {node_name}:")
                    if hasattr(last_message, 'content'):
                        content = last_message.content
                        # Print full content if short, otherwise truncate
                        if len(content) <= 200:
                            print(f"   {content}")
                        else:
                            print(f"   {content[:200]}...")
                    else:
                        print(f"   {last_message}")
    except Exception as e:
        print(f"\n⚠️ Error occurred: {str(e)}")
        print("This might be due to model compatibility issues. Try using 'gpt-3.5-turbo' or 'gpt-4o-mini'")
    
    print("\n" + "="*50)
    print("✅ Process completed!")

def verify_results():
    """Verify the final state of the CSV"""
    df = pd.read_csv('member_management.csv')
    print(f"\n📊 Total members in CSV: {len(df)}")
    print("\n📋 Last 3 members:")
    print(df.tail(3).to_string())

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main execution function"""
    
    print("🤖 Multi-Agent Supervisor System with create_supervisor")
    print("=" * 50)
    
    # Setup
    setup_environment()
    
    # Create sample CSV
    create_sample_csv()
    
    # Create supervisor graph using create_supervisor
    supervisor_graph = create_supervisor_graph()
    
    # Test the system
    print("\n🚀 Testing the system with a new member addition")
    print("=" * 50)
    
    new_member = {
        'member_id': 1011,
        'name': 'Michael Jordan',
        'email': 'michael@email.com',
        'membership_type': 'Premium',
        'join_date': '2024-01-15'
    }
    
    test_add_member(supervisor_graph, new_member)
    
    # Verify results
    verify_results()
    
    # Optional: Add another member to test duplicate detection
    print("\n\n🔍 Testing duplicate detection")
    print("=" * 50)
    
    duplicate_member = {
        'member_id': 1011,  # Same ID as before
        'name': 'Another Person',
        'email': 'another@email.com',
        'membership_type': 'Basic',
        'join_date': '2024-02-01'
    }
    
    test_add_member(supervisor_graph, duplicate_member)
    
    # Verify results again
    verify_results()

    graph_image = supervisor_graph.get_graph().draw_mermaid_png()
    with open("supervisor_graph.png", "wb") as f:
        f.write(graph_image)

    print("✅ Test completed successfully")

if __name__ == "__main__":
    main()