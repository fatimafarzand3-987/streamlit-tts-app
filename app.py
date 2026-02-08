import streamlit as st
from gtts import gTTS
import pyttsx3
import io
import base64
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

# Page config
st.set_page_config(
    page_title="VoiceCraft Pro",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern glassmorphism design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        min-height: 100vh;
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 2px solid #06b6d4;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(6, 182, 212, 0.15);
    }
    
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 3rem;
        background: rgba(255, 255, 255, 0.98);
        border-radius: 24px;
        border: 2px solid #06b6d4;
        box-shadow: 0 20px 60px rgba(6, 182, 212, 0.25);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #0891b2 0%, #06b6d4 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 700;
        transition: all 0.3s ease;
        width: 100%;
        font-size: 1rem;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(6, 182, 212, 0.6);
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #0f172a !important;
        border: 2px solid #06b6d4 !important;
        border-radius: 12px;
        padding: 0.75rem !important;
        transition: all 0.3s ease;
        font-size: 1rem !important;
    }
    
    .stTextInput>div>div>input::placeholder, .stTextArea>div>div>textarea::placeholder {
        color: #64748b !important;
    }
    
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #0891b2 !important;
        box-shadow: 0 0 0 4px rgba(6, 182, 212, 0.3) !important;
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(14, 165, 233, 0.1));
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        border: 2px solid rgba(6, 182, 212, 0.5);
    }
    
    .history-item {
        background: rgba(6, 182, 212, 0.08);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #0891b2;
    }
    
    h1, h2, h3, h4 {
        color: #0f172a !important;
        font-weight: 800 !important;
    }
    
    p, div, label, span {
        color: #1e293b !important;
    }
    
    .welcome-text {
        font-size: 2.5rem;
        background: linear-gradient(120deg, #0891b2 0%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    .user-card {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(14, 165, 233, 0.1));
        border: 2px solid #06b6d4;
        border-radius: 16px;
        padding: 1.2rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .user-card h3 {
        color: #0891b2;
        margin: 0;
        font-size: 1.3rem;
    }
    
    .user-card p {
        color: #1e293b;
        margin: 0;
        font-size: 0.95rem;
        font-weight: 600;
    }
    
    .stSelectbox>div>div>select {
        background-color: rgba(255, 255, 255, 0.95) !important;
        color: #0f172a !important;
        border: 2px solid #06b6d4 !important;
    }
    
    .stRadio>div {
        color: #0f172a !important;
    }
    
    .stRadio label, .stCheckbox label {
        color: #1e293b !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #1e293b !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'audio_history' not in st.session_state:
    st.session_state.audio_history = []
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# Auto-restore login state if user_data exists
if st.session_state.user_data is not None and st.session_state.current_user is not None:
    st.session_state.logged_in = True
else:
    st.session_state.logged_in = False

# User data file
USER_DATA_FILE = 'users.json'

def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, name):
    users = load_users()
    if username in users:
        return False, "Username already exists!"
    
    users[username] = {
        'password': hash_password(password),
        'name': name,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'total_conversions': 0
    }
    save_users(users)
    return True, "Registration successful!"

def login_user(username, password):
    users = load_users()
    if username not in users:
        return False, "User not found!"
    
    if users[username]['password'] != hash_password(password):
        return False, "Incorrect password!"
    
    return True, users[username]

def text_to_speech(text, lang='en', slow=False):
    try:
        tts = gTTS(text=text, lang=lang, slow=slow)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp, None
    except Exception as e:
        return None, str(e)

def text_to_speech_advanced(text, voice_type='normal', gender='female', emotion='neutral'):
    """
    Advanced TTS with voice and emotion options using pyttsx3
    """
    try:
        engine = pyttsx3.init()
        
        # Get available voices
        voices = engine.getProperty('voices')
        
        # Select voice based on gender
        if gender == 'male':
            # Usually the first voice is male, second is female (varies by system)
            voice_id = voices[0].id if len(voices) > 0 else voices[0].id
        else:
            # Female voice
            voice_id = voices[1].id if len(voices) > 1 else voices[0].id
        
        engine.setProperty('voice', voice_id)
        
        # Modify speech parameters based on emotion/voice type
        rate = engine.getProperty('rate')  # Default rate
        volume = engine.getProperty('volume')
        
        if voice_type == 'angry':
            rate = 150  # Faster, more aggressive
            volume = 1.0
        elif voice_type == 'kind':
            rate = 110  # Slower, gentler
            volume = 0.9
        elif voice_type == 'exclamation':
            rate = 140  # Fast and excited
            volume = 1.0
        elif voice_type == 'question':
            rate = 115  # Slightly slower for clarity
            volume = 0.95
        elif voice_type == 'whisper':
            rate = 100
            volume = 0.6
        else:  # normal
            rate = 125
            volume = 0.95
        
        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)
        
        # Save to bytes
        fp = io.BytesIO()
        engine.save_to_file(text, 'temp_audio.mp3')
        engine.runAndWait()
        
        # Read the saved file
        if os.path.exists('temp_audio.mp3'):
            with open('temp_audio.mp3', 'rb') as f:
                fp.write(f.read())
            fp.seek(0)
            os.remove('temp_audio.mp3')
            return fp, None
        else:
            return None, "Could not generate audio"
    except Exception as e:
        return None, str(e)

def get_audio_download_link(audio_buffer, filename):
    audio_buffer.seek(0)
    b64 = base64.b64encode(audio_buffer.read()).decode()
    href = f'<a href="data:audio/mp3;base64,{b64}" download="{filename}.mp3" style="text-decoration:none;">'
    href += f'<button style="background:linear-gradient(135deg, #11998e 0%, #38ef7d 100%);color:white;padding:10px 20px;border:none;border-radius:8px;cursor:pointer;width:100%;">⬇️ Download Audio</button></a>'
    return href

# Authentication Pages
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<h2 style="text-align:center;color:#0891b2;font-size:2.2rem;">🎙️ VoiceCraft Pro</h2>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center;color:#1e293b;margin-bottom:2rem;font-size:1.05rem;font-weight:500;">Sign in to continue</p>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Login", key="login_btn"):
                if username and password:
                    success, result = login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.current_user = username
                        st.session_state.user_data = result
                        st.success(f"Welcome back, {result['name']}! 👋")
                        st.rerun()
                    else:
                        st.error(result)
                else:
                    st.warning("Please fill in all fields")
        
        with tab2:
            new_username = st.text_input("Username", key="reg_user")
            new_name = st.text_input("Full Name", key="reg_name")
            new_password = st.text_input("Password", type="password", key="reg_pass")
            confirm_pass = st.text_input("Confirm Password", type="password", key="reg_confirm")
            
            if st.button("Sign Up", key="signup_btn"):
                if new_username and new_name and new_password:
                    if new_password != confirm_pass:
                        st.error("Passwords don't match!")
                    else:
                        success, msg = register_user(new_username, new_password, new_name)
                        if success:
                            st.success(msg)
                            st.info("Please login with your new account")
                        else:
                            st.error(msg)
                else:
                    st.warning("Please fill in all fields")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Main App
def main_app():
    user_data = st.session_state.user_data
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div class="user-card">
            <h3>👤 {user_data['name']}</h3>
            <p>@{st.session_state.current_user}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Stats
        st.markdown("### 📊 Your Stats")
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color:#0891b2;margin:0;font-size:2rem;">{user_data.get('total_conversions', 0)}</h4>
            <p style="color:#1e293b;margin:0;font-weight:600;">Total Conversions</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
        page = st.radio("Navigate", 
                       ["🎙️ Text to Speech", "📁 File Upload", "📜 History", "⚙️ Settings"],
                       label_visibility="collapsed")
        
        st.markdown("---")
        
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.session_state.user_data = None
            st.rerun()
    
    # Main Content Area
    st.markdown(f'<h1 class="welcome-text">Welcome, {user_data["name"]}! 🎉</h1>', unsafe_allow_html=True)
    
    if "Text to Speech" in page:
        tts_page()
    elif "File Upload" in page:
        file_upload_page()
    elif "History" in page:
        history_page()
    elif "Settings" in page:
        settings_page()

def tts_page():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 📝 Enter Text")
        text_input = st.text_area(
            "Type or paste your text here:",
            height=200,
            placeholder="Enter the text you want to convert to speech..."
        )
        
        # Quick actions
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("📝 Load Sample"):
                st.session_state.sample_text = "Hello! Welcome to VoiceCraft Pro. This is a sample text to demonstrate the text-to-speech functionality. You can convert any text to natural-sounding speech!"
                st.rerun()
        
        with col_btn2:
            if st.button("🗑️ Clear"):
                st.session_state.sample_text = ""
                st.rerun()
        
        with col_btn3:
            if st.button("📋 Paste"):
                st.info("Use Ctrl+V to paste")
    
    with col2:
        st.markdown("### ⚙️ Settings")
        
        # Voice Type Selection
        voice_type = st.selectbox(
            "Voice Type",
            ["Normal", "Angry", "Kind", "Exclamation", "Question", "Whisper"],
            help="Choose the emotion/style of the voice"
        )
        
        # Gender Selection
        gender = st.radio(
            "Voice Gender",
            ["Female", "Male"],
            horizontal=True,
            help="Select voice gender"
        )
        
        st.markdown("---")
        
        languages = {
            'English (US)': 'en',
            'English (UK)': 'en-uk',
            'Spanish': 'es',
            'French': 'fr',
            'German': 'de',
            'Italian': 'it',
            'Portuguese': 'pt',
            'Russian': 'ru',
            'Japanese': 'ja',
            'Korean': 'ko',
            'Chinese': 'zh-cn',
            'Hindi': 'hi',
            'Arabic': 'ar'
        }
        
        selected_lang = st.selectbox("Language", list(languages.keys()))
        lang_code = languages[selected_lang]
        
        speed = st.select_slider("Speed", options=["Slow", "Normal", "Fast"], value="Normal")
        slow_speed = speed == "Slow"
        
        st.markdown("---")
        st.info(f"Characters: {len(text_input)}/5000")
    
    # Use sample text if available
    if 'sample_text' in st.session_state and st.session_state.sample_text:
        text_input = st.session_state.sample_text
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Convert button
    if st.button("🎙️ Generate Speech", type="primary", use_container_width=True):
        if not text_input.strip():
            st.error("⚠️ Please enter some text!")
        elif len(text_input) > 5000:
            st.error("⚠️ Text too long! Max 5000 characters.")
        else:
            with st.spinner("🎵 Generating audio... Please wait"):
                # Map voice type to lowercase for function
                voice_type_lower = voice_type.lower()
                gender_lower = gender.lower()
                
                audio_buffer, error = text_to_speech_advanced(
                    text_input, 
                    voice_type=voice_type_lower, 
                    gender=gender_lower
                )
                
                if error:
                    st.error(f"❌ Error: {error}")
                else:
                    st.success("✅ Audio generated successfully!")
                    
                    # Display audio
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.audio(audio_buffer, format='audio/mp3')
                    
                    # Download and save options
                    col_dl, col_save = st.columns(2)
                    
                    with col_dl:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"voicecraft_{timestamp}"
                        st.markdown(get_audio_download_link(audio_buffer, filename), unsafe_allow_html=True)
                    
                    with col_save:
                        if st.button("💾 Save to History"):
                            audio_buffer.seek(0)
                            st.session_state.audio_history.append({
                                'text': text_input[:100] + "..." if len(text_input) > 100 else text_input,
                                'audio': audio_buffer.getvalue(),
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                'language': selected_lang,
                                'voice_type': voice_type,
                                'gender': gender
                            })
                            st.success("Saved!")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Update user stats
                    users = load_users()
                    if st.session_state.current_user in users:
                        users[st.session_state.current_user]['total_conversions'] = \
                            users[st.session_state.current_user].get('total_conversions', 0) + 1
                        save_users(users)

def file_upload_page():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📁 Upload File")
    
    uploaded_file = st.file_uploader("Choose a file", type=['txt', 'pdf', 'docx'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.type == "text/plain":
                text_content = uploaded_file.read().decode('utf-8')
                st.success(f"✅ Loaded {len(text_content)} characters")
                
                st.markdown("### Preview:")
                st.text_area("Content", text_content[:1000] + "..." if len(text_content) > 1000 else text_content, height=200)
                
                if st.button("🎙️ Convert to Speech"):
                    if len(text_content) > 5000:
                        st.warning("File too large! Using first 5000 characters.")
                        text_content = text_content[:5000]
                    
                    with st.spinner("Generating audio..."):
                        audio_buffer, error = text_to_speech(text_content, 'en')
                        if audio_buffer:
                            st.audio(audio_buffer, format='audio/mp3')
                            st.download_button("⬇️ Download", audio_buffer, "file_audio.mp3", "audio/mp3")
                        else:
                            st.error(f"Error: {error}")
            else:
                st.warning("📄 Currently only .txt files are fully supported. PDF/DOCX support coming soon!")
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def history_page():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📜 Conversion History")
    
    if not st.session_state.audio_history:
        st.info("No history yet. Start converting text to see your history here!")
    else:
        for idx, item in enumerate(reversed(st.session_state.audio_history[-10:])):
            voice_info = f"{item.get('voice_type', 'Normal')} | {item.get('gender', 'Female')} | {item['language']}"
            with st.expander(f"🎵 {item['timestamp']} - {voice_info}"):
                st.write(f"**Text:** {item['text']}")
                st.audio(io.BytesIO(item['audio']), format='audio/mp3')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("⬇️ Download", io.BytesIO(item['audio']), f"history_{idx}.mp3", "audio/mp3")
                with col2:
                    if st.button("🗑️ Delete", key=f"del_{idx}"):
                        st.session_state.audio_history.remove(item)
                        st.rerun()
    
    if st.session_state.audio_history and st.button("🗑️ Clear All History"):
        st.session_state.audio_history = []
        st.success("History cleared!")
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def settings_page():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Account Settings")
    
    users = load_users()
    user = users.get(st.session_state.current_user, {})
    
    with st.form("settings_form"):
        new_name = st.text_input("Display Name", value=user.get('name', ''))
        current_pass = st.text_input("Current Password", type="password")
        new_pass = st.text_input("New Password", type="password")
        confirm_new_pass = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("💾 Save Changes"):
            if current_pass:
                if hash_password(current_pass) != user['password']:
                    st.error("Current password is incorrect!")
                elif new_pass and new_pass != confirm_new_pass:
                    st.error("New passwords don't match!")
                else:
                    users[st.session_state.current_user]['name'] = new_name
                    if new_pass:
                        users[st.session_state.current_user]['password'] = hash_password(new_pass)
                    save_users(users)
                    st.session_state.user_data = users[st.session_state.current_user]
                    st.success("Settings updated!")
                    st.rerun()
            else:
                st.warning("Please enter current password to make changes")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # App Info
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### ℹ️ About")
    st.markdown("""
    **VoiceCraft Pro** v1.0
    
    Features:
    - 🔐 Secure user authentication
    - 🎙️ High-quality text-to-speech
    - 📁 File upload support
    - 📜 Conversion history
    - 🌍 Multiple languages
    
    Made with ❤️ using Streamlit & gTTS
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# Main execution
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
