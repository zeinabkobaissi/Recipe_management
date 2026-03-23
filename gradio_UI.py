import re

import gradio as gr

from database import Base, SessionLocal,engine

from services.langraph_agent import run_recipe_agent

Base.metadata.create_all(bind=engine)  # create tables if they don't exist

def _infer_intent(user_text: str):
    """
    Very small keyword-based intent inference for the UI.

    The LangGraph router currently relies on an explicit `intent` to call DB tools.
    """
    text = (user_text or "").lower()

    if "create" in text:
        return "create"
    if "update" in text or "edit" in text:
        return "update"
    if "delete" in text or "remove" in text:
        return "delete"
    if "search" in text:
        return "search"

    # One recipe by name (use \\brecipe\\b so "get recipes" is not mistaken for "get recipe")
    if (
        re.search(r"\b(get|fetch|find)\s+recipe\b", text)
        or "recipe by name" in text
        or re.search(r"\bshow\s+(me\s+)?(the\s+)?recipe\b", text)
    ) and " all " not in f" {text} ":
        return "get"

    # List all recipes (avoid treating "get recipe X" as list)
    if ("list" in text or "get all" in text or "show all" in text) and re.search(
        r"\brecipes?\b", text
    ):
        return "list"
    if "all" in text and re.search(r"\brecipes?\b", text) and not re.search(
        r"\b(get|fetch)\s+recipe\b", text
    ):
        return "list"

    return None


def chat_fn(user_text: str, chat_history):
    # Older Gradio versions use "messages" format by default:
    # [{"role": "user"|"assistant", "content": "..."}]
    chat_history = chat_history or []

    intent = _infer_intent(user_text)
    reply = run_recipe_agent(user_text, intent=intent)

    chat_history = chat_history + [
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": reply},
    ]
    # Clear the textbox after sending.
    return chat_history, ""




def clear_chat():
   return [], ""

def main():
    with gr.Blocks() as demo:
        gr.Markdown("# Recipe Management System")
        gr.Markdown("Manage your recipes using AI.")

        chatbot = gr.Chatbot(label="Chat Interface")
        user_input = gr.Textbox(
            label="Your message",
            placeholder="Ask me something about your recipes..."
        )

        send = gr.Button("Send")
        clear = gr.Button("Clear Chat")

        send.click(
            fn=chat_fn,
            inputs=[user_input, chatbot],
            outputs=[chatbot, user_input],
        )

        clear.click(
            fn=clear_chat,
            inputs=[],
            outputs=[chatbot, user_input],
        )

    demo.launch()

if __name__ == "__main__":
    main()