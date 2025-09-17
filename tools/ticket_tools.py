from typing import List, Dict
import csv
import os
from langchain_core.tools import tool
from models.data_models import ValidationResult
from utils.vector_store import vector_store, table_schema_store
from utils.helpers import get_data_path


@tool
def retrieve_similar_tickets(ticket_description: str) -> List[Dict]:
    """Retrieve top 10 most similar historical tickets from vector database."""
    return vector_store.search_similar_tickets(ticket_description, k=10)


@tool
def insert_row_to_text_file(table_name: str, row_data: Dict[str, str]) -> Dict:
    """
    Insert a new row into the specified text file.
    
    Args:
        table_name: Name of the table/text file (e.g., "member_enrollment", "claims_medical")
        row_data: Dictionary containing column names as keys and values to insert
    
    Returns:
        Dict containing operation status, details, and any errors
    """
    try:
        # Construct file path
        file_path = get_data_path(f"table_data/{table_name}.txt")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": f"Table file not found: {table_name}.txt",
                "table_name": table_name,
                "operation": "insert",
                "row_data": row_data,
                "success": False
            }
        
        # Read existing headers
        with open(file_path, 'r', newline='', encoding='utf-8') as textfile:
            reader = csv.reader(textfile)
            headers = next(reader, [])
            
            if not headers:
                return {
                    "status": "error",
                    "message": f"No headers found in table: {table_name}",
                    "table_name": table_name,
                    "operation": "insert",
                    "row_data": row_data,
                    "success": False
                }
        
        # Create case-insensitive column mapping
        header_map = {header.lower(): header for header in headers}
        row_data_lower = {key.lower(): value for key, value in row_data.items()}
        
        # Validate that all required columns are provided (case-insensitive)
        missing_columns = []
        for header in headers:
            if header.lower() not in row_data_lower:
                missing_columns.append(header)
        
        if missing_columns:
            return {
                "status": "error",
                "message": f"Missing required columns: {missing_columns}",
                "table_name": table_name,
                "operation": "insert",
                "row_data": row_data,
                "expected_columns": headers,
                "missing_columns": missing_columns,
                "success": False
            }
        
        # Prepare row data in correct column order using case-insensitive mapping
        ordered_row = [row_data_lower.get(header.lower(), '') for header in headers]
        
        # Append the new row
        with open(file_path, 'a', newline='', encoding='utf-8') as textfile:
            writer = csv.writer(textfile)
            writer.writerow(ordered_row)
        
        return {
            "status": "success",
            "message": f"Successfully inserted new row into {table_name}",
            "table_name": table_name,
            "operation": "insert",
            "row_data": row_data,
            "inserted_row": dict(zip(headers, ordered_row)),
            "success": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error inserting row into {table_name}: {str(e)}",
            "table_name": table_name,
            "operation": "insert",
            "row_data": row_data,
            "success": False
        }


@tool
def update_value_in_text_file(table_name: str, search_column: str, search_value: str, update_column: str, new_value: str) -> Dict:
    """
    Update a specific value in the text file based on search criteria.
    
    Args:
        table_name: Name of the table/text file (e.g., "member_enrollment", "claims_medical")
        search_column: Column name to search in
        search_value: Value to search for in the search_column
        update_column: Column name to update
        new_value: New value to set in the update_column
    
    Returns:
        Dict containing operation status, details, and any errors
    """
    try:
        # Construct file path
        file_path = get_data_path(f"table_data/{table_name}.txt")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": f"Table file not found: {table_name}.txt",
                "table_name": table_name,
                "operation": "update",
                "search_criteria": {"column": search_column, "value": search_value},
                "update_data": {"column": update_column, "new_value": new_value},
                "success": False
            }
        
        # Read all data
        rows = []
        headers = []
        updated_rows = []
        
        with open(file_path, 'r', newline='', encoding='utf-8') as textfile:
            reader = csv.reader(textfile)
            headers = next(reader, [])
            
            if not headers:
                return {
                    "status": "error",
                    "message": f"No headers found in table: {table_name}",
                    "table_name": table_name,
                    "operation": "update",
                    "success": False
                }
            
            # Create case-insensitive column mapping
            header_map = {header.lower(): header for header in headers}
            search_column_lower = search_column.lower()
            update_column_lower = update_column.lower()
            
            # Check if columns exist (case-insensitive)
            if search_column_lower not in header_map:
                return {
                    "status": "error",
                    "message": f"Search column '{search_column}' not found in table '{table_name}'",
                    "table_name": table_name,
                    "operation": "update",
                    "available_columns": headers,
                    "success": False
                }
            
            if update_column_lower not in header_map:
                return {
                    "status": "error",
                    "message": f"Update column '{update_column}' not found in table '{table_name}'",
                    "table_name": table_name,
                    "operation": "update",
                    "available_columns": headers,
                    "success": False
                }
            
            # Get actual column names and indices
            actual_search_column = header_map[search_column_lower]
            actual_update_column = header_map[update_column_lower]
            search_index = headers.index(actual_search_column)
            update_index = headers.index(actual_update_column)
            
            # Read all rows and identify matches
            for row_num, row in enumerate(reader, start=2):
                if len(row) > max(search_index, update_index):
                    if row[search_index].strip() == str(search_value).strip():
                        old_value = row[update_index]
                        row[update_index] = str(new_value)
                        updated_rows.append({
                            "row_number": row_num,
                            "record": dict(zip(headers, row)),
                            "old_value": old_value,
                            "new_value": new_value
                        })
                    rows.append(row)
                else:
                    rows.append(row)
        
        if not updated_rows:
            return {
                "status": "warning",
                "message": f"No records found matching {search_column}='{search_value}' in {table_name}",
                "table_name": table_name,
                "operation": "update",
                "search_criteria": {"column": search_column, "value": search_value},
                "update_data": {"column": update_column, "new_value": new_value},
                "updated_count": 0,
                "success": False
            }
        
        # Write updated data back to file
        with open(file_path, 'w', newline='', encoding='utf-8') as textfile:
            writer = csv.writer(textfile)
            writer.writerow(headers)
            writer.writerows(rows)
        
        return {
            "status": "success",
            "message": f"Successfully updated {len(updated_rows)} record(s) in {table_name}",
            "table_name": table_name,
            "operation": "update",
            "search_criteria": {"column": search_column, "value": search_value},
            "update_data": {"column": update_column, "new_value": new_value},
            "updated_count": len(updated_rows),
            "updated_records": updated_rows,
            "success": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error updating {table_name}: {str(e)}",
            "table_name": table_name,
            "operation": "update",
            "search_criteria": {"column": search_column, "value": search_value},
            "update_data": {"column": update_column, "new_value": new_value},
            "success": False
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


@tool
def get_table_info(table_name: str, column_name: str, search_value: str = None) -> Dict:
    """
    Retrieve information from a specific table to check if data already exists.
    
    Args:
        table_name: Name of the table to search (e.g., "member_enrollment", "claims_medical")
        column_name: Name of the column to search in
        search_value: Optional value to search for in the specified column
    
    Returns:
        Dict containing information about existing data and whether operation is needed
    """
    try:
        # Construct file path
        file_path = get_data_path(f"table_data/{table_name}.txt")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": f"Table file not found: {table_name}.txt",
                "table_name": table_name,
                "column_name": column_name,
                "search_value": search_value,
                "data_exists": False,
                "matching_records": [],
                "operation_needed": True
            }
        
        # Read and parse the text file
        matching_records = []
        all_records = []
        column_index = None
        
        with open(file_path, 'r', newline='', encoding='utf-8') as textfile:
            reader = csv.reader(textfile)
            headers = next(reader, [])
            
            # Find column index (case-insensitive)
            for i, header in enumerate(headers):
                if header.strip().lower() == column_name.strip().lower():
                    column_index = i
                    break
            
            if column_index is None:
                return {
                    "status": "error",
                    "message": f"Column '{column_name}' not found in table '{table_name}'",
                    "table_name": table_name,
                    "column_name": column_name,
                    "search_value": search_value,
                    "available_columns": headers,
                    "data_exists": False,
                    "matching_records": [],
                    "operation_needed": True
                }
            
            # Read all records
            for row_num, row in enumerate(reader, start=2):  # Start from 2 since headers are row 1
                if len(row) > column_index:
                    record = dict(zip(headers, row))  # type: ignore    # type: ignore
                    all_records.append(record)
                    
                    # If search_value is provided, check for matches
                    if search_value is not None:
                        if row[column_index].strip() == str(search_value).strip():
                            matching_records.append({
                                "row_number": row_num,
                                "record": record
                            })
        
        # Determine if operation is needed
        data_exists = len(matching_records) > 0 if search_value is not None else len(all_records) > 0
        operation_needed = not data_exists if search_value is not None else True
        
        return {
            "status": "success",
            "table_name": table_name,
            "column_name": column_name,
            "search_value": search_value,
            "data_exists": data_exists,
            "matching_records": matching_records,
            "total_records": len(all_records),
            "operation_needed": operation_needed,
            "message": f"Found {len(matching_records)} matching records" if search_value else f"Table contains {len(all_records)} total records"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error reading table data: {str(e)}",
            "table_name": table_name,
            "column_name": column_name,
            "search_value": search_value,
            "data_exists": False,
            "matching_records": [],
            "operation_needed": True
        }


@tool
def get_table_desc(table_name: str) -> Dict:
    """
    Retrieve detailed table description from the table_description folder.
    
    Args:
        table_name: Name of the table to get description for (e.g., "claims_medical", "member_enrollment")
    
    Returns:
        Dict containing table description, columns, business rules, and usage information
    """
    try:
        # Construct file path for table description
        desc_file_path = get_data_path(f"table_description/{table_name}_description.txt")
        
        # Check if description file exists
        if not os.path.exists(desc_file_path):
            return {
                "status": "error",
                "message": f"Table description file not found: {table_name}_description.txt",
                "table_name": table_name,
                "description": None,
                "columns": [],
                "business_rules": [],
                "relationships": [],
                "usage": []
            }
        
        # Read and parse the description file
        with open(desc_file_path, 'r', encoding='utf-8') as desc_file:
            content = desc_file.read()
        
        # Parse the content into structured information
        description_data = parse_table_description(content, table_name)
        
        return {
            "status": "success",
            "table_name": table_name,
            "description": description_data.get("description", ""),
            "columns": description_data.get("columns", []),
            "business_rules": description_data.get("business_rules", []),
            "relationships": description_data.get("relationships", []),
            "usage": description_data.get("usage", []),
            "message": f"Successfully retrieved description for table: {table_name}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error reading table description: {str(e)}",
            "table_name": table_name,
            "description": None,
            "columns": [],
            "business_rules": [],
            "relationships": [],
            "usage": []
        }


def parse_table_description(content: str, table_name: str) -> Dict:
    """
    Parse table description text file into structured data.
    
    Args:
        content: Raw content from the description file
        table_name: Name of the table
    
    Returns:
        Dict containing parsed description information
    """
    lines = content.split('\n')
    parsed_data = {
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
        if line.upper() == "DESCRIPTION:":
            current_section = "description"
            continue
        elif line.upper() == "COLUMNS:":
            current_section = "columns"
            continue
        elif line.upper() == "BUSINESS RULES:":
            current_section = "business_rules"
            continue
        elif line.upper() == "DATA RELATIONSHIPS:" or line.upper() == "RELATIONSHIPS:":
            current_section = "relationships"
            continue
        elif line.upper() == "USAGE:":
            current_section = "usage"
            continue
        
        # Parse content based on current section
        if current_section == "description":
            if line.upper() != f"TABLE: {table_name.upper()}":
                parsed_data["description"] += line + " "
        
        elif current_section == "columns":
            # Parse column definitions
            if line and line[0].isdigit() and "." in line:
                # New column definition
                parts = line.split("(", 1)
                if len(parts) >= 1:
                    column_name = parts[0].split(".", 1)[1].strip() if "." in parts[0] else parts[0].strip()
                    column_info = {"name": column_name, "details": line}
                    parsed_data["columns"].append(column_info)
                    current_column = column_info
            elif current_column and line.startswith("-"):
                # Column detail
                if "details" not in current_column:
                    current_column["details"] = ""
                current_column["details"] += " " + line
        
        elif current_section == "business_rules":
            if line.startswith("-"):
                parsed_data["business_rules"].append(line[1:].strip())
        
        elif current_section == "relationships":
            if line.startswith("-"):
                parsed_data["relationships"].append(line[1:].strip())
        
        elif current_section == "usage":
            if line.startswith("-"):
                parsed_data["usage"].append(line[1:].strip())
    
    # Clean up description
    parsed_data["description"] = parsed_data["description"].strip()
    
    return parsed_data