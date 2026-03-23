# services/langgraph_agent.py

import ast
import os
from typing import Literal, Optional
import re
import json

from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from database import SessionLocal
from services.recipe import (
    create_recipe,
    get_all_recipes,
    update_recipe,
    delete_recipe,
    search_recipes,
    get_recipe_by_name,
)
# Load environment variables from `.env` (if present).
load_dotenv()

_openai_api_key = os.getenv("openai_key") or os.getenv("OPENAI_API_KEY")
if not _openai_api_key:
    raise RuntimeError(
        "OpenAI API key is not set. Make sure your .env contains `openai_key=...` "
        "and you run `python gradio_UI.py` from the project root."
    )

# ---------- State definition ----------

class AgentState(TypedDict):
    # Conversation history
    messages: Annotated[list, add_messages]
    # Optional explicit intent provided by the UI / user
    intent: Optional[str]


llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=_openai_api_key,
)


def _to_int(value):
    """Convert values like '15', '15 minutes', or 15 to int; otherwise None."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            return int(match.group(0))
    return None


def _json_loads_lenient(raw: str) -> dict:
    """
    Parse JSON from LLMs that often add trailing commas or minor noise.
    """
    s = (raw or "").strip()
    if not s:
        raise ValueError("empty JSON string")

    # Drop trailing commas before } or ] (invalid in strict JSON but common from LLMs).
    s = re.sub(r",\s*}", "}", s)
    s = re.sub(r",\s*]", "]", s)

    try:
        out = json.loads(s)
        if isinstance(out, dict):
            return out
    except json.JSONDecodeError:
        pass

    # Python dict literal (single-quoted keys) — only when it looks like a dict literal.
    if s.startswith("{") and s.endswith("}"):
        try:
            out = ast.literal_eval(s)
            if isinstance(out, dict):
                return out
        except (SyntaxError, ValueError):
            pass

    raise ValueError(f"Could not parse as JSON object: {s[:300]}")


def _parse_json_from_llm(content: str) -> dict:
    """
    Parse JSON from LLM output, including fenced markdown like ```json ... ```.
    """
    text = (content or "").strip()
    if not text:
        raise ValueError("LLM returned empty content")

    # Direct JSON first.
    try:
        return _json_loads_lenient(text)
    except ValueError:
        pass

    # Try fenced code block extraction.
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence_match:
        fenced = fence_match.group(1).strip()
        return _json_loads_lenient(fenced)

    # Try extracting first JSON object in the text.
    obj_match = re.search(r"\{[\s\S]*\}", text)
    if obj_match:
        return _json_loads_lenient(obj_match.group(0))

    raise ValueError(f"Could not parse JSON from LLM output: {text[:200]}")

# ---------- Tool nodes (use your existing functions) ----------

def create_recipe_node(state: AgentState) -> AgentState:
    db = SessionLocal()
    user_msg = state["messages"][-1]
    text = user_msg.content

    # Simple extraction – in a real app you’d parse this more robustly or call another LLM
    # Here we just ask the LLM to produce a JSON and then call `create_recipe`.
    extract = llm.invoke(
        [
            (
                "system",
                "Extract a JSON object with keys: title, ingredients, instructions, "
                "status, cuisine_type, preparation_time, serving_size from the user text. "
                "If something is missing, make a reasonable assumption.",
            ),
            ("human", text),
        ]
    )
    data = _parse_json_from_llm(extract.content)

    recipe = create_recipe(
        db=db,
        title=data["title"],
        ingredients=data["ingredients"],
        instructions=data["instructions"],
        status=data["status"],
        cuisine_type=data["cuisine_type"],
        preparation_time=_to_int(data.get("preparation_time")),
        serving_size=_to_int(data.get("serving_size")),
    )
    db.close()

    reply = f"Created recipe '{recipe.title}' with id {recipe.id}."
    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=reply)],
    }


def update_recipe_node(state: AgentState) -> AgentState:
    db = SessionLocal()
    user_msg = state["messages"][-1]
    text = user_msg.content

    extract = llm.invoke(
        [
            (
                "system",
                "Extract a single JSON object with keys: id (integer, required), and "
                "optional keys: title, ingredients, instructions, status, cuisine_type, "
                "preparation_time, serving_size.\n"
                "Rules:\n"
                "- Use double quotes for all keys and string values. No trailing commas.\n"
                "- Include only fields the user wants to change; omit keys you are not updating.\n"
                "- id must be the recipe id to update.",
            ),
            ("human", text),
        ]
    )
    try:
        data = _parse_json_from_llm(extract.content)
    except (ValueError, json.JSONDecodeError) as e:
        db.close()
        reply = (
            "I could not read the update details from your message (invalid JSON from the model). "
            "Try again with the recipe id and only the fields to change, e.g. "
            '"update recipe 2: change ingredients to ...". '
            f"Detail: {e}"
        )
        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=reply)],
        }

    if "id" not in data or data["id"] is None:
        db.close()
        reply = "I need a recipe **id** to update (e.g. “update recipe 3: …”). Use **list recipes** to see ids."
        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=reply)],
        }

    recipe = update_recipe(
        db=db,
        id=data["id"],
        title=data.get("title"),
        ingredients=data.get("ingredients"),
        instructions=data.get("instructions"),
        status=data.get("status"),
        cuisine_type=data.get("cuisine_type"),
        preparation_time=_to_int(data.get("preparation_time")),
        serving_size=_to_int(data.get("serving_size")),
    )
    db.close()

    if recipe is None:
        reply = "I couldn't find a recipe with that id to update."
    else:
        reply = f"Updated recipe '{recipe.title}' (id {recipe.id})."

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=reply)],
    }


def delete_recipe_node(state: AgentState) -> AgentState:
    db = SessionLocal()
    user_msg = state["messages"][-1]
    text = user_msg.content

    extract = llm.invoke(
        [
            (
                "system",
                "Extract a JSON object with key: id (int) from the user text.",
            ),
            ("human", text),
        ]
    )
    data = _parse_json_from_llm(extract.content)

    recipe = delete_recipe(db=db, recipe_id=data["id"])
    db.close()

    if recipe is None:
        reply = "I couldn't find a recipe with that id to delete."
    else:
        reply = f"Deleted recipe '{recipe.title}' (id {recipe.id})."

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=reply)],
    }


def list_recipes_node(state: AgentState) -> AgentState:
    db = SessionLocal()
    recipes = get_all_recipes(db)
    db.close()

    if not recipes:
        reply = "You don't have any recipes saved yet."
    else:
        lines = [
            f"{r.id}: {r.title} ({r.cuisine_type}, status: {r.status})"
            for r in recipes
        ]
        reply = "Here are your recipes:\n" + "\n".join(lines)

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=reply)],
    }


def search_recipes_node(state: AgentState) -> AgentState:
    db = SessionLocal()
    user_msg = state["messages"][-1]
    text = user_msg.content

    extract = llm.invoke(
        [
            (
                "system",
                "From the user text, extract a JSON object like {\"query\": \"...\"} "
                "representing the search query.",
            ),
            ("human", text),
        ]
    )
    data = _parse_json_from_llm(extract.content)

    results = search_recipes(db=db, query=data["query"])
    db.close()

    if not results:
        reply = f"No recipes found matching '{data['query']}'."
    else:
        lines = [
            f"{r.id}: {r.title} ({r.cuisine_type}, status: {r.status})"
            for r in results
        ]
        reply = "Here are the recipes I found:\n" + "\n".join(lines)

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=reply)],
    }

def get_recipe_by_name_node(state: AgentState) -> AgentState:
    user_msg = state["messages"][-1]
    text = user_msg.content
    extract = llm.invoke(
        [
            (
                "system",
                "The user wants ONE recipe loaded from the database by name/title.\n"
                'Return ONLY valid JSON: {"name": "<recipe title as the user means it>"}.\n'
                "Rules:\n"
                "- Put the recipe name/title in `name` (strip quotes). Examples: after "
                "'get recipe for', 'recipe called', 'named', 'about', use that phrase.\n"
                "- If the user says only 'get recipe' / 'show the recipe' with no title, "
                'use {"name": ""}.\n'
                "- Do not invent a title; use the closest phrase from the user message.",
            ),
            ("human", text),
        ]
    )
    data = _parse_json_from_llm(extract.content)
    raw_name = (data.get("name") or "").strip()

    if not raw_name:
        db = SessionLocal()
        titles = [r.title for r in get_all_recipes(db)]
        db.close()
        if not titles:
            reply = "You don't have any recipes saved yet. Create one first, then ask again with its title."
        else:
            preview = "\n".join(f"  - {t}" for t in titles[:20])
            more = "\n  ..." if len(titles) > 20 else ""
            reply = (
                "Say which recipe you want, e.g. **get recipe Chicken Burger**.\n"
                f"Saved titles:\n{preview}{more}"
            )
        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=reply)],
        }

    db = SessionLocal()
    recipe = get_recipe_by_name(db=db, name=raw_name)
    db.close()
    if recipe is None:
        reply = f"No recipe found matching '{raw_name}'. Try **list** recipes to see exact titles."
    else:
        # Every ORM column from the database row
        reply = (
            "Here is all information for that recipe from the database:\n"
            f"id: {recipe.id}\n"
            f"title: {recipe.title}\n"
            f"status: {recipe.status}\n"
            f"cuisine_type: {recipe.cuisine_type}\n"
            f"preparation_time (minutes): {recipe.preparation_time}\n"
            f"serving_size: {recipe.serving_size}\n"
            f"ingredients:\n{recipe.ingredients}\n"
            f"instructions:\n{recipe.instructions}"
        )
    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=reply)],
    }
# ---------- LLM-only node (no tools) ----------

def llm_only_node(state: AgentState) -> AgentState:
    # The model just answers based on conversation, without DB tools.
    answer = llm.invoke(
        [
            (
                "system",
                "You are a helpful recipe assistant. Answer based only on your own "
                "knowledge and the conversation so far. Do NOT create, update, or "
                "delete anything in the database.",
            ),
            *state["messages"],
        ]
    )
    return {
        **state,
        "messages": state["messages"] + [answer],
    }


# ---------- Router node ----------

def router_node(state: AgentState) -> Literal[
    "create_recipe_node",
    "update_recipe_node",
    "delete_recipe_node",
    "list_recipes_node",
    "search_recipes_node",
    "get_recipe_by_name_node",
    "llm_only_node",
]:
    """
    Decide what to do based on explicit intent.
    If no intent (or unrecognized), let the LLM handle it alone (llm_only_node).
    """
    intent = (state.get("intent") or "").lower()

    if intent == "create":
        return "create_recipe_node"
    if intent == "update":
        return "update_recipe_node"
    if intent == "delete":
        return "delete_recipe_node"
    if intent in ("list", "get_all", "all"):
        return "list_recipes_node"
    if intent == "search":
        return "search_recipes_node"
    if intent == "get":
        return "get_recipe_by_name_node"
    # No explicit usable intent: let the LLM "do its research alone"
    return "llm_only_node"


# ---------- Build the graph ----------

workflow = StateGraph(AgentState)

def _passthrough_node(state: AgentState) -> AgentState:
    return state

# Start from a router step, then choose the path
workflow.add_node("router", _passthrough_node)
workflow.add_node("create_recipe_node", create_recipe_node)
workflow.add_node("update_recipe_node", update_recipe_node)
workflow.add_node("delete_recipe_node", delete_recipe_node)
workflow.add_node("list_recipes_node", list_recipes_node)
workflow.add_node("search_recipes_node", search_recipes_node)
workflow.add_node("get_recipe_by_name_node", get_recipe_by_name_node)
workflow.add_node("llm_only_node", llm_only_node)

workflow.set_entry_point("router")

# From router to the chosen node, and from each node to END
workflow.add_conditional_edges(
    "router",
    router_node,
    {
        "create_recipe_node": "create_recipe_node",
        "update_recipe_node": "update_recipe_node",
        "delete_recipe_node": "delete_recipe_node",
        "list_recipes_node": "list_recipes_node",
        "search_recipes_node": "search_recipes_node",
        "get_recipe_by_name_node": "get_recipe_by_name_node",
        "llm_only_node": "llm_only_node",
    },
)
workflow.add_edge("create_recipe_node", END)
workflow.add_edge("update_recipe_node", END)
workflow.add_edge("delete_recipe_node", END)
workflow.add_edge("list_recipes_node", END)
workflow.add_edge("search_recipes_node", END)
workflow.add_edge("get_recipe_by_name_node", END)
workflow.add_edge("llm_only_node", END)

app = workflow.compile()


# ---------- Convenience function for your UI ----------

def run_recipe_agent(user_input: str, intent: Optional[str] = None) -> str:
    """
    Call this from your Gradio UI.

    - If `intent` is one of: create, update, delete, list, search,get
      the router will call the corresponding tool node.
    - If `intent` is None or unrecognized, the router sends it to llm_only_node.
    """
    initial_state: AgentState = {
        "messages": [HumanMessage(content=user_input)],
        "intent": intent,
    }

    final_state = app.invoke(initial_state)
    last_message = final_state["messages"][-1]
    return last_message.content