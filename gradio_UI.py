import gradio as gr

from database import Base, SessionLocal
from services.ai_services import agent_chat  

Base.metadata.create_all(bind=SessionLocal().get_bind())  # create tables if they don't exist

def user_message(user_input, history):
    db = SessionLocal()  # create a new database session
    bot_answer = agent_chat(user_input, db)  # pass the db session to the agent
    db.close()  # close the database session after use
    history = history + [(user_input, bot_answer)]
    return history, ""

def clear_chat():
    return [], ""

def main():
    with gr.Blocks() as demo:
        gr.Markdown("# Recipe Management System")
        gr.Markdown("Manage your recipes using AI.")

        chatbot = gr.Chatbot(label="Chat Interface")  # remove type="messages"
        user_input = gr.Textbox(
            label="Your message",
            placeholder="Ask me something about your recipes..."
        )

        send = gr.Button("Send")
        clear = gr.Button("Clear Chat")

        send.click(
            fn=user_message,
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