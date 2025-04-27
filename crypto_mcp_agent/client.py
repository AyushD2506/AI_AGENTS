import asyncio
import gradio as gr
from langchain_groq import ChatGroq
from mcp_use import MCPClient, MCPAgent
import os
from dotenv import load_dotenv

# Initialize environment and MCP components
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
config_file = "crypto_mcp_agent/config.json"

# Initialize MCP client and agent
client = MCPClient.from_config_file(config_file)
llm = ChatGroq(model="qwen-qwq-32b")
agent = MCPAgent(
    llm=llm,
    client=client,
    max_steps=15,
    memory_enabled=True
)

# Store chat history
chat_history = []

async def process_user_input(user_input, history):
    global chat_history
    if user_input.lower() == "exit":
        yield history + [["You", "Ending Conversation"]]
        if client and client.sessions():
            await client.close_all_sessions()
        return
    elif user_input.lower() == "clear":
        agent.clear_conversation_history()
        chat_history = []
        yield [["System", "Memory Rebooted"]]
        return

    # Append user input to history
    history.append(["You", user_input])
    yield history

    # Process agent response
    try:
        response = await agent.run(user_input)
        history.append(["Assistant", response])
        yield history
    except Exception as e:
        history.append(["System", f"Error: {str(e)}"])
        yield history

def update_chat_history(history):
    """Format chat history for Gradio Chatbot component"""
    return [(msg[0], msg[1]) for msg in history]

def clear_conversation():
    """Clear the conversation history and reset the agent"""
    global chat_history
    agent.clear_conversation_history()
    chat_history = []
    return [["System", "Memory Rebooted"]], ""

def exit_conversation():
    """Simulate exit and close sessions"""
    global chat_history
    asyncio.run(client.close_all_sessions())
    chat_history.append(["System", "Conversation Ended"])
    return chat_history, ""

# Gradio interface
with gr.Blocks(title="MCP Interactive Chatbot") as demo:
    gr.Markdown("# MCP Interactive Chatbot")
    gr.Markdown("Type your message below. Use 'clear' to reset the conversation or 'exit' to end.")
    
    # Chatbot display
    chatbot = gr.Chatbot(label="Conversation", height=400)
    
    # Input and buttons
    with gr.Row():
        user_input = gr.Textbox(label="Your Message", placeholder="Type your message here...")
        send_button = gr.Button("Send")
    
    with gr.Row():
        clear_button = gr.Button("Clear Conversation")
        exit_button = gr.Button("Exit")
    
    # Event handlers
    send_button.click(
        fn=process_user_input,
        inputs=[user_input, chatbot],
        outputs=[chatbot],
    ).then(
        fn=update_chat_history,
        inputs=chatbot,
        outputs=chatbot
    )
    
    user_input.submit(
        fn=process_user_input,
        inputs=[user_input, chatbot],
        outputs=[chatbot],
    ).then(
        fn=update_chat_history,
        inputs=chatbot,
        outputs=chatbot
    )
    
    clear_button.click(
        fn=clear_conversation,
        inputs=None,
        outputs=[chatbot, user_input]
    )
    
    exit_button.click(
        fn=exit_conversation,
        inputs=None,
        outputs=[chatbot, user_input]
    )

# Launch the Gradio app
if __name__ == "__main__":
    demo.launch()