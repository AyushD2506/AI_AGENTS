import streamlit as st
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from dotenv import load_dotenv
import os

# Load .env file
# load_dotenv
import os

api_key = os.getenv("GROQ_API_KEY")
# API Key - Replace with your actual Groq API key
# api_key = api_key

# Page configuration
st.set_page_config(
    page_title="AI News Reporter",
    page_icon="📰",
    layout="wide"
)

# Title and description
st.title("📰 AI News Reporter")
st.markdown("*An enthusiastic AI agent that fetches and reports breaking news with flair!*")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Model selection
    model_options = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile", 
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768"
    ]
    selected_model = st.selectbox(
        "Select Model",
        model_options,
        index=0,
        help="Choose the language model for the agent"
    )
    
    # Agent settings
    st.subheader("Agent Settings")
    show_tool_calls = st.checkbox("Show Tool Calls", value=True)
    markdown_output = st.checkbox("Markdown Output", value=True)

# Main content area
if api_key == "YOUR_GROQ_API_KEY_HERE":
    st.warning("⚠️ Please replace 'YOUR_GROQ_API_KEY_HERE' with your actual Groq API key in the code.")
    st.stop()

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Initialize agent
try:
    if st.session_state.agent is None:
        st.session_state.agent = Agent(
            model=Groq(id=selected_model, api_key=api_key),
            description="You are an enthusiastic news reporter with a flair for storytelling!",
            tools=[DuckDuckGoTools()],
            show_tool_calls=show_tool_calls,
            markdown=markdown_output
        )
        st.success("✅ Agent initialized successfully!")
except Exception as e:
    st.error(f"❌ Error initializing agent: {str(e)}")
    st.stop()

# Chat interface
st.header("💬 Chat with the News Reporter")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about breaking news from any location..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Fetching latest news..."):
            try:
                # Create a placeholder for streaming response
                response_placeholder = st.empty()
                
                # Get response from agent
                response = st.session_state.agent.run(prompt)
                
                # Display the response
                if hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)
                
                response_placeholder.markdown(response_text)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
            except Exception as e:
                st.error(f"Error getting response: {str(e)}")

# Quick action buttons
st.header("🚀 Quick News Queries")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏔️ Jammu & Kashmir News"):
        prompt = "Tell me about a breaking news story from Jammu And Kashmir."
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

with col2:
    if st.button("🌍 World News"):
        prompt = "Tell me about the latest breaking news happening around the world."
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

with col3:
    if st.button("💼 Business News"):
        prompt = "Tell me about the latest breaking business news."
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

# Clear chat button
if st.button("🗑️ Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Powered by Groq LLM and DuckDuckGo Search • Built with Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Instructions
with st.expander("ℹ️ How to Use"):
    st.markdown("""
    1. **Setup**: Enter your Groq API key in the sidebar
    2. **Configure**: Choose your preferred model and settings
    3. **Chat**: Type any news query in the chat input
    4. **Quick Actions**: Use the preset buttons for common news queries
    5. **History**: View your conversation history in the chat area
    
    **Example Queries:**
    - "Tell me about breaking news from Delhi"
    - "What's happening in the tech industry today?"
    - "Give me sports news from India"
    - "What are the latest political developments?"
    """)