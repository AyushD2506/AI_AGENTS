import streamlit as st
import requests
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
import base64
from datetime import datetime
import os
import tempfile
import hashlib
from groq import Groq
import numpy as np
import random
import re
from typing import List, Tuple, Dict

import os

api_key = os.getenv("GROQ_API_KEY")
print("API Key:", api_key)
# Configure page
st.set_page_config(
    page_title="🔥 Meme Generator Pro - AI Comedy Engine",
    page_icon="😎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with professional styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        text-align: center;
        padding: 3rem 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        color: white;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 100" fill="rgba(255,255,255,0.1)"><polygon points="0,0 1000,0 1000,100 0,100"/></svg>');
        opacity: 0.1;
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.2rem;
        margin: 1rem 0 0 0;
        opacity: 0.9;
    }
    
    .pro-card {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        margin: 1rem 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .pro-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }
    
    .comedy-caption {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 50%, #f0932b 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        font-weight: 600;
        text-align: center;
        font-style: italic;
        box-shadow: 0 8px 20px rgba(255,107,107,0.3);
        position: relative;
        overflow: hidden;
    }
    
    .comedy-caption::before {
        content: '😂';
        position: absolute;
        top: -10px;
        right: -10px;
        font-size: 2rem;
        opacity: 0.3;
    }
    
    .meme-style-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 12px;
        color: white;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }
    
    .meme-style-card:hover {
        transform: scale(1.02);
        border-color: rgba(255,255,255,0.5);
    }
    
    .meme-style-card.selected {
        border-color: #fff;
        box-shadow: 0 0 20px rgba(255,255,255,0.5);
    }
    
    .analysis-box {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
        color: #2c3e50;
    }
    
    .success-box {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #00b894;
        color: #00b894;
        font-weight: 600;
    }
    
    .error-box {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #e74c3c;
        color: #e74c3c;
        font-weight: 600;
    }
    
    .step-indicator {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-weight: 600;
        text-align: center;
        box-shadow: 0 8px 20px rgba(102,126,234,0.3);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102,126,234,0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102,126,234,0.6);
    }
    
    .comedy-stats {
        display: flex;
        justify-content: space-around;
        background: rgba(255,255,255,0.1);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .stat-item {
        text-align: center;
        color: white;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        display: block;
    }
    
    .preview-container {
        background: #000;
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    .meme-template-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .template-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 2px solid transparent;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .template-card:hover {
        transform: translateY(-5px);
        border-color: #667eea;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .viral-score {
        background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(255,107,107,0.3);
    }
    
    .comedy-genre-tag {
        background: rgba(102,126,234,0.2);
        color: #667eea;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 0.25rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Initialize enhanced session state
if 'uploaded_image' not in st.session_state:
    st.session_state.uploaded_image = None
if 'generated_captions' not in st.session_state:
    st.session_state.generated_captions = []
if 'final_meme' not in st.session_state:
    st.session_state.final_meme = None
if 'selected_caption' not in st.session_state:
    st.session_state.selected_caption = ""
if 'groq_client' not in st.session_state:
    st.session_state.groq_client = None
if 'layout_type' not in st.session_state:
    st.session_state.layout_type = "single"
if 'image_analysis' not in st.session_state:
    st.session_state.image_analysis = ""
if 'meme_style' not in st.session_state:
    st.session_state.meme_style = "sarcastic"
if 'comedy_genre' not in st.session_state:
    st.session_state.comedy_genre = "observational"
if 'viral_score' not in st.session_state:
    st.session_state.viral_score = 0

# Comedy knowledge base
COMEDY_STYLES = {
    "sarcastic": {
        "name": "Sarcastic & Savage",
        "description": "Brutally honest, cutting wit",
        "prompts": ["When you realize", "That moment when", "POV:", "Imagine thinking", "Nobody asked but"],
        "intensity": "savage"
    },
    "absurd": {
        "name": "Absurd & Random",
        "description": "Unexpected, weird humor",
        "prompts": ["When reality glitches", "Local man discovers", "Breaking:", "Scientists baffled by", "This you?"],
        "intensity": "chaotic"
    },
    "relatable": {
        "name": "Relatable & Wholesome",
        "description": "Everyone gets it",
        "prompts": ["Me when", "Us:", "This is fine", "Why is this so accurate", "Called out"],
        "intensity": "friendly"
    },
    "roast": {
        "name": "Roast Mode",
        "description": "Maximum destruction",
        "prompts": ["Ratio + L +", "Skill issue", "This ain't it chief", "Bro really thought", "The audacity"],
        "intensity": "nuclear"
    },
    "gen_z": {
        "name": "Gen Z Humor",
        "description": "Chronically online",
        "prompts": ["It's giving", "No cap", "Fr fr", "Periodt", "And I oop"],
        "intensity": "unhinged"
    },
    "dark": {
        "name": "Dark Comedy",
        "description": "Morbid but funny",
        "prompts": ["Death finds a way", "Plot twist:", "Conspiracy theory:", "Final boss:", "Error 404"],
        "intensity": "edgy"
    }
}

MEME_FORMATS = {
    "classic": {"name": "Classic Impact", "font": "Impact", "style": "traditional"},
    "modern": {"name": "Modern Clean", "font": "Arial", "style": "minimal"},
    "handwriting": {"name": "Handwritten", "font": "Comic Sans", "style": "casual"},
    "bold": {"name": "Bold Statement", "font": "Arial Black", "style": "heavy"},
    "elegant": {"name": "Elegant", "font": "Times", "style": "classy"}
}

# Enhanced header
st.markdown("""
<div class="main-header">
    <h1>🔥 Meme Generator Pro</h1>
    <p>AI-Powered Comedy Engine for Professional Meme Creators</p>
    <div class="comedy-stats">
        <div class="stat-item">
            <span class="stat-number">∞</span>
            <span>Comedy Styles</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">🎯</span>
            <span>Viral Potential</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">⚡</span>
            <span>Instant Memes</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Enhanced sidebar
with st.sidebar:
    st.header("🎮 Meme Studio Pro")
    
    # API Configuration
    st.subheader("🔑 AI Engine")
    groq_api_key = st.text_input(
        "Groq API Key", 
        type="password",
        help="Get your free API key from console.groq.com"
    )
    
    if groq_api_key:
        try:
            st.session_state.groq_client = Groq(api_key=api_key)
            st.success("🚀 AI Engine Online!")
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)}")
    
    # Vision Model
    vision_model = st.selectbox(
        "🤖 Vision Model",
        ["meta-llama/llama-4-scout-17b-16e-instruct", "llava-v1.5-7b-4096-preview"],
        help="Choose your AI comedy assistant"
    )
    
    # Comedy Style Selection
    st.subheader("🎭 Comedy Style")
    
    style_cols = st.columns(2)
    for i, (key, style) in enumerate(COMEDY_STYLES.items()):
        col = style_cols[i % 2]
        with col:
            if st.button(f"{style['name']}", key=f"style_{key}", help=style['description']):
                st.session_state.meme_style = key
    
    current_style = COMEDY_STYLES[st.session_state.meme_style]
    st.markdown(f"""
    <div class="meme-style-card selected">
        <strong>Active:</strong> {current_style['name']}<br>
        <small>{current_style['description']}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Advanced Settings
    st.subheader("⚙️ Advanced Settings")
    
    # Comedy parameters
    comedy_intensity = st.slider("🔥 Comedy Intensity", 1, 10, 8)
    humor_intelligence = st.slider("🧠 Humor Intelligence", 1, 10, 7)
    cultural_awareness = st.slider("🌍 Cultural Awareness", 1, 10, 8)
    
    # Visual settings
    st.subheader("🎨 Visual Design")
    
    meme_format = st.selectbox("Format Style", list(MEME_FORMATS.keys()), 
                              format_func=lambda x: MEME_FORMATS[x]['name'])
    
    font_size = st.slider("Font Size", 20, 100, 50)
    
    # Color scheme
    color_scheme = st.selectbox("Color Scheme", 
                               ["Classic (White/Black)", "Neon (Bright)", "Pastel (Soft)", 
                                "Dark Mode", "Rainbow", "Custom"])
    
    # Effects
    st.subheader("✨ Effects")
    add_shadow = st.checkbox("Drop Shadow", value=True)
    add_glow = st.checkbox("Glow Effect")
    add_border = st.checkbox("Border Effect")
    distort_text = st.checkbox("Distort Text (Chaos Mode)")
    
    # Watermark
    st.subheader("🏷️ Branding")
    add_watermark = st.checkbox("Add Watermark")
    if add_watermark:
        watermark_text = st.text_input("Watermark Text", "Made with Meme Pro")

def encode_image_to_base64(image: Image.Image) -> str:
    """Enhanced image encoding with optimization"""
    buffer = io.BytesIO()
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Optimize for API
    max_size = (1024, 1024)
    if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    image.save(buffer, format='JPEG', quality=85, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def advanced_image_analysis(image: Image.Image) -> Dict:
    """Advanced image analysis for better comedy generation"""
    try:
        img_array = np.array(image.convert('RGB'))
        height, width, _ = img_array.shape
        
        # Color analysis
        avg_color = np.mean(img_array, axis=(0, 1))
        brightness = np.mean(avg_color)
        
        # Dominant colors
        pixels = img_array.reshape(-1, 3)
        unique_colors = len(np.unique(pixels.view(np.dtype((np.void, pixels.dtype.itemsize * pixels.shape[1])))))
        
        # Complexity analysis
        edges = np.gradient(np.mean(img_array, axis=2))
        complexity = np.std(edges)
        
        # Layout analysis
        thirds_h = [height//3, 2*height//3]
        thirds_w = [width//3, 2*width//3]
        
        sections = {
            'top': img_array[:thirds_h[0], :],
            'middle': img_array[thirds_h[0]:thirds_h[1], :],
            'bottom': img_array[thirds_h[1]:, :],
            'left': img_array[:, :thirds_w[0]],
            'center': img_array[:, thirds_w[0]:thirds_w[1]],
            'right': img_array[:, thirds_w[1]:]
        }
        
        section_brightness = {k: np.mean(v) for k, v in sections.items()}
        
        # Determine best text placement
        dark_sections = [k for k, v in section_brightness.items() if v < 100]
        light_sections = [k for k, v in section_brightness.items() if v > 150]
        
        # Format detection
        aspect_ratio = width / height
        if aspect_ratio > 1.5:
            format_type = "wide"
        elif aspect_ratio < 0.7:
            format_type = "tall"
        else:
            format_type = "square"
        
        # Meme potential analysis
        meme_potential = {
            'reaction_worthy': brightness < 120 or brightness > 180,
            'text_friendly': len(dark_sections) > 0 and len(light_sections) > 0,
            'complexity_score': min(complexity / 50, 10),
            'color_diversity': min(unique_colors / 1000, 10)
        }
        
        return {
            'format_type': format_type,
            'aspect_ratio': aspect_ratio,
            'brightness': brightness,
            'complexity': complexity,
            'best_text_areas': dark_sections + light_sections,
            'section_brightness': section_brightness,
            'meme_potential': meme_potential,
            'recommended_style': 'dark' if brightness > 150 else 'light'
        }
        
    except Exception as e:
        return {
            'format_type': 'square',
            'aspect_ratio': 1.0,
            'brightness': 128,
            'complexity': 5,
            'best_text_areas': ['top', 'bottom'],
            'section_brightness': {},
            'meme_potential': {'reaction_worthy': True, 'text_friendly': True, 'complexity_score': 5, 'color_diversity': 5},
            'recommended_style': 'light'
        }

def generate_pro_comedy_captions(image: Image.Image, groq_client: Groq, model: str, 
                                style: str, intensity: int, intelligence: int, 
                                cultural_awareness: int, analysis: Dict) -> List[Tuple[str, str]]:
    """Enhanced comedy generation with multiple AI techniques"""
    
    try:
        base64_image = encode_image_to_base64(image)
        style_config = COMEDY_STYLES[style]
        
        # Build comprehensive prompt
        prompt = f"""You are a professional meme creator and comedy writer with expertise in viral content creation. 

ANALYSIS CONTEXT:
- Image format: {analysis['format_type']} ({analysis['aspect_ratio']:.2f} ratio)
- Visual complexity: {analysis['complexity']:.1f}/10
- Brightness: {analysis['brightness']:.0f}/255
- Meme potential: {analysis['meme_potential']}

COMEDY STYLE: {style_config['name']}
- Description: {style_config['description']}
- Intensity: {style_config['intensity']}
- Common starters: {', '.join(style_config['prompts'])}

GENERATION PARAMETERS:
- Comedy Intensity: {intensity}/10
- Humor Intelligence: {intelligence}/10  
- Cultural Awareness: {cultural_awareness}/10

INSTRUCTIONS:
1. Analyze the image for comedic elements: facial expressions, objects, situations, contexts, ironies, contradictions
2. Identify what makes this image meme-worthy: reactions, situations, universal experiences
3. Generate 8 DISTINCT caption variations in the {style_config['name']} style
4. Each caption should be either single-line or setup/punchline format
5. Focus on making content that actual meme creators would use
6. Consider current internet culture, trends, and slang
7. Make captions that would get engagement: likes, shares, comments

COMEDY TECHNIQUES TO USE:
- Observational humor about the image
- Relatable life situations
- Pop culture references
- Internet culture and memes
- Unexpected twists and subversion
- Exaggeration and hyperbole
- Self-deprecating humor
- Social commentary (when appropriate)

OUTPUT FORMAT:
Return as JSON array. Use either format:
- Single line: {{"single": "caption text"}}
- Two lines: {{"top": "setup text", "bottom": "punchline text"}}

QUALITY STANDARDS:
- Must be genuinely funny, not just trying to be funny
- Should feel natural and authentic
- Avoid cringe or forced humor
- Consider what would actually go viral
- Make it shareable and quotable

Remember: You're creating content for real meme creators who need professional-quality captions that will perform well on social media."""

        # Make API call with enhanced parameters
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            model=model,
            temperature=0.8 + (intensity * 0.02),  # Dynamic temperature based on intensity
            max_tokens=1500,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.1
        )
        
        response_text = chat_completion.choices[0].message.content
        
        # Enhanced parsing with fallback
        try:
            # Try to extract JSON
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                captions_json = json.loads(json_match.group())
                captions = []
                for item in captions_json:
                    if isinstance(item, dict):
                        if 'single' in item:
                            captions.append((item['single'], ""))
                        elif 'top' in item and 'bottom' in item:
                            captions.append((item['top'], item['bottom']))
                    else:
                        captions.append((str(item), ""))
            else:
                # Fallback: parse line by line
                lines = response_text.split('\n')
                captions = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith(('*', '-', '•', '1.', '2.')):
                        captions.append((line, ""))
        except:
            # Emergency fallback with style-appropriate captions
            captions = generate_fallback_captions(style, analysis)
        
        # Ensure we have enough captions
        while len(captions) < 6:
            captions.extend(generate_fallback_captions(style, analysis))
        
        return captions[:8]  # Return up to 8 captions
        
    except Exception as e:
        st.error(f"Comedy generation error: {str(e)}")
        return generate_fallback_captions(style, analysis)

def generate_fallback_captions(style: str, analysis: Dict) -> List[Tuple[str, str]]:
    """Generate style-appropriate fallback captions"""
    
    style_captions = {
        "sarcastic": [
            ("When you think you're the main character", "But you're actually the side quest NPC"),
            ("POV: You're confident about something", "Reality is about to humble you"),
            ("That moment when you realize", "You played yourself"),
            ("Imagine being this confident", "Couldn't be me with my trust issues"),
            ("When life hits different", "And by different I mean worse")
        ],
        "absurd": [
            ("Local man discovers", "Gravity still works"),
            ("Breaking: Reality glitches", "Turns out nothing makes sense"),
            ("Scientists baffled by", "This absolutely normal occurrence"),
            ("When the universe decides", "To be extra chaotic today"),
            ("Plot twist:", "Everything is actually cake")
        ],
        "relatable": [
            ("Me trying to adult", "Spoiler: it's not going well"),
            ("When you're just vibing", "And life decides to happen"),
            ("This is fine", "Narrator: It was not fine"),
            ("Us pretending we have it together", "While everything falls apart"),
            ("Why is this so accurate", "I feel personally attacked")
        ],
        "roast": [
            ("The audacity", "The unmitigated gall"),
            ("Bro really thought", "That was going to work"),
            ("This ain't it chief", "This is the opposite of it"),
            ("Skill issue", "Have you tried getting better?"),
            ("Ratio + L + You fell off", "Plus you're cringe")
        ],
        "gen_z": [
            ("It's giving", "Main character energy"),
            ("No cap", "This is bussin fr fr"),
            ("And I oop", "Spilled the tea"),
            ("Periodt", "Said what I said"),
            ("This is sending me", "I can't even")
        ],
        "dark": [
            ("Plot twist:", "Nothing matters anyway"),
            ("Death finds a way", "To make everything awkward"),
            ("Error 404:", "Happiness not found"),
            ("Final boss:", "Your own expectations"),
            ("Conspiracy theory:", "Life is just a simulation of suffering")
        ]
    }
    
    return style_captions.get(style, style_captions["sarcastic"])

def calculate_viral_score(caption: Tuple[str, str], style: str, analysis: Dict) -> int:
    """Calculate potential viral score for a caption"""
    
    score = 50  # Base score
    
    top_text, bottom_text = caption
    full_text = f"{top_text} {bottom_text}".lower()
    
    # Viral indicators
    viral_words = ["when", "pov", "me", "us", "that moment", "nobody", "everyone", "this", "why", "how"]
    score += sum(5 for word in viral_words if word in full_text)
    
    # Engagement triggers
    engagement_words = ["fr", "literally", "actually", "honestly", "seriously", "basically"]
    score += sum(3 for word in engagement_words if word in full_text)
    
    # Length optimization (Twitter/TikTok friendly)
    total_length = len(full_text)
    if 20 <= total_length <= 100:
        score += 15
    elif total_length <= 140:
        score += 10
    
    # Style bonus
    style_bonuses = {"roast": 20, "sarcastic": 15, "gen_z": 12, "absurd": 10, "relatable": 18, "dark": 8}
    score += style_bonuses.get(style, 5)
    
    # Image compatibility
    if analysis['meme_potential']['reaction_worthy']:
        score += 10
    if analysis['meme_potential']['text_friendly']:
        score += 10
    
    return min(score, 100)

def create_professional_meme(image: Image.Image, caption: Tuple[str, str], 
                           format_style: str, font_size: int, color_scheme: str,
                           effects: Dict, analysis: Dict) -> Image.Image:
    """Create professional-quality meme with advanced features"""
    
    # Prepare image
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    meme_img = image.copy()
    
    # Apply image enhancements
    if effects.get('enhance_contrast'):
        enhancer = ImageEnhance.Contrast(meme_img)
        meme_img = enhancer.enhance(1.2)
    
    # Create drawing context
    draw = ImageDraw.Draw(meme_img)
    img_width, img_height = meme_img.size
    
    # Font selection based on format
    font_map = {
        'classic': 'arial.ttf',
        'modern': 'calibri.ttf',
        'handwriting': 'comic.ttf',
        'bold': 'arialbd.ttf',
        'elegant': 'times.ttf'
    }
    
    try:
        font_path = font_map.get(format_style, 'arial.ttf')
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
    
    # Color scheme configuration
    color_schemes = {
        "Classic (White/Black)": {"text": "#FFFFFF", "stroke": "#000000", "shadow": "#808080"},
        "Neon (Bright)": {"text": "#00FFFF", "stroke": "#FF00FF", "shadow": "#FFFF00"},
        "Pastel (Soft)": {"text": "#FFE4E1", "stroke": "#B0C4DE", "shadow": "#DDA0DD"},
        "Dark Mode": {"text": "#E0E0E0", "stroke": "#2C2C2C", "shadow": "#404040"},
        "Rainbow": {"text": "#FF0000", "stroke": "#0000FF", "shadow": "#00FF00"},
        "Custom": {"text": "#FFFFFF", "stroke": "#000000", "shadow": "#808080"}
    }
    
    colors = color_schemes.get(color_scheme, color_schemes["Classic (White/Black)"])
    
    def get_text_size(text, font):
        """Get text dimensions"""
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    def draw_enhanced_text(text, x, y, effects_dict):
        """Draw text with multiple effects"""
        if not text.strip():
            return
        
        # Shadow effect
        if effects_dict.get('add_shadow'):
            shadow_offset = max(2, font_size // 20)
            draw.text((x + shadow_offset, y + shadow_offset), text, 
                     font=font, fill=colors['shadow'])
        
        # Glow effect
        if effects_dict.get('add_glow'):
            glow_radius = max(3, font_size // 15)
            for i in range(glow_radius):
                alpha = 255 - (i * 50)
                glow_color = colors['text'] + f"{alpha:02x}"
                for dx in range(-i, i+1):
                    for dy in range(-i, i+1):
                        if dx*dx + dy*dy <= i*i:
                            draw.text((x + dx, y + dy), text, font=font, fill=glow_color)
        
        # Stroke/outline
        stroke_width = max(2, font_size // 20)
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=colors['stroke'])
        
        # Main text
        text_color = colors['text']
        if effects_dict.get('distort_text'):
            # Add slight randomization for chaos effect
            x += random.randint(-2, 2)
            y += random.randint(-2, 2)
        
        draw.text((x, y), text, font=font, fill=text_color)
        
        # Border effect
        if effects_dict.get('add_border'):
            text_width, text_height = get_text_size(text, font)
            border_padding = 10
            draw.rectangle([x - border_padding, y - border_padding, 
                          x + text_width + border_padding, y + text_height + border_padding],
                         outline=colors['stroke'], width=3)
    
    def get_optimal_text_position(text, position='top'):
        """Calculate optimal text position based on image analysis"""
        text_width, text_height = get_text_size(text, font)
        
        # Center horizontally
        x = (img_width - text_width) // 2
        
        # Vertical positioning based on image analysis
        bright_sections = analysis.get('section_brightness', {})
        
        if position == 'top':
            # Check if top section is dark enough for white text
            if bright_sections.get('top', 128) < 100:
                y = int(img_height * 0.15)
            else:
                y = int(img_height * 0.05)
        elif position == 'bottom':
            if bright_sections.get('bottom', 128) < 100:
                y = int(img_height * 0.85) - text_height
            else:
                y = int(img_height * 0.95) - text_height
        else:  # center
            y = (img_height - text_height) // 2
        
        return x, y
    
    # Text placement logic
    top_text, bottom_text = caption
    
    # Smart text formatting
    def format_text_for_meme(text, max_width=None):
        """Format text to fit properly on meme"""
        if not max_width:
            max_width = img_width - 40
        
        words = text.upper().split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            text_width, _ = get_text_size(test_line, font)
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    # Render top text
    if top_text:
        top_lines = format_text_for_meme(top_text)
        start_y = int(img_height * 0.1)
        
        for i, line in enumerate(top_lines):
            x, y = get_optimal_text_position(line, 'top')
            y = start_y + (i * int(font_size * 1.2))
            draw_enhanced_text(line, x, y, effects)
    
    # Render bottom text
    if bottom_text:
        bottom_lines = format_text_for_meme(bottom_text)
        
        # Calculate starting position for bottom text
        total_height = len(bottom_lines) * int(font_size * 1.2)
        start_y = int(img_height * 0.9) - total_height
        
        for i, line in enumerate(bottom_lines):
            x, y = get_optimal_text_position(line, 'bottom')
            y = start_y + (i * int(font_size * 1.2))
            draw_enhanced_text(line, x, y, effects)
    
    # Add watermark if requested
    if effects.get('add_watermark') and effects.get('watermark_text'):
        try:
            wm_font = ImageFont.truetype('arial.ttf', 12)
        except:
            wm_font = ImageFont.load_default()
        
        wm_text = effects['watermark_text']
        wm_width, wm_height = get_text_size(wm_text, wm_font)
        
        # Position watermark
        wm_x = img_width - wm_width - 15
        wm_y = img_height - wm_height - 15
        
        # Semi-transparent background
        overlay = Image.new('RGBA', (wm_width + 10, wm_height + 6), (0, 0, 0, 128))
        meme_img.paste(overlay, (wm_x - 5, wm_y - 3), overlay)
        
        draw.text((wm_x, wm_y), wm_text, font=wm_font, fill="#FFFFFF")
    custom_objects = st.session_state.get("custom_text_positions", [])
    for obj in custom_objects:
        if obj.get("type") == "text":
            text = obj.get("text", "")
            left = int(obj.get("left", 0))
            top = int(obj.get("top", 0))

            # Reuse the draw_enhanced_text method
            draw_enhanced_text(text.upper(), left, top, effects)
    return meme_img

# Main interface
col1, col2 = st.columns([1.2, 0.8])

with col1:
    st.markdown('<div class="step-indicator">🎯 Step 1: Upload Your Image</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose an image to transform into comedy gold", 
        type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        help="Upload any image - our AI will find the comedy potential"
    )
    
    if uploaded_file is not None:
        st.session_state.uploaded_image = Image.open(uploaded_file)
        
        # Perform advanced analysis
        analysis = advanced_image_analysis(st.session_state.uploaded_image)
        st.session_state.image_analysis = analysis
        
        # Display image with professional preview
        st.markdown('<div class="preview-container">', unsafe_allow_html=True)
        st.image(st.session_state.uploaded_image, caption="Ready for Meme Transformation", use_column_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        from streamlit_drawable_canvas import st_canvas

        st.subheader("✏️ Drag & Drop Text Anywhere")

        # Set drawing canvas dimensions
        canvas_width = st.session_state.uploaded_image.width
        canvas_height = st.session_state.uploaded_image.height

        # Choose custom text
        user_text = st.text_input("Enter Meme Text to Place Anywhere", "Type something funny!")

        # Display canvas
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0.0)",  # Transparent fill
            stroke_width=0,
            background_image=st.session_state.uploaded_image,
            update_streamlit=True,
            height=canvas_height,
            width=canvas_width,
            drawing_mode="text",
            key="canvas_editor",
            initial_drawing=[{
                "type": "text",
                "left": 50,
                "top": 50,
                "text": user_text,
                "font": {"size": 30}
            }]
        )

        # Save the custom placed text for rendering
        if canvas_result.json_data is not None and "objects" in canvas_result.json_data:
            st.session_state.custom_text_positions = canvas_result.json_data["objects"]

        # Show analysis insights
        st.markdown(f"""
        <div class="analysis-box">
            <h4>🔍 AI Image Analysis</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <strong>Format:</strong> {analysis['format_type'].title()}<br>
                    <strong>Aspect Ratio:</strong> {analysis['aspect_ratio']:.2f}<br>
                    <strong>Complexity:</strong> {analysis['complexity']:.1f}/10
                </div>
                <div>
                    <strong>Brightness:</strong> {analysis['brightness']:.0f}/255<br>
                    <strong>Text Areas:</strong> {len(analysis['best_text_areas'])}<br>
                    <strong>Meme Score:</strong> {sum(analysis['meme_potential'].values()) * 2:.0f}/10
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate button
        if st.button("🚀 Generate Professional Memes", type="primary", use_container_width=True):
            if not st.session_state.groq_client:
                st.markdown('<div class="error-box">❌ Please enter your Groq API key in the sidebar first!</div>', unsafe_allow_html=True)
            else:
                with st.spinner("🎭 AI Comedy Engine at work... Analyzing humor potential..."):
                    # Generate captions
                    captions = generate_pro_comedy_captions(
                        st.session_state.uploaded_image,
                        st.session_state.groq_client,
                        vision_model,
                        st.session_state.meme_style,
                        comedy_intensity,
                        humor_intelligence,
                        cultural_awareness,
                        analysis
                    )
                    
                    # Calculate viral scores
                    caption_data = []
                    for caption in captions:
                        viral_score = calculate_viral_score(caption, st.session_state.meme_style, analysis)
                        caption_data.append((caption, viral_score))
                    
                    # Sort by viral score
                    caption_data.sort(key=lambda x: x[1], reverse=True)
                    st.session_state.generated_captions = caption_data
                
                st.markdown('<div class="success-box">🎉 Professional meme captions generated! Ready to go viral!</div>', unsafe_allow_html=True)

with col2:
    if st.session_state.uploaded_image is not None:
        st.markdown('<div class="step-indicator">✨ Step 2: Choose Your Caption</div>', unsafe_allow_html=True)
        
        if st.session_state.generated_captions:
            st.subheader("🎭 AI-Generated Comedy Gold")
            
            for i, (caption, viral_score) in enumerate(st.session_state.generated_captions):
                top_text, bottom_text = caption
                
                # Create expandable caption card
                with st.expander(f"🎯 Caption {i+1} - Viral Score: {viral_score}/100"):
                    
                    # Display caption
                    if bottom_text:
                        st.markdown(f"""
                        <div class="comedy-caption">
                            <strong>Setup:</strong> {top_text}<br>
                            <strong>Punchline:</strong> {bottom_text}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="comedy-caption">
                            <strong>Caption:</strong> {top_text}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Viral score indicator
                    if viral_score >= 80:
                        score_color = "#00ff00"
                        score_text = "🔥 Viral Potential"
                    elif viral_score >= 60:
                        score_color = "#ffff00"
                        score_text = "⚡ High Engagement"
                    else:
                        score_color = "#ff9900"
                        score_text = "💫 Good Content"
                    
                    st.markdown(f'<div class="viral-score" style="background-color: {score_color}; color: black;">{score_text}: {viral_score}/100</div>', unsafe_allow_html=True)
                    
                    # Use button
                    if st.button(f"🎨 Create Meme with Caption {i+1}", key=f"use_caption_{i}"):
                        st.session_state.selected_caption = caption
                        st.session_state.viral_score = viral_score
        
        # Custom caption section
        st.subheader("✏️ Custom Caption Creator")
        
        # Quick templates
        st.write("**Quick Templates:**")
        template_cols = st.columns(2)
        
        templates = [
            ("When you...", "Reality: ..."),
            ("POV:", "You're..."),
            ("Me:", "Also me:"),
            ("Nobody:", "Me: ..."),
            ("Expectation:", "Reality:"),
            ("Them:", "Me: ...")
        ]
        
        for i, (top, bottom) in enumerate(templates):
            col = template_cols[i % 2]
            with col:
                if st.button(f"{top} / {bottom}", key=f"template_{i}"):
                    st.session_state.selected_caption = (top, bottom)
        
        # Manual input
        custom_top = st.text_input("Top Text", 
                                  value=st.session_state.selected_caption[0] if st.session_state.selected_caption else "")
        custom_bottom = st.text_input("Bottom Text", 
                                     value=st.session_state.selected_caption[1] if st.session_state.selected_caption else "")
        
        # Preview viral score for custom caption
        if custom_top or custom_bottom:
            custom_score = calculate_viral_score((custom_top, custom_bottom), 
                                               st.session_state.meme_style, 
                                               st.session_state.image_analysis)
            st.markdown(f'<div class="viral-score">Custom Caption Score: {custom_score}/100</div>', unsafe_allow_html=True)

# Step 3: Generate Final Meme
if st.session_state.uploaded_image is not None:
    st.markdown('<div class="step-indicator">🎨 Step 3: Create Your Masterpiece</div>', unsafe_allow_html=True)
    
    col3, col4 = st.columns([1, 1])
    
    with col3:
        if st.button("🚀 Generate Professional Meme", type="primary", use_container_width=True):
            if custom_top or custom_bottom:
                with st.spinner("🎨 Creating your professional meme..."):
                    effects_dict = {
                        'add_shadow': add_shadow,
                        'add_glow': add_glow,
                        'add_border': add_border,
                        'distort_text': distort_text,
                        'add_watermark': add_watermark,
                        'watermark_text': watermark_text if add_watermark else None,
                        'enhance_contrast': True
                    }
                    
                    st.session_state.final_meme = create_professional_meme(
                        st.session_state.uploaded_image,
                        (custom_top, custom_bottom),
                        meme_format,
                        font_size,
                        color_scheme,
                        effects_dict,
                        st.session_state.image_analysis
                    )
                
                st.markdown('<div class="success-box">🎉 Professional meme created! Ready to dominate social media!</div>', unsafe_allow_html=True)
            else:
                st.error("💡 Add some text to create your meme!")
    
    with col4:
        if st.session_state.final_meme is not None:
            # Quick actions
            st.subheader("⚡ Quick Actions")
            
            # Download options
            img_buffer = io.BytesIO()
            st.session_state.final_meme.save(img_buffer, format='PNG')
            img_bytes = img_buffer.getvalue()
            
            download_cols = st.columns(2)
            with download_cols[0]:
                st.download_button(
                    label="📥 Download PNG",
                    data=img_bytes,
                    file_name=f"meme_pro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png",
                    use_container_width=True
                )
            
            with download_cols[1]:
                # JPEG version
                jpg_buffer = io.BytesIO()
                st.session_state.final_meme.convert('RGB').save(jpg_buffer, format='JPEG', quality=95)
                jpg_bytes = jpg_buffer.getvalue()
                
                st.download_button(
                    label="📥 Download JPG",
                    data=jpg_bytes,
                    file_name=f"meme_pro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )

# Display final meme
if st.session_state.final_meme is not None:
    st.markdown('<div class="step-indicator">🏆 Your Professional Meme</div>', unsafe_allow_html=True)
    
    # Main display
    col5, col6 = st.columns([2, 1])
    
    with col5:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        st.image(st.session_state.final_meme, caption="Professional Meme - Ready for Social Media", use_column_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col6:
        st.subheader("📈 Meme Analytics")
        
        # Performance prediction
        viral_score = st.session_state.viral_score or 75
        
        metrics_col1, metrics_col2 = st.columns(2)
        with metrics_col1:
            st.metric("Viral Score", f"{viral_score}/100", f"+{viral_score-50}")
        with metrics_col2:
            engagement_rate = min(viral_score * 1.2, 100)
            st.metric("Engagement Rate", f"{engagement_rate:.0f}%", f"+{engagement_rate-60:.0f}%")
        
        # Platform optimization
        st.subheader("📱 Platform Guide")
        
        platforms = {
            "📘 Facebook": "Perfect for sharing with friends and family",
            "📷 Instagram": "Great for Stories and Posts", 
            "🐦 Twitter": "Ideal for viral moments",
            "📱 TikTok": "Add trending audio for maximum reach",
            "💬 Discord": "Share in your favorite servers",
            "📧 WhatsApp": "Send to group chats"
        }
        
        for platform, tip in platforms.items():
            st.markdown(f"**{platform}**: {tip}")
        
        # Hashtag suggestions
        st.subheader("🏷️ Trending Hashtags")
        
        style_hashtags = {
            "sarcastic": ["#SarcasmLevel100", "#BrutallyHonest", "#RealityCheck", "#SavageMeme"],
            "absurd": ["#RandomHumor", "#WeirdMemes", "#AbsurdMemes", "#ChaoticEnergy"],
            "relatable": ["#Relatable", "#MoodAF", "#TooReal", "#MeIRL"],
            "roast": ["#RoastMode", "#SavageMode", "#NoMercy", "#DestroyedByWords"],
            "gen_z": ["#GenZHumor", "#ChronicallyOnline", "#ItsGiving", "#NoCap"],
            "dark": ["#DarkHumor", "#DarkMemes", "#EdgeLord", "#TooReal"]
        }
        
        current_tags = style_hashtags.get(st.session_state.meme_style, style_hashtags["sarcastic"])
        st.code(" ".join(current_tags + ["#MemePro", "#AIGenerated", "#ViralContent"]))

# Footer with professional branding
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 3rem 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 15px; margin-top: 2rem;">
    <h3 style="margin: 0 0 1rem 0;">🔥 Meme Generator Pro</h3>
    <p style="margin: 0 0 1rem 0; opacity: 0.9;">Professional AI-Powered Comedy Engine for Serious Meme Creators</p>
    <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1rem;">
        <div><strong>∞</strong><br>AI Models</div>
        <div><strong>🎯</strong><br>Viral Prediction</div>
        <div><strong>⚡</strong><br>Instant Generation</div>
        <div><strong>🏆</strong><br>Professional Quality</div>
    </div>
    <p style="margin: 2rem 0 0 0; font-size: 0.9rem; opacity: 0.7;">
        Built with Streamlit, Groq AI, and a deep understanding of internet culture.<br>
        Create memes that actually go viral. 🚀
    </p>
</div>
""", unsafe_allow_html=True)