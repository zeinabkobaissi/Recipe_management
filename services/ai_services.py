from openai import OpenAI
import json
import os
from dotenv import load_dotenv
from database import SessionLocal
from services.recipe import create_recipe, get_all_recipes, update_recipe, delete_recipe
load_dotenv()


client = OpenAI(api_key=os.getenv("openai_key"))


tools = [
    {
        "type": "function",
        "function": {
            "name": "create_recipe",
            "description": "Create a new recipe",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "ingredients": {"type": "string"},
                    "instructions": {"type": "string"},
                    "status": {"type": "string"},
                    "cuisine_type": {"type": "string"}
                },
                "required": ["title", "ingredients", "instructions", "status", "cuisine_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_recipes",
            "description": "Get all recipes",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_recipe",
            "description": "Update an existing recipe",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "ingredients": {"type": "string"},
                    "instructions": {"type": "string"},
                    "status": {"type": "string"},
                    "cuisine_type": {"type": "string"}
                },
                "required": ["id", "title", "ingredients", "instructions", "status", "cuisine_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_recipe",
            "description": "Delete a recipe",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"}
                },
                "required": ["id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "search_recipes",
            "description": "Search recipes by query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    }
]
db = SessionLocal()  # create a new database session

def agent_chat(user_input, db):

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a recipe management assistant. "
                    "You can create, update, delete, or retrieve all recipes, and search recipes based on user queries. "
                    "Always call the correct tool when needed."
                ),
            },
            {"role": "user", "content": user_input},
        ],
        tools=tools,
    )

    message = response.choices[0].message

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        function_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        # Call backend function
        if function_name == "create_recipe":
            result = create_recipe(db, **args)

        elif function_name == "update_recipe":
            result = update_recipe(db, **args)

        elif function_name == "delete_recipe":
            result = delete_recipe(db, **args)

        elif function_name == "get_all_recipes":
            result = get_all_recipes(db)

        # Convert result to string for model
        tool_result = json.dumps(
            result if isinstance(result, dict) else str(result)
        )

        
        second_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a recipe management assistant."
                    ),
                },
                {"role": "user", "content": user_input},
                message,  # assistant tool call message
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                },
            ],
        )

        return second_response.choices[0].message.content

    return message.content