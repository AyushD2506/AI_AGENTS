import streamlit as st
import importlib
import sys
import os
from pathlib import Path
import subprocess

# Configure page
st.set_page_config(
    page_title="AI Agents Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for grid layout and styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .agents-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
        padding: 20px 0;
    }
    
    .agent-card {
        background: linear-gradient(145deg, #f0f0f0, #ffffff);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        cursor: pointer;
        border: 2px solid transparent;
        text-align: center;
    }
    
    .agent-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
        border-color: #667eea;
    }
    
    .agent-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
    }
    
    .agent-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    .agent-description {
        color: #666;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    .back-button {
        margin: 1rem 0;
    }
    
    .stButton > button {
        width: 100%;
        height: 100%;
        border: none;
        background: transparent;
        padding: 0;
    }
</style>
""", unsafe_allow_html=True)

# Agent configurations
AGENTS = {
    "career_assistant": {
        "name": "Career Assistant",
        "icon": "💼",
        "description": "Get personalized career guidance and job recommendations",
        "module": "career_Assitant_agent.main",
        "folder": "career_Assitant_agent"
    },
    "crypto_mcp": {
        "name": "Crypto MCP Agent",
        "icon": "₿",
        "description": "Cryptocurrency market analysis and predictions",
        "module": "crypto_mcp_agent.main",
        "folder": "crypto_mcp_agent"
    },
    "data_analysis": {
        "name": "Data Analysis Agent",
        "icon": "📊",
        "description": "Advanced data analysis and visualization tools",
        "module": "Data_analysis_agent.main",
        "folder": "Data_analysis_agent"
    },
    "essay_grading": {
        "name": "Essay Grading",
        "icon": "📝",
        "description": "AI-powered essay evaluation and feedback",
        "module": "essay_grading_agent",
        "folder": "."
    },
    "meme_generator": {
        "name": "Meme Generator",
        "icon": "😂",
        "description": "Create hilarious memes with AI assistance",
        "module": "meme_generator.main",
        "folder": "meme_generator"
    },
    "mental_wellbeing": {
        "name": "Mental Wellbeing",
        "icon": "🧘",
        "description": "Mental health support and wellness tracking",
        "module": "mental_wellbeing.main",
        "folder": "mental_wellbeing"
    },
    "movie_generator": {
        "name": "Movie Generator",
        "icon": "🎬",
        "description": "Generate movie plots and recommendations",
        "module": "movie_generator.main",
        "folder": "movie_generator"
    },
    "multi_recruit": {
        "name": "Multi Recruit Agent",
        "icon": "👥",
        "description": "Advanced recruitment and candidate matching",
        "module": "multi_recruit_agent.main",
        "folder": "multi_recruit_agent"
    },
    "music_agent": {
        "name": "Music Agent",
        "icon": "🎵",
        "description": "Music generation and recommendation system",
        "module": "music_Agent.main",
        "folder": "music_Agent"
    },
    "qr_generator": {
        "name": "QR Code Generator",
        "icon": "📱",
        "description": "Generate custom QR codes with styling options",
        "module": "QR_code_generator.main",
        "folder": "QR_code_generator"
    },
    "simple_agent": {
        "name": "Simple Agent",
        "icon": "🤖",
        "description": "Basic AI agent using AGNO framework",
        "module": "simple_agent_using_agno.main",
        "folder": "simple_agent_using_agno"
    },
    "system_design": {
        "name": "System Design",
        "icon": "🏗️",
        "description": "System architecture and design assistant",
        "module": "system_design.main",
        "folder": "system_design"
    },
    "tic_tac_toe": {
        "name": "Tic Tac Toe",
        "icon": "⭕",
        "description": "Play Tic Tac Toe against AI",
        "module": "tic_tac_toe.main",
        "folder": "tic_tac_toe"
    },
    "travel_planner": {
        "name": "Travel Planner",
        "icon": "✈️",
        "description": "Plan and organize your perfect trip",
        "module": "travel_planner.main",
        "folder": "travel_planner"
    },
    "voice_agent": {
        "name": "Voice Agent",
        "icon": "🎤",
        "description": "Voice-powered AI interactions",
        "module": "voice_agent.main",
        "folder": "voice_agent"
    },
    "web_scraper": {
        "name": "Web Scraper",
        "icon": "🕷️",
        "description": "Extract data from websites efficiently",
        "module": "web_scraper_agent.main",
        "folder": "web_scraper_agent"
    },
    "web_search": {
        "name": "Web Search Summarizer",
        "icon": "🔍",
        "description": "Search and summarize web content",
        "module": "Web_search_summerizer.main",
        "folder": "Web_search_summerizer"
    }
}

def load_agent_module(agent_key):
    """Dynamically load agent module"""
    try:
        agent_config = AGENTS[agent_key]
        folder_path = Path(agent_config['folder'])
        
        # Add agent folder to Python path if it exists
        if folder_path.exists() and folder_path != Path('.'):
            sys.path.insert(0, str(folder_path.absolute()))
        
        # Try to import the module
        module_name = agent_config['module'].split('.')[-1]  # Get the last part
        
        # Look for common Streamlit app file names
        possible_files = ['main.py', 'app.py', 'streamlit_app.py', f'{module_name}.py']
        
        for file_name in possible_files:
            file_path = folder_path / file_name
            if file_path.exists():
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                return module
                
        # If no specific file found, try direct import
        return importlib.import_module(agent_config['module'])
        
    except Exception as e:
        st.error(f"Error loading {agent_key}: {str(e)}")
        return None

def run_agent_in_subprocess(agent_key):
    """Run agent as subprocess (alternative approach)"""
    try:
        agent_config = AGENTS[agent_key]
        folder_path = Path(agent_config['folder'])
        
        # Look for the main file
        possible_files = ['main.py', 'app.py', 'streamlit_app.py']
        
        for file_name in possible_files:
            file_path = folder_path / file_name
            if file_path.exists():
                # Run streamlit app in subprocess
                cmd = f"streamlit run {file_path} --server.port 8502 --server.headless true"
                process = subprocess.Popen(cmd, shell=True)
                st.success(f"Started {agent_config['name']} on port 8502")
                st.markdown(f"[Open {agent_config['name']}](http://localhost:8502)")
                return
                
        st.error(f"Could not find main file for {agent_config['name']}")
        
    except Exception as e:
        st.error(f"Error running {agent_key}: {str(e)}")

def main():
    # Initialize session state
    if 'current_agent' not in st.session_state:
        st.session_state.current_agent = None
    
    # Main dashboard view
    if st.session_state.current_agent is None:
        # Header
        st.markdown("""
        <div class="main-header">
            <h1>🤖 AI Agents Hub</h1>
            <p>Your comprehensive collection of AI-powered tools and assistants</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create grid layout
        st.markdown('<div class="agents-grid">', unsafe_allow_html=True)
        
        # Create columns for grid layout
        cols = st.columns(4)  # 4 columns for responsive grid
        
        for idx, (agent_key, agent_config) in enumerate(AGENTS.items()):
            col = cols[idx % 4]
            
            with col:
                # Create clickable card
                if st.button(
                    f"{agent_config['icon']}\n\n**{agent_config['name']}**\n\n{agent_config['description']}",
                    key=f"btn_{agent_key}",
                    use_container_width=True,
                    help=f"Click to open {agent_config['name']}"
                ):
                    st.session_state.current_agent = agent_key
                    st.rerun()
                    
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem;">
            <p>Built with ❤️ using Streamlit | Select any agent above to get started</p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # Agent view
        current_agent = st.session_state.current_agent
        agent_config = AGENTS[current_agent]
        
        # Back button
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back to Hub", key="back_btn"):
                st.session_state.current_agent = None
                st.rerun()
        
        with col2:
            st.title(f"{agent_config['icon']} {agent_config['name']}")
        
        st.markdown("---")
        
        # Try to load and run the agent
        try:
            # Method 1: Try to load as module
            module = load_agent_module(current_agent)
            if module and hasattr(module, 'main'):
                module.main()
            elif module and hasattr(module, 'run'):
                module.run()
            else:
                # Method 2: Try to execute the file directly
                agent_folder = Path(agent_config['folder'])
                possible_files = ['main.py', 'app.py', 'streamlit_app.py']
                
                executed = False
                for file_name in possible_files:
                    file_path = agent_folder / file_name
                    if file_path.exists():
                        # Read and execute the file
                        with open(file_path, 'r') as f:
                            code = f.read()
                        
                        # Create a new namespace for execution
                        exec_globals = {'__name__': '__main__', 'st': st}
                        exec(code, exec_globals)
                        executed = True
                        break
                
                if not executed:
                    st.error(f"Could not load {agent_config['name']}. Please check the file structure.")
                    st.info("Available options:")
                    st.code(f"""
1. Ensure the agent folder '{agent_config['folder']}' exists
2. Add a main.py, app.py, or streamlit_app.py file in the folder
3. Make sure the main file has a main() or run() function
                    """)
                    
        except Exception as e:
            st.error(f"Error running {agent_config['name']}: {str(e)}")
            st.info("You can also try running this agent independently:")
            st.code(f"streamlit run {agent_config['folder']}/main.py")

if __name__ == "__main__":
    main()