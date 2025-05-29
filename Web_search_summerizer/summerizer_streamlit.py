import streamlit as st
import os
from typing import List, Dict, Any, TypedDict, Annotated
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError as e:
    DDGS_AVAILABLE = False
    st.error(f"Error importing duckduckgo-search: {str(e)}")

# Alternative search implementation using requests
try:
    import requests
    from urllib.parse import quote_plus
    import json
    import re
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, END
import operator
import json
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="WebSearch React Agent",
    page_icon="🔍",
    layout="wide"
)

# Custom search class to handle different versions and fallbacks
class CustomSearchTool:
    def __init__(self):
        self.ddgs_available = DDGS_AVAILABLE
        self.requests_available = REQUESTS_AVAILABLE
        self.session = requests.Session() if REQUESTS_AVAILABLE else None
        if self.session:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
    
    def search_with_ddgs(self, query, max_results=10):
        """Try different DDGS methods"""
        methods_to_try = [
            lambda: list(DDGS().text(query, max_results=max_results)),
            lambda: list(DDGS(timeout=30).text(query, max_results=max_results)),
            lambda: self._ddgs_context_manager(query, max_results)
        ]
        
        for i, method in enumerate(methods_to_try):
            try:
                results = method()
                if results:
                    return results
            except Exception as e:
                if i == len(methods_to_try) - 1:  # Last method
                    raise e
                continue
        return []
    
    def _ddgs_context_manager(self, query, max_results):
        """Try with context manager"""
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    
    def search_with_requests(self, query, max_results=10):
        """Fallback search using direct requests to DuckDuckGo"""
        try:
            # First, get a token from DuckDuckGo
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get('https://api.duckduckgo.com/', params=params, timeout=10)
            data = response.json()
            
            results = []
            
            # Extract results from the API response
            if 'RelatedTopics' in data:
                for topic in data['RelatedTopics'][:max_results]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        result = {
                            'title': topic.get('Text', '')[:100] + '...' if len(topic.get('Text', '')) > 100 else topic.get('Text', ''),
                            'href': topic.get('FirstURL', ''),
                            'body': topic.get('Text', '')
                        }
                        results.append(result)
            
            # If no results from RelatedTopics, try Abstract
            if not results and 'Abstract' in data and data['Abstract']:
                result = {
                    'title': data.get('Heading', 'Search Result'),
                    'href': data.get('AbstractURL', ''),
                    'body': data.get('Abstract', '')
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            raise Exception(f"Requests fallback failed: {str(e)}")
    
    def search(self, query, max_results=10):
        """Main search method with fallbacks"""
        results = []
        error_messages = []
        
        # Try DDGS first if available
        if self.ddgs_available:
            try:
                results = self.search_with_ddgs(query, max_results)
                if results:
                    return results
            except Exception as e:
                error_messages.append(f"DDGS error: {str(e)}")
        
        # Try requests fallback
        if self.requests_available and not results:
            try:
                results = self.search_with_requests(query, max_results)
                if results:
                    return results
            except Exception as e:
                error_messages.append(f"Requests error: {str(e)}")
        
        # If no results, create a mock result with error info
        if not results:
            results = [{
                'title': f'Search Error for: {query}',
                'href': '',
                'body': f'Unable to perform search. Errors: {"; ".join(error_messages)}'
            }]
        
        return results
# State definition for LangGraph
class AgentState(TypedDict):
    messages: Annotated[List[Dict], operator.add]
    query: str
    search_results: List[str]
    processed_results: List[Document]
    final_answer: str
    iteration_count: int

class WebSearchReactAgent:
    def __init__(self, groq_api_key: str):
        self.groq_api_key = groq_api_key
        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.1
        )
        
        # Use custom search tool instead of DDGS directly
        self.search_tool = CustomSearchTool()
        
        # Initialize embeddings - try local model first, then fallback to online
        local_model_path = "./models/embeddings/all-MiniLM-L6-v2"
        if os.path.exists(local_model_path):
            try:
                self.embeddings = HuggingFaceEmbeddings(
                    model_name=local_model_path,
                    model_kwargs={'device': 'cpu'}
                )
                st.success(f"✅ Using local embeddings model from: {local_model_path}")
            except Exception as e:
                st.warning(f"Failed to load local model: {str(e)}")
                st.info("Falling back to online model...")
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
        else:
            st.info("Local embeddings model not found. Using online model...")
            st.warning("💡 Tip: Run the download_embeddings.py script to cache the model locally for faster loading!")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.vector_store = None
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("search", self._search_node)
        workflow.add_node("process", self._process_node)
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("decide", self._decide_node)
        
        # Set entry point
        workflow.set_entry_point("search")
        
        # Add edges
        workflow.add_edge("search", "process")
        workflow.add_edge("process", "generate")
        workflow.add_edge("generate", "decide")
        workflow.add_conditional_edges(
            "decide",
            self._should_continue,
            {
                "continue": "search",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def _search_node(self, state: AgentState) -> AgentState:
        """Perform web search using custom search tool"""
        try:
            query = state["query"]
            
            # Use custom search tool
            results = self.search_tool.search(query, max_results=10)
            
            search_results = []
            for result in results:
                search_result = f"Title: {result.get('title', '')}\nURL: {result.get('href', '')}\nSnippet: {result.get('body', '')}\n\n"
                search_results.append(search_result)
            
            combined_results = "\n".join(search_results)
            state["search_results"].append(combined_results)
            
            state["messages"].append({
                "type": "search",
                "content": f"Searched for: {query} (Found {len(search_results)} results)",
                "timestamp": datetime.now().isoformat(),
                "results_preview": combined_results[:300] + "..." if len(combined_results) > 300 else combined_results
            })
            
        except Exception as e:
            state["messages"].append({
                "type": "error",
                "content": f"Search error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        
        return state
    
    def _process_node(self, state: AgentState) -> AgentState:
        """Process search results and create vector store"""
        try:
            if not state["search_results"]:
                return state
            
            # Combine all search results
            combined_text = "\n\n".join(state["search_results"])
            
            # Split into chunks
            chunks = self.text_splitter.split_text(combined_text)
            
            # Create documents
            documents = [
                Document(page_content=chunk, metadata={"source": "web_search"})
                for chunk in chunks
            ]
            
            state["processed_results"].extend(documents)
            
            # Create or update vector store
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(documents, self.embeddings)
            else:
                self.vector_store.add_documents(documents)
            
            state["messages"].append({
                "type": "process",
                "content": f"Processed {len(documents)} document chunks",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            state["messages"].append({
                "type": "error",
                "content": f"Processing error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        
        return state
    
    def _generate_node(self, state: AgentState) -> AgentState:
        """Generate answer using retrieved context"""
        try:
            if self.vector_store is None:
                state["final_answer"] = "No search results available to generate an answer."
                return state
            
            # Retrieve relevant documents
            retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
            relevant_docs = retriever.get_relevant_documents(state["query"])
            
            # Create context from relevant documents
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Generate prompt
            prompt = f"""Based on the following search results, provide a comprehensive answer to the question: {state["query"]}

Search Context:
{context}

Please provide a detailed, accurate answer based on the search results. If the search results don't contain enough information to answer the question completely, mention what additional information might be needed.

Answer:"""
            
            # Generate response
            response = self.llm.invoke(prompt)
            state["final_answer"] = response.content
            
            state["messages"].append({
                "type": "generate",
                "content": "Generated answer based on search results",
                "timestamp": datetime.now().isoformat(),
                "context_docs": len(relevant_docs)
            })
            
        except Exception as e:
            state["final_answer"] = f"Error generating answer: {str(e)}"
            state["messages"].append({
                "type": "error",
                "content": f"Generation error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        
        return state
    
    def _decide_node(self, state: AgentState) -> AgentState:
        """Decide whether to continue searching or end"""
        state["iteration_count"] += 1
        
        # Simple decision logic - could be enhanced with LLM-based decision making
        if state["iteration_count"] >= 3 or state["final_answer"]:
            state["messages"].append({
                "type": "decision",
                "content": "Ending search process",
                "timestamp": datetime.now().isoformat()
            })
        else:
            state["messages"].append({
                "type": "decision",
                "content": "Continuing search for more information",
                "timestamp": datetime.now().isoformat()
            })
        
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if the agent should continue or end"""
        if state["iteration_count"] >= 3 or (state["final_answer"] and len(state["final_answer"]) > 100):
            return "end"
        return "continue"
    
    def run_query(self, query: str) -> Dict[str, Any]:
        """Run the agent with a query"""
        initial_state = AgentState(
            messages=[],
            query=query,
            search_results=[],
            processed_results=[],
            final_answer="",
            iteration_count=0
        )
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return {
            "query": query,
            "final_answer": final_state["final_answer"],
            "messages": final_state["messages"],
            "total_iterations": final_state["iteration_count"],
            "total_documents": len(final_state["processed_results"])
        }

# Streamlit UI
def main():
    st.title("🔍 WebSearch React Agent")
    st.markdown("*Powered by LangGraph, LangChain, DuckDuckGo, FAISS, and ChatGroq*")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        groq_api_key = st.text_input(
            "Groq API Key",
            type="password",
            help="Enter your Groq API key to use the ChatGroq model"
        )
        
        st.markdown("---")
        st.markdown("### About This App")
        st.markdown("""
        This WebSearch React Agent uses:
        - **LangGraph**: Workflow orchestration
        - **LangChain**: Agent framework
        - **DuckDuckGo Search**: Direct web search API
        - **FAISS**: Vector storage
        - **ChatGroq**: LLM processing
        - **Streamlit**: User interface
        """)
    
    if not groq_api_key:
        st.warning("Please enter your Groq API key in the sidebar to continue.")
        st.info("You can get a free API key from [console.groq.com](https://console.groq.com)")
        return
    
    # Initialize agent
    if "agent" not in st.session_state:
        try:
            st.session_state.agent = WebSearchReactAgent(groq_api_key)
            st.success("Agent initialized successfully!")
        except Exception as e:
            st.error(f"Error initializing agent: {str(e)}")
            return
    
    # Query interface
    st.header("Ask a Question")
    query = st.text_input(
        "Enter your question:",
        placeholder="e.g., What are the latest developments in artificial intelligence?",
        help="The agent will search the web and provide a comprehensive answer"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        search_button = st.button("🔍 Search", type="primary")
    with col2:
        if st.button("🗑️ Clear History"):
            if "search_history" in st.session_state:
                del st.session_state.search_history
            st.rerun()
    
    # Process query
    if search_button and query:
        with st.spinner("Searching and processing..."):
            try:
                result = st.session_state.agent.run_query(query)
                
                # Store in history
                if "search_history" not in st.session_state:
                    st.session_state.search_history = []
                st.session_state.search_history.append(result)
                
                # Display result
                st.success("Search completed!")
                
            except Exception as e:
                st.error(f"Error during search: {str(e)}")
    
    # Display results
    # if "search_history" in st.session_state and st.session_state.search_history:
    #     st.header("Search Results")
        
    #     for i, result in enumerate(reversed(st.session_state.search_history)):
    #         with st.expander(f"Query: {result['query']}", expanded=(i == 0)):
                
    #             # Main answer
    #             st.subheader("Answer")
    #             st.write(result["final_answer"])
                
    #             # Metrics
    #             col1, col2, col3 = st.columns(3)
    #             with col1:
    #                 st.metric("Iterations", result["total_iterations"])
    #             with col2:
    #                 st.metric("Documents Processed", result["total_documents"])
    #             with col3:
    #                 st.metric("Process Steps", len(result["messages"]))
                
    #             # Process details
    #             if st.checkbox(f"Show Process Details", key=f"details_{i}"):
    #                 st.subheader("Agent Process")
    #                 for msg in result["messages"]:
    #                     msg_type = msg["type"]
    #                     timestamp = msg["timestamp"]
    #                     content = msg["content"]
                        
    #                     if msg_type == "search":
    #                         st.info(f"🔍 **Search**: {content}")
    #                         if "results_preview" in msg:
    #                             with st.expander("Search Results Preview"):
    #                                 st.text(msg["results_preview"])
    #                     elif msg_type == "process":
    #                         st.success(f"⚙️ **Process**: {content}")
    #                     elif msg_type == "generate":
    #                         st.success(f"✨ **Generate**: {content}")
    #                     elif msg_type == "decision":
    #                         st.info(f"🤔 **Decision**: {content}")
    #                     elif msg_type == "error":
    #                         st.error(f"❌ **Error**: {content}")
                        
    #                     st.caption(f"Time: {timestamp}")
    # Display results
    if "search_history" in st.session_state and st.session_state.search_history:
        st.header("Search Results")

        for i, result in enumerate(reversed(st.session_state.search_history)):
            with st.expander(f"Query: {result['query']}", expanded=(i == 0)):
                
                # Main answer
                st.subheader("Answer")
                st.write(result["final_answer"])
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Iterations", result["total_iterations"])
                with col2:
                    st.metric("Documents Processed", result["total_documents"])
                with col3:
                    st.metric("Process Steps", len(result["messages"]))
                
                # Process details
                if st.checkbox(f"Show Process Details", key=f"details_{i}"):
                    st.subheader("Agent Process")
                    for msg in result["messages"]:
                        msg_type = msg["type"]
                        timestamp = msg["timestamp"]
                        content = msg["content"]
                        
                        if msg_type == "search":
                            st.info(f"🔍 **Search**: {content}")
                            if "results_preview" in msg:
                                st.subheader("Search Results Preview")
                                st.text(msg["results_preview"])
                        elif msg_type == "process":
                            st.success(f"⚙️ **Process**: {content}")
                        elif msg_type == "generate":
                            st.success(f"✨ **Generate**: {content}")
                        elif msg_type == "decision":
                            st.info(f"🤔 **Decision**: {content}")
                        elif msg_type == "error":
                            st.error(f"❌ **Error**: {content}")
                        
                        st.caption(f"Time: {timestamp}")
if __name__ == "__main__":
    main()