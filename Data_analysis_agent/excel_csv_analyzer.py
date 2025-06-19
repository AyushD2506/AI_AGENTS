import streamlit as st
import pandas as pd
import os
import tempfile
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentType
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage
import hashlib
import json
import os

api_key = os.getenv("GROQ_API_KEY")
print("API Key:", api_key)
# Set page config
st.set_page_config(
    page_title="Enhanced Data Analysis Assistant",
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

if "memory" not in st.session_state:
    st.session_state.memory = None

if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = []

if "data_summary" not in st.session_state:
    st.session_state.data_summary = None

# Helper functions
def generate_data_summary(df):
    """Generate a comprehensive summary of the dataset for the agent"""
    summary = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "column_info": {},
        "data_types": df.dtypes.to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
        "categorical_columns": df.select_dtypes(include=['object']).columns.tolist(),
        "date_columns": df.select_dtypes(include=['datetime']).columns.tolist()
    }
    
    # Add basic statistics for numeric columns
    if summary["numeric_columns"]:
        summary["numeric_stats"] = df[summary["numeric_columns"]].describe().to_dict()
    
    # Add unique value counts for categorical columns (limited to avoid too much data)
    for col in summary["categorical_columns"][:5]:  # Limit to first 5 categorical columns
        unique_count = df[col].nunique()
        if unique_count <= 20:  # Only show unique values if reasonable number
            summary["column_info"][col] = {
                "unique_values": df[col].unique().tolist(),
                "unique_count": unique_count
            }
        else:
            summary["column_info"][col] = {"unique_count": unique_count}
    
    return summary

def create_context_aware_prompt(user_question, conversation_history, data_summary):
    """Create a context-aware prompt that includes conversation history and data info"""
    context_prompt = f"""
You are analyzing a dataset with the following characteristics:
- Total rows: {data_summary['total_rows']}
- Total columns: {data_summary['total_columns']}
- Column names and types: {data_summary['data_types']}
- Missing values per column: {data_summary['missing_values']}

IMPORTANT: You have access to the COMPLETE dataset with {data_summary['total_rows']} rows. 
Do NOT limit your analysis to just the first few rows - analyze the entire dataset.

Previous conversation context:
{conversation_history[-3:] if conversation_history else "No previous context"}

Current question: {user_question}

Please provide a comprehensive analysis using the entire dataset.
"""
    return context_prompt

def update_conversation_context(user_input, ai_response):
    """Update conversation context for memory"""
    context_entry = {
        "user": user_input,
        "assistant": ai_response,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    st.session_state.conversation_context.append(context_entry)
    
    # Keep only last 10 interactions to prevent context from getting too long
    if len(st.session_state.conversation_context) > 10:
        st.session_state.conversation_context = st.session_state.conversation_context[-10:]

# App title
st.title("📊 Enhanced Data Analysis Assistant with Memory")

# Sidebar for configuration and file upload
with st.sidebar:
    st.header("Configuration")
    
    # Memory settings
    st.subheader("Memory Settings")
    memory_window = st.slider("Conversation Memory Window", min_value=5, max_value=20, value=10, 
                             help="Number of previous interactions to remember")

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
            
            # Generate data summary for the agent
            st.session_state.data_summary = generate_data_summary(df)

            st.success(f"File loaded: {uploaded_file.name}")
            st.write(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")

            # Initialize memory for this session
            st.session_state.memory = ConversationBufferWindowMemory(
                k=memory_window,
                return_messages=True,
                memory_key="chat_history"
            )

            if True:  # Always true since API key is hardcoded
                llm = ChatGroq(
                    api_key="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",
                    model_name=model_name,
                    temperature=0.1  # Lower temperature for more consistent analysis
                )

                # Create agent with memory
                agent = create_pandas_dataframe_agent(
                    llm=llm,
                    df=df,  # Pass the complete dataframe
                    verbose=True,
                    handle_parsing_errors=True,
                    allow_dangerous_code=True,
                    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    memory=st.session_state.memory,
                    prefix=f"""
You are working with a pandas dataframe called `df` with {df.shape[0]} rows and {df.shape[1]} columns.
CRITICAL: Always analyze the COMPLETE dataframe with all {df.shape[0]} rows, not just a subset.
The dataframe columns are: {list(df.columns)}

When performing analysis:
1. Always use the full dataset (df) not df.head() or subsets
2. Provide comprehensive statistics and insights
3. Reference previous conversation context when relevant
4. Be specific about the data you're analyzing

Remember: You have access to the entire dataset with {df.shape[0]} rows of data.
"""
                )

                st.session_state.agent = agent
                # Don't reset messages - preserve conversation history
                
                st.success("🧠 Agent initialized with memory capabilities!")

            else:
                st.error("Please enter your Groq API key.")

        except Exception as e:
            st.error(f"Error loading file: {e}")

    # Data preview section
    if st.session_state.df is not None:
        st.subheader("📋 Data Overview")
        
        # Dataset info
        st.metric("Total Rows", st.session_state.df.shape[0])
        st.metric("Total Columns", st.session_state.df.shape[1])
        
        # Show preview (for user reference only)
        with st.expander("Data Preview (First 5 rows - for reference only)", expanded=False):
            st.info("⚠️ This preview shows only the first 5 rows for your reference. The AI agent analyzes the complete dataset.")
            st.dataframe(st.session_state.df.head(5), use_container_width=True)

        # Column information
        with st.expander("Column Information", expanded=False):
            col_info_df = pd.DataFrame({
                'Column': st.session_state.df.columns,
                'Data Type': st.session_state.df.dtypes,
                'Non-Null Count': st.session_state.df.count(),
                'Missing Values': st.session_state.df.isnull().sum()
            })
            st.dataframe(col_info_df, use_container_width=True)
        
        # Memory status
        if st.session_state.conversation_context:
            st.subheader("🧠 Memory Status")
            st.write(f"Remembered interactions: {len(st.session_state.conversation_context)}")
            
            if st.button("Clear Memory"):
                st.session_state.conversation_context = []
                st.session_state.memory = ConversationBufferWindowMemory(
                    k=memory_window,
                    return_messages=True,
                    memory_key="chat_history"
                )
                st.success("Memory cleared!")
                st.rerun()

# Chat interface
st.subheader("💬 Chat with your data")

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
            response = "Please upload a CSV or Excel file first."
            st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    else:
        with st.spinner("🤔 Analyzing your data..."):
            try:
                with st.chat_message("assistant"):
                    # Create context-aware prompt
                    if st.session_state.data_summary:
                        enhanced_prompt = create_context_aware_prompt(
                            prompt, 
                            st.session_state.conversation_context,
                            st.session_state.data_summary
                        )
                    else:
                        enhanced_prompt = prompt
                    
                    # Get response from agent
                    response = st.session_state.agent.invoke({"input": enhanced_prompt})
                    output = response.get("output", str(response))
                    
                    st.write(output)
                    
                    # Update conversation context
                    update_conversation_context(prompt, output)
                    
                    # Add to message history
                    st.session_state.messages.append({"role": "assistant", "content": output})
                    
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                with st.chat_message("assistant"):
                    st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Enhanced initial instructions
if not st.session_state.messages:
    st.info("""
    👋 **Welcome to the Data Analysis Assistant!**

   

    **How to use:**
    1. 📁 Upload a CSV or Excel file from the sidebar
    2. 💬 Ask questions about your data
    3. 🔄 Follow up with related questions - the assistant remembers your conversation!

    **Example questions:**
    - "What are the key statistics of this dataset?"
    - "Show me correlations between numeric columns"
    - "Based on our previous analysis, can you dive deeper into [specific finding]?"
    - "What patterns do you see in the data we explored earlier?"
    
    """)

# Footer with tips
if st.session_state.df is not None:
    st.markdown("---")
    st.markdown("""
    💡 **Tips for better analysis:**
    - Ask follow-up questions to dive deeper into insights
    - 
    """)