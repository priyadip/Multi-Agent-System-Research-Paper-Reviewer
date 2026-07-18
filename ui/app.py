"""
Streamlit UI for the Multi-Agent Paper Reviewer.
Advanced version with real-time progress tracking, animations, and enhanced features.
"""

import streamlit as st
import sys
import os
import json
import time
from datetime import datetime
import re

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import PaperReviewOrchestrator

# Helper function to convert markdown to HTML
def markdown_to_html(text):
    """Convert markdown syntax to HTML"""
    if not text:
        return text
    
    # Convert **bold** to <strong>bold</strong>
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    # Convert *italic* to <em>italic</em>
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    # Convert `code` to <code>code</code>
    text = re.sub(r'`([^`]+)`', r'<code style="background-color: rgba(255,255,255,0.1); padding: 2px 4px; border-radius: 3px;">\1</code>', text)
    # Convert newlines to <br>
    text = text.replace('\n', '<br>')
    
    return text

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Paper Reviewer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'progress_data' not in st.session_state:
    st.session_state.progress_data = {}
if 'scroll_to_results' not in st.session_state:
    st.session_state.scroll_to_results = False

# Dark mode colors
colors = {
    'bg_primary': '#0f0f23',
    'bg_secondary': '#1a1a2e',
    'bg_card': 'rgba(255, 255, 255, 0.08)',
    'text_primary': '#ffffff',
    'text_secondary': '#cbd5e1',
    'text_tertiary': '#9ca3af',
    'accent': '#667eea',
    'accent_secondary': '#764ba2',
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'border': 'rgba(255, 255, 255, 0.12)',
    'shadow': 'rgba(0, 0, 0, 0.3)',
    'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'gradient_card': 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)'
}

# Dark mode theme settings
bg_gradient = "linear-gradient(-45deg, #1a1a3e, #0f0f23, #16213e, #0f0f23)"
card_bg = "rgba(26, 26, 46, 0.7)"
text_shadow = "0 2px 10px rgba(102, 126, 234, 0.2)"

# All code uses dark mode exclusively

# Custom CSS for dark mode with animated video-like background
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {{
        font-family: 'Inter', sans-serif;
    }}
    
    /* Video-like background animation keyframes */
    @keyframes video-flow {{
        0% {{ background-position: 0% 0%, 0% 0%; }}
        25% {{ background-position: 100% 0%, 50% 50%; }}
        50% {{ background-position: 0% 100%, 0% 100%; }}
        75% {{ background-position: 100% 100%, 100% 0%; }}
        100% {{ background-position: 0% 0%, 0% 0%; }}
    }}
    
    /* Network mesh animation */
    @keyframes mesh-shift {{
        0% {{ background-position: 0% 0%; }}
        50% {{ background-position: 100% 100%; }}
        100% {{ background-position: 0% 0%; }}
    }}
    
    /* Node pulse animation */
    @keyframes node-pulse {{
        0%, 100% {{ opacity: 0.3; }}
        50% {{ opacity: 0.8; }}
    }}
    
    /* Connection line animation */
    @keyframes line-flow {{
        0% {{ background-position: 0% 0%; }}
        100% {{ background-position: 100% 100%; }}
    }}
    
    /* Particle animation */
    @keyframes particle-float {{
        0%, 100% {{ transform: translateY(0px) translateX(0px); opacity: 0.3; }}
        25% {{ transform: translateY(-20px) translateX(10px); opacity: 0.6; }}
        50% {{ transform: translateY(-40px) translateX(-10px); opacity: 0.4; }}
        75% {{ transform: translateY(-20px) translateX(20px); opacity: 0.5; }}
    }}
    
    /* Animated background keyframes */
    @keyframes gradient-shift {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}

    /* Floating orbs animation */
    @keyframes float-orb {{
        0%, 100% {{ transform: translate(0, 0) scale(1); opacity: 0.3; }}
        25% {{ transform: translate(30px, -30px) scale(1.1); opacity: 0.5; }}
        50% {{ transform: translate(-20px, 30px) scale(0.9); opacity: 0.3; }}
        75% {{ transform: translate(40px, 20px) scale(1.05); opacity: 0.4; }}
    }}
    
    /* Animated connecting lines flowing */
    @keyframes line-flow-1 {{
        0% {{ background-position: 0% 0%; }}
        100% {{ background-position: 100% 100%; }}
    }}
    
    @keyframes line-flow-2 {{
        0% {{ background-position: 0% 100%; }}
        100% {{ background-position: 100% 0%; }}
    }}
    
    @keyframes pulse-rope {{
        0%, 100% {{ opacity: 0.3; }}
        50% {{ opacity: 0.3; }}
    }}
    
    @keyframes pulse-nodes {{
        0%, 100% {{ opacity: 0.8; }}
        50% {{ opacity: 1; }}
    }}
    
    /* Main container - Black Background with Subtle Neural Network */
    .main {{
        background-color: #000000;
        background-image: 
            /* Subtle glowing orbs */
            radial-gradient(circle at 5% 10%, rgba(255, 0, 0, 0.08) 0%, transparent 30%),
            radial-gradient(circle at 95% 15%, rgba(255, 0, 0, 0.08) 0%, transparent 30%),
            radial-gradient(circle at 15% 50%, rgba(100, 150, 200, 0.05) 0%, transparent 35%),
            radial-gradient(circle at 85% 70%, rgba(100, 150, 200, 0.05) 0%, transparent 35%),
            radial-gradient(circle at 50% 50%, rgba(100, 150, 200, 0.03) 0%, transparent 40%),
            /* Sparse, subtle nodes */
            radial-gradient(circle 0.8px at 5% 10%, rgba(200, 200, 200, 0.6), transparent 0.8px),
            radial-gradient(circle 0.8px at 15% 8%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 25% 12%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 95% 15%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 85% 10%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 75% 18%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 10% 25%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 30% 22%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 50% 15%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 70% 20%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 90% 25%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 8% 40%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 20% 38%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 40% 42%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 60% 40%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 80% 45%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 12% 60%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 35% 55%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 55% 58%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 75% 60%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 25% 78%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 45% 82%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 65% 78%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 20% 90%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 50% 95%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 80% 90%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            /* Subtle flowing rope connections */
            radial-gradient(ellipse 350px 180px at 20% 30%, rgba(150, 150, 200, 0.08) 0%, transparent 70%),
            radial-gradient(ellipse 400px 200px at 50% 20%, rgba(150, 150, 200, 0.08) 0%, transparent 70%),
            radial-gradient(ellipse 320px 160px at 70% 40%, rgba(150, 150, 200, 0.06) 0%, transparent 70%),
            radial-gradient(ellipse 380px 190px at 30% 60%, rgba(150, 150, 200, 0.08) 0%, transparent 70%),
            radial-gradient(ellipse 350px 180px at 60% 70%, rgba(150, 150, 200, 0.06) 0%, transparent 70%),
            radial-gradient(ellipse 400px 200px at 40% 50%, rgba(150, 150, 200, 0.08) 0%, transparent 70%),
            radial-gradient(ellipse 320px 160px at 75% 65%, rgba(150, 150, 200, 0.06) 0%, transparent 70%),
            radial-gradient(ellipse 380px 190px at 25% 80%, rgba(150, 150, 200, 0.08) 0%, transparent 70%);
        background-size: 
            100% 100%, 100% 100%, 100% 100%, 100% 100%, 100% 100%,
            150px 150px, 160px 160px, 170px 170px, 180px 180px, 190px 190px, 200px 200px, 210px 210px, 220px 220px,
            230px 230px, 240px 240px, 250px 250px, 260px 260px, 270px 270px, 280px 280px, 290px 290px, 300px 300px,
            310px 310px, 320px 320px, 330px 330px, 340px 340px, 350px 350px, 360px 360px, 370px 370px, 380px 380px,
            800px 800px, 900px 900px, 850px 850px, 950px 950px, 800px 800px, 900px 900px, 850px 850px, 950px 950px;
        background-position: 
            0% 0%, 0% 0%, 0% 0%, 0% 0%, 0% 0%,
            0% 0%, 10px 10px, 20px 20px, 30px 30px, 40px 40px, 50px 50px, 60px 60px, 70px 70px,
            80px 80px, 90px 90px, 100px 100px, 110px 110px, 120px 120px, 130px 130px, 140px 140px, 150px 150px,
            160px 160px, 170px 170px, 180px 180px, 190px 190px, 200px 200px, 210px 210px, 220px 220px, 230px 230px,
            0% 0%, 30px 30px, 60px 60px, 90px 90px, 120px 120px, 150px 150px, 180px 180px, 210px 210px;
        animation: line-flow-1 40s ease-in-out infinite, line-flow-2 45s ease-in-out infinite;
        color: {colors['text_primary']};
        position: relative;
        overflow: hidden;
    }}
    
    .stApp {{
        background-color: #000000;
        background-image: 
            /* Subtle glowing orbs */
            radial-gradient(circle at 5% 10%, rgba(255, 0, 0, 0.08) 0%, transparent 30%),
            radial-gradient(circle at 95% 15%, rgba(255, 0, 0, 0.08) 0%, transparent 30%),
            radial-gradient(circle at 15% 50%, rgba(100, 150, 200, 0.05) 0%, transparent 35%),
            radial-gradient(circle at 85% 70%, rgba(100, 150, 200, 0.05) 0%, transparent 35%),
            radial-gradient(circle at 50% 50%, rgba(100, 150, 200, 0.03) 0%, transparent 40%),
            /* Sparse, subtle nodes */
            radial-gradient(circle 0.8px at 5% 10%, rgba(200, 200, 200, 0.6), transparent 0.8px),
            radial-gradient(circle 0.8px at 15% 8%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 25% 12%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 95% 15%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 85% 10%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 75% 18%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 10% 25%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 30% 22%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 50% 15%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 70% 20%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 90% 25%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 8% 40%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 20% 38%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 40% 42%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 60% 40%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 80% 45%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 12% 60%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 35% 55%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 55% 58%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 75% 60%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 25% 78%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 45% 82%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 65% 78%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 20% 90%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            radial-gradient(circle 0.8px at 50% 95%, rgba(200, 200, 200, 0.4), transparent 0.8px),
            radial-gradient(circle 0.8px at 80% 90%, rgba(200, 200, 200, 0.5), transparent 0.8px),
            /* Subtle flowing rope connections */
            radial-gradient(ellipse 350px 180px at 20% 30%, rgba(150, 150, 200, 0.08) 0%, transparent 70%),
            radial-gradient(ellipse 400px 200px at 50% 20%, rgba(150, 150, 200, 0.08) 0%, transparent 70%),
            radial-gradient(ellipse 320px 160px at 70% 40%, rgba(150, 150, 200, 0.06) 0%, transparent 70%),
            radial-gradient(ellipse 380px 190px at 30% 60%, rgba(150, 150, 200, 0.08) 0%, transparent 70%),
            radial-gradient(ellipse 350px 180px at 60% 70%, rgba(150, 150, 200, 0.06) 0%, transparent 70%),
            radial-gradient(ellipse 400px 200px at 40% 50%, rgba(150, 150, 200, 0.08) 0%, transparent 70%),
            radial-gradient(ellipse 320px 160px at 75% 65%, rgba(150, 150, 200, 0.06) 0%, transparent 70%),
            radial-gradient(ellipse 380px 190px at 25% 80%, rgba(150, 150, 200, 0.08) 0%, transparent 70%);
        background-size: 
            100% 100%, 100% 100%, 100% 100%, 100% 100%, 100% 100%,
            150px 150px, 160px 160px, 170px 170px, 180px 180px, 190px 190px, 200px 200px, 210px 210px, 220px 220px,
            230px 230px, 240px 240px, 250px 250px, 260px 260px, 270px 270px, 280px 280px, 290px 290px, 300px 300px,
            310px 310px, 320px 320px, 330px 330px, 340px 340px, 350px 350px, 360px 360px, 370px 370px, 380px 380px,
            800px 800px, 900px 900px, 850px 850px, 950px 950px, 800px 800px, 900px 900px, 850px 850px, 950px 950px;
        background-position: 
            0% 0%, 0% 0%, 0% 0%, 0% 0%, 0% 0%,
            0% 0%, 10px 10px, 20px 20px, 30px 30px, 40px 40px, 50px 50px, 60px 60px, 70px 70px,
            80px 80px, 90px 90px, 100px 100px, 110px 110px, 120px 120px, 130px 130px, 140px 140px, 150px 150px,
            160px 160px, 170px 170px, 180px 180px, 190px 190px, 200px 200px, 210px 210px, 220px 220px, 230px 230px,
            0% 0%, 30px 30px, 60px 60px, 90px 90px, 120px 120px, 150px 150px, 180px 180px, 210px 210px;
        animation: line-flow-1 40s ease-in-out infinite, line-flow-2 45s ease-in-out infinite;
    }}
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {{
        color: {colors['text_primary']} !important;
        font-weight: 700 !important;
        text-shadow: {text_shadow};
    }}
    
    h1 {{
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        text-align: center;
        margin-bottom: 2rem !important;
        letter-spacing: -0.02em;
        animation: fade-in-down 0.8s ease-out;
    }}

    @keyframes fade-in-down {{
        from {{
            opacity: 0;
            transform: translateY(-30px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    /* Gradient title */
    .gradient-title {{
        background: {colors['gradient']};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        display: inline-block;
    }}
    
    /* Agent cards */
    .agent-card {{
        background: {card_bg};
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1.5px solid {colors['border']};
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        animation: fade-in-up 0.6s ease-out;
        box-shadow: 0 4px 15px {colors['shadow']};
    }}
    
    @keyframes fade-in-up {{
        from {{
            opacity: 0;
            transform: translateY(30px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .agent-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.08) 100%);
        opacity: 0;
        transition: opacity 0.4s ease;
        z-index: 0;
    }}
    
    .agent-card:hover {{
        transform: translateY(-8px);
        box-shadow: 0 12px 30px rgba(102, 126, 234, 0.3);
        border-color: {colors['accent']};
        background: {card_bg};
    }}
    
    .agent-card:hover::before {{
        opacity: 1;
    }}
    
    .agent-card > * {{
        position: relative;
        z-index: 1;
    }}
    
    .agent-emoji {{
        font-size: 2.5rem;
        display: inline-block;
        margin-bottom: 0.5rem;
        animation: float 3s ease-in-out infinite;
    }}
    
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
    }}
    
    .agent-title {{
        font-size: 1.3rem;
        font-weight: 700;
        color: {colors['text_primary']};
        margin: 0.5rem 0;
    }}
    
    .agent-desc {{
        font-size: 0.95rem;
        color: {colors['text_secondary']};
        line-height: 1.5;
    }}
    
    /* Description box */
    .description-box {{
        background: {card_bg};
        backdrop-filter: blur(20px);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        border-left: 5px solid {colors['accent']};
        border: 1.5px solid {colors['border']};
        box-shadow: 0 4px 20px {colors['shadow']};
        animation: fade-in-up 0.8s ease-out 0.2s backwards;
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: {colors['bg_secondary']};
        border-right: 1px solid {colors['border']};
    }}
    
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] li {{
        color: {colors['text_primary']} !important;
    }}
    
    /* Buttons */
    .stButton > button {{
        background: {colors['gradient']};
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px;
        background: {colors['bg_card']};
        border-radius: 12px;
        padding: 0.75rem;
        border: 1px solid {colors['border']};
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: {colors['text_secondary']};
        transition: all 0.3s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {colors['gradient']};
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }}
    
    /* Metrics */
    [data-testid="stMetricValue"] {{
        color: {colors['accent']} !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {colors['text_secondary']} !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }}
    
    /* Inputs */
    .stTextInput input {{
        background: {colors['bg_card']} !important;
        color: {colors['text_primary']} !important;
        border: 2px solid {colors['border']} !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }}
    
    .stTextInput input:focus {{
        border-color: {colors['accent']} !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background: {colors['bg_card']} !important;
        border-radius: 10px !important;
        color: {colors['text_primary']} !important;
        font-weight: 600 !important;
        border: 1px solid {colors['border']} !important;
    }}
    
    .streamlit-expanderHeader:hover {{
        background: {colors['gradient_card']} !important;
        border-color: {colors['accent']} !important;
    }}
    
    .streamlit-expanderContent {{
        background: {colors['bg_card']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        border-top: none !important;
    }}
    
    /* Progress Container */
    .progress-container {{
        background: {card_bg};
        backdrop-filter: blur(20px);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1.5px solid {colors['border']};
        box-shadow: 0 4px 20px {colors['shadow']};
    }}
    
    .progress-title {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {colors['text_primary']};
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    /* Progress Step - Enhanced Styling */
    .progress-step {{
        display: flex;
        align-items: center;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.05);
        border-left: 5px solid transparent;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1.5px solid {colors['border']};
        position: relative;
        overflow: hidden;
    }}
    
    .progress-step::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
        opacity: 0;
        transition: opacity 0.4s ease;
    }}
    
    .progress-step.pending {{
        border-left-color: {colors['text_tertiary']};
        opacity: 0.65;
    }}
    
    .progress-step.pending::after {{
        content: '';
        position: absolute;
        right: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 8px;
        height: 8px;
        background: {colors['text_tertiary']};
        border-radius: 50%;
        margin-right: 1.5rem;
    }}
    
    .progress-step.active {{
        border-left-color: {colors['accent']};
        background: linear-gradient(90deg, rgba(102, 126, 234, 0.12), rgba(118, 75, 162, 0.08));
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.25);
        border-color: {colors['accent']};
        transform: translateX(4px);
    }}
    
    .progress-step.active::before {{
        opacity: 1;
        animation: shimmer 2s infinite;
    }}
    
    @keyframes shimmer {{
        0% {{ transform: translateX(-100%); }}
        100% {{ transform: translateX(100%); }}
    }}
    
    .progress-step.completed {{
        border-left-color: {colors['success']};
        background: linear-gradient(90deg, rgba(16, 185, 129, 0.08), rgba(16, 185, 129, 0.04));
        opacity: 1;
    }}
    
    .progress-step.error {{
        border-left-color: {colors['error']};
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.08), rgba(239, 68, 68, 0.04));
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.7; }}
    }}
    
    .progress-icon {{
        font-size: 2rem;
        margin-right: 1.25rem;
        min-width: 3rem;
        text-align: center;
        transition: all 0.4s ease;
    }}
    
    .progress-step.active .progress-icon {{
        animation: bounce 0.8s ease infinite;
        filter: drop-shadow(0 0 8px {colors['accent']});
    }}
    
    @keyframes bounce {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-8px); }}
    }}
    
    .progress-content {{
        flex: 1;
    }}
    
    .progress-step-title {{
        font-weight: 700;
        font-size: 1.1rem;
        color: {colors['text_primary']};
        margin-bottom: 0.35rem;
    }}
    
    .progress-step-desc {{
        font-size: 0.95rem;
        color: {colors['text_secondary']};
        line-height: 1.4;
    }}
    
    .progress-status {{
        font-size: 0.85rem;
        font-weight: 700;
        padding: 0.5rem 1.2rem;
        border-radius: 20px;
        white-space: nowrap;
        transition: all 0.3s ease;
        letter-spacing: 0.5px;
    }}
    
    .status-pending {{
        background: rgba(148, 163, 184, 0.15);
        color: {colors['text_tertiary']};
        border: 1px solid rgba(148, 163, 184, 0.3);
    }}
    
    .status-active {{
        background: rgba(102, 126, 234, 0.2);
        color: {colors['accent']};
        border: 1.5px solid {colors['accent']};
        box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
        animation: pulse 2s ease-in-out infinite;
    }}
    
    .status-completed {{
        background: rgba(16, 185, 129, 0.15);
        color: {colors['success']};
        border: 1px solid rgba(16, 185, 129, 0.4);
    }}
    
    .status-error {{
        background: rgba(239, 68, 68, 0.15);
        color: {colors['error']};
        border: 1px solid rgba(239, 68, 68, 0.4);
    }}
    
    /* Spinner */
    .spinner {{
        display: inline-block;
        width: 14px;
        height: 14px;
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-top-color: {colors['accent']};
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin-right: 0.5rem;
        vertical-align: middle;
    }}
    
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    /* Stats cards */
    .stats-card {{
        background: {card_bg};
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        border: 1.5px solid {colors['border']};
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
        box-shadow: 0 2px 12px {colors['shadow']};
    }}
    
    .stats-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        border-color: {colors['accent']};
        background: {card_bg};
    }}
    
    .stats-icon {{
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }}
    
    .stats-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {colors['accent']};
        margin: 0.5rem 0;
    }}
    
    .stats-label {{
        font-size: 0.9rem;
        color: {colors['text_secondary']};
        font-weight: 600;
    }}
    
    /* Results card */
    .results-card {{
        background: {card_bg};
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1.5px solid {colors['border']};
        backdrop-filter: blur(10px);
        box-shadow: 0 2px 12px {colors['shadow']};
    }}
    
    /* Links */
    a {{
        color: {colors['accent']} !important;
        text-decoration: none !important;
        transition: all 0.3s ease;
    }}
    
    a:hover {{
        color: {colors['accent_secondary']} !important;
        text-decoration: underline !important;
    }}
    
    /* Divider */
    hr {{
        border: none;
        height: 1px;
        background: {colors['border']};
        margin: 3rem 0;
    }}
    
    /* Success/Error messages */
    .stSuccess, .stError, .stWarning, .stInfo {{
        border-radius: 12px !important;
        border: 1px solid {colors['border']} !important;
    }}
    
    /* Text colors */
    p, div, span, li {{
        color: {colors['text_primary']};
    }}

    /* Code blocks and inline code */
    pre, code {{
        color: {colors['text_primary']} !important;
        background: rgba(255,255,255,0.02);
        padding: 0.35rem 0.5rem;
        border-radius: 6px;
        font-family: 'Inter', monospace;
        font-size: 0.95rem;
    }}

    /* Ensure links are visible on dark backgrounds */
    a {{
        color: {colors['accent']} !important;
    }}
    
    /* Download button special styling */
    .download-section {{
        background: {colors['bg_card']};
        border-radius: 12px;
        padding: 1.5rem;
        margin: 2rem 0;
        border: 1px solid {colors['border']};
    }}
    
    /* Metric styling */
    [data-testid="stMetricValue"] {{
        color: {colors['accent']} !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {colors['text_secondary']} !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }}
    
    /* Ensure all text is readable in both modes */
    body, p, span, div, li, a, button {{
        color: {colors['text_primary']} !important;
    }}
    
    /* Input fields */
    .stTextInput input {{
        background: {colors['bg_secondary']} !important;
        color: {colors['text_primary']} !important;
        border: 2px solid {colors['border']} !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }}
    
    .stTextInput input:focus {{
        border-color: {colors['accent']} !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
    }}
    
    .stTextInput input::placeholder {{
        color: {colors['text_tertiary']} !important;
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background: {colors['bg_card']} !important;
        border-radius: 10px !important;
        color: {colors['text_primary']} !important;
        font-weight: 600 !important;
        border: 1px solid {colors['border']} !important;
    }}
    
    .streamlit-expanderHeader:hover {{
        background: {card_bg} !important;
        border-color: {colors['accent']} !important;
        transition: all 0.3s ease !important;
    }}
    
    .streamlit-expanderContent {{
        background: {colors['bg_card']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        border-top: none !important;
    }}
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px;
        background: {colors['bg_card']};
        border-radius: 12px;
        padding: 0.75rem;
        border: 1px solid {colors['border']};
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: {colors['text_secondary']};
        transition: all 0.3s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {colors['gradient']};
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }}
    
    /* Buttons */
    .stButton > button {{
        background: {colors['gradient']};
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
    }}
    
    /* Success/Error messages */
    .stSuccess, .stError, .stWarning, .stInfo {{
        border-radius: 12px !important;
        border: 1px solid {colors['border']} !important;
        background: {colors['bg_card']} !important;
        color: {colors['text_primary']} !important;
    }}
    
    /* Divider */
    hr {{
        border: none;
        height: 1px;
        background: {colors['border']};
        margin: 3rem 0;
    }}
    
    /* Code blocks */
    pre, code {{
        color: {colors['text_primary']} !important;
        background: {colors['bg_card']};
        padding: 0.35rem 0.5rem;
        border-radius: 6px;
        font-family: 'Inter', monospace;
        font-size: 0.95rem;
        border: 1px solid {colors['border']};
    }}
    
    /* Links */
    a {{
        color: {colors['accent']} !important;
        text-decoration: none !important;
        transition: all 0.3s ease;
    }}
    
    a:hover {{
        color: {colors['accent_secondary']} !important;
        text-decoration: underline !important;
    }}
    
    /* Markdown styling */
    .stMarkdown {{
        color: {colors['text_primary']} !important;
    }}
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {{
        color: {colors['text_primary']} !important;
    }}
    
    /* Progress status badges with proper contrast */
    .progress-status {{
        font-size: 0.85rem;
        font-weight: 700;
        padding: 0.5rem 1.2rem;
        border-radius: 20px;
        white-space: nowrap;
        transition: all 0.3s ease;
        letter-spacing: 0.5px;
    }}
    
    /* Metric containers */
    [data-testid="stMetric"] {{
        background: {colors['bg_card']} !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        border: 1px solid {colors['border']} !important;
    }}
    
    /* Full page background with neural network effect */
    html, body {{
        background-color: #0a0e27;
        background-image: 
            /* Glowing orbs */
            radial-gradient(circle at 15% 30%, rgba(102, 126, 234, 0.2) 0%, rgba(102, 126, 234, 0.08) 15%, transparent 40%),
            radial-gradient(circle at 85% 70%, rgba(118, 75, 162, 0.2) 0%, rgba(118, 75, 162, 0.08) 15%, transparent 40%),
            radial-gradient(circle at 50% 50%, rgba(102, 126, 234, 0.1) 0%, transparent 30%),
            /* Neural network nodes */
            radial-gradient(circle at 20% 20%, rgba(102, 126, 234, 0.6) 1px, transparent 1px),
            radial-gradient(circle at 80% 20%, rgba(118, 75, 162, 0.6) 1px, transparent 1px),
            radial-gradient(circle at 20% 80%, rgba(102, 126, 234, 0.6) 1px, transparent 1px),
            radial-gradient(circle at 80% 80%, rgba(118, 75, 162, 0.6) 1px, transparent 1px),
            radial-gradient(circle at 50% 30%, rgba(102, 126, 234, 0.5) 1.5px, transparent 1.5px),
            radial-gradient(circle at 30% 60%, rgba(118, 75, 162, 0.5) 1.5px, transparent 1.5px),
            radial-gradient(circle at 70% 60%, rgba(102, 126, 234, 0.5) 1.5px, transparent 1.5px),
            radial-gradient(circle at 50% 90%, rgba(118, 75, 162, 0.5) 1.5px, transparent 1.5px),
            /* Connecting lines */
            linear-gradient(105deg, transparent 30%, rgba(102, 126, 234, 0.1) 30%, rgba(102, 126, 234, 0.1) 31%, transparent 31%),
            linear-gradient(75deg, transparent 30%, rgba(118, 75, 162, 0.1) 30%, rgba(118, 75, 162, 0.1) 31%, transparent 31%),
            linear-gradient(45deg, transparent 30%, rgba(102, 126, 234, 0.08) 30%, rgba(102, 126, 234, 0.08) 31%, transparent 31%);
        background-size: 
            100% 100%, 100% 100%, 100% 100%,
            200px 200px, 200px 200px, 200px 200px, 200px 200px, 300px 300px, 300px 300px, 300px 300px, 300px 300px,
            100% 100%, 100% 100%, 100% 100%;
        background-position: 0% 0%, 0% 0%, 0% 0%, 0% 0%, 0% 0%, 0% 0%, 0% 0%, 0% 0%, 0% 0%, 0% 0%, 0% 0%, 0% 0%, 0% 0%, 0% 0%;
        animation: video-flow 30s ease infinite, mesh-shift 25s ease infinite !important;
    }}
    
    /* Header and toolbar with neural network */
    [data-testid="stHeader"] {{
        background-color: #0a0e27;
        background-image: 
            /* Glowing orbs */
            radial-gradient(circle at 15% 30%, rgba(102, 126, 234, 0.15) 0%, rgba(102, 126, 234, 0.05) 15%, transparent 40%),
            radial-gradient(circle at 85% 70%, rgba(118, 75, 162, 0.15) 0%, rgba(118, 75, 162, 0.05) 15%, transparent 40%),
            /* Neural network nodes */
            radial-gradient(circle at 20% 20%, rgba(102, 126, 234, 0.4) 1px, transparent 1px),
            radial-gradient(circle at 80% 20%, rgba(118, 75, 162, 0.4) 1px, transparent 1px),
            radial-gradient(circle at 50% 30%, rgba(102, 126, 234, 0.3) 1.5px, transparent 1.5px),
            /* Connecting lines */
            linear-gradient(105deg, transparent 40%, rgba(102, 126, 234, 0.05) 40%, rgba(102, 126, 234, 0.05) 41%, transparent 41%);
        background-size: 100% 100%, 100% 100%, 200px 200px, 200px 200px, 300px 300px, 100% 100%;
        animation: video-flow 30s ease infinite, mesh-shift 25s ease infinite !important;
    }}
    
    [data-testid="stToolbar"] {{
        background-color: #0a0e27;
        background-image: 
            /* Glowing orbs */
            radial-gradient(circle at 15% 30%, rgba(102, 126, 234, 0.15) 0%, rgba(102, 126, 234, 0.05) 15%, transparent 40%),
            radial-gradient(circle at 85% 70%, rgba(118, 75, 162, 0.15) 0%, rgba(118, 75, 162, 0.05) 15%, transparent 40%),
            /* Neural network nodes */
            radial-gradient(circle at 20% 20%, rgba(102, 126, 234, 0.4) 1px, transparent 1px),
            radial-gradient(circle at 80% 20%, rgba(118, 75, 162, 0.4) 1px, transparent 1px),
            radial-gradient(circle at 50% 30%, rgba(102, 126, 234, 0.3) 1.5px, transparent 1.5px),
            /* Connecting lines */
            linear-gradient(105deg, transparent 40%, rgba(102, 126, 234, 0.05) 40%, rgba(102, 126, 234, 0.05) 41%, transparent 41%);
        background-size: 100% 100%, 100% 100%, 200px 200px, 200px 200px, 300px 300px, 100% 100%;
        animation: video-flow 30s ease infinite, mesh-shift 25s ease infinite !important;
    }}
    
    /* Deployment container with neural network */
    [data-testid="stDeployLogoContainer"] {{
        background-color: #0a0e27;
        background-image: 
            /* Glowing orbs */
            radial-gradient(circle at 15% 30%, rgba(102, 126, 234, 0.15) 0%, rgba(102, 126, 234, 0.05) 15%, transparent 40%),
            radial-gradient(circle at 85% 70%, rgba(118, 75, 162, 0.15) 0%, rgba(118, 75, 162, 0.05) 15%, transparent 40%),
            /* Neural network nodes */
            radial-gradient(circle at 20% 20%, rgba(102, 126, 234, 0.4) 1px, transparent 1px),
            radial-gradient(circle at 80% 20%, rgba(118, 75, 162, 0.4) 1px, transparent 1px),
            radial-gradient(circle at 50% 30%, rgba(102, 126, 234, 0.3) 1.5px, transparent 1.5px),
            /* Connecting lines */
            linear-gradient(105deg, transparent 40%, rgba(102, 126, 234, 0.05) 40%, rgba(102, 126, 234, 0.05) 41%, transparent 41%);
        background-size: 100% 100%, 100% 100%, 200px 200px, 200px 200px, 300px 300px, 100% 100%;
        animation: video-flow 30s ease infinite, mesh-shift 25s ease infinite !important;
    }}
</style>
""", unsafe_allow_html=True)

# Initialize orchestrator.
# NOT cached: it is built fresh per review with the visitor's own API key, which
# must never persist on the shared server (st.cache_resource is global to all users).
def get_orchestrator(api_key):
    return PaperReviewOrchestrator(api_key=api_key)

# Main title
st.markdown(f"""
<h1><span class="gradient-title">📄 Multi-Agent Research Paper Reviewer</span></h1>
""", unsafe_allow_html=True)

# ===== PRIMARY FOCUS: PAPER SUBMISSION SECTION =====
st.markdown(f"""
<div style='background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.1) 100%); 
            padding: 3rem; border-radius: 20px; border: 2px solid {colors['accent']}; 
            margin: 2rem 0; box-shadow: 0 8px 32px rgba(102, 126, 234, 0.25);'>
    <h2 style='color: {colors['accent']}; margin-top: 0; font-size: 2rem; text-align: center;'>🚀 Start Your Analysis</h2>
    <p style='color: {colors['text_secondary']}; text-align: center; font-size: 1.1rem; margin: 1rem 0 2rem 0;'>
        Enter an arXiv paper ID to begin comprehensive multi-agent analysis
    </p>
</div>
""", unsafe_allow_html=True)

# Input section with prominent styling - Full Width Design
st.markdown("<br>", unsafe_allow_html=True)

# Create a more unified layout
input_col, button_col = st.columns([3, 1])

with input_col:
    arxiv_id = st.text_input(
        "📋 Enter arXiv Paper ID",
        placeholder="e.g., 2301.12345 or 1706.03762",
        value=st.session_state.get("arxiv_id", ""),
        key="arxiv_input",
        help="Enter the arXiv identifier to analyze"
    )

with button_col:
    st.write("")
    st.write("")
    review_button = st.button("🚀 Review", type="primary", use_container_width=True, key="review_btn_top", help="Start analysis")

# Popular papers section - Better layout
st.markdown(f"<h4 style='color: {colors['accent']}; margin-top: 1.5rem; margin-bottom: 0.75rem;'>⚡ Popular Papers - Quick Load</h4>", unsafe_allow_html=True)

example_col1, example_col2, example_col3 = st.columns(3)

with example_col1:
    if st.button("🎯 Attention is All You Need\n1706.03762", use_container_width=True, key="ex_1706"):
        st.session_state.arxiv_id = "1706.03762"
        st.rerun()

with example_col2:
    if st.button("🎯 RecZero\n2510.23077", use_container_width=True, key="ex_2510"):
        st.session_state.arxiv_id = "2510.23077"
        st.rerun()

with example_col3:
    if st.button("🎯 SimCLR\n2002.05709", use_container_width=True, key="ex_2002"):
        st.session_state.arxiv_id = "2002.05709"
        st.rerun()

st.divider()

# Sidebar
with st.sidebar:
    st.markdown(f"<h3 style='color: {colors['accent']};'>🔑 Groq API Key</h3>", unsafe_allow_html=True)
    groq_key = st.text_input(
        "Groq API Key",
        type="password",
        label_visibility="collapsed",
        placeholder="gsk_...",
        key="groq_key_input",
        help="Your key is used only for this session and is never stored or logged."
    )
    st.caption("🔒 Used only for this session — never stored. Get a free key at [console.groq.com](https://console.groq.com/keys).")
    if groq_key and not groq_key.startswith("gsk_"):
        st.warning("That doesn't look like a Groq key (they start with `gsk_`).")
    st.divider()

    st.markdown(f"<h3 style='color: {colors['accent']};'>🎯 Quick Access</h3>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='font-size: 0.9rem; line-height: 1.6; color: {colors['text_secondary']};'>
    <p><strong style='color: {colors['text_primary']};'>📚 Example Papers</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    examples = {
        "1706.03762": "Attention is All You Need",
        "2510.23077": "RecZero",
        "2002.05709": "SimCLR"
    }
    
    for ex_id, title in examples.items():
        if st.button(f"📄 {ex_id}", key=f"ex_{ex_id}", use_container_width=True, help=title):
            st.session_state.arxiv_id = ex_id
            st.rerun()
    
    st.divider()
    
    st.markdown(f"<h3 style='color: {colors['accent']};'>🏗️ System Info</h3>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='font-size: 0.85rem; line-height: 1.8; color: {colors['text_secondary']};'>
    <p><strong style='color: {colors['text_primary']};'>Architecture</strong></p>
    <ul style='margin-left: 1rem; margin-top: 0.5rem;'>
        <li>🧠 LLM: Groq Llama-3.1-8b</li>
        <li>🔗 Framework: LangGraph</li>
        <li>🌐 Protocol: MCP Server</li>
        <li>🤖 Agents: 5 Specialized</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# Advanced Architecture Section
st.markdown(f"""
<div class="description-box">
    <h3 style='color: {colors['accent']}; margin-top: 0; font-size: 1.4rem;'>🤖 Advanced AI-Powered Analysis System</h3>
    <p style='font-size: 1rem; line-height: 1.6; color: {colors['text_secondary']}; margin-bottom: 1.5rem;'>
        Deploy cutting-edge multi-agent orchestration powered by LangGraph and Groq's high-performance LLMs. 
        Our architecture leverages specialized agents with real-time streaming, advanced reasoning, and comprehensive paper analysis.
    </p>
</div>
""", unsafe_allow_html=True)

# Architecture Grid Display
st.markdown(f"<h4 style='color: {colors['accent']};'>🏗️ System Architecture</h4>", unsafe_allow_html=True)

arch_col1, arch_col2, arch_col3, arch_col4 = st.columns(4)

with arch_col1:
    st.markdown(f"""
    <div style='background: rgba(102, 126, 234, 0.12); padding: 1.5rem; border-radius: 12px; border: 1.5px solid {colors['border']}; text-align: center;'>
        <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🧠</div>
        <div style='font-weight: 600; color: {colors['accent']}; margin-bottom: 0.5rem;'>LLM Engine</div>
        <div style='font-size: 0.85rem; color: {colors['text_secondary']}; line-height: 1.5;'>
            Groq Llama-3.1-8b<br/>⚡ 100+ tokens/sec
        </div>
    </div>
    """, unsafe_allow_html=True)

with arch_col2:
    st.markdown(f"""
    <div style='background: rgba(102, 126, 234, 0.12); padding: 1.5rem; border-radius: 12px; border: 1.5px solid {colors['border']}; text-align: center;'>
        <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🔗</div>
        <div style='font-weight: 600; color: {colors['accent']}; margin-bottom: 0.5rem;'>Orchestration</div>
        <div style='font-size: 0.85rem; color: {colors['text_secondary']}; line-height: 1.5;'>
            LangGraph<br/>🔄 Agentic workflows
        </div>
    </div>
    """, unsafe_allow_html=True)

with arch_col3:
    st.markdown(f"""
    <div style='background: rgba(102, 126, 234, 0.12); padding: 1.5rem; border-radius: 12px; border: 1.5px solid {colors['border']}; text-align: center;'>
        <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🌐</div>
        <div style='font-weight: 600; color: {colors['accent']}; margin-bottom: 0.5rem;'>Protocol</div>
        <div style='font-size: 0.85rem; color: {colors['text_secondary']}; line-height: 1.5;'>
            MCP Server<br/>📡 Model Context
        </div>
    </div>
    """, unsafe_allow_html=True)

with arch_col4:
    st.markdown(f"""
    <div style='background: rgba(102, 126, 234, 0.12); padding: 1.5rem; border-radius: 12px; border: 1.5px solid {colors['border']}; text-align: center;'>
        <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🤖</div>
        <div style='font-weight: 600; color: {colors['accent']}; margin-bottom: 0.5rem;'>Analysis</div>
        <div style='font-size: 0.85rem; color: {colors['text_secondary']}; line-height: 1.5;'>
            5 Specialized Agents<br/>📊 Parallel processing
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Description
st.markdown(f"""
<div class="description-box">
    <h3 style='color: {colors['accent']}; margin-top: 0; font-size: 1.2rem;'>🤖 How It Works</h3>
    <p style='font-size: 0.95rem; line-height: 1.8; color: {colors['text_secondary']}; margin: 0;'>
        Our system deploys 5 specialized agents that work in parallel: The Reader Agent extracts content, 
        Meta-Reviewer evaluates quality, Critic Agent performs deep analysis, Citation Agent analyzes references, 
        and Publication Agent discovers venues. All orchestrated through LangGraph with real-time progress tracking.
    </p>
</div>
""", unsafe_allow_html=True)

# Agent showcase
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

agents_row1 = [
    ("📖", "Reader Agent", "Intelligently extracts and summarizes paper content with contextual understanding"),
    ("⭐", "Meta-Reviewer", "Provides comprehensive quality assessment and methodology evaluation"),
    ("🔍", "Critic Agent", "Performs deep analysis to identify strengths, weaknesses, and improvements")
]

for col, (emoji, name, desc) in zip([col1, col2, col3], agents_row1):
    with col:
        st.markdown(f"""
        <div class="agent-card">
            <div class="agent-emoji">{emoji}</div>
            <div class="agent-title">{name}</div>
            <div class="agent-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

col4, col5 = st.columns(2)

agents_row2 = [
    ("📚", "Cite Agent", "Analyzes citation patterns, reference quality, and academic context"),
    ("📅", "Publication Agent", "Discovers official publication venues through intelligent web search")
]

for col, (emoji, name, desc) in zip([col4, col5], agents_row2):
    with col:
        st.markdown(f"""
        <div class="agent-card">
            <div class="agent-emoji">{emoji}</div>
            <div class="agent-title">{name}</div>
            <div class="agent-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

# Progress steps definition
progress_steps = [
    {'id': 'reader', 'icon': '📖', 'title': 'Reading Paper', 
     'desc': 'Extracting content from arXiv...', 'active': 'Analyzing paper content...', 'done': 'Content extracted'},
    {'id': 'meta', 'icon': '⭐', 'title': 'Meta-Review', 
     'desc': 'Evaluating quality...', 'active': 'Assessing quality...', 'done': 'Quality assessed'},
    {'id': 'critic', 'icon': '🔍', 'title': 'Critical Analysis', 
     'desc': 'Identifying insights...', 'active': 'Analyzing critically...', 'done': 'Analysis complete'},
    {'id': 'cite', 'icon': '📚', 'title': 'Citation Analysis', 
     'desc': 'Analyzing references...', 'active': 'Processing citations...', 'done': 'Citations analyzed'},
    {'id': 'pub', 'icon': '📅', 'title': 'Publication Search', 
     'desc': 'Finding venue...', 'active': 'Searching venue...', 'done': 'Venue found'},
    {'id': 'final', 'icon': '🎯', 'title': 'Finalizing Report', 
     'desc': 'Compiling results...', 'active': 'Generating report...', 'done': 'Report ready'}
]

# Review process with advanced progress tracking
if review_button and arxiv_id and not groq_key:
    st.warning("🔑 Please paste your Groq API key in the sidebar to run the review.")
elif review_button and arxiv_id:
    # Initialize progress
    st.session_state.progress_data = {step['id']: 'pending' for step in progress_steps}
    
    # Create progress display
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-title">🤖 Multi-Agent Analysis Pipeline</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress placeholders
    step_placeholders = []
    for step in progress_steps:
        step_placeholders.append(st.empty())
    
    status_container = st.empty()
    
    def update_step_display(step_idx, status):
        step = progress_steps[step_idx]
        
        if status == 'active':
            status_class = 'active'
            status_badge = '🔄 In Progress'
            message = step['active']
        elif status == 'completed':
            status_class = 'completed'
            status_badge = '✓ Completed'
            message = step['done']
        elif status == 'error':
            status_class = 'error'
            status_badge = '✗ Failed'
            message = 'Error occurred'
        else:
            status_class = 'pending'
            status_badge = '⏳ Pending'
            message = step['desc']
        
        step_placeholders[step_idx].markdown(f"""
        <div class="progress-step {status_class}">
            <div class="progress-icon">{step['icon']}</div>
            <div class="progress-content">
                <div class="progress-step-title">{step['title']}</div>
                <div class="progress-step-desc">{message}</div>
            </div>
            <span class="progress-status status-{status_class}">{status_badge}</span>
        </div>
        """, unsafe_allow_html=True)
    
    try:
        # Initial display
        for idx in range(len(progress_steps)):
            update_step_display(idx, 'pending')
        
        orchestrator = get_orchestrator(groq_key)
        start_time = time.time()
        
        # Execute review with progress updates
        with status_container.container():
            st.info("🚀 Starting multi-agent analysis...")
        
        # Update each step as active, then execute
        for idx, step in enumerate(progress_steps):
            update_step_display(idx, 'active')
            time.sleep(0.2)  # Small delay for visual effect
            
            # Execute the actual review on the last step
            if idx == len(progress_steps) - 1:
                result = orchestrator.review_paper(arxiv_id)
        
        # Mark all as completed
        for idx in range(len(progress_steps)):
            update_step_display(idx, 'completed')
        
        duration = time.time() - start_time
        
        if result["status"] == "success":
            status_container.success(f"✅ Review completed successfully in {duration:.2f}s!")
            st.session_state.review_result = result
            st.session_state.scroll_to_results = True
            time.sleep(1)
            st.rerun()
        else:
            status_container.error(f"❌ Error: {result.get('error', 'Unknown error')}")
            # Mark last active step as error
            for idx in range(len(progress_steps) - 1, -1, -1):
                if st.session_state.progress_data.get(progress_steps[idx]['id']) == 'active':
                    update_step_display(idx, 'error')
                    break
            
    except Exception as e:
        status_container.error(f"❌ Exception: {str(e)}")
        # Mark current active step as error
        for idx, step in enumerate(progress_steps):
            if st.session_state.progress_data.get(step['id']) == 'active':
                update_step_display(idx, 'error')

# Display results
if "review_result" in st.session_state:
    result = st.session_state.review_result
    
    # Auto-scroll to results section if flag is set
    if st.session_state.get("scroll_to_results", False):
        st.markdown("""
        <script>
            // Find the main Streamlit container and scroll it
            setTimeout(function() {
                // Method 1: Scroll the iframe/main window
                window.scrollTo({top: 0, behavior: 'smooth'});
                document.documentElement.scrollTop = 0;
                
                // Method 2: Also try scrolling parent if in iframe
                try {
                    parent.window.scrollTo({top: 0, behavior: 'smooth'});
                } catch(e) {}
                
                // Method 3: Find and scroll to results heading
                var headings = document.querySelectorAll('h2');
                for (var i = 0; i < headings.length; i++) {
                    if (headings[i].textContent.includes('Comprehensive Review Results')) {
                        headings[i].scrollIntoView({behavior: 'smooth', block: 'start'});
                        break;
                    }
                }
            }, 300);
        </script>
        """, unsafe_allow_html=True)
        st.session_state.scroll_to_results = False
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; color: {colors['text_primary']};'>📊 Comprehensive Review Results</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Paper info stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-icon">📄</div>
            <div class="stats-value">{len(result['paper_title'][:30])}</div>
            <div class="stats-label">Title Length</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-icon">👥</div>
            <div class="stats-value">{len(result['authors'])}</div>
            <div class="stats-label">Authors</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        pub_venue = result.get('publication_info', {}).get('venue', 'Unknown')[:15]
        st.markdown(f"""
        <div class="stats-card">
            <div class="stats-icon">📅</div>
            <div class="stats-value" style="font-size: 1.2rem;">Unavailable</div>
            <div class="stats-label">Publication Venue</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Paper details
    st.markdown(f"""
    <div class="results-card">
        <h3 style='color: {colors['accent']}; margin-top: 0;'>📋 Paper Information</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(result["paper_title"])
        authors = ', '.join(result['authors'][:5])
        if len(result['authors']) > 5:
            authors += f" et al. (+{len(result['authors']) - 5})"
        st.markdown(f"**Authors**: {authors}")
    
    with col2:
        st.metric("📑 arXiv ID", result["arxiv_id"])
        cats = ', '.join(result['categories'][:3])
        st.markdown(f"**Categories**: {cats}")
    
    # Performance metrics
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⏱️ Duration", f"{result['metrics']['duration_seconds']:.2f}s")
    with col2:
        st.metric("🔧 Tool Calls", result['metrics']['total_tool_calls'])
    with col3:
        st.metric("🤖 Agents", result['metrics']['agents_executed'])
    
    # Detailed results in tabs
    st.divider()
    st.markdown(f"<h3 style='text-align: center; color: {colors['text_primary']};'>📚 Detailed Analysis</h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📖 Summary",
        "⭐ Meta-Review",
        "🔍 Critical Analysis",
        "📚 Citations",
        "📅 Publication"
    ])
    
    with tab1:
        st.markdown(f"<h3 style='color: {colors['accent']};'>📖 Paper Summary</h3>", unsafe_allow_html=True)
        
        with st.expander("📄 Abstract", expanded=True):
            st.markdown(f"<p style='line-height: 1.8; color: {colors['text_primary']};'>{markdown_to_html(result['summary']['abstract'])}</p>", unsafe_allow_html=True)
        
        with st.expander("🎯 Key Points", expanded=True):
            st.markdown(f"<p style='line-height: 1.8; color: {colors['text_primary']};'>{markdown_to_html(result['summary']['key_points']['summary'])}</p>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown(f"<h3 style='color: {colors['accent']};'>⭐ Meta-Review Analysis</h3>", unsafe_allow_html=True)
        
        with st.expander("🔬 Methodology Analysis", expanded=True):
            st.markdown(f"<p style='line-height: 1.8; color: {colors['text_primary']};'>{markdown_to_html(result['meta_review']['methodology']['methodology_analysis'])}</p>", unsafe_allow_html=True)
        
        with st.expander("💡 Contribution Evaluation", expanded=True):
            st.markdown(f"<p style='line-height: 1.8; color: {colors['text_primary']};'>{markdown_to_html(result['meta_review']['contribution']['contribution_evaluation'])}</p>", unsafe_allow_html=True)
        
        with st.expander("📊 Overall Review", expanded=True):
            st.markdown(f"<p style='line-height: 1.8; color: {colors['text_primary']};'>{markdown_to_html(result['meta_review']['overall_review'])}</p>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown(f"<h3 style='color: {colors['accent']};'>🔍 Critical Analysis</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="results-card">
                <h4 style='color: {colors['success']};'>✅ Strengths</h4>
                <ul style='line-height: 1.8; color: {colors['text_primary']};'>
            """, unsafe_allow_html=True)
            for strength in result['critical_analysis']['strengths']:
                st.markdown(f"<li>{markdown_to_html(strength)}</li>", unsafe_allow_html=True)
            st.markdown("</ul></div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="results-card">
                <h4 style='color: {colors['error']};'>⚠️ Weaknesses</h4>
                <ul style='line-height: 1.8; color: {colors['text_primary']};'>
            """, unsafe_allow_html=True)
            for weakness in result['critical_analysis']['weaknesses']:
                st.markdown(f"<li>{markdown_to_html(weakness)}</li>", unsafe_allow_html=True)
            st.markdown("</ul></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.expander("💭 Suggested Improvements", expanded=True):
            st.markdown(f"<p style='line-height: 1.8; color: {colors['text_primary']};'>{markdown_to_html(result['critical_analysis']['improvements'])}</p>", unsafe_allow_html=True)
    
    with tab4:
        st.markdown(f"<h3 style='color: {colors['accent']};'>📚 Citation Analysis</h3>", unsafe_allow_html=True)

        cite = result['citation_analysis']

        # Two headline numbers: references in the bibliography, and distinct
        # in-text markers found in the body.
        m1, m2 = st.columns(2)
        with m1:
            st.metric("📚 Total Citations Used", cite.get('total_references', 0),
                      help="Entries counted in the paper's References/Bibliography section")
        with m2:
            st.metric("🔖 In-Text Citations", cite.get('in_text_citation_count', 0),
                      help="Distinct citation markers found in the body text")

        # Tell the user how the reference count was derived (exact vs estimate).
        _method = cite.get('reference_detection_method', '')
        _method_note = {
            'bracketed': "✅ Exact — counted numbered [n] entries in the reference list.",
            'author_year_estimate': "≈ Estimate — author-year references counted by publication year (PDF text can't be counted exactly).",
            'no_references_section': "⚠️ Reference list not found in the extracted PDF text.",
            'unrecognized_format': "⚠️ Reference format not recognized — count may be unavailable.",
        }.get(_method, "" if not _method else f"Detection method: {_method}")
        if _method_note:
            st.caption(_method_note)

        st.markdown("<br>", unsafe_allow_html=True)

        # List every in-text citation with the sentence around it for context.
        in_text = cite.get('in_text_citations', [])
        if in_text:
            with st.expander(f"🔖 In-Text Citations & Context ({len(in_text)})", expanded=True):
                for item in in_text:
                    marker = item.get('marker', '')
                    context = item.get('context', '')
                    st.markdown(
                        f"<div style='margin-bottom: 0.9rem; padding: 0.75rem 1rem; "
                        f"background: rgba(102,126,234,0.10); border-left: 3px solid {colors['accent']}; "
                        f"border-radius: 8px;'>"
                        f"<span style='color: {colors['accent']}; font-weight: 700;'>{marker}</span>"
                        f"<div style='color: {colors['text_secondary']}; font-size: 0.9rem; "
                        f"line-height: 1.6; margin-top: 0.3rem;'>…{markdown_to_html(context)}…</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

        with st.expander("🌐 Citation Context", expanded=True):
            st.markdown(f"<p style='line-height: 1.8; color: {colors['text_primary']};'>{markdown_to_html(result['citation_analysis']['context']['citation_context'])}</p>", unsafe_allow_html=True)
        
        with st.expander("📊 Reference Quality Assessment", expanded=True):
            st.markdown(f"<p style='line-height: 1.8; color: {colors['text_primary']};'>{markdown_to_html(result['citation_analysis']['quality']['reference_quality'])}</p>", unsafe_allow_html=True)
        
        with st.expander("💡 Recommendations", expanded=True):
            st.markdown(f"<p style='line-height: 1.8; color: {colors['text_primary']};'>{markdown_to_html(result['citation_analysis']['recommendations'])}</p>", unsafe_allow_html=True)
    
    with tab5:
        st.markdown(f"<h3 style='color: {colors['accent']};'>📅 Publication Information</h3>", unsafe_allow_html=True)
        
        pub_data = result.get('publication_info', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📍 Status", pub_data.get('publication_status', 'Unknown'))
        with col2:
            st.metric("🏛️ Venue", pub_data.get('venue', 'N/A'))
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if pub_data.get('link'):
            st.markdown(f"""
            <div class="results-card">
                <h4 style='color: {colors['accent']};'>🔗 Publication Link</h4>
                <p><a href="{pub_data['link']}" target="_blank">{pub_data['link']}</a></p>
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("🔍 Web Search Evidence", expanded=True):
            st.markdown(f"<p style='line-height: 1.8; color: {colors['text_primary']};'>{markdown_to_html(pub_data.get('web_search_evidence', 'No evidence found.'))}</p>", unsafe_allow_html=True)
    
    # Download section
    st.divider()
    st.markdown(f"<h3 style='text-align: center; color: {colors['text_primary']};'>📥 Export & Actions</h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        json_str = json.dumps(result, indent=2, default=str)
        st.download_button(
            "📥 Download JSON",
            json_str,
            f"review_{result['arxiv_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json",
            use_container_width=True
        )
    
    with col2:
        # Generate markdown report
        report = f"""# Research Paper Review Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Paper Information
- **Title**: {result['paper_title']}
- **Authors**: {', '.join(result['authors'])}
- **arXiv ID**: {result['arxiv_id']}
- **Categories**: {', '.join(result['categories'])}

## Summary
{result['summary']['abstract']}

### Key Points
{result['summary']['key_points']['summary']}

## Meta-Review

### Methodology
{result['meta_review']['methodology']['methodology_analysis']}

### Contribution
{result['meta_review']['contribution']['contribution_evaluation']}

### Overall Assessment
{result['meta_review']['overall_review']}

## Critical Analysis

### Strengths
{chr(10).join('- ' + s for s in result['critical_analysis']['strengths'])}

### Weaknesses
{chr(10).join('- ' + w for w in result['critical_analysis']['weaknesses'])}

### Improvements
{result['critical_analysis']['improvements']}

## Citation Analysis
- **Total Citations Used (references)**: {result['citation_analysis'].get('total_references', 0)}
- **In-Text Citations (distinct markers)**: {result['citation_analysis'].get('in_text_citation_count', 0)}

### In-Text Citations & Context
{chr(10).join(f"- **{c.get('marker','')}** — …{c.get('context','')}…" for c in result['citation_analysis'].get('in_text_citations', [])) or "- None detected"}

### Context
{result['citation_analysis']['context']['citation_context']}

### Quality
{result['citation_analysis']['quality']['reference_quality']}

### Recommendations
{result['citation_analysis']['recommendations']}

## Publication Information
- **Status**: {pub_data.get('publication_status', 'Unknown')}
- **Venue**: {pub_data.get('venue', 'N/A')}
- **Link**: {pub_data.get('link', 'N/A')}

---
*Generated by Multi-Agent Paper Reviewer*
"""
        
        st.download_button(
            "📄 Download Report (MD)",
            report,
            f"review_{result['arxiv_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            "text/markdown",
            use_container_width=True
        )
    
    with col3:
        if st.button("🔄 New Review", use_container_width=True):
            if 'review_result' in st.session_state:
                del st.session_state.review_result
            if 'arxiv_id' in st.session_state:
                del st.session_state.arxiv_id
            if 'progress_data' in st.session_state:
                st.session_state.progress_data = {}
            st.rerun()

elif review_button and not arxiv_id:
    st.warning("⚠️ Please enter an arXiv paper ID to begin analysis")

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div style='color: {colors['text_primary']};'>
        <h4>Multi-Agent Reviewer</h4>
        <p style='font-size: 0.85rem; color: {colors['text_secondary']}; line-height: 1.6;'>
            Advanced AI system for academic paper analysis. Built with LangGraph, Groq, and modern web technologies.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style='color: {colors['text_primary']};'>
        <h4>Developer</h4>
        <p style='font-weight: 600; margin-bottom: 0.25rem;'>Priyadip Sau</p>
        <p style='font-size: 0.85rem; color: {colors['text_secondary']};'>
            Indian Institute of Technology Jodhpur<br>
            Rajasthan, India
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style='color: {colors['text_primary']};'>
        <h4>Connect</h4>
        <div style='display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.9rem;'>
            <a href='mailto:saupriyadip571@gmail.com' target='_blank'>📧 Email</a>
            <a href='https://priyadipsau.in/' target='_blank'>🌐 Website</a>
            <a href='https://github.com/priyadip' target='_blank'>💻 GitHub</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div style='color: {colors['text_primary']};'>
        <h4>Social</h4>
        <div style='display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.9rem;'>
            <a href='https://linkedin.com/in/priyadip-cs' target='_blank'>💼 LinkedIn</a>
            <a href='https://twitter.com/PriyadipSau' target='_blank'>🐦 Twitter</a>
            <a href='https://instagram.com/priyadipsau' target='_blank'>📷 Instagram</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown(f"""
    <p style='font-size: 0.85rem; color: {colors['text_tertiary']};'>
        © 2025 Priyadip Sau. All rights reserved. | Powered by Groq & LangGraph
    </p>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style='display: flex; gap: 1.5rem; justify-content: flex-end; font-size: 0.85rem;'>
        <a href='https://priyadipsau.in/' target='_blank'>About</a>
        <a href='https://github.com/priyadip' target='_blank'>Projects</a>
        <a href='mailto:saupriyadip571@gmail.com'>Contact</a>
    </div> 
    """, unsafe_allow_html=True)
# End of code
  