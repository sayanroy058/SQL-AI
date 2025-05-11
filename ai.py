import os
import json
from openai import OpenAI

# Get OpenAI API key from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def generate_sql_query(natural_language_query, schema_info, db_type='mysql'):
    """
    Generate SQL query from natural language using OpenAI API

    Args:
        natural_language_query (str): User's question in natural language
        schema_info (dict): Database schema information
        db_type (str): Database type ('mysql' or 'postgresql')

    Returns:
        str: Generated SQL query
    """
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

    # Format the schema information for the prompt
    schema_description = ""
    for table_name, columns in schema_info.items():
        schema_description += f"Table: {table_name}\n"
        schema_description += "Columns:\n"
        for column in columns:
            schema_description += f"  - {column['Field']} ({column['Type']})"
            if column.get('Key') == 'PRI':
                schema_description += " PRIMARY KEY"
            schema_description += "\n"
        schema_description += "\n"

    # Adjust syntax guidance based on database type
    syntax_guide = "MySQL" if db_type.lower() == 'mysql' else "PostgreSQL"

    # Create prompt for OpenAI with strict output formatting
    prompt = f"""
You are a SQL generator. Based on the following database schema:

{schema_description}

Convert this natural language question into a valid, clean, and properly formatted SQL query:
"{natural_language_query}"

- Use correct {syntax_guide} syntax.
- Only return the SQL query. Do NOT include explanations, code blocks, or markdown.
- Do not wrap the query in backticks or any additional formatting.
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert SQL developer that converts natural language to valid SQL."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Lower temperature for more deterministic output
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        raise Exception(f"Error generating SQL query: {str(e)}")

def generate_natural_language_result(natural_language_query, sql_query, result):
    """
    Generate natural language explanation of query results

    Args:
        natural_language_query (str): Original user question
        sql_query (str): Generated SQL query
        result (list/dict): Result of SQL query execution

    Returns:
        str: Natural language explanation of results
    """
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

    # Convert result to string representation
    result_str = json.dumps(result, indent=2)

    # Create prompt for OpenAI
    prompt = f"""
I generated the following SQL query based on this question:
Question: "{natural_language_query}"
SQL Query: {sql_query}

The query produced these results:
{result_str}

Please explain these results in natural language. Use a friendly, concise tone. Include specific data points from the results but don't simply list everything. Focus on answering the original question in a way that would be helpful to someone who doesn't know SQL.
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at explaining database query results in plain language."},
                {"role": "user", "content": prompt}
            ],
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        raise Exception(f"Error generating natural language explanation: {str(e)}")
