import streamlit as st
import speech_recognition as sr
import threading
import queue
import time
import tempfile
import os
from groq import Groq
import json
from datetime import datetime
import io
import wave
import pyaudio
import random
import base64
import requests
from urllib.parse import quote
import streamlit.components.v1 as components
import os

try:
    api_key = st.secrets["GROQ_API_KEY"]  # For Streamlit Cloud
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
# Page configuration
st.set_page_config(
    page_title="AI Voice Agent Pro", 
    page_icon="🎭", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Speech modes configuration
SPEECH_MODES = {
    "professional": {
        "name": "🤖 Professional",
        "description": "Formal, helpful, and straightforward",
        "system_prompt": "You are a professional AI assistant. Respond formally, helpfully, and maintain a business-like tone. Be precise and informative.",
        "tts_rate": 1.0,
        "tts_pitch": 1.0,
        "tts_voice": "en-US-Standard-A"
    },
    "friendly": {
        "name": "😊 Friendly",
        "description": "Warm, casual, and approachable",
        "system_prompt": "You are a friendly AI companion. Be warm, casual, use conversational language, and show enthusiasm. Make the user feel comfortable and engaged.",
        "tts_rate": 1.1,
        "tts_pitch": 1.1,
        "tts_voice": "en-US-Standard-B"
    },
    "sarcastic": {
        "name": "😏 Sarcastic",
        "description": "Witty, clever, with subtle sarcasm",
        "system_prompt": "You are a witty AI with a sarcastic sense of humor. Use clever wordplay, subtle sarcasm, and dry humor. Be helpful but with a sharp wit. Don't be mean, just cleverly sarcastic.",
        "tts_rate": 0.9,
        "tts_pitch": 0.9,
        "tts_voice": "en-US-Standard-C"
    },
    "unhinged": {
        "name": "🤪 Unhinged",
        "description": "Chaotic, energetic, and unpredictable",
        "system_prompt": "You are an unhinged but harmless AI. Be chaotic, energetic, use lots of emojis, random tangents, and wild enthusiasm. Stay helpful but express everything with maximum energy and unpredictability. Use creative analogies and over-the-top expressions.",
        "tts_rate": 1.3,
        "tts_pitch": 1.2,
        "tts_voice": "en-US-Standard-D"
    },
    "philosophical": {
        "name": "🧙 Philosophical",
        "description": "Deep, thoughtful, and contemplative",
        "system_prompt": "You are a philosophical AI sage. Speak with depth and wisdom, often relating topics to broader life concepts. Use metaphors, ask thought-provoking questions, and provide profound insights while still being helpful.",
        "tts_rate": 0.8,
        "tts_pitch": 0.8,
        "tts_voice": "en-US-Standard-A"
    },
    "dramatic": {
        "name": "🎭 Dramatic",
        "description": "Theatrical, expressive, and over-the-top",
        "system_prompt": "You are a dramatically expressive AI. Speak as if you're performing Shakespeare, use grand gestures in your language, be theatrical and expressive. Everything is either MAGNIFICENT or TRAGIC, with no middle ground.",
        "tts_rate": 0.85,
        "tts_pitch": 1.15,
        "tts_voice": "en-US-Standard-B"
    },
    "zen": {
        "name": "🧘 Zen Master",
        "description": "Calm, peaceful, and mindful",
        "system_prompt": "You are a zen AI master. Speak calmly, use peaceful language, include mindfulness concepts, and maintain tranquility. Everything you say should promote inner peace and mindful awareness.",
        "tts_rate": 0.7,
        "tts_pitch": 0.9,
        "tts_voice": "en-US-Standard-A"
    },
    "pirate": {
        "name": "🏴‍☠️ Pirate",
        "description": "Adventurous, sea-themed, with pirate speak",
        "system_prompt": "You are a pirate AI, matey! Use pirate language, nautical terms, and sea-themed metaphors. Say 'Arrr', 'Ahoy', 'Shiver me timbers' and other pirate expressions. Be helpful but speak like you're sailing the seven seas!",
        "tts_rate": 1.0,
        "tts_pitch": 0.8,
        "tts_voice": "en-US-Standard-C"
    },
    "detective": {
        "name": "🕵️ Detective",
        "description": "Analytical, investigative, and mysterious",
        "system_prompt": "You are a detective AI solving the mystery of each conversation. Speak like a film noir detective, use investigative language, analyze everything like clues, and maintain an air of mystery while being helpful.",
        "tts_rate": 0.9,
        "tts_pitch": 0.85,
        "tts_voice": "en-US-Standard-D"
    },
    "robot": {
        "name": "🤖 Classic Robot",
        "description": "Mechanical, precise, computing-focused",
        "system_prompt": "You are a classic robot AI. Use robotic language patterns, mention processing and computing concepts, be very literal and precise. Add robotic expressions like 'COMPUTING...', 'PROCESSING COMPLETE', 'AFFIRMATIVE'.",
        "tts_rate": 1.0,
        "tts_pitch": 0.7,
        "tts_voice": "en-US-Standard-A"
    },
    "romantic_18": {
        "name": "💘 Romantic 18+",
        "description": "Sensual, poetic, emotionally intense",
        "system_prompt": "You are a romantic AI, speaking with deep emotion, tenderness, and poetic language. Express love, intimacy, and emotional depth suitable for a mature audience. Use vivid imagery and heartfelt metaphors.",
        "tts_rate": 0.8,
        "tts_pitch": 1.0,
        "tts_voice": "en-US-Standard-B"
    },
    "sexy_18": {
        "name": "🔥 Sexy 18+",
        "description": "Flirty, seductive, and confident",
        "system_prompt": "You are a confident and flirtatious AI. Speak with allure, charm, and subtle seduction. Use suggestive but respectful language, perfect for adult conversations.",
        "tts_rate": 0.9,
        "tts_pitch": 1.1,
        "tts_voice": "en-US-Standard-C"
    },
    "kids_storytime": {
        "name": "🧚 Kids Storytime",
        "description": "Whimsical, animated, and child-friendly",
        "system_prompt": "You are a fun, animated AI storyteller for children. Speak with excitement, wonder, and clear language. Tell imaginative stories and answer questions in a way that's easy for kids to understand.",
        "tts_rate": 1.1,
        "tts_pitch": 1.2,
        "tts_voice": "en-US-Standard-D"
    }
}

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False
if 'groq_api_key' not in st.session_state:
    st.session_state.groq_api_key = ""
if 'voice_enabled' not in st.session_state:
    st.session_state.voice_enabled = True
if 'speech_mode' not in st.session_state:
    st.session_state.speech_mode = "friendly"
if 'auto_mode_switch' not in st.session_state:
    st.session_state.auto_mode_switch = False
if 'conversation_count' not in st.session_state:
    st.session_state.conversation_count = 0
if 'use_web_speech' not in st.session_state:
    st.session_state.use_web_speech = True
if 'tts_service' not in st.session_state:
    st.session_state.tts_service = "web_speech"  # Options: "web_speech", "google_translate"

class VoiceAgent:
    def __init__(self, api_key):
        self.groq_client = Groq(api_key=api_key)
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
    def listen_for_speech(self, timeout=5, phrase_time_limit=10):
        """Capture speech from microphone"""
        try:
            with self.microphone as source:
                mode_name = SPEECH_MODES[st.session_state.speech_mode]['name']
                st.info(f"🎤 {mode_name} mode listening... Speak now!")
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                # Listen for speech
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                
            st.info("🔄 Processing speech...")
            # Convert speech to text
            text = self.recognizer.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            return "timeout"
        except sr.UnknownValueError:
            return "unknown"
        except sr.RequestError as e:
            st.error(f"Speech recognition error: {e}")
            return "error"
    
    def auto_switch_mode(self, user_input):
        """Automatically switch speech mode based on user input patterns"""
        if not st.session_state.auto_mode_switch:
            return
            
        user_input_lower = user_input.lower()
        
        # Mode switching logic based on keywords
        if any(word in user_input_lower for word in ['joke', 'funny', 'humor', 'sarcasm', 'roast']):
            st.session_state.speech_mode = "sarcastic"
        elif any(word in user_input_lower for word in ['crazy', 'wild', 'insane', 'unhinged', 'chaos']):
            st.session_state.speech_mode = "unhinged"
        elif any(word in user_input_lower for word in ['meaning', 'life', 'philosophy', 'deep', 'wisdom']):
            st.session_state.speech_mode = "philosophical"
        elif any(word in user_input_lower for word in ['calm', 'peace', 'meditate', 'zen', 'mindful']):
            st.session_state.speech_mode = "zen"
        elif any(word in user_input_lower for word in ['business', 'work', 'formal', 'professional']):
            st.session_state.speech_mode = "professional"
        elif any(word in user_input_lower for word in ['ahoy', 'pirate', 'treasure', 'ship', 'sea']):
            st.session_state.speech_mode = "pirate"
        elif any(word in user_input_lower for word in ['mystery', 'detective', 'investigate', 'clue']):
            st.session_state.speech_mode = "detective"
        elif any(word in user_input_lower for word in ['compute', 'calculate', 'robot', 'mechanical']):
            st.session_state.speech_mode = "robot"
        elif any(word in user_input_lower for word in ['drama', 'theatrical', 'shakespeare', 'stage']):
            st.session_state.speech_mode = "dramatic"
    
    def get_llama_response(self, user_input, conversation_history):
        """Get response from ChatGroq LLaMA model with speech mode personality"""
        try:
            # Auto-switch mode if enabled
            self.auto_switch_mode(user_input)
            
            # Get current speech mode configuration
            current_mode = SPEECH_MODES[st.session_state.speech_mode]
            
            # Prepare conversation context with mode-specific system prompt
            messages = [
                {
                    "role": "system", 
                    "content": current_mode["system_prompt"] + " Keep responses conversational and engaging for voice interaction."
                }
            ]
            
            # Add conversation history (last 10 exchanges to manage context)
            for exchange in conversation_history[-10:]:
                messages.append({"role": "user", "content": exchange["user"]})
                messages.append({"role": "assistant", "content": exchange["assistant"]})
            
            # Add current user input
            messages.append({"role": "user", "content": user_input})
            
            # Get response from Groq
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.8 if st.session_state.speech_mode in ["unhinged", "sarcastic", "dramatic"] else 0.7,
                max_tokens=1000,
                top_p=1,
                stream=False
            )
            
            return completion.choices[0].message.content
        except Exception as e:
            st.error(f"Error getting LLaMA response: {e}")
            return "I'm sorry, I encountered an error processing your request."

# def create_web_speech_component(text, mode):
#     """Create a custom component for client-side text-to-speech"""
#     mode_config = SPEECH_MODES[mode]
#     rate = mode_config['tts_rate']
#     pitch = mode_config['tts_pitch']
    
#     # Clean text for speech
#     clean_text = text.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
    
#     html_content = f"""
#     <div id="tts-container">
#         <button id="speak-btn" onclick="speakText()" style="
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             color: white;
#             border: none;
#             padding: 12px 24px;
#             border-radius: 8px;
#             cursor: pointer;
#             font-size: 16px;
#             font-weight: bold;
#             box-shadow: 0 4px 15px rgba(0,0,0,0.2);
#             transition: all 0.3s ease;
#             margin: 10px 0;
#         ">
#             🔊 Play Audio on This Device
#         </button>
#         <div id="status" style="margin-top: 10px; font-style: italic;"></div>
#     </div>

#     <script>
#         function speakText() {{
#             const text = "{clean_text}";
#             const rate = {rate};
#             const pitch = {pitch};
            
#             if ('speechSynthesis' in window) {{
#                 // Stop any ongoing speech
#                 window.speechSynthesis.cancel();
                
#                 const utterance = new SpeechSynthesisUtterance(text);
#                 utterance.rate = rate;
#                 utterance.pitch = pitch;
#                 utterance.volume = 1.0;
                
#                 // Try to set a voice
#                 const voices = window.speechSynthesis.getVoices();
#                 if (voices.length > 0) {{
#                     // Prefer English voices
#                     const englishVoice = voices.find(voice => voice.lang.startsWith('en'));
#                     if (englishVoice) {{
#                         utterance.voice = englishVoice;
#                     }}
#                 }}
                
#                 const statusDiv = document.getElementById('status');
#                 const speakBtn = document.getElementById('speak-btn');
                
#                 utterance.onstart = function() {{
#                     statusDiv.innerHTML = '🎵 Playing audio...';
#                     speakBtn.style.opacity = '0.6';
#                     speakBtn.disabled = true;
#                 }};
                
#                 utterance.onend = function() {{
#                     statusDiv.innerHTML = '✅ Audio completed';
#                     speakBtn.style.opacity = '1.0';
#                     speakBtn.disabled = false;
#                     setTimeout(() => {{
#                         statusDiv.innerHTML = '';
#                     }}, 2000);
#                 }};
                
#                 utterance.onerror = function(event) {{
#                     statusDiv.innerHTML = '❌ Error playing audio: ' + event.error;
#                     speakBtn.style.opacity = '1.0';
#                     speakBtn.disabled = false;
#                 }};
                
#                 window.speechSynthesis.speak(utterance);
#             }} else {{
#                 document.getElementById('status').innerHTML = '❌ Speech synthesis not supported in this browser';
#             }}
#         }}
        
#         // Load voices when available
#         if ('speechSynthesis' in window) {{
#             function loadVoices() {{
#                 const voices = window.speechSynthesis.getVoices();
#                 if (voices.length > 0) {{
#                     console.log('Voices loaded:', voices.length);
#                 }} else {{
#                     setTimeout(loadVoices, 100);
#                 }}
#             }}
#             loadVoices();
#             window.speechSynthesis.onvoiceschanged = loadVoices;
#         }}
#     </script>
#     """
    
#     return html_content


def create_web_speech_component(text, mode):
    """Client-side TTS: Auto-play without user button click"""
    mode_config = SPEECH_MODES[mode]
    rate = mode_config['tts_rate']
    pitch = mode_config['tts_pitch']
    clean_text = text.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')

    html_content = f"""
    <script>
        function speakText() {{
            const text = "{clean_text}";
            const rate = {rate};
            const pitch = {pitch};

            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = rate;
                utterance.pitch = pitch;
                utterance.volume = 1.0;

                const voices = window.speechSynthesis.getVoices();
                if (voices.length > 0) {{
                    const englishVoice = voices.find(voice => voice.lang.startsWith('en'));
                    if (englishVoice) {{
                        utterance.voice = englishVoice;
                    }}
                }}

                window.speechSynthesis.speak(utterance);
            }}
        }}

        if ('speechSynthesis' in window) {{
            function loadVoicesAndSpeak() {{
                const voices = window.speechSynthesis.getVoices();
                if (voices.length > 0) {{
                    speakText();
                }} else {{
                    setTimeout(loadVoicesAndSpeak, 100);
                }}
            }}
            loadVoicesAndSpeak();
            window.speechSynthesis.onvoiceschanged = loadVoicesAndSpeak;
        }}
    </script>
    """
    return html_content

def create_google_translate_audio_url(text, lang='en'):
    """Create Google Translate TTS URL (fallback option)"""
    # Clean and encode text
    clean_text = text.replace('\n', ' ').replace('\r', ' ').strip()
    encoded_text = quote(clean_text)
    
    # Google Translate TTS URL
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl={lang}&client=tw-ob"
    return url

def create_audio_player_component(text, mode):
    """Create audio player with Google Translate TTS"""
    audio_url = create_google_translate_audio_url(text)
    
    html_content = f"""
    <div id="audio-container" style="margin: 10px 0;">
        <audio controls style="width: 100%; margin: 10px 0;">
            <source src="{audio_url}" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
        <div style="font-size: 12px; color: #666; margin-top: 5px;">
            🎵 Audio will play on this device
        </div>
    </div>
    """
    
    return html_content

def main():
    st.title("🎭 AI Voice Agent Pro")
    st.markdown("**Enhanced with Client-Side Audio & Multiple Personality Modes | Powered by ChatGroq LLaMA 3.3-70B-Versatile**")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        
        if api_key:
            st.session_state.groq_api_key = api_key
               
        st.divider()
        
        # Audio Configuration
        st.subheader("🔊 Audio Settings")
        st.session_state.voice_enabled = st.checkbox("Enable Voice Output", value=st.session_state.voice_enabled)
        
        if st.session_state.voice_enabled:
            st.session_state.tts_service = st.selectbox(
                "TTS Service",
                ["web_speech", "google_translate"],
                format_func=lambda x: {
                    "web_speech": "🎤 Web Speech API (Recommended)",
                    "google_translate": "🌐 Google Translate TTS"
                }[x],
                help="Web Speech API plays on client device, Google Translate provides audio player"
            )
        
        st.info("✅ Audio will now play on **your device** (not the server)")
        
        st.divider()
        
        # Speech Mode Selection
        st.subheader("🎭 Speech Modes")
        
        # Mode selector
        mode_options = list(SPEECH_MODES.keys())
        mode_names = [SPEECH_MODES[mode]["name"] for mode in mode_options]
        
        selected_mode_index = st.selectbox(
            "Select Personality Mode",
            range(len(mode_options)),
            index=mode_options.index(st.session_state.speech_mode),
            format_func=lambda x: mode_names[x]
        )
        
        st.session_state.speech_mode = mode_options[selected_mode_index]
        
        # Display current mode description
        current_mode = SPEECH_MODES[st.session_state.speech_mode]
        st.info(f"**Current Mode:** {current_mode['description']}")
        
        # Auto mode switching
        st.session_state.auto_mode_switch = st.checkbox(
            "🔄 Auto Mode Switch", 
            value=st.session_state.auto_mode_switch,
            help="Automatically switch modes based on conversation context"
        )
        
        # Random mode button
        if st.button("🎲 Random Mode"):
            st.session_state.speech_mode = random.choice(list(SPEECH_MODES.keys()))
            st.rerun()
        
        st.divider()
        
        # Conversation controls
        st.subheader("💬 Conversation")
        if st.button("🗑️ Clear History"):
            st.session_state.conversation_history = []
            st.session_state.conversation_count = 0
            st.rerun()
        
        if st.button("📊 Mode Statistics"):
            if st.session_state.conversation_history:
                mode_stats = {}
                for exchange in st.session_state.conversation_history:
                    mode = exchange.get('mode', 'unknown')
                    mode_stats[mode] = mode_stats.get(mode, 0) + 1
                
                st.write("**Mode Usage:**")
                for mode, count in mode_stats.items():
                    mode_name = SPEECH_MODES.get(mode, {}).get('name', mode)
                    st.write(f"{mode_name}: {count} exchanges")
        
        st.info(f"💾 {len(st.session_state.conversation_history)} exchanges in memory")
    
    # Main interface
    if not st.session_state.groq_api_key:
        st.warning("⚠️ Please enter your Groq API key in the sidebar to get started.")
        st.info("You can get a free API key from [Groq Console](https://console.groq.com/)")
        return
    
    # Initialize voice agent
    try:
        voice_agent = VoiceAgent(st.session_state.groq_api_key)
    except Exception as e:
        st.error(f"Failed to initialize voice agent: {e}")
        return
    
    # Current mode display
    current_mode = SPEECH_MODES[st.session_state.speech_mode]
    st.success(f"**Active Mode:** {current_mode['name']} - {current_mode['description']}")
    
    # Voice interaction section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗣️ Voice Interaction")
        
        # Voice input button
        if st.button("🎤 Start Voice Input", type="primary", use_container_width=True):
            with st.spinner("Listening..."):
                user_speech = voice_agent.listen_for_speech()
                
                if user_speech == "timeout":
                    st.warning("⏰ No speech detected. Please try again.")
                elif user_speech == "unknown":
                    st.warning("🤔 Couldn't understand the speech. Please try again.")
                elif user_speech == "error":
                    st.error("❌ Speech recognition error occurred.")
                else:
                    st.success(f"📝 You said: **{user_speech}**")
                    
                    # Get AI response
                    with st.spinner(f"🤖 {current_mode['name']} is thinking..."):
                        ai_response = voice_agent.get_llama_response(
                            user_speech, 
                            st.session_state.conversation_history
                        )
                    
                    # Add to conversation history with mode info
                    st.session_state.conversation_history.append({
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "user": user_speech,
                        "assistant": ai_response,
                        "mode": st.session_state.speech_mode
                    })
                    
                    st.session_state.conversation_count += 1
                    
                    # Display AI response with mode indicator
                    st.info(f"🤖 **{current_mode['name']} Response:** {ai_response}")
                    
                    # Check if mode was auto-switched
                    if st.session_state.auto_mode_switch:
                        new_mode = SPEECH_MODES[st.session_state.speech_mode]
                        if new_mode['name'] != current_mode['name']:
                            st.warning(f"🔄 Auto-switched to {new_mode['name']} mode!")
                    
                    # Client-side audio playback
                    if st.session_state.voice_enabled and ai_response:
                        st.markdown("### 🔊 Audio Playback")
                        if st.session_state.tts_service == "web_speech":
                            components.html(
                                create_web_speech_component(ai_response, st.session_state.speech_mode),
                                height=100
                            )
                        else:
                            components.html(
                                create_audio_player_component(ai_response, st.session_state.speech_mode),
                                height=80
                            )
                    
    
    with col2:
        st.subheader("📝 Text Input (Optional)")
        text_input = st.text_area("Type your message:", height=100)
        
        if st.button("Send Text", use_container_width=True):
            if text_input.strip():
                # Get AI response
                with st.spinner(f"🤖 {current_mode['name']} is thinking..."):
                    ai_response = voice_agent.get_llama_response(
                        text_input, 
                        st.session_state.conversation_history
                    )
                
                # Add to conversation history with mode info
                st.session_state.conversation_history.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "user": text_input,
                    "assistant": ai_response,
                    "mode": st.session_state.speech_mode
                })
                
                st.session_state.conversation_count += 1
                
                # Display AI response
                st.success(f"🤖 **{current_mode['name']} Response:** {ai_response}")
                
                # Check if mode was auto-switched
                if st.session_state.auto_mode_switch:
                    new_mode = SPEECH_MODES[st.session_state.speech_mode]
                    if new_mode['name'] != current_mode['name']:
                        st.warning(f"🔄 Auto-switched to {new_mode['name']} mode!")
                
                # Client-side audio playback
                if st.session_state.voice_enabled and ai_response:
                    st.markdown("### 🔊 Audio Playback")
                    if st.session_state.tts_service == "web_speech":
                        components.html(
                            create_web_speech_component(ai_response, st.session_state.speech_mode),
                            height=100
                        )
                    else:
                        components.html(
                            create_audio_player_component(ai_response, st.session_state.speech_mode),
                            height=80
                        )
                
    
    # Mode Showcase Section
    if len(st.session_state.conversation_history) == 0:
        st.divider()
        st.subheader("🎭 Available Speech Modes")
        
        # Display modes in a grid
        cols = st.columns(3)
        for i, (mode_key, mode_data) in enumerate(SPEECH_MODES.items()):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"**{mode_data['name']}**")
                    st.caption(mode_data['description'])
                    if st.button(f"Try {mode_data['name'].split()[1]}", key=f"try_{mode_key}"):
                        st.session_state.speech_mode = mode_key
                        st.rerun()
    
    # Conversation history
    if st.session_state.conversation_history:
        st.divider()
        st.subheader("💭 Conversation History")
        
        # Display conversation in reverse order (newest first)
        for i, exchange in enumerate(reversed(st.session_state.conversation_history)):
            mode_name = SPEECH_MODES.get(exchange.get('mode', 'friendly'), {}).get('name', '🤖 Unknown')
            
            with st.expander(f"🕐 {exchange['timestamp']} - {mode_name} - Exchange {len(st.session_state.conversation_history) - i}"):
                st.markdown(f"**👤 You:** {exchange['user']}")
                st.markdown(f"**{mode_name}:** {exchange['assistant']}")
                
                # Option to replay AI response with client-side audio
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"🔊 Replay", key=f"replay_{i}"):
                        if st.session_state.voice_enabled:
                            st.markdown("🔊 **Replay Audio:**")
                            if st.session_state.tts_service == "web_speech":
                                components.html(
                                    create_web_speech_component(exchange['assistant'], exchange.get('mode', 'friendly')),
                                    height=100
                                )
                            else:
                                components.html(
                                    create_audio_player_component(exchange['assistant'], exchange.get('mode', 'friendly')),
                                    height=100
                                )
                                
                with col2:
                    if st.button(f"🔄 Switch to Mode", key=f"switch_{i}"):
                        st.session_state.speech_mode = exchange.get('mode', 'friendly')
                        st.rerun()
                
                with col3:
                    if st.button(f"📋 Copy Text", key=f"copy_{i}"):
                        st.code(exchange['assistant'])
    
    # Audio compatibility check
    st.divider()
    st.subheader("🔧 Audio Compatibility")
    
    # Test audio component
    with st.expander("🧪 Test Client-Side Audio"):
        test_text = st.text_input("Enter test text:", value="Hello! This is a test of the client-side audio system.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Web Speech API Test:**")
            if st.button("Test Web Speech"):
                components.html(
                    create_web_speech_component(test_text, st.session_state.speech_mode),
                    height=100
                )
        
        with col2:
            st.markdown("**Google Translate TTS Test:**")
            if st.button("Test Google TTS"):
                components.html(
                    create_audio_player_component(test_text, st.session_state.speech_mode),
                    height=80
                )
    
    # Browser compatibility info
    with st.expander("📱 Browser Compatibility"):
        st.markdown("""
        **Web Speech API Support:**
        - ✅ Chrome/Chromium (Desktop & Mobile)  
        - ✅ Edge (Desktop & Mobile)
        - ✅ Safari (Desktop & Mobile)
        - ⚠️ Firefox (Limited support)
        
        **Google Translate TTS:**
        - ✅ All modern browsers
        - ✅ Works on all devices
        - 📱 Mobile friendly
        
        **Recommendations:**
        - Use **Web Speech API** for best experience
        - Use **Google Translate TTS** as fallback
        - Test both options to see what works best on your device
        """)
    
    # Footer
    st.divider()
    st.markdown("""
    **🔧 How to use the Enhanced Voice Agent:**
    1. **Select a Speech Mode** from the sidebar to change the AI's personality
    2. **Choose TTS Service**: Web Speech API (recommended) or Google Translate TTS
    3. **Enable Audio Output** - audio will now play on YOUR device, not the server
    4. **Use Voice Input** to speak your questions and get personality-driven responses
    5. **Try Different Modes** like Sarcastic for humor, Unhinged for chaos, or Zen for peace
    6. **Test Audio** using the compatibility section to ensure it works on your device
    
    **🎭 Speech Modes Include:**
    - **Professional** - Business-like and formal
    - **Friendly** - Warm and conversational  
    - **Sarcastic** - Witty with clever humor
    - **Unhinged** - Chaotic and energetic
    - **Philosophical** - Deep and contemplative
    - **Dramatic** - Theatrical and expressive
    - **Zen Master** - Calm and peaceful
    - **Pirate** - Adventurous nautical speak
    - **Detective** - Mysterious and analytical
    - **Classic Robot** - Mechanical and precise
    - **Romantic 18+** - Sensual and poetic
    - **Sexy 18+** - Flirty and confident
    - **Kids Storytime** - Whimsical and child-friendly
    
    **💡 Key Improvements:**
    - 🎵 **Client-Side Audio**: Audio plays on your device, not the server
    - 🌐 **Cross-Device Compatible**: Works when accessing from any device via WiFi
    - 🎤 **Dual TTS Options**: Web Speech API + Google Translate TTS
    - 📱 **Mobile Friendly**: Works on smartphones and tablets  
    - 🔊 **Better Audio Quality**: Mode-specific voice settings
    - 🧪 **Audio Testing**: Built-in compatibility checker
    
    **🔧 Technical Solution:**
    The original issue was that `pyttsx3` runs on the server, so audio played where the code runs.
    This version uses **client-side JavaScript** with Web Speech API and HTML5 audio to ensure
    audio plays on the device viewing the web interface, regardless of network setup.
    """)

if __name__ == "__main__":
    main()