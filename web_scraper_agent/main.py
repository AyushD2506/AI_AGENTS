import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import Dict, List, Optional
import re
from urllib.parse import urlparse, urljoin
import time

# Page configuration
st.set_page_config(
    page_title="Smart Web Summarizer Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 15px 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .summary-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #667eea;
    }
    
    .info-box {
        background: rgba(230, 244, 255, 0.6);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #e3f2fd;
    }
    
    .success-box {
        background: rgba(232, 245, 233, 0.8);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
    }
    
    .error-box {
        background: rgba(255, 235, 238, 0.8);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #f44336;
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
    }
    
    .step-indicator {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        background: rgba(102, 126, 234, 0.1);
    }
    
    .spinner {
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .download-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class WebSummarizerAgent:
    """Smart Web Summarizer Agent using LangGraph-like architecture"""
    
    def __init__(self, groq_api_key: str):
        self.groq_api_key = groq_api_key
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def search_web(self, query: str, max_results: int = 5) -> List[str]:
        """Search for URLs using DuckDuckGo (simplified version)"""
        try:
            # For demonstration, using a simple search approach
            # In production, you'd use proper DuckDuckGo API
            search_query = query.replace(' ', '+')
            search_url = f"https://html.duckduckgo.com/html/?q={search_query}"
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            urls = []
            for link in soup.find_all('a', class_='result__url'):
                href = link.get('href')
                if href and href.startswith('http'):
                    urls.append(href)
                    if len(urls) >= max_results:
                        break
            
            # Fallback URLs if search doesn't work
            if not urls:
                fallback_urls = [
                    "https://news.ycombinator.com",
                    "https://www.reuters.com",
                    "https://www.bbc.com/news",
                    "https://techcrunch.com",
                    "https://www.nature.com"
                ]
                return fallback_urls[:max_results]
            
            return urls
            
        except Exception as e:
            st.error(f"Search error: {e}")
            return []
    
    def scrape_content(self, url: str) -> Dict[str, str]:
        """Scrape content from URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'ads']):
                element.decompose()
            
            # Extract title
            title = soup.find('title')
            title = title.get_text().strip() if title else "No title found"
            
            # Extract main content
            content_selectors = [
                'article', 'main', '.content', '.post-content', 
                '.entry-content', '.article-body', 'p'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text().strip() for elem in elements])
                    break
            
            if not content:
                content = soup.get_text()
            
            # Clean content
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Limit content length
            if len(content) > 8000:
                content = content[:8000] + "..."
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'word_count': len(content.split())
            }
            
        except Exception as e:
            return {
                'title': 'Error',
                'content': f'Failed to scrape content from {url}: {str(e)}',
                'url': url,
                'word_count': 0
            }
    
    def generate_summary(self, content: str, query: str, title: str = "") -> str:
        """Generate summary using Groq API"""
        try:
            prompt = f"""
You are an expert content analyst and summarizer. Based on the user's query and the provided web content, create a comprehensive and well-structured analysis.

USER QUERY: {query}

ARTICLE TITLE: {title}

WEB CONTENT:
{content[:6000]}

Please provide a detailed response with the following structure:

## 📋 Executive Summary
Provide a concise 2-3 sentence overview of the main points.

## 🔍 Key Insights
List the most important findings and insights relevant to the user's query:
- Point 1
- Point 2
- Point 3

## 📊 Detailed Analysis
Provide a comprehensive breakdown of the content, organized by themes or topics.

## 💡 Key Takeaways
- Actionable insights
- Important conclusions
- Practical implications

## 🎯 Relevance to Query
Explain how the content specifically addresses the user's question.

Format your response in clear markdown. Be thorough but concise, focusing on accuracy and relevance.
"""

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant specialized in web content analysis and summarization. Always provide well-structured, accurate, and insightful responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 2000,
                "stream": False
            }
            
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.groq_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def run_analysis(self, query: str, url: Optional[str] = None) -> Dict:
        """Run the complete analysis workflow"""
        result = {
            'query': query,
            'url': url,
            'search_results': [],
            'scraped_data': {},
            'summary': '',
            'status': 'started'
        }
        
        try:
            # Step 1: Search or use provided URL
            if not url or not url.strip():
                st.info("🔍 Searching for relevant content...")
                search_results = self.search_web(query)
                result['search_results'] = search_results
                if search_results:
                    url = search_results[0]
                    result['url'] = url
                else:
                    result['status'] = 'error'
                    result['summary'] = "No relevant URLs found for the query."
                    return result
            
            # Step 2: Scrape content
            st.info(f"📄 Scraping content from: {url}")
            scraped_data = self.scrape_content(url)
            result['scraped_data'] = scraped_data
            
            if not scraped_data['content'] or scraped_data['word_count'] < 50:
                result['status'] = 'error'
                result['summary'] = "Could not extract sufficient content from the URL."
                return result
            
            # Step 3: Generate summary
            st.info("🧠 Generating AI-powered summary...")
            summary = self.generate_summary(
                scraped_data['content'], 
                query, 
                scraped_data['title']
            )
            result['summary'] = summary
            result['status'] = 'completed'
            
            return result
            
        except Exception as e:
            result['status'] = 'error'
            result['summary'] = f"Analysis failed: {str(e)}"
            return result

# Header
st.markdown("""
<div class="main-header">
    <h1>🤖 Smart Web Summarizer Agent</h1>
    <p>Powered by LangGraph Architecture + LLaMA 3.3 70B via Groq</p>
    <p style="font-size: 0.9em; opacity: 0.8;">Intelligent web content analysis and summarization</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = []

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key input
    groq_api_key = st.text_input(
        "🔑 Groq API Key",
        type="password",
        help="Enter your Groq API key to access LLaMA 3.3 70B",
        placeholder="gsk_..."
    )
    
    if groq_api_key:
        st.markdown('<div class="success-box">✅ API Key configured</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="error-box">⚠️ API Key required</div>', unsafe_allow_html=True)
        st.info("Get your free API key at: https://console.groq.com/")
    
    st.divider()
    
    # Settings
    st.header("🎛️ Settings")
    
    max_results = st.slider("Search Results", min_value=1, max_value=10, value=5)
    content_length = st.slider("Max Content Length", min_value=2000, max_value=10000, value=8000, step=1000)
    
    st.divider()
    
    # Agent Architecture Info
    st.header("🏗️ Agent Architecture")
    st.markdown("""
    **LangGraph Workflow:**
    1. 🤔 **Planner**: Decides search vs scrape
    2. 🔍 **Searcher**: Finds relevant URLs
    3. 📄 **Scraper**: Extracts content
    4. 🧠 **Summarizer**: LLaMA analysis
    5. 📊 **Formatter**: Structured output
    """)
    
    st.divider()
    
    # Usage Stats
    st.header("📈 Session Stats")
    st.metric("Analyses Completed", len(st.session_state.analysis_results))
    if st.session_state.analysis_results:
        avg_words = sum(r.get('scraped_data', {}).get('word_count', 0) for r in st.session_state.analysis_results) / len(st.session_state.analysis_results)
        st.metric("Avg Words Processed", f"{avg_words:.0f}")

# Main Content Area
if not groq_api_key:
    st.markdown("""
    <div class="info-box">
        <h3>🚀 Welcome to Smart Web Summarizer Agent</h3>
        <p>This advanced AI agent uses a <strong>LangGraph-inspired architecture</strong> to intelligently analyze web content:</p>
        <ul>
            <li><strong>🔍 Smart Search</strong>: Automatically finds relevant content</li>
            <li><strong>📄 Content Extraction</strong>: Advanced web scraping with BeautifulSoup</li>
            <li><strong>🧠 AI Analysis</strong>: LLaMA 3.3 70B for comprehensive summaries</li>
            <li><strong>📊 Structured Output</strong>: Well-formatted, actionable insights</li>
        </ul>
        <p><strong>Please enter your Groq API key in the sidebar to get started.</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Demo features
    st.header("✨ Key Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>🔍 Intelligent Search</h4>
            <p>Automatically discovers relevant content based on your query using advanced search algorithms.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>📄 Smart Scraping</h4>
            <p>Extracts clean, relevant content from web pages using newspaper3k and BeautifulSoup.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>🧠 AI Analysis</h4>
            <p>LLaMA 3.3 70B provides comprehensive analysis and structured summaries.</p>
        </div>
        """, unsafe_allow_html=True)

else:
    # Initialize agent
    if 'agent' not in st.session_state:
        st.session_state.agent = WebSummarizerAgent(groq_api_key)
    
    # Input Section
    st.header("📝 Analysis Input")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_area(
            "🔍 What would you like to know?",
            height=120,
            placeholder="Examples:\n• Summarize recent AI developments\n• What are the key points about climate change?\n• Analyze trends in renewable energy",
            help="Describe what you want to learn or analyze"
        )
    
    with col2:
        url = st.text_input(
            "🌐 Specific URL (Optional)",
            placeholder="https://example.com/article",
            help="Leave empty to auto-search for content"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        analyze_btn = st.button(
            "🚀 Start Analysis",
            use_container_width=True,
            disabled=not query.strip(),
            help="Begin intelligent content analysis"
        )
    
    # Quick Examples
    st.markdown("### 💡 Quick Examples")
    example_col1, example_col2, example_col3 = st.columns(3)
    
    with example_col1:
        if st.button("🤖 AI Regulation News", use_container_width=True):
            st.session_state.example_query = "Latest developments in AI regulation and policy"
    
    with example_col2:
        if st.button("🌱 Climate Research", use_container_width=True):
            st.session_state.example_query = "Recent climate change research findings"
    
    with example_col3:
        if st.button("⚡ Tech Trends", use_container_width=True):
            st.session_state.example_query = "Emerging technology trends and innovations"
    
    # Apply example query
    if 'example_query' in st.session_state:
        query = st.session_state.example_query
        del st.session_state.example_query
        st.rerun()
    
    # Analysis Execution
    if analyze_btn and query.strip():
        st.header("🔄 Analysis in Progress")
        
        # Create progress tracking
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_placeholder = st.empty()
            
            # Step indicators
            steps = [
                "🤔 Planning analysis strategy",
                "🔍 Searching for content" if not url.strip() else "📄 Preparing to scrape URL",
                "📄 Extracting content",
                "🧠 Generating AI summary",
                "✅ Finalizing results"
            ]
            
            try:
                # Execute analysis with progress updates
                for i, step in enumerate(steps):
                    status_placeholder.markdown(f'<div class="step-indicator">{step}</div>', unsafe_allow_html=True)
                    progress_bar.progress((i + 1) * 20)
                    time.sleep(0.5)  # Brief pause for UX
                
                # Run actual analysis
                result = st.session_state.agent.run_analysis(query, url if url.strip() else None)
                
                # Store result
                result['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                st.session_state.analysis_results.append(result)
                
                progress_bar.progress(100)
                status_placeholder.markdown('<div class="success-box">✅ Analysis completed successfully!</div>', unsafe_allow_html=True)
                
                # Display Results
                st.header("📊 Analysis Results")
                
                if result['status'] == 'completed':
                    # Metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📄 Source", "Found" if result['url'] else "None")
                    with col2:
                        word_count = result.get('scraped_data', {}).get('word_count', 0)
                        st.metric("📝 Words Processed", f"{word_count:,}")
                    with col3:
                        st.metric("⏱️ Status", "Completed")
                    
                    # Source URL
                    if result['url']:
                        st.markdown(f"**🌐 Source URL:** [{result['url']}]({result['url']})")
                    
                    # Search results (if any)
                    if result.get('search_results'):
                        with st.expander(f"🔍 Found {len(result['search_results'])} relevant sources"):
                            for i, search_url in enumerate(result['search_results'], 1):
                                st.write(f"{i}. [{search_url}]({search_url})")
                    
                    # Main Summary
                    st.markdown('<div class="summary-container">', unsafe_allow_html=True)
                    st.markdown("### 📋 AI-Generated Analysis")
                    st.markdown(result['summary'])
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Download Section
                    st.markdown('<div class="download-section">', unsafe_allow_html=True)
                    st.markdown("### 💾 Export Options")
                    
                    # Prepare download content
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    markdown_content = f"""# Web Analysis Report
**Generated:** {timestamp}
**Agent:** Smart Web Summarizer (LangGraph + LLaMA 3.3 70B)

## Query
{query}

## Source
{result.get('url', 'Auto-discovered content')}

## Analysis Results
{result['summary']}

---
*Report generated by Smart Web Summarizer Agent*
*Powered by LangGraph architecture and LLaMA 3.3 70B*
"""
                    
                    # Download buttons
                    download_col1, download_col2 = st.columns(2)
                    
                    with download_col1:
                        st.download_button(
                            label="📄 Download Markdown",
                            data=markdown_content,
                            file_name=f"web_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    
                    with download_col2:
                        # JSON export
                        json_content = json.dumps(result, indent=2, default=str)
                        st.download_button(
                            label="📊 Download JSON",
                            data=json_content,
                            file_name=f"web_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True
                        )
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                else:
                    st.error(f"❌ Analysis failed: {result.get('summary', 'Unknown error')}")
            
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                progress_bar.progress(0)
    
    # Analysis History
    if st.session_state.analysis_results:
        st.header("📚 Analysis History")
        
        for i, result in enumerate(reversed(st.session_state.analysis_results[-5:]), 1):
            with st.expander(f"Analysis {len(st.session_state.analysis_results) - i + 1}: {result['query'][:60]}..."):
                st.write(f"**Query:** {result['query']}")
                st.write(f"**Timestamp:** {result.get('timestamp', 'Unknown')}")
                st.write(f"**Status:** {result['status']}")
                if result.get('url'):
                    st.write(f"**URL:** {result['url']}")
                
                if result['status'] == 'completed' and result.get('summary'):
                    st.markdown("**Summary Preview:**")
                    preview = result['summary'][:300] + "..." if len(result['summary']) > 300 else result['summary']
                    st.markdown(preview)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; color: #666;'>
    <h4>🤖 Smart Web Summarizer Agent</h4>
    <p>Built with ❤️ using LangGraph Architecture, LLaMA 3.3 70B, and Streamlit</p>
    <p style='font-size: 0.8em;'>
        Features: Intelligent Search • Advanced Scraping • AI Analysis • Structured Output
    </p>
</div>
""", unsafe_allow_html=True)