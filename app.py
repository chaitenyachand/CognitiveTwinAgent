# app.py
import streamlit as st
import base64

import os
import sys # <-- IMPORTED SYS
import json
from datetime import datetime
import time
# --- Robust Import Logic ---
# Add the project's root directory (where app.py is) to the Python path
# This ensures that all module imports (utils, auth, etc.) work reliably
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Import project modules
import database_utils as db # Or import db
import auth
import generative_ai
import agentic_ai
import quiz_module
import dashboard
import utils
from config import OPENAI_API_KEY # Ensure config is imported

# --- Page Configuration ---
st.set_page_config(page_title="Cognitive Twin Agent", page_icon="🧠", layout="wide")

# --- Initialize Session State ---
def init_session_state():
    defaults = {
        "logged_in": False,
        "user_id": None,
        "username": None,
        "page": "login",
        "current_topic_text": None,
        "current_topic_id": None,
        "current_summary": None,
        "current_mindmap": None,
        "current_flashcards": None,
        "current_formula_sheet": None, 
        "current_quiz": None,
        "user_answers": [],
        "latest_score": 0,
        "latest_weak_areas": [],
        "agent_recommendation": None,
        "focused_review": None,
        "view_topic": None,
        "view_content_type": None,
        "current_topic_name_to_review": None,
        "topic_chat_history": [],
        "topic_name": None, # <-- ADD THIS LINE
        "source_type": None,
        "default_tab": 0
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- AESTHETIC STYLING (CSS) ---
def set_custom_theme():
    """Injects unified design system matching the login page aesthetic."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global Styles */
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main App Background - Light cream/beige */
    [data-testid="stAppViewContainer"] {
        background-color: #f5f1ed;
    }

    /* Sidebar - Dark slate/charcoal */
    [data-testid="stSidebar"] {
        background-color: #2d3748;
        padding: 20px 10px;
    }
    
    [data-testid="stSidebar"] h1 {
        color: #FFFFFF;
        font-size: 1.4rem;
        font-weight: 700;
        padding: 10px;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background-color: #3d4d60;
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 12px 20px;
        font-weight: 500;
        width: 100%;
        margin-bottom: 8px;
        transition: all 0.3s ease;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #4a5a70;
        transform: translateX(5px);
    }
    
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #5b6fd8;
    }
    
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background-color: #4a5bc4;
    }

    /* Main Content Area */
    .main .block-container {
        padding-top: 3rem;
        max-width: 1400px;
    }

    /* Header Styling */
    h1 {
        color: #1a202c;
        font-weight: 800;
        font-size: 2.5rem;
    }
    
    h2 {
        color: #2d3748;
        font-weight: 700;
        font-size: 1.8rem;
    }
    
    h3 {
        color: #4a5568;
        font-weight: 600;
    }

    /* Cards - White with subtle shadow */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0 !important;
        padding: 25px;
    }

    /* Tabs - Matching the Topics design */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background-color: transparent;
        border-bottom: 2px solid #e2e8f0;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 12px 24px;
        background-color: transparent;
        border: none;
        color: #718096;
        font-weight: 500;
        font-size: 1rem;
        border-bottom: 3px solid transparent;
    }

    .stTabs [aria-selected="true"] {
        background-color: transparent !important;
        color: #1a202c !important;
        border-bottom: 3px solid #5b6fd8 !important;
        font-weight: 600;
    }

    /* Buttons - Primary style */
    div.stButton > button:first-child {
        background-color: #5b6fd8;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        font-size: 0.95rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:first-child:hover {
        background-color: #4a5bc4;
        box-shadow: 0 4px 12px rgba(91, 111, 216, 0.4);
    }

    /* Secondary Button */
    div.stButton > button[kind="secondary"] {
        background-color: #4a5a70;
        color: white;
        border: none;
    }
    
    div.stButton > button[kind="secondary"]:hover {
        background-color: #3d4d60;
    }

    /* Input Fields */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        background-color: #f7fafc !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 10px !important;
        color: #2d3748 !important;
        font-weight: 500;
    }
    
    .stTextInput input:focus, .stSelectbox select:focus, .stTextArea textarea:focus {
        border-color: #5b6fd8 !important;
        box-shadow: 0 0 0 3px rgba(91, 111, 216, 0.1) !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #1a202c;
    }

    /* Progress bars */
    [data-testid="stProgressBar"] > div > div {
        background-color: #5b6fd8 !important;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background-color: #f7fafc;
        border: 2px dashed #cbd5e0;
        border-radius: 12px;
        padding: 20px;
    }

    /* Success/Error/Warning messages */
    .stSuccess {
        background-color: #c6f6d5;
        color: #22543d;
        border-left: 4px solid #38a169;
    }
    
    .stError {
        background-color: #fed7d7;
        color: #742a2a;
        border-left: 4px solid #e53e3e;
    }
    
    .stWarning {
        background-color: #feebc8;
        color: #7c2d12;
        border-left: 4px solid #ed8936;
    }
    
    .stInfo {
        background-color: #bee3f8;
        color: #2c5282;
        border-left: 4px solid #3182ce;
    }

    /* Contribution Heatmap Styles */
    .contribution-container {
        background: white;
        border-radius: 16px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    .contribution-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 20px;
    }
    
    .heatmap-grid {
        display: grid;
        grid-template-columns: repeat(53, 12px);
        gap: 3px;
        margin: 20px 0;
    }
    
    .heatmap-cell {
        width: 12px;
        height: 12px;
        border-radius: 2px;
        background-color: #e2e8f0;
    }
    
    .heatmap-cell.level-1 { background-color: #c3dafe; }
    .heatmap-cell.level-2 { background-color: #7f9cf5; }
    .heatmap-cell.level-3 { background-color: #5b6fd8; }
    .heatmap-cell.level-4 { background-color: #4a5bc4; }

    /* Streak Badge */
    .streak-badge {
        position: fixed;
        top: 80px;
        right: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 25px;
        border-radius: 50px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        font-weight: 700;
        font-size: 1.1rem;
        z-index: 1000;
        animation: pulse 2s infinite;
    }
    
    .streak-badge .streak-icon {
        font-size: 1.5rem;
        margin-right: 8px;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }

    /* Topic Cards (for Topics tab) */
    .topic-card {
        background: white;
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }
    
    .topic-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        transform: translateY(-2px);
    }
    
    .topic-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 10px;
    }
    
    .topic-date {
        color: #718096;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }
    
    .progress-section {
        margin: 20px 0;
    }
    
    .progress-label {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-weight: 600;
        color: #2d3748;
    }
    
    .progress-bar-custom {
        height: 12px;
        background-color: #e2e8f0;
        border-radius: 6px;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #5b6fd8 0%, #7f9cf5 100%);
        border-radius: 6px;
        transition: width 0.5s ease;
    }

    /* Material Buttons Row */
    .material-buttons {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 12px;
        margin-top: 20px;
    }
    
    .material-button {
        background-color: #4a5a70;
        color: white;
        padding: 12px 20px;
        border-radius: 10px;
        text-align: center;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .material-button:hover {
        background-color: #3d4d60;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Login Page UI ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_bg_from_local(image_file):
    if not os.path.exists(image_file):
        st.warning(f"⚠️ Background image '{image_file}' not found.")
        return
    bin_str = get_base64_of_bin_file(image_file)
    page_bg_img = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Roboto:wght@400;500&display=swap');
    
    /* Apply background image */
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    
    /* Ensure header is transparent */
    [data-testid="stHeader"] {{background: rgba(0,0,0,0);}}
    
    /* Original left block styling */
    .left-block {{
        background: rgba(0, 0, 0, 0.45);
        padding: 2rem;
        border-radius: 12px;
        display: inline-block;
    }}
    .left-block h1 {{
        color: #ffffff;
        font-family: 'Playfair Display', serif;
        font-size: 3.2rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }}
    .left-block p {{
        color: #ffffff;
        font-family: 'Roboto', sans-serif;
        font-size: 1.5rem;
        line-height: 1.5;
        text-align: left;
    }}
    
    /* Original login title styling */
    .login-title {{
        font-family: 'Playfair Display', serif;
        font-size: 3.8rem;
        color: #1a1a1a;
        text-align: center;
        margin-bottom: 2rem;
    }}
    
    /* Original login button styling */
    div.stButton > button:first-child {{
        background-color: #144b3d;
        color: white;
        width: 100%;
        border-radius: 10px;
        height: 3rem;
        font-size: 1.1rem;
        font-weight: 600;
        border: none;
    }}
    div.stButton > button:hover {{
        background-color: #1e6b56;
        color: white;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

def show_login_page():
    # --- 1. Background Setup ---
    if os.path.exists("background.png"):
        bin_str = get_base64_of_bin_file("background.png")
        bg_img = f'url("data:image/png;base64,{bin_str}")'
    else:
        bg_img = 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'

    # --- 2. Aggressive CSS Styling ---
    st.markdown(f"""
    <style>
    /* Main Background */
    [data-testid="stAppViewContainer"] {{
        background-image: {bg_img};
        background-size: cover;
        background-attachment: fixed;
    }}
    [data-testid="stHeader"] {{ background: transparent; }}

    /* FORCE LOGIN CARD SOLID WHITE - Aggressive Selectors */
    /* Target the container with border=True specifically in the 2nd column */
    [data-testid="column"]:nth-of-type(2) [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="column"]:nth-of-type(2) [data-testid="stVerticalBlock"] > div {{
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        opacity: 1 !important;
        border-radius: 20px !important;
    }}
    
    /* Ensure text inside is visible */
    [data-testid="column"]:nth-of-type(2) h1,
    [data-testid="column"]:nth-of-type(2) h2,
    [data-testid="column"]:nth-of-type(2) h3,
    [data-testid="column"]:nth-of-type(2) p {{
        color: #31333F !important; /* Dark grey for high contrast */
    }}

    /* Left side styling (kept for aesthetics) */
    .benefit-box {{
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        border-left: 5px solid #5A67D8;
    }}

    /* Button styling */
    .stButton > button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px 28px !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
        margin-top: 10px !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
    }}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        justify-content: center;
        margin-bottom: 30px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px;
        padding: 12px 30px;
        font-weight: 600;
        background-color: #f5f5f5;
        color: #666;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }}
    
    /* Footer */
    .login-footer {{
        text-align: center;
        color: white;
        margin-top: 30px;
        font-size: 0.85rem;
    }}
    
    /* Responsive */
    @media (max-width: 1024px) {{
        .main-container {{
            flex-direction: column;
        }}
        .benefits-section {{
            max-width: 100%;
        }}
        .login-section {{
            flex: 0 0 auto;
            width: 100%;
            max-width: 480px;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- 3. Page Layout ---
    col1, col2 = st.columns([1.3, 1.3], gap="large")

    with col1:
        st.markdown("""
            <h1 style='font-size: 3.5rem; color: #2D3748;'>Cognitive Twin Agent</h1>
            <h3 style='color: #4A5568; margin-bottom: 40px;'>Your AI-Powered Learning Companion</h3>
            <div class="benefit-box"><b>Personalized Learning Paths</b><br>AI adapts to your pace.</div>
            <div class="benefit-box"><b>Interactive Mind Maps</b><br>Visualize complex topics instantly.</div>
            <div class="benefit-box"><b>Smart Flashcards</b><br>Reinforce memory with active recall.</div>
        """, unsafe_allow_html=True)

    with col2:
        with st.container(border=True):
            st.markdown("""
                <div style='
                    background: rgba(255, 255, 255, 0.85);
                    border-radius: 12px;
                    padding: 20px 0;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                    text-align: center;
                    margin-bottom: 15px;
                '>
                    <h2 style='
                        color: #1A1A1A;
                        font-weight: 800;
                        font-size: 2.2rem;
                        letter-spacing: 0.5px;
                        margin-bottom: 8px;
                    '>
                        Welcome Back 
                    </h2>
                    <p style='
                        color: #444;
                        font-size: 1.05rem;
                        font-weight: 500;
                        margin: 0;
                    '>
                        Sign in to continue your journey
                    </p>
                </div>
        """, unsafe_allow_html=True)
            tab1, tab2 = st.tabs(["Sign In", "Register"])
            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submitted = st.form_submit_button("Sign In")
                    
                    if submitted:
                        success, user = auth.login_user(username, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user['user_id']
                            st.session_state.username = user['username']
                            st.session_state.page = "dashboard"
                            st.success("Login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
            with tab2:
                with st.form("register_form"):
                    new_username = st.text_input("Username", placeholder="Choose a unique username")
                    new_email = st.text_input("Email", placeholder="your.email@example.com")
                    new_password = st.text_input("Password", type="password", placeholder="Create a strong password")
                    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
                    reg_submitted = st.form_submit_button("Create Account")
                    
                    if reg_submitted:
                        if new_password != confirm_password:
                            st.error("Passwords do not match.")
                        elif not all([new_username, new_email, new_password]):
                            st.error("Please fill all fields.")
                        else:
                            success, message = auth.register_user(new_username, new_email, new_password)
                            if success:
                                st.success(f"{message} Please log in.")
                            else:
                                st.error(message)
            
# --- Onboarding Flow (New Topic) ---
def show_onboarding_flow():
    """Renders the 6-step new topic flow."""
    st.title("Start a New Learning Journey")
    
    with st.container(border=True):
        st.subheader("Step 1: Choose Your Topic")
        
        if "topic_submitted" not in st.session_state:
            st.session_state.current_topic_text = None
        
        # --- MODIFIED: Radio button label and logic ---
        input_type = st.radio("How do you want to provide the topic?", 
                              ("Type a topic name", "Upload a PDF", "Upload Handwritten Notes (PDF)", "Choose from a list"),
                              horizontal=True)
        
        topic_name = ""
        source_type = "text"
        content = None
        uploaded_file = None

        if input_type == "Type a topic name":
            topic_name = st.text_input("What do you want to learn about?")
            if topic_name:
                content = f"Provide a detailed overview of the topic: {topic_name}"
                source_type = "text"
                
        elif input_type == "Upload a PDF":
            uploaded_file = st.file_uploader("Upload your PDF document", type="pdf")
            if uploaded_file:
                topic_name = uploaded_file.name
                source_type = "pdf"
            
        elif input_type == "Upload Handwritten Notes (PDF)":
            # --- MODIFIED: Now only accepts PDF ---
            uploaded_file = st.file_uploader("Upload a PDF of your notes", type="pdf")
            if uploaded_file:
                topic_name = f"Notes: {uploaded_file.name}"
                source_type = "ocr" # We still call it 'ocr' to trigger the right parser

        elif input_type == "Choose from a list":
            topic_name = st.selectbox("Select a popular topic:", 
                                      ["", "Artificial Intelligence", "Data Science", "Computer Networking", "Blockchain"])
            if topic_name:
                content = f"Provide a detailed overview of the topic: {topic_name}"
                source_type = "predefined"

        # --- MODIFIED: Centralized Processing ---
        if st.button("Generate Learning Module", type="primary"):
            if uploaded_file:
                with st.spinner("Analyzing document..."):
                    # This function handles PDF and OCR-PDF
                    content = utils.process_uploaded_file(uploaded_file, source_type)
            
            if content:
                st.session_state.current_topic_text = content
                st.session_state.topic_name = topic_name
                st.session_state.source_type = source_type
                st.session_state.page = "onboarding_processing"
                st.rerun()
            else:
                st.error("Could not extract content. Please try a different file or topic.")

# --- REBUILT LEARNING PAGE (AESTHETIC) ---
def process_new_topic():
    """Generates and displays all learning materials in a tabbed view."""
    st.title(f"Learning: {st.session_state.topic_name}")
    
    # --- CHECK IF WE'RE RETAKING A QUIZ (materials already exist) ---
    is_retake = (
        st.session_state.get('current_summary') and 
        st.session_state.get('current_mindmap') and 
        st.session_state.get('current_flashcards')
    )
    
    # --- Generate all content ONLY if not retaking ---
    if not is_retake:
        if not st.session_state.current_summary:
            with st.spinner("Generating detailed summary..."):
                st.session_state.current_summary = generative_ai.generate_summary(st.session_state.current_topic_text)
                st.session_state.current_topic_id = db.create_topic(
                    st.session_state.user_id,
                    st.session_state.topic_name,
                    st.session_state.source_type,
                    st.session_state.current_summary
                )
                st.session_state.current_topic_text = st.session_state.current_summary
        
        if not st.session_state.current_mindmap:
            with st.spinner("Generating mind map..."):
                st.session_state.current_mindmap = generative_ai.generate_mindmap_markdown(st.session_state.current_topic_text)
                if st.session_state.current_mindmap:
                    db.save_mindmap(st.session_state.current_topic_id, st.session_state.current_mindmap)

        if not st.session_state.current_flashcards:
            with st.spinner("Generating flashcards..."):
                st.session_state.current_flashcards = generative_ai.generate_flashcards(st.session_state.current_topic_text)
                if st.session_state.current_flashcards:
                    db.save_flashcards(st.session_state.current_topic_id, st.session_state.current_flashcards)
        
        if not st.session_state.current_formula_sheet:
            with st.spinner("Generating formula sheet..."):
                st.session_state.current_formula_sheet = generative_ai.generate_formula_sheet(st.session_state.current_topic_text)
                if st.session_state.current_formula_sheet:
                    db.save_formula_sheet(st.session_state.current_topic_id, st.session_state.current_formula_sheet)

    with st.container(border=True):
        # Create tabs - using a workaround to set default tab
        # Streamlit doesn't support setting active tab directly, so we'll use a different approach
        
        # Show a message if retaking
        if is_retake and st.session_state.get("default_tab") == 5:
            st.info("Scroll down to the Quiz tab below to start your quiz!")
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Summary", 
            "Mind Map", 
            "Flashcards", 
            "Formula Sheet", 
            "Q&A", 
            "📝 Quiz" if st.session_state.get("default_tab") == 5 else "Quiz"
        ])

        with tab1:
            st.subheader("Topic Summary")
            st.markdown(st.session_state.current_summary)

        with tab2:
            st.subheader("Interactive Mind Map")
            if st.session_state.current_mindmap:
                utils.render_markmap_html(st.session_state.current_mindmap)
            else:
                st.error("Could not generate mind map for this topic.")

        with tab3:
            st.subheader("Flashcards (Hover to flip)")
            if st.session_state.current_flashcards:
                utils.render_flashcards(st.session_state.current_flashcards)
            else:
                st.error("Could not generate flashcards for this topic.")
        
        with tab4:
            st.subheader("Key Formulas & Concepts")
            if st.session_state.current_formula_sheet:
                st.markdown(st.session_state.current_formula_sheet)
            else:
                st.info("No distinct formulas or key equations were found for this topic.")

        with tab5:
            st.subheader("Ask a Question")
            st.info("Your questions will be answered based on the topic summary.")
            
            qa_style = st.radio("Response Style:", ("Simple", "Normal", "Detailed"), index=1, horizontal=True)

            for msg in st.session_state.topic_chat_history:
                st.chat_message(msg["role"]).write(msg["content"])

            prompt = st.chat_input("Ask a question about this topic...")
            
            if prompt:
                st.session_state.topic_chat_history.append({"role": "user", "content": prompt})
                st.chat_message("user").write(prompt)
                
                with st.spinner("Finding an answer..."):
                    response = generative_ai.answer_question(st.session_state.current_summary, prompt, style=qa_style.lower())
                    
                st.session_state.topic_chat_history.append({"role": "assistant", "content": response})
                st.chat_message("assistant").write(response)
                st.rerun()

        with tab6:
            st.subheader("Test Your Knowledge")
            
            # Generate quiz ONLY if it doesn't exist
            if "current_quiz" not in st.session_state or not st.session_state.current_quiz:
                with st.spinner("Generating quiz..."):
                    quiz_module.setup_quiz(st.session_state.current_summary, st.session_state.current_topic_id)
            
            submitted = quiz_module.display_quiz()
            
            if submitted:
                st.session_state.page = "quiz_results"
                st.rerun()
        
        # Reset default tab after rendering
        if st.session_state.get("default_tab") == 5:
            st.session_state.default_tab = 0

# --- Page for Quiz Results ---
def show_quiz_results_page():
    title = db.get_topic_name_by_id(st.session_state.current_topic_id) or "Results"
    st.title(f"Results for {title}")
    
    with st.container(border=True):
        quiz_module.grade_and_store_quiz()
        st.divider()
        
        if not st.session_state.agent_recommendation:
            st.session_state.agent_recommendation = "processing"
            agent_output = agentic_ai.run_agent_analysis(
                st.session_state.username,
                st.session_state.latest_score,
                st.session_state.latest_weak_areas,
                st.session_state.current_summary
            )
            st.write(f"**Cognitive Twin Analysis:** {agent_output}")
        
        # Ensure recommendation is loaded and is a dictionary
        rec = st.session_state.agent_recommendation
        if not isinstance(rec, dict) or 'type' not in rec:
             st.error("There was an issue loading your recommendation. Please go back to the dashboard.")
             if st.button("Back to Dashboard", key="error_back_btn"):
                 st.session_state.page = "dashboard"
                 st.rerun()
             return

        if rec['type'] == 'review':
            st.warning(f"**Next Step:** Let's review the topics you struggled with: **{rec['topics']}**.")
            
            review_data = st.session_state.focused_review
            
            # FIXED: Using markdown headers instead of expanders to avoid the key overlap
            st.markdown("---")
            st.markdown("### Focused Review Summary")
            if 'summary' in review_data:
                st.markdown(review_data['summary'])
            else:
                st.error("Could not load summary.")
            
            st.markdown("---")
            st.markdown("### Focused Review Mind Map")
            if 'mindmap' in review_data:
                utils.render_markmap_html(review_data['mindmap'])
            else:
                st.error("Could not load mind map.")

            st.markdown("---")
            st.markdown("### Focused Review Flashcards")
            if 'flashcards' in review_data:
                utils.render_flashcards(review_data['flashcards'])
            else:
                st.error("Could not load flashcards.")
                
            st.info("Study this new material, then retake the quiz.")
            
            if st.button("Retake Focused Quiz", type="primary"):
                # Update materials with focused review content
                st.session_state.current_summary = review_data['summary']
                st.session_state.current_topic_text = review_data['summary']
                st.session_state.current_mindmap = review_data['mindmap']
                st.session_state.current_flashcards = review_data['flashcards']
                
                # Clear ONLY quiz-related data
                if "current_quiz" in st.session_state:
                    del st.session_state['current_quiz']
                if "user_answers" in st.session_state:
                    del st.session_state['user_answers']
                
                # Clear recommendation to get fresh analysis after retake
                st.session_state.agent_recommendation = None
                
                # Set default tab to Quiz (index 5)
                st.session_state.default_tab = 5
                
                # Generate new quiz immediately
                num_q_retake = st.session_state.get("quiz_num_q", 5)
                with st.spinner("Generating new focused quiz..."):
                    quiz_module.setup_quiz(
                        st.session_state.current_summary, 
                        st.session_state.current_topic_id, 
                        num_q_retake
                    )

                # Navigate to the learning page
                st.session_state.page = "onboarding_processing"
                st.rerun()

    def clear_topic_state():
        keys_to_clear = [
            "current_topic_text", "current_topic_id", "current_summary", 
            "current_mindmap", "current_flashcards", "current_formula_sheet", "current_quiz", 
            "user_answers", "latest_score", "latest_weak_areas", 
            "agent_recommendation", "focused_review", "topic_name", "source_type",
            "current_topic_name_to_review", "topic_chat_history",
            "quiz_num_q"
        ]
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
    
    if st.button("Back to Dashboard", key="stButton-secondary"):
        clear_topic_state()
        st.session_state.page = "dashboard"
        st.rerun()

# --- General Q&A Page ---
def show_general_qa_page():
    st.title("General Q&A")
    st.info("Ask any question, not related to a specific topic.")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    with st.container(border=True, height=500):
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])
    
    prompt = st.chat_input("What's on your mind?")
    
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        with st.spinner("Thinking..."):
            response = generative_ai.answer_question(None, prompt, style="normal") # No style needed
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.chat_message("assistant").write(response)
        st.rerun()

def show_agora_voice_twin():
    st.title("Voice Tutor")
    st.markdown(
        "Your Cognitive Twin is now **voice-first**. Speak naturally — the AI will listen, respond, and guide you Socratically in real time."
    )

    # --- Initialize Session State ---
    if "voice_session" not in st.session_state:
        st.session_state.voice_session = {
            "topic": None,
            "session_id": None,
            "persona": "empathetic"
        }

    # --- Step 1: Topic Setup ---
    if not st.session_state.voice_session["topic"]:
        st.info("Let's get started! What subject would you like to learn today?")
        topic_input = st.text_input("Enter your topic:", key="voice_topic_input")

        if st.button("Start Voice Session", type="primary"):
            if not topic_input:
                st.warning("Please enter a topic first.")
            else:
                st.session_state.voice_session["topic"] = topic_input
                user_id = st.session_state.get("user_id")
                session_id = db.create_voice_session(user_id, topic_input)
                st.session_state.voice_session["session_id"] = session_id
                st.success(f"Starting your live session on **{topic_input}**")
                st.rerun()
    else:
        # --- Step 2: Agora Live Interface ---
        topic = st.session_state.voice_session["topic"]
        st.markdown(f"### Topic: **{topic}**")
        st.caption("You are now connected to your live Cognitive Twin Tutor")

        try:
            # Read Agora frontend
            with open("agora_rtc.html", "r", encoding="utf-8") as f:
                html_code = f.read()

            # Embed HTML
            st.components.v1.html(html_code, height=700, scrolling=False)
        except FileNotFoundError:
            st.error("'agora_rtc.html' not found. Please ensure it exists in the project directory.")

        st.divider()
        st.markdown("##### Voice Tutor Controls")

        persona_choice = st.radio(
            "Select AI Tone:",
            ["empathetic", "encouraging", "authoritative", "neutral"],
            index=0,
            horizontal=True,
            key="persona_select"
        )
        st.session_state.voice_session["persona"] = persona_choice

        if st.button("End Voice Session", type="secondary"):
            session_id = st.session_state.voice_session.get("session_id")
            if session_id:
                summary = {
                    "ended": str(datetime.now()),
                    "persona": st.session_state.voice_session["persona"]
                }
                db.end_voice_session(session_id, summary)
            st.success("🎤 Voice session ended and saved.")
            st.session_state.voice_session = None
            st.session_state.page = "dashboard"
            st.rerun()


# --- Focused Review Page ---
def show_review_page():
    st.title(f"Focused Review: {st.session_state.current_topic_name_to_review}")
    
    if "focused_review" not in st.session_state or st.session_state.focused_review is None:
        st.session_state.focused_review = agentic_ai.generate_focused_review_materials(
            st.session_state.current_summary,
            [st.session_state.current_topic_name_to_review]
        )

    review_data = st.session_state.focused_review
    
    with st.container(border=True):
        tab1, tab2, tab3 = st.tabs(["Summary", "Mind Map", "Flashcards"])
        with tab1:
            st.subheader("Focused Review Summary")
            st.markdown(review_data['summary'])
        with tab2:
            st.subheader("Focused Review Mind Map")
            utils.render_markmap_html(review_data['mindmap'])
        with tab3:
            st.subheader("Focused Review Flashcards")
            utils.render_flashcards(review_data['flashcards'])
            
    st.divider()
    
    if st.button("Take Quiz Now", type="primary"):
        st.session_state.current_summary = review_data['summary']
        st.session_state.current_topic_text = review_data['summary']
        if "current_quiz" in st.session_state: del st.session_state['current_quiz']
        if "user_answers" in st.session_state: del st.session_state['user_answers']
        st.session_state.focused_review = None
        st.session_state.agent_recommendation = None
        st.session_state.page = "onboarding_processing" # Go back to the learning module
        st.rerun()

    if st.button("Back to Dashboard", key="stButton-secondary"):
        st.session_state.focused_review = None
        st.session_state.page = "dashboard"
        st.rerun()

# --- Main Application Logic ---
def main():
    if "db_initialized" not in st.session_state:
        db.create_tables()
        st.session_state.db_initialized = True
        
    init_session_state()

    if not st.session_state.logged_in:
        show_login_page() # Only show login page if not logged in
    else:
        # --- KEY CHANGE: INJECT THEME ONLY *AFTER* LOGIN ---
        set_custom_theme()

        # --- Logged-in App ---
        with st.sidebar:
            st.title(f"Welcome, {st.session_state.username}!")
            
            def on_page_change():
                st.session_state.view_topic = None
                st.session_state.view_content_type = None

            if st.button("Dashboard", on_click=on_page_change, use_container_width=True, key="dash_btn"):
                st.session_state.page = "dashboard"
                st.rerun()
            
            if st.button("Start New Topic", on_click=on_page_change, use_container_width=True, type="primary", key="new_topic_btn"):
                 st.session_state.page = "onboarding_start"
                 st.rerun()

            if st.button("Ask a General Question", on_click=on_page_change, use_container_width=True, key="qa_btn"):
                st.session_state.page = "general_qa"
                st.rerun()
            if st.button("Voice Tutor (Agora AI)", use_container_width=True, key="voice_btn"):
                st.session_state.page = "voice_twin"
                st.rerun()
            st.divider()
            
            logout_clicked = st.button("Logout", use_container_width=True, key="logout_btn")
            if logout_clicked:
                 for key in list(st.session_state.keys()):
                    del st.session_state[key]
                 st.rerun()

        # --- Main Content Area Router ---
        if st.session_state.page == "dashboard":
            dashboard.show_dashboard()
        elif st.session_state.page == "review_topic":
            show_review_page()
        elif st.session_state.page == "voice_twin":
            show_agora_voice_twin()
        elif st.session_state.page == "general_qa":
            show_general_qa_page()
        elif st.session_state.page == "onboarding_start":
            show_onboarding_flow()
        elif st.session_state.page == "onboarding_processing":
            process_new_topic()
        elif st.session_state.page == "quiz_results":
            show_quiz_results_page()

if __name__ == "__main__":
    main()


