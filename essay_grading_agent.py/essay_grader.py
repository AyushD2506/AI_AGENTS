import os
import re
import streamlit as st
from typing import TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# Load from .env for fallback
try:
    api_key = st.secrets["GROQ_API_KEY"]  # For Streamlit Cloud
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
st.sidebar.markdown("🔑 **API Key Loaded:** " + ("✅" if api_key else "❌"))
  # Local fallback
model ="llama-3.3-70b-versatile"

# Essay input
st.title("📄 Essay Grader using LLMs")
essay = st.text_area("Enter your essay here:", height=400)
submit = st.button("Grade Essay")

# Define the State type
class State(TypedDict):
    essay: str
    relevance_score: float
    grammar_score: float
    structure_score: float
    depth_score: float
    final_score: float

# Helper to extract numeric score from model response
def extract_score(content: str) -> float:
    match = re.search(r'Score:\s*(\d+(\.\d+)?)', content)
    if match:
        return float(match.group(1))
    raise ValueError(f"Could not extract score from: {content}")

# Initialize LLM
def get_llm():
    return ChatGroq(model=model, api_key=api_key)

# Component scoring functions
def check_relevance(state: State) -> State:
    prompt = ChatPromptTemplate.from_template(
        "Analyze the relevance of the following essay to the given topic. "
        "Provide a relevance score between 0 and 1. "
        "Your response should start with 'Score: ' followed by the numeric score.\n\nEssay: {essay}"
    )
    result = get_llm().invoke(prompt.format(essay=state["essay"]))
    try:
        state["relevance_score"] = extract_score(result.content)
    except ValueError as e:
        st.error(f"Relevance Error: {e}")
        state["relevance_score"] = 0.0
    return state

def check_grammar(state: State) -> State:
    prompt = ChatPromptTemplate.from_template(
        "Analyze the grammar of the following essay. "
        "Provide a grammar score between 0 and 1. "
        "Your response should start with 'Score: ' followed by the numeric score.\n\nEssay: {essay}"
    )
    result = get_llm().invoke(prompt.format(essay=state["essay"]))
    try:
        state["grammar_score"] = extract_score(result.content)
    except ValueError as e:
        st.error(f"Grammar Error: {e}")
        state["grammar_score"] = 0.0
    return state

def analyze_structure(state: State) -> State:
    prompt = ChatPromptTemplate.from_template(
        "Analyze the structure of the following essay. "
        "Provide a structure score between 0 and 1. "
        "Your response should start with 'Score: ' followed by the numeric score.\n\nEssay: {essay}"
    )
    result = get_llm().invoke(prompt.format(essay=state["essay"]))
    try:
        state["structure_score"] = extract_score(result.content)
    except ValueError as e:
        st.error(f"Structure Error: {e}")
        state["structure_score"] = 0.0
    return state

def evaluate_depth(state: State) -> State:
    prompt = ChatPromptTemplate.from_template(
        "Evaluate the depth of analysis in the following essay. "
        "Provide a depth score between 0 and 1. "
        "Your response should start with 'Score: ' followed by the numeric score.\n\nEssay: {essay}"
    )
    result = get_llm().invoke(prompt.format(essay=state["essay"]))
    try:
        state["depth_score"] = extract_score(result.content)
    except ValueError as e:
        st.error(f"Depth Error: {e}")
        state["depth_score"] = 0.0
    return state

def calculate_final_score(state: State) -> State:
    state["final_score"] = (
        state["relevance_score"] * 0.3 +
        state["grammar_score"] * 0.2 +
        state["structure_score"] * 0.2 +
        state["depth_score"] * 0.3
    )
    return state

# Build graph
workflow = StateGraph(State)
workflow.add_node("check_relevance", check_relevance)
workflow.add_node("check_grammar", check_grammar)
workflow.add_node("analyze_structure", analyze_structure)
workflow.add_node("evaluate_depth", evaluate_depth)
workflow.add_node("calculate_final_score", calculate_final_score)

workflow.add_conditional_edges("check_relevance", lambda x: "check_grammar" if x["relevance_score"] > 0.5 else "calculate_final_score")
workflow.add_conditional_edges("check_grammar", lambda x: "analyze_structure" if x["grammar_score"] > 0.6 else "calculate_final_score")
workflow.add_conditional_edges("analyze_structure", lambda x: "evaluate_depth" if x["structure_score"] > 0.7 else "calculate_final_score")
workflow.add_conditional_edges("evaluate_depth", lambda x: "calculate_final_score")

workflow.set_entry_point("check_relevance")
workflow.add_edge("calculate_final_score", END)

app = workflow.compile()

# When user clicks "Grade Essay"
if submit:
    if not api_key:
        st.warning("Please enter your GROQ API key in the sidebar.")
    elif not essay.strip():
        st.warning("Please enter an essay.")
    else:
        with st.spinner("Evaluating essay..."):
            initial_state = State(
                essay=essay,
                relevance_score=0.0,
                grammar_score=0.0,
                structure_score=0.0,
                depth_score=0.0,
                final_score=0.0
            )
            result = app.invoke(initial_state)

        st.success("✅ Essay evaluation complete!")

        st.subheader("📊 Evaluation Scores")
        st.write(f"**Relevance Score:** {result['relevance_score']:.2f}")
        st.write(f"**Grammar Score:** {result['grammar_score']:.2f}")
        st.write(f"**Structure Score:** {result['structure_score']:.2f}")
        st.write(f"**Depth Score:** {result['depth_score']:.2f}")
        st.markdown("---")
        st.write(f"### 🏁 Final Score: `{result['final_score']:.2f}`")

