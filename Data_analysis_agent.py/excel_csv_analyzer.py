import streamlit as st
import pandas as pd
import os
import tempfile
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentType
from langchain_groq import ChatGroq  # <--- Groq integration

# Set page config
st.set_page_config(
    page_title="Data Analysis Assistant",
    page_icon="📊",
    layout="wide"
)

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "df" not in st.session_state:
    st.session_state.df = None

if "agent" not in st.session_state:
    st.session_state.agent = None

if "file_name" not in st.session_state:
    st.session_state.file_name = None

# App title
st.title("📊 Data Analysis Assistant")

# Sidebar for configuration and file upload
with st.sidebar:
    st.header("Configuration")

    # Groq API key input
    groq_api_key = st.text_input("Groq API Key", type="password")

    # Groq model selection
    model_name = st.selectbox(
        "Select Groq Model",
        ["llama3-8b-8192", "llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma-7b-it"],
        index=1
    )

    # File uploader (CSV and XLSX)
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

    if uploaded_file is not None and (st.session_state.file_name != uploaded_file.name):
        # Save the file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        # Load CSV or XLSX
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(tmp_path)
            else:
                df = pd.read_excel(tmp_path)
            
            st.session_state.df = df
            st.session_state.file_name = uploaded_file.name

            st.success(f"File loaded: {uploaded_file.name}")
            st.write(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")

            if groq_api_key:
                llm = ChatGroq(
                    api_key=groq_api_key,
                    model_name=model_name
                )

                agent = create_pandas_dataframe_agent(
                    llm=llm,
                    df=df,
                    verbose=True,
                    handle_parsing_errors=True,
                    allow_dangerous_code=True,
                    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                )

                st.session_state.agent = agent
                st.session_state.messages = []  # Reset messages

            else:
                st.error("Please enter your Groq API key.")

        except Exception as e:
            st.error(f"Error loading file: {e}")

    # Data preview
    if st.session_state.df is not None:
        st.subheader("Data Preview")
        st.dataframe(st.session_state.df.head(5), use_container_width=True)

        st.subheader("Column Information")
        cols = st.session_state.df.columns.tolist()
        col_info = "\n".join([f"- {col} ({st.session_state.df[col].dtype})" for col in cols])
        st.text(col_info)

# Chat interface
st.subheader("Chat with your data")

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Input for new question
if prompt := st.chat_input("Ask a question about your data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    if st.session_state.df is None:
        with st.chat_message("assistant"):
            st.write("Please upload a CSV or Excel file first.")
        st.session_state.messages.append({"role": "assistant", "content": "Please upload a CSV or Excel file first."})
    elif not groq_api_key:
        with st.chat_message("assistant"):
            st.write("Please enter your Groq API key in the sidebar.")
        st.session_state.messages.append({"role": "assistant", "content": "Please enter your Groq API key in the sidebar."})
    else:
        with st.spinner("Thinking..."):
            try:
                with st.chat_message("assistant"):
                    response = st.session_state.agent.invoke({"input": prompt})
                    output = response.get("output", str(response))
                    st.write(output)
                    st.session_state.messages.append({"role": "assistant", "content": output})
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                with st.chat_message("assistant"):
                    st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Initial instructions
if not st.session_state.messages:
    st.info("""
    👋 Welcome to the Data Analysis Assistant!

    1. Upload a CSV or Excel file from the sidebar
    2. Enter your Groq API key
    3. Ask questions like:
        - What are the first 5 rows?
        - How many missing values are in each column?
        - What's the average of [column]?
        - Show a histogram of [column]
    """)
