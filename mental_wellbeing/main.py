import streamlit as st
import json
import os
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
import time
import random
from pathlib import Path
import hashlib

# Configuration
st.set_page_config(
    page_title="MindWell - Your Mental Health Companion",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Groq client (you'll need to add your API key)
def init_groq_client():
    # Replace with your actual Groq API key
    api_key = "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"
    return Groq(api_key=api_key)

# Data management functions
def get_user_data_path(username):
    """Get path for user's data file"""
    user_dir = Path("user_data")
    user_dir.mkdir(exist_ok=True)
    # Hash username for privacy
    hashed_name = hashlib.md5(username.encode()).hexdigest()
    return user_dir / f"{hashed_name}.json"

def load_user_data(username):
    """Load user data from local JSON file"""
    data_path = get_user_data_path(username)
    if data_path.exists():
        try:
            with open(data_path, 'r') as f:
                return json.load(f)
        except:
            return create_empty_user_data()
    return create_empty_user_data()

def create_empty_user_data():
    """Create empty user data structure"""
    return {
        "mood_entries": [],
        "journal_entries": [],
        "goals": [],
        "meditation_sessions": [],
        "wellness_habits": {
            "hydration": [],
            "exercise": [],
            "sleep": []
        }
    }

def save_user_data(username, data):
    """Save user data to local JSON file"""
    data_path = get_user_data_path(username)
    with open(data_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# Authentication (simple for demo)
def authenticate_user():
    """Simple authentication system"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🧠 MindWell - Your Mental Health Companion")
        st.markdown("### Welcome! Please enter your username to continue")
        
        username = st.text_input("Username", key="login_username")
        if st.button("Enter"):
            if username:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.user_data = load_user_data(username)
                st.rerun()
            else:
                st.error("Please enter a username")
        return False
    return True

# AI Chat functions
def get_ai_response(user_input, context="general"):
    """Get AI response using Groq"""
    try:
        client = init_groq_client()
        
        system_prompts = {
            "mood_check": """You are a compassionate mental health companion. The user is sharing their current mood and feelings. 
            Respond with empathy, validate their feelings, and offer gentle CBT-inspired suggestions or coping strategies. 
            Keep responses supportive, non-judgmental, and encouraging. End with a thoughtful follow-up question.""",
            
            "journal": """You are helping the user reflect on their journal entry. Provide thoughtful insights, 
            highlight positive patterns, and gently suggest areas for growth. Be supportive and encouraging.""",
            
            "crisis": """You are a mental health support companion. The user may be experiencing distress. 
            Respond with immediate empathy and care. Suggest professional help resources and crisis hotlines when appropriate. 
            Always prioritize their safety and wellbeing."""
        }
        
        system_prompt = system_prompts.get(context, system_prompts["mood_check"])
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"I'm having trouble responding right now. Please try again. Error: {str(e)}"

# Mood tracking functions
def mood_check_in():
    """Daily mood check-in interface"""
    st.header("💬 Daily Mood Check-In")
    
    # Mood scale
    mood_scale = st.slider(
        "How are you feeling today? (1=Very Low, 10=Excellent)", 
        1, 10, 5, 
        help="Rate your overall mood and energy level"
    )
    
    # Quick mood descriptors
    mood_tags = st.multiselect(
        "What words describe your mood today?",
        ["Happy", "Sad", "Anxious", "Calm", "Stressed", "Excited", "Tired", "Energetic", 
         "Frustrated", "Content", "Overwhelmed", "Peaceful", "Angry", "Grateful"]
    )
    
    # Detailed input
    mood_description = st.text_area(
        "Tell me more about how you're feeling today...",
        placeholder="What's on your mind? How has your day been?"
    )
    
    if st.button("Share with AI Companion", type="primary"):
        if mood_description:
            # Get AI response
            with st.spinner("Your AI companion is thinking..."):
                ai_response = get_ai_response(
                    f"Mood level: {mood_scale}/10. Mood tags: {', '.join(mood_tags)}. "
                    f"User says: {mood_description}",
                    context="mood_check"
                )
            
            # Save mood entry
            mood_entry = {
                "date": datetime.now().isoformat(),
                "mood_scale": mood_scale,
                "mood_tags": mood_tags,
                "description": mood_description,
                "ai_response": ai_response
            }
            
            st.session_state.user_data["mood_entries"].append(mood_entry)
            save_user_data(st.session_state.username, st.session_state.user_data)
            
            # Display AI response
            st.success("Entry saved!")
            st.markdown("### 🤖 Your AI Companion responds:")
            st.markdown(f"*{ai_response}*")
            
            # Crisis detection (simple keyword-based)
            crisis_keywords = ["suicide", "kill myself", "end it all", "can't go on"]
            if any(keyword in mood_description.lower() for keyword in crisis_keywords):
                st.error("🚨 Crisis Support Resources")
                st.markdown("""
                **If you're in immediate danger, please call emergency services.**
                
                **Crisis Hotlines:**
                - National Suicide Prevention Lifeline: 988
                - Crisis Text Line: Text HOME to 741741
                - International: befrienders.org
                
                Please reach out to a mental health professional or trusted person.
                """)

def mood_analytics():
    """Display mood analytics and trends"""
    st.header("📊 Mood Analytics")
    
    mood_entries = st.session_state.user_data.get("mood_entries", [])
    
    if not mood_entries:
        st.info("No mood entries yet. Complete some daily check-ins to see your trends!")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(mood_entries)
    df['date'] = pd.to_datetime(df['date']).dt.date
    df['datetime'] = pd.to_datetime(pd.DataFrame(mood_entries)['date'])
    
    # Time period selector
    period = st.selectbox("View data for:", ["Last 7 days", "Last 30 days", "All time"])
    
    if period == "Last 7 days":
        cutoff = datetime.now() - timedelta(days=7)
        df = df[df['datetime'] >= cutoff]
    elif period == "Last 30 days":
        cutoff = datetime.now() - timedelta(days=30)
        df = df[df['datetime'] >= cutoff]
    
    if df.empty:
        st.info(f"No entries found for {period.lower()}")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Mood trend chart
        fig = px.line(df, x='date', y='mood_scale', 
                     title='Mood Trend Over Time',
                     labels={'mood_scale': 'Mood (1-10)', 'date': 'Date'})
        fig.update_traces(mode='markers+lines')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Average mood by day of week
        df['day_of_week'] = df['datetime'].dt.day_name()
        daily_avg = df.groupby('day_of_week')['mood_scale'].mean().reset_index()
        
        fig2 = px.bar(daily_avg, x='day_of_week', y='mood_scale',
                     title='Average Mood by Day of Week',
                     labels={'mood_scale': 'Average Mood', 'day_of_week': 'Day'})
        st.plotly_chart(fig2, use_container_width=True)
    
    # Mood statistics
    st.subheader("📈 Your Mood Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Average Mood", f"{df['mood_scale'].mean():.1f}/10")
    with col2:
        st.metric("Best Day", f"{df['mood_scale'].max()}/10")
    with col3:
        st.metric("Entries Logged", len(df))
    with col4:
        trend = "📈" if df['mood_scale'].iloc[-1] > df['mood_scale'].iloc[0] else "📉"
        st.metric("Trend", trend)

# Journaling functions
def journaling():
    """Guided journaling interface"""
    st.header("📓 Guided Journaling")
    
    # Journal prompts
    prompts = [
        "What are three things you're grateful for today?",
        "What challenged you today and how did you handle it?",
        "What's one thing you learned about yourself recently?",
        "Describe a moment today when you felt proud of yourself.",
        "What are you looking forward to tomorrow?",
        "What emotions did you experience today? Why?",
        "What would you tell your past self from a week ago?",
        "What's something that made you smile recently?"
    ]
    
    # Random prompt or custom
    col1, col2 = st.columns([3, 1])
    with col1:
        prompt_type = st.radio("Choose journal type:", ["Random Prompt", "Free Writing"])
    with col2:
        if st.button("🎲 New Random Prompt"):
            st.session_state.random_prompt = random.choice(prompts)
    
    if prompt_type == "Random Prompt":
        if 'random_prompt' not in st.session_state:
            st.session_state.random_prompt = random.choice(prompts)
        st.info(f"💭 **Today's Prompt:** {st.session_state.random_prompt}")
        journal_entry = st.text_area("Your response:", height=200, key="prompted_journal")
    else:
        journal_entry = st.text_area("Write freely about anything on your mind:", height=200, key="free_journal")
    
    if st.button("Save Journal Entry", type="primary"):
        if journal_entry:
            # Get AI insights
            with st.spinner("Generating insights..."):
                ai_insights = get_ai_response(
                    f"Journal entry: {journal_entry}",
                    context="journal"
                )
            
            # Save entry
            entry = {
                "date": datetime.now().isoformat(),
                "prompt": st.session_state.get('random_prompt', 'Free writing') if prompt_type == "Random Prompt" else "Free writing",
                "content": journal_entry,
                "ai_insights": ai_insights
            }
            
            st.session_state.user_data["journal_entries"].append(entry)
            save_user_data(st.session_state.username, st.session_state.user_data)
            
            st.success("Journal entry saved!")
            st.markdown("### 💡 AI Insights:")
            st.markdown(f"*{ai_insights}*")
    
    # Recent entries
    st.subheader("📖 Recent Journal Entries")
    journal_entries = st.session_state.user_data.get("journal_entries", [])
    
    if journal_entries:
        for i, entry in enumerate(reversed(journal_entries[-5:])):  # Show last 5
            with st.expander(f"Entry from {pd.to_datetime(entry['date']).strftime('%B %d, %Y')}"):
                if entry.get('prompt') != 'Free writing':
                    st.markdown(f"**Prompt:** {entry['prompt']}")
                st.markdown(f"**Entry:** {entry['content']}")
                if entry.get('ai_insights'):
                    st.markdown(f"**AI Insights:** *{entry['ai_insights']}*")
    else:
        st.info("No journal entries yet. Start writing to see your entries here!")

# Relaxation tools
def relaxation_tools():
    """Meditation and breathing exercises"""
    st.header("🎧 Relaxation & Mindfulness")
    
    tab1, tab2, tab3 = st.tabs(["🧘 Guided Meditation", "🫁 Breathing Exercises", "🎵 Ambient Sounds"])
    
    with tab1:
        st.subheader("Guided Meditation Sessions")
        
        meditation_types = {
            "Mindfulness (5 min)": "Focus on the present moment and your breath",
            "Body Scan (10 min)": "Progressive relaxation through your entire body",
            "Loving-kindness (7 min)": "Cultivate compassion for yourself and others",
            "Stress Relief (8 min)": "Release tension and anxiety",
            "Sleep Preparation (12 min)": "Prepare your mind and body for rest"
        }
        
        selected_meditation = st.selectbox("Choose a meditation:", list(meditation_types.keys()))
        st.info(meditation_types[selected_meditation])
        
        # Meditation timer simulation
        if st.button("🧘 Start Meditation", type="primary"):
            duration = int(selected_meditation.split('(')[1].split(' ')[0])
            
            # Simple meditation guidance
            st.success(f"Starting {selected_meditation}...")
            st.markdown("""
            ### 🧘‍♀️ Meditation Guidance:
            
            1. **Find a comfortable position** - Sit or lie down comfortably
            2. **Close your eyes** - Or soften your gaze downward
            3. **Focus on your breath** - Notice the natural rhythm
            4. **When your mind wanders** - Gently return attention to breath
            5. **Be kind to yourself** - There's no "perfect" meditation
            
            *Take your time and remember: this is your moment of peace.*
            """)
            
            # Log meditation session
            session = {
                "date": datetime.now().isoformat(),
                "type": selected_meditation,
                "duration": duration,
                "completed": True
            }
            st.session_state.user_data["meditation_sessions"].append(session)
            save_user_data(st.session_state.username, st.session_state.user_data)
    
    with tab2:
        st.subheader("Breathing Exercises")
        
        breathing_exercises = {
            "4-7-8 Breathing": {"inhale": 4, "hold": 7, "exhale": 8, "description": "Calming and sleep-inducing"},
            "Box Breathing": {"inhale": 4, "hold": 4, "exhale": 4, "description": "Stress reduction and focus"},
            "Triangle Breathing": {"inhale": 4, "hold": 4, "exhale": 4, "description": "Simple and effective"},
        }
        
        exercise = st.selectbox("Choose breathing pattern:", list(breathing_exercises.keys()))
        pattern = breathing_exercises[exercise]
        
        st.info(f"**{exercise}:** {pattern['description']}")
        st.markdown(f"**Pattern:** Inhale {pattern['inhale']}s → Hold {pattern['hold']}s → Exhale {pattern['exhale']}s")
        
        if st.button("🫁 Start Breathing Exercise"):
            st.success("Follow the breathing pattern below:")
            
            # Create breathing guide
            breathing_container = st.empty()
            progress_bar = st.progress(0)
            
            cycles = st.number_input("Number of cycles:", 1, 20, 5)
            
            for cycle in range(cycles):
                # Inhale
                breathing_container.markdown(f"### 🌬️ **INHALE** (Cycle {cycle + 1}/{cycles})")
                for i in range(pattern['inhale']):
                    progress_bar.progress((i + 1) / pattern['inhale'])
                    time.sleep(1)
                
                # Hold
                breathing_container.markdown(f"### ⏸️ **HOLD** (Cycle {cycle + 1}/{cycles})")
                for i in range(pattern['hold']):
                    time.sleep(1)
                
                # Exhale
                breathing_container.markdown(f"### 🌊 **EXHALE** (Cycle {cycle + 1}/{cycles})")
                for i in range(pattern['exhale']):
                    progress_bar.progress(1 - (i + 1) / pattern['exhale'])
                    time.sleep(1)
                
                progress_bar.progress(0)
            
            breathing_container.markdown("### ✨ **Complete!** Great job!")
    
    with tab3:
        st.subheader("Ambient Sounds")
        st.info("🎵 Relaxing ambient sounds to help you focus and relax")
        
        # Since we can't actually play audio in Streamlit easily, we'll provide descriptions and suggestions
        sounds = {
            "🌧️ Rain": "Gentle rainfall for relaxation and focus",
            "🌊 Ocean Waves": "Calming ocean sounds for stress relief",
            "🔥 Crackling Fire": "Cozy fireplace ambiance",
            "🌲 Forest": "Peaceful nature sounds with birds and wind",
            "☕ Coffee Shop": "Ambient café atmosphere for productivity",
            "🎼 White Noise": "Consistent background sound for concentration"
        }
        
        for sound, description in sounds.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{sound}** - {description}")
            with col2:
                if st.button(f"Play", key=f"play_{sound}"):
                    st.info(f"🎵 Imagine the soothing sounds of {sound.split(' ', 1)[1].lower()}...")

# Goals and habits tracking
def goals_habits():
    """Goal setting and habit tracking"""
    st.header("🎯 Goals & Wellness Habits")
    
    tab1, tab2 = st.tabs(["🎯 Goals", "📋 Daily Habits"])
    
    with tab1:
        st.subheader("Set & Track Wellness Goals")
        
        # Add new goal
        with st.expander("➕ Add New Goal"):
            goal_title = st.text_input("Goal Title:", placeholder="e.g., Meditate 10 minutes daily")
            goal_category = st.selectbox("Category:", ["Mental Health", "Physical Health", "Sleep", "Mindfulness", "Other"])
            goal_target = st.number_input("Target (days/times per week):", 1, 7, 3)
            goal_description = st.text_area("Description:", placeholder="Why is this goal important to you?")
            
            if st.button("Add Goal"):
                if goal_title:
                    goal = {
                        "id": len(st.session_state.user_data.get("goals", [])),
                        "title": goal_title,
                        "category": goal_category,
                        "target": goal_target,
                        "description": goal_description,
                        "created_date": datetime.now().isoformat(),
                        "progress": []
                    }
                    st.session_state.user_data.setdefault("goals", []).append(goal)
                    save_user_data(st.session_state.username, st.session_state.user_data)
                    st.success("Goal added!")
                    st.rerun()
        
        # Display existing goals
        goals = st.session_state.user_data.get("goals", [])
        if goals:
            for goal in goals:
                with st.expander(f"{goal['category']}: {goal['title']}"):
                    st.markdown(f"**Target:** {goal['target']} times per week")
                    st.markdown(f"**Description:** {goal['description']}")
                    
                    # Progress tracking
                    today = date.today().isoformat()
                    if st.button(f"✅ Mark Complete for Today", key=f"goal_{goal['id']}"):
                        if today not in [p.get('date') for p in goal['progress']]:
                            goal['progress'].append({"date": today, "completed": True})
                            save_user_data(st.session_state.username, st.session_state.user_data)
                            st.success("Progress logged!")
                            st.rerun()
                        else:
                            st.info("Already logged for today!")
                    
                    # Show recent progress
                    recent_progress = [p for p in goal['progress'] if pd.to_datetime(p['date']).date() >= date.today() - timedelta(days=7)]
                    if recent_progress:
                        st.markdown(f"**This week:** {len(recent_progress)}/{goal['target']} completed")
                        progress_pct = len(recent_progress) / goal['target']
                        st.progress(min(progress_pct, 1.0))
        else:
            st.info("No goals set yet. Add your first wellness goal above!")
    
    with tab2:
        st.subheader("Daily Wellness Habits")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 💧 Hydration")
            if st.button("Log Water Glass"):
                today = date.today().isoformat()
                st.session_state.user_data.setdefault("wellness_habits", {}).setdefault("hydration", []).append({
                    "date": today,
                    "time": datetime.now().time().isoformat()
                })
                save_user_data(st.session_state.username, st.session_state.user_data)
                st.success("💧 Water logged!")
            
            # Show today's count
            today_water = len([h for h in st.session_state.user_data.get("wellness_habits", {}).get("hydration", []) 
                             if h['date'] == date.today().isoformat()])
            st.metric("Today's Glasses", today_water)
        
        with col2:
            st.markdown("### 🚶 Exercise")
            exercise_duration = st.number_input("Minutes exercised:", 0, 300, 0, key="exercise_input")
            if st.button("Log Exercise"):
                if exercise_duration > 0:
                    today = date.today().isoformat()
                    st.session_state.user_data.setdefault("wellness_habits", {}).setdefault("exercise", []).append({
                        "date": today,
                        "duration": exercise_duration
                    })
                    save_user_data(st.session_state.username, st.session_state.user_data)
                    st.success(f"🚶 {exercise_duration} minutes logged!")
        
        with col3:
            st.markdown("### 😴 Sleep")
            sleep_hours = st.number_input("Hours slept last night:", 0.0, 12.0, 0.0, 0.5, key="sleep_input")
            if st.button("Log Sleep"):
                if sleep_hours > 0:
                    yesterday = (date.today() - timedelta(days=1)).isoformat()
                    st.session_state.user_data.setdefault("wellness_habits", {}).setdefault("sleep", []).append({
                        "date": yesterday,
                        "hours": sleep_hours
                    })
                    save_user_data(st.session_state.username, st.session_state.user_data)
                    st.success(f"😴 {sleep_hours} hours logged!")

# Wellness reminders
def wellness_reminders():
    """Display wellness tips and reminders"""
    st.header("💡 Wellness Tips & Reminders")
    
    # Daily wellness tip
    tips = [
        "💧 Remember to stay hydrated! Aim for 8 glasses of water today.",
        "🚶 Take a 5-minute walk break - your mind and body will thank you.",
        "🧘 Try a 2-minute breathing exercise when you feel stressed.",
        "😴 Good sleep hygiene starts 1 hour before bedtime - dim the lights and avoid screens.",
        "🙏 Practice gratitude - name three things you're thankful for today.",
        "🤝 Reach out to a friend or family member you haven't talked to in a while.",
        "🌱 Spend a few minutes in nature or looking at something green.",
        "📚 Learn something new today, even if it's just for 10 minutes.",
        "🎵 Listen to your favorite music - it's an instant mood booster!",
        "🧠 Your thoughts are not facts - observe them without judgment."
    ]
    
    # Get consistent daily tip based on date
    tip_index = hash(str(date.today())) % len(tips)
    daily_tip = tips[tip_index]
    
    st.info(f"**Today's Wellness Tip:** {daily_tip}")
    
    # Quick wellness actions
    st.subheader("🔔 Quick Wellness Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💧 Hydration Reminder", use_container_width=True):
            st.balloons()
            st.success("Great reminder! Drink a glass of water now. Your body needs it! 💧")
    
    with col2:
        if st.button("🧘 Mini Meditation", use_container_width=True):
            st.success("Take 5 deep breaths with me:")
            st.markdown("""
            1. Breathe in slowly through your nose... 🌬️
            2. Hold for a moment... ⏸️
            3. Breathe out slowly through your mouth... 🌊
            
            Repeat 4 more times. You've got this! 🧘‍♀️
            """)
    
    with col3:
        if st.button("🚶 Movement Break", use_container_width=True):
            st.success("Time to move! Try one of these:")
            movements = [
                "🤸 10 jumping jacks",
                "🧘 Touch your toes 5 times",
                "💪 Wall push-ups (10 reps)",
                "🌀 Neck and shoulder rolls",
                "🚶 Walk around your space for 2 minutes"
            ]
            st.markdown(f"**Suggested movement:** {random.choice(movements)}")
    
    # Mental health resources
    st.subheader("🆘 Mental Health Resources")
    with st.expander("Crisis Support & Professional Help"):
        st.markdown("""
        **🚨 Emergency/Crisis Support:**
        - **National Suicide Prevention Lifeline:** 988
        - **Crisis Text Line:** Text HOME to 741741
        - **International Association for Suicide Prevention:** iasp.info
        
        **🏥 Professional Help:**
        - **Psychology Today:** Find therapists near you
        - **BetterHelp:** Online therapy platform
        - **Talkspace:** Text-based therapy
        - **Your healthcare provider:** Ask for mental health referrals
        
        **📚 Educational Resources:**
        - **National Alliance on Mental Illness (NAMI):** nami.org
        - **Mental Health America:** mha.org
        - **Anxiety and Depression Association of America:** adaa.org
        
        *Remember: This app is a companion tool and not a replacement for professional mental health care.*
        """)

# Main app function
def main():
    """Main application function"""
    if not authenticate_user():
        return
    
    # Sidebar navigation
    st.sidebar.title(f"👋 Welcome, {st.session_state.username}")
    
    # Navigation menu
    pages = {
        "🏠 Home": "home",
        "💬 Mood Check-In": "mood_checkin", 
        "📊 Mood Analytics": "mood_analytics",
        "📓 Journal": "journal",
        "🧘 Relaxation": "relaxation",
        "🎯 Goals & Habits": "goals",
        "💡 Wellness Tips": "wellness"
    }
    
    selected_page = st.sidebar.selectbox("Navigate to:", list(pages.keys()))
    page_key = pages[selected_page]
    
    # User stats in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📈 Your Stats")
    
    mood_entries = len(st.session_state.user_data.get("mood_entries", []))
    journal_entries = len(st.session_state.user_data.get("journal_entries", []))
    meditation_sessions = len(st.session_state.user_data.get("meditation_sessions", []))
    
    st.sidebar.metric("Mood Check-ins", mood_entries)
    st.sidebar.metric("Journal Entries", journal_entries)
    st.sidebar.metric("Meditation Sessions", meditation_sessions)
    
    # Logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # Main content area
    if page_key == "home":
        st.title("🧠 MindWell - Your Mental Health Companion")
        st.markdown("### How are you feeling today?")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_mood = "N/A"
            if mood_entries > 0:
                recent_moods = [entry['mood_scale'] for entry in st.session_state.user_data['mood_entries'][-7:]]
                avg_mood = f"{sum(recent_moods)/len(recent_moods):.1f}/10"
            st.metric("7-Day Avg Mood", avg_mood)
        
        with col2:
            st.metric("Total Check-ins", mood_entries)
        
        with col3:
            st.metric("Journal Entries", journal_entries)
        
        with col4:
            streak = 0  # Simple streak calculation
            today = date.today()
            for i in range(7):
                check_date = (today - timedelta(days=i)).isoformat()
                if any(pd.to_datetime(entry['date']).date().isoformat() == check_date 
                      for entry in st.session_state.user_data.get('mood_entries', [])):
                    streak += 1
                else:
                    break
            st.metric("Current Streak", f"{streak} days")
        
        # Quick actions
        st.markdown("---")
        st.subheader("🚀 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💬 Quick Mood Check", use_container_width=True):
                st.session_state.quick_mood_check = True
        
        with col2:
            if st.button("📓 Write in Journal", use_container_width=True):
                st.switch_page = "journal"
        
        with col3:
            if st.button("🧘 Start Meditation", use_container_width=True):
                st.switch_page = "relaxation"
        
        # Quick mood check
        if st.session_state.get('quick_mood_check', False):
            st.markdown("---")
            st.subheader("💬 Quick Mood Check")
            
            quick_mood = st.slider("How are you feeling right now?", 1, 10, 5)
            quick_note = st.text_input("One word to describe your mood:")
            
            if st.button("Submit Quick Check"):
                entry = {
                    "date": datetime.now().isoformat(),
                    "mood_scale": quick_mood,
                    "mood_tags": [quick_note] if quick_note else [],
                    "description": f"Quick check: {quick_note}",
                    "type": "quick_check"
                }
                st.session_state.user_data["mood_entries"].append(entry)
                save_user_data(st.session_state.username, st.session_state.user_data)
                st.success("Quick mood logged! 👍")
                st.session_state.quick_mood_check = False
                st.rerun()
        
        # Recent activity
        st.markdown("---")
        st.subheader("📅 Recent Activity")
        
        # Combine recent entries
        recent_activities = []
        
        for entry in st.session_state.user_data.get("mood_entries", [])[-3:]:
            recent_activities.append({
                "type": "Mood Check-in",
                "date": entry["date"],
                "content": f"Mood: {entry['mood_scale']}/10"
            })
        
        for entry in st.session_state.user_data.get("journal_entries", [])[-3:]:
            recent_activities.append({
                "type": "Journal Entry",
                "date": entry["date"],
                "content": entry["content"][:100] + "..." if len(entry["content"]) > 100 else entry["content"]
            })
        
        for session in st.session_state.user_data.get("meditation_sessions", [])[-3:]:
            recent_activities.append({
                "type": "Meditation",
                "date": session["date"],
                "content": f"{session['type']} - {session['duration']} min"
            })
        
        # Sort by date
        recent_activities.sort(key=lambda x: x["date"], reverse=True)
        
        if recent_activities:
            for activity in recent_activities[:5]:  # Show last 5
                activity_date = pd.to_datetime(activity["date"]).strftime("%m/%d at %I:%M %p")
                st.markdown(f"**{activity['type']}** - {activity_date}")
                st.markdown(f"*{activity['content']}*")
                st.markdown("---")
        else:
            st.info("No recent activity. Start by doing a mood check-in or writing in your journal!")
    
    elif page_key == "mood_checkin":
        mood_check_in()
    
    elif page_key == "mood_analytics":
        mood_analytics()
    
    elif page_key == "journal":
        journaling()
    
    elif page_key == "relaxation":
        relaxation_tools()
    
    elif page_key == "goals":
        goals_habits()
    elif page_key == "wellness":
        wellness_reminders()

if __name__ == "__main__":
    main()