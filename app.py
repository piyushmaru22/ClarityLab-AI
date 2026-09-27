import hashlib
import html
import io
import json
import os
import re
import textwrap
import sys

import streamlit as st
from PIL import Image

# Groq Client
try:
    from groq import Groq
except ImportError:
    Groq = None

# PDF and OCR Parsers
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import pdf2image
except ImportError:
    pdf2image = None

# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="ClarityLab AI | Biomarker Dashboard",
    page_icon=":material/biotech:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def render_html(html_str: str) -> None:
    st.html(textwrap.dedent(html_str).strip())

def esc(value) -> str:
    return html.escape(str(value if value is not None else ""))

# ---------------------------------------------------------
# Theme: Ultra-Premium Crimson & Obsidian Glass
# ---------------------------------------------------------
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
    --bg-deep: #030303;
    --surface-glass: rgba(15, 15, 18, 0.6);
    --surface-glass-hover: rgba(22, 22, 26, 0.85);
    --border-glass: rgba(255, 255, 255, 0.05);
    --border-red: rgba(255, 0, 60, 0.2);
    
    --text-main: #f5f5f7;
    --text-muted: #86868b;
    
    /* Striking Premium Palette */
    --neon-crimson: #ff003c;
    --neon-blood: #990024;
    --neon-white: #ffffff;
    --neon-gold: #ffaa00;
    
    --ease-cinematic: cubic-bezier(0.19, 1, 0.22, 1);
    --ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

/* Global Body & Background */
html, body, .stApp, [class*="css"], .stMarkdown, button, input, label {
    font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp { 
    background: var(--bg-deep) !important; 
    color: var(--text-main); 
}

/* Ambient Breathing Background Orbs */
.stApp::before { 
    content: ""; 
    position: fixed; 
    inset: 0; 
    background: radial-gradient(circle at 20% 0%, rgba(255, 0, 60, 0.08) 0%, transparent 40%), 
                radial-gradient(circle at 80% 100%, rgba(255, 0, 60, 0.03) 0%, transparent 50%); 
    z-index: -1; 
    pointer-events: none; 
    animation: ambientBreathe 10s ease-in-out infinite alternate;
}

header[data-testid="stHeader"] { background: transparent !important; }
.block-container { max-width: 1250px; padding-top: 3rem !important; padding-bottom: 5rem !important; }

/* Cinematic Micro-Animations */
@keyframes cinematicReveal { 
    0% { opacity: 0; transform: translateY(35px) scale(0.97); filter: blur(12px); } 
    100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); } 
}
@keyframes floatSpatial { 
    0%, 100% { transform: translateY(0) rotateX(0deg); } 
    50% { transform: translateY(-12px) rotateX(2deg); } 
}
@keyframes breatheCrimson { 
    0%, 100% { box-shadow: 0 0 15px rgba(255, 0, 60, 0.15); border-color: rgba(255, 0, 60, 0.4); } 
    50% { box-shadow: 0 0 35px rgba(255, 0, 60, 0.6); border-color: rgba(255, 0, 60, 1); } 
}
@keyframes laserScan { 
    0% { top: 0; opacity: 0; box-shadow: 0 0 0 transparent; } 
    10% { opacity: 1; box-shadow: 0 0 15px var(--neon-crimson); } 
    90% { opacity: 1; box-shadow: 0 0 15px var(--neon-crimson); } 
    100% { top: 100%; opacity: 0; box-shadow: 0 0 0 transparent; } 
}
@keyframes ambientBreathe {
    0% { opacity: 0.7; transform: scale(1); }
    100% { opacity: 1; transform: scale(1.05); }
}

/* Typography & Headings */
.cl-title { 
    font-size: 2.8rem; font-weight: 700; letter-spacing: -0.05em; margin: 0; 
    background: linear-gradient(135deg, #ffffff 0%, #86868b 100%); 
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
}
.cl-tagline { font-size: 1.1rem; color: var(--text-muted); margin-top: 6px; font-weight: 400; letter-spacing: 0.02em; }
.cl-h2 { font-size: 1.8rem; font-weight: 600; letter-spacing: -0.03em; color: var(--text-main); margin-bottom: 8px; }
.cl-eyebrow { font: 600 12px/1 'JetBrains Mono', monospace; letter-spacing: 0.3em; text-transform: uppercase; color: var(--neon-crimson); margin-bottom: 12px; }

/* Header & Ribbons */
.cl-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 30px; border-bottom: 1px solid var(--border-glass); margin-bottom: 30px; flex-wrap: wrap; gap: 20px; animation: cinematicReveal 1s var(--ease-cinematic) both; }
.cl-brand { display: flex; align-items: center; gap: 24px; }
.cl-logo { width: 56px; height: 56px; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.5); border: 1px solid var(--neon-crimson); border-radius: 14px; color: var(--neon-crimson); box-shadow: 0 0 30px rgba(255, 0, 60, 0.25); position: relative; overflow: hidden; }
.cl-logo::after { content: ''; position: absolute; inset: 0; background: linear-gradient(135deg, transparent 40%, rgba(255,255,255,0.1) 50%, transparent 60%); animation: ambientBreathe 3s infinite linear; }
.cl-logo svg { width: 28px; height: 28px; }

/* Status Chip */
.cl-chip { display: inline-flex; align-items: center; gap: 10px; padding: 8px 18px; border-radius: 999px; background: rgba(255, 0, 60, 0.05); border: 1px solid rgba(255, 0, 60, 0.3); font: 500 12px 'JetBrains Mono', monospace; color: var(--text-main); backdrop-filter: blur(8px); letter-spacing: 0.05em; }
.cl-chip-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--neon-crimson); box-shadow: 0 0 10px var(--neon-crimson); animation: ambientBreathe 1.5s infinite alternate; }

.cl-prefs { display: flex; gap: 24px; flex-wrap: wrap; margin: 16px 0 12px; font-size: 0.95rem; color: var(--text-muted); animation: cinematicReveal 1s var(--ease-cinematic) 0.1s both; }
.cl-prefs strong { color: var(--text-main); font-weight: 500; padding: 6px 14px; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid rgba(255,255,255,0.08); }

/* Sci-Fi Crimson Laser Uploader */
[data-testid="stFileUploaderDropzone"] { 
    position: relative; overflow: hidden; background: var(--surface-glass) !important; 
    border: 1px dashed var(--border-red) !important; border-radius: 20px !important; 
    transition: all 0.4s var(--ease-cinematic) !important; backdrop-filter: blur(16px); 
    animation: cinematicReveal 1s var(--ease-cinematic) 0.2s both;
}
[data-testid="stFileUploaderDropzone"]:hover { 
    border-color: var(--neon-crimson) !important; background: var(--surface-glass-hover) !important; 
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), inset 0 0 40px rgba(255, 0, 60, 0.05) !important; 
}
[data-testid="stFileUploaderDropzone"]::after { 
    content: ""; position: absolute; left: 0; right: 0; top: 0; height: 1px; 
    background: var(--neon-crimson); 
    animation: laserScan 2.5s cubic-bezier(0.4, 0, 0.2, 1) infinite; pointer-events: none; 
}

/* Master Glass Cards */
.metric-card, .food-card, .cl-summary, .ob-card, details.dq { 
    background: var(--surface-glass); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); 
    border: 1px solid var(--border-glass); border-radius: 20px; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4); 
    animation: cinematicReveal 0.8s var(--ease-cinematic) both; 
    transition: all 0.4s var(--ease-cinematic); 
}
.metric-card:hover, .food-card:hover { 
    transform: translateY(-10px) scale(1.02); border-color: rgba(255, 255, 255, 0.15); 
    box-shadow: 0 30px 60px rgba(0, 0, 0, 0.7), 0 0 40px rgba(255, 0, 60, 0.05); 
    z-index: 10;
}

/* Metric Cards specific */
.metric-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; margin-top: 16px; perspective: 1000px; }
.metric-card { padding: 30px; position: relative; overflow: hidden; display: flex; flex-direction: column; justify-content: space-between; }
.metric-card.is-flagged { border-color: rgba(255, 0, 60, 0.3); background: linear-gradient(180deg, rgba(255, 0, 60, 0.05) 0%, transparent 100%), var(--surface-glass); }
.metric-card.is-flagged:hover { box-shadow: 0 30px 60px rgba(0,0,0,0.8), 0 0 50px rgba(255, 0, 60, 0.15); border-color: rgba(255, 0, 60, 0.8); }
.metric-card.is-low { border-color: rgba(255, 170, 0, 0.25); background: linear-gradient(180deg, rgba(255, 170, 0, 0.05) 0%, transparent 100%), var(--surface-glass); }
.metric-card.is-low:hover { box-shadow: 0 30px 60px rgba(0,0,0,0.8), 0 0 50px rgba(255, 170, 0, 0.1); border-color: rgba(255, 170, 0, 0.6); }

.flag-bar { position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--neon-crimson); box-shadow: 0 0 20px var(--neon-crimson); }
.metric-card.is-low .flag-bar { background: var(--neon-gold); box-shadow: 0 0 20px var(--neon-gold); }

.metric-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; gap: 12px; }
.metric-cat { font: 500 11px/1.2 'JetBrains Mono', monospace; letter-spacing: 0.2em; text-transform: uppercase; color: var(--text-muted); margin: 0 0 8px; }
.metric-name { font-size: 1.25rem; font-weight: 500; margin: 0; color: var(--text-main); letter-spacing: -0.02em; }
.metric-value { display: flex; align-items: baseline; gap: 10px; margin: 0 0 8px; }

/* Typography for Numbers */
.metric-number { font: 300 4rem/1 'Space Grotesk', sans-serif; letter-spacing: -0.05em; color: var(--text-main); }
.metric-card.is-flagged .metric-number { color: var(--neon-crimson); text-shadow: 0 4px 30px rgba(255, 0, 60, 0.4); font-weight: 500; }
.metric-card.is-low .metric-number { color: var(--neon-gold); text-shadow: 0 4px 30px rgba(255, 170, 0, 0.3); font-weight: 500; }
.metric-unit { font: 400 1.1rem 'JetBrains Mono', monospace; color: var(--text-muted); }
.metric-raw { font: 500 1.4rem/1.5 'JetBrains Mono', monospace; color: var(--text-main); }

/* High-End Agency Range Track */
.range { margin-top: 28px; display: flex; flex-direction: column; gap: 12px; }
.range-track { height: 4px; background: rgba(255,255,255,0.08); border-radius: 999px; position: relative; overflow: visible; }
.range-safe { position: absolute; top: 0; bottom: 0; background: rgba(255, 255, 255, 0.2); border-radius: 999px; }
.range-marker { position: absolute; top: 50%; width: 14px; height: 14px; transform: translate(-50%, -50%); border-radius: 50%; background: var(--text-main); box-shadow: 0 0 15px rgba(255,255,255,0.5); z-index: 2; transition: left 1s var(--ease-cinematic); }
.metric-card.is-flagged .range-marker { background: var(--neon-crimson); box-shadow: 0 0 20px var(--neon-crimson); width: 16px; height: 16px; }
.metric-card.is-low .range-marker { background: var(--neon-gold); box-shadow: 0 0 20px var(--neon-gold); width: 16px; height: 16px; }
.range-labels { display: flex; justify-content: space-between; font: 500 11px 'JetBrains Mono', monospace; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; }

.metric-explain { padding-top: 22px; margin-top: 22px; border-top: 1px solid rgba(255,255,255,0.05); font-size: 1rem; line-height: 1.7; color: rgba(255,255,255,0.7); margin-bottom: 0; }
.metric-explain strong { color: var(--text-main); font-weight: 500; display: block; margin-bottom: 8px; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; }

/* Status Pills */
.pill { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 6px; font: 600 11px/1 'JetBrains Mono', monospace; letter-spacing: 0.15em; text-transform: uppercase; white-space: nowrap; border: 1px solid transparent; }
.pill svg { width: 14px; height: 14px; }
.pill-dot { position: relative; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.pill-normal { background: rgba(255, 255, 255, 0.05); color: var(--text-main); border-color: rgba(255, 255, 255, 0.2); }
.pill-high { background: rgba(255, 0, 60, 0.08); color: var(--neon-crimson); animation: breatheCrimson 3s ease-in-out infinite; }
.pill-low { background: rgba(255, 170, 0, 0.08); color: var(--neon-gold); border-color: rgba(255, 170, 0, 0.4); box-shadow: 0 0 20px rgba(255, 170, 0, 0.1); }

/* Dashboard Summary Panel */
.cl-summary { padding: 40px; display: grid; gap: 32px; margin: 36px 0 24px; border-radius: 24px; background: linear-gradient(145deg, rgba(20,20,25,0.8) 0%, rgba(10,10,12,0.9) 100%); border-top: 1px solid rgba(255,255,255,0.1); }
.cl-summary-text { font-size: 1.2rem; line-height: 1.8; color: rgba(255,255,255,0.85); margin: 0; font-weight: 300; }
.cl-stats { display: flex; gap: 20px; flex-wrap: wrap; }
.cl-stat { flex: 1; min-width: 160px; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.03); padding: 24px; border-radius: 16px; display: flex; flex-direction: column; gap: 12px; }
.cl-stat-label { font: 500 11px 'JetBrains Mono', monospace; letter-spacing: 0.2em; text-transform: uppercase; color: var(--text-muted); }
.cl-stat-value { font: 300 3.2rem/1 'Space Grotesk', sans-serif; color: var(--text-main); }
.cl-stat-normal .cl-stat-value { color: var(--text-main); }
.cl-stat-flagged .cl-stat-value { color: var(--neon-crimson); text-shadow: 0 0 30px rgba(255,0,60,0.4); font-weight: 500; }
.cl-flag-tag { background: transparent; color: var(--neon-crimson); padding: 8px 16px; border-radius: 8px; font-weight: 500; font-size: 0.9rem; border: 1px solid rgba(255,0,60,0.4); box-shadow: inset 0 0 15px rgba(255,0,60,0.1); }
.cl-flag-list { display: flex; gap: 12px; flex-wrap: wrap; }

/* Accordions / Doctor Panel */
.dq-list { display: flex; flex-direction: column; gap: 16px; margin-top: 24px; }
details.dq { margin-bottom: 0; background: rgba(10,10,12,0.7); }
details.dq > summary { padding: 24px 30px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; list-style: none; gap: 16px; transition: all 0.3s ease; }
details.dq > summary::-webkit-details-marker { display: none; }
details.dq[open] { border-color: rgba(255, 0, 60, 0.4); box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6); background: rgba(20,15,15,0.6); }
details.dq[open] > summary { border-bottom: 1px solid rgba(255,255,255,0.05); }
.dq-left { display: flex; align-items: center; gap: 20px; }
.dq-count { background: transparent; color: var(--text-main); border: 1px solid rgba(255,255,255,0.2); width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; border-radius: 50%; font: 400 15px 'JetBrains Mono', monospace; }
details.dq[open] .dq-count { border-color: var(--neon-crimson); color: var(--neon-crimson); box-shadow: 0 0 15px rgba(255,0,60,0.2); }
.dq-name { font-size: 1.2rem; font-weight: 500; color: var(--text-main); }
.dq-right { display: flex; align-items: center; gap: 20px; }
.dq-chev { width: 24px; height: 24px; color: var(--text-muted); transition: transform 0.5s var(--ease-spring); }
details.dq[open] .dq-chev { transform: rotate(180deg); color: var(--neon-crimson); }
.dq-body { padding: 30px; }
.dq-body ol { list-style: none; counter-reset: q; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 16px; }
.dq-body li { counter-increment: q; background: rgba(0,0,0,0.4); border: 1px solid transparent; padding: 20px 24px; border-radius: 12px; font-size: 1.1rem; color: rgba(255,255,255,0.8); display: flex; gap: 20px; line-height: 1.6; transition: border-color 0.3s ease; }
.dq-body li:hover { border-color: rgba(255,0,60,0.3); }
.dq-body li::before { content: counter(q, decimal-leading-zero); font: 500 14px/1.5 'JetBrains Mono', monospace; color: var(--neon-crimson); flex-shrink: 0; opacity: 0.8; }

/* Streamlit Tabs - Sleek Pill Design */
.stTabs [data-baseweb="tab-list"] { background: rgba(0,0,0,0.5); backdrop-filter: blur(20px); border-radius: 999px; padding: 6px; gap: 8px; border: 1px solid var(--border-glass); display: inline-flex; margin-bottom: 36px; }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 999px; padding: 12px 32px; transition: all 0.4s var(--ease-cinematic); border: none; color: var(--text-muted); font-weight: 500; font-size: 1.05rem; }
.stTabs [aria-selected="true"] { background: var(--neon-crimson) !important; color: #fff !important; box-shadow: 0 4px 20px rgba(255,0,60,0.4); }
.stTabs [data-baseweb="tab-highlight"] { display: none; }

/* Buttons & Inputs */
.stButton > button, .stDownloadButton > button {
    background: var(--text-main) !important; color: #000 !important;
    border: none !important; border-radius: 8px !important; font-weight: 600 !important;
    padding: 0.8rem 1.8rem !important; font-size: 1.05rem !important;
    transition: all 0.4s var(--ease-cinematic) !important; letter-spacing: 0.02em !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-4px) !important; background: var(--neon-crimson) !important; color: #fff !important;
    box-shadow: 0 10px 30px rgba(255, 0, 60, 0.4) !important;
}
.st-key-change_prefs button { background: transparent !important; color: var(--text-main) !important; border: 1px solid rgba(255,255,255,0.15) !important; box-shadow: none !important; }
.st-key-change_prefs button:hover { background: rgba(255,255,255,0.05) !important; border-color: rgba(255,255,255,0.4) !important; transform: none !important; }

/* Floating Spatial Onboarding */
.ob-card { animation: cinematicReveal 1s var(--ease-cinematic) both, floatSpatial 8s ease-in-out infinite; padding: 60px 48px; text-align: center; border: 1px solid rgba(255, 0, 60, 0.15); box-shadow: 0 30px 80px rgba(0,0,0,0.8), inset 0 0 60px rgba(255, 0, 60, 0.03); margin-top: 60px; background: linear-gradient(180deg, rgba(20,20,25,0.8) 0%, rgba(10,10,12,0.9) 100%); }
.ob-card .cl-logo { margin: 0 auto 32px; width: 80px; height: 80px; border-radius: 24px; box-shadow: 0 0 40px rgba(255, 0, 60, 0.3); border-color: var(--neon-crimson); }
.ob-card .cl-logo svg { width: 38px; height: 38px; }
.ob-step { display: inline-block; font: 500 11px 'JetBrains Mono', monospace; letter-spacing: 0.3em; text-transform: uppercase; color: var(--neon-crimson); margin-bottom: 20px; background: rgba(255,0,60,0.08); padding: 8px 20px; border-radius: 999px; border: 1px solid rgba(255,0,60,0.2); }
.ob-title { font-size: 2.6rem; font-weight: 600; color: var(--text-main); margin: 0 0 20px; letter-spacing: -0.04em; }
.ob-desc { font-size: 1.2rem; line-height: 1.7; color: rgba(255,255,255,0.7); margin: 0 auto; max-width: 540px; font-weight: 300; }

.cl-footer { margin-top: 80px; padding-top: 30px; border-top: 1px solid rgba(255,255,255,0.05); text-align: center; font-size: 0.9rem; color: rgba(255,255,255,0.3); letter-spacing: 0.02em; animation: cinematicReveal 1s var(--ease-cinematic) 0.5s both; }
</style>
"""
render_html(THEME_CSS)

# Inline SVG Icons
ICON_LOGO = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h4l3-8 4 16 3-8h4"/></svg>'
ICON_UP = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>'
ICON_DOWN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>'
ICON_CHEV = '<svg class="dq-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>'

# Session state
if "onboarding_step" not in st.session_state:
    st.session_state.onboarding_step = 1
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = "English"
if "selected_diet" not in st.session_state:
    st.session_state.selected_diet = "Vegetarian"
if "analysis_cache" not in st.session_state:
    st.session_state.analysis_cache = {}

TEXTS = {
    "English": {
        "title": "ClarityLab AI",
        "tagline": "Personalized Diagnostic Medical Interpreter",
        "system_status": "Groq LPU Diagnostic Engine Active",
        "lang_modal_title": "Choose Your Language",
        "lang_modal_desc": "Select the language you feel most comfortable reading your medical report analysis in:",
        "lang_modal_btn": "Proceed to Diet Selection →",
        "diet_modal_title": "Choose Dietary Preference",
        "diet_modal_desc": "To give you exact, realistic food solutions from Indian cuisine, please select your diet profile:",
        "diet_modal_btn": "Launch Health Workspace →",
        "radio_lang_label": "Preferred Language",
        "radio_diet_label": "Diet Preference",
        "veg_opt": "Vegetarian",
        "nonveg_opt": "Non-Vegetarian",
        "change_prefs": "Adjust Settings",
        "selected_lang_label": "Language:",
        "diet_profile_label": "Diet Plan:",
        "upload_header": "Upload Medical Lab Report",
        "upload_desc": "Upload your lab test report in PDF or image format (PNG, JPG). The engine reads, evaluates, and explains your biomarkers instantly.",
        "upload_label": "Upload PDF or Image File",
        "summary_title": "Diagnostic Health Overview",
        "missing_title": "Biological Breakdown of Your Biomarkers",
        "recorded_val": "Observed Test Value:",
        "what_happening": "What this means for your body:",
        "food_title": "Evidence-Based Food Suggestions",
        "questions_title": "Important Questions for Your Next Doctor Visit",
        "download_questions": "Save Doctor Questions (.txt)",
        "disclaimer": "Clinical Disclaimer: ClarityLab AI is designed for informational and educational support only. It does not replace medical advice, clinical diagnosis, or prescriptions from a licensed healthcare physician.",
        "pill_normal": "Normal", "pill_high": "High", "pill_low": "Low",
        "stat_total": "Biomarkers", "stat_normal": "In range", "stat_flagged": "Needs attention",
        "range_low": "Low", "range_high": "High",
        "tab_biomarkers": "Biomarkers", "tab_food": "Nutrition", "tab_doctor": "Doctor questions",
        "questions_hint": "Flagged biomarkers are listed first. Tap a biomarker to expand its questions.",
        "no_results": "No medical biomarkers could be extracted from this document. Please ensure the scan is clear.",
        "step": "Step", "general_questions": "General questions",
    },
    "हिंदी": {
        "title": "क्लैरिटीलैब एआई",
        "tagline": "सरल और सटीक मेडिकल रिपोर्ट विश्लेषक",
        "system_status": "ग्रोक एआई डायग्नोस्टिक इंजन सक्रिय है",
        "lang_modal_title": "अपनी भाषा चुनें (Select Language)",
        "lang_modal_desc": "अपनी मेडिकल रिपोर्ट को आसानी से समझने के लिए अपनी पसंदीदा भाषा चुनें:",
        "lang_modal_btn": "आहार चयन के लिए आगे बढ़ें →",
        "diet_modal_title": "खान-पान की आदत चुनें (Diet Preference)",
        "diet_modal_desc": "आपको आपकी जीवनशैली के अनुसार सटीक भोजन और परहेज बताने के लिए अपना आहार चुनें:",
        "diet_modal_btn": "हेल्थ डैशबोर्ड खोलें →",
        "radio_lang_label": "पसंदीदा भाषा",
        "radio_diet_label": "आहार विकल्प",
        "veg_opt": "शाकाहारी (Vegetarian)",
        "nonveg_opt": "मांसाहारी (Non-Vegetarian)",
        "change_prefs": "भाषा / आहार बदलें",
        "selected_lang_label": "भाषा:",
        "diet_profile_label": "आहार शैली:",
        "upload_header": "अपनी मेडिकल लैब रिपोर्ट अपलोड करें",
        "upload_desc": "किसी भी फॉर्मेट (PDF या फोटो) में अपनी रिपोर्ट अपलोड करें। ऐप आपकी रिपोर्ट को पढ़कर सरल हिंदी में जानकारी देगा।",
        "upload_label": "PDF या फोटो फाइल अपलोड करें",
        "summary_title": "स्वास्थ्य रिपोर्ट का मुख्य सारांश",
        "missing_title": "आपके शरीर के अंगों में क्या हो रहा है",
        "recorded_val": "रिपोर्ट में दर्ज मात्रा:",
        "what_happening": "सरल शब्दों में इसका अर्थ:",
        "food_title": "खाने योग्य पोषक आहार और घरेलू परहेज",
        "questions_title": "अगली बार डॉक्टर से पूछने योग्य जरूरी सवाल",
        "download_questions": "सवालों की सूची डाउनलोड करें (.txt)",
        "disclaimer": "चिकित्सा अस्वीकरण: क्लैरिटीलैब एआई केवल आपकी जानकारी और समझ के लिए है। किसी भी चिकित्सीय निर्णय या दवा बदलने से पहले योग्य डॉक्टर से सलाह जरूर लें।",
        "pill_normal": "सामान्य", "pill_high": "अधिक", "pill_low": "कम",
        "stat_total": "कुल पैरामीटर", "stat_normal": "सामान्य सीमा में", "stat_flagged": "ध्यान दें",
        "range_low": "न्यूनतम", "range_high": "अधिकतम",
        "tab_biomarkers": "बायोमार्कर", "tab_food": "आहार", "tab_doctor": "डॉक्टर से सवाल",
        "questions_hint": "असामान्य पैरामीटर पहले दिखाए गए हैं। सवाल देखने के लिए किसी पैरामीटर पर टैप करें।",
        "no_results": "इस फाइल से कोई मेडिकल पैरामीटर नहीं पढ़ा जा सका। कृपया स्पष्ट स्कैन अपलोड करें।",
        "step": "चरण", "general_questions": "सामान्य सवाल",
    },
    "ગુજરાતી": {
        "title": "ક્લેરિટીલેબ એઆઈ",
        "tagline": "તબીબી લેબ રિપોર્ટનું સરળ વિશ્લેષણ",
        "system_status": "ગ્રોક એઆઈ સિસ્ટમ કાર્યરત છે",
        "lang_modal_title": "તમારી ભાષા પસંદ કરો",
        "lang_modal_desc": "તમારા મેડિકલ રિપોર્ટને સરળતાથી સમજવા માટે તમારી અનુકૂળ ભાષા પસંદ કરો:",
        "lang_modal_btn": "ખોરાક પસંદ કરવા માટે આગળ વધો →",
        "diet_modal_title": "ખોરાકની પસંદગી નક્કી કરો",
        "diet_modal_desc": "તમારા રોજીંદા ભોજન મુજબ યોગ્ય આહાર સૂચવવા માટે પસંદગી કરો:",
        "diet_modal_btn": "હેલ્થ ડેશબોર્ડ શરૂ કરો →",
        "radio_lang_label": "ભાષા",
        "radio_diet_label": "ખોરાકની રીત",
        "veg_opt": "શાકાહારી (Vegetarian)",
        "nonveg_opt": "માસાહારી (Non-Vegetarian)",
        "change_prefs": "સેટિંગ્સ બદલો",
        "selected_lang_label": "પસંદ કરેલી ભાષા:",
        "diet_profile_label": "આહાર પ્રોફાઇલ:",
        "upload_header": "તમારો લેબ રિપોર્ટ અપલોડ કરો",
        "upload_desc": "કોઈ પણ ફોર્મેટમાં (PDF અથવા ફોટો) રિપોર્ટ અપલોડ કરો. રિપોર્ટ વાંચીને તરત સરળ ગુજરાતીમાં સલાહ મળશે.",
        "upload_label": "PDF અથવા ફોટો ફાઇલ અપલોડ કરો",
        "summary_title": "આરોગ્ય રિપોર્ટનો મુખ્ય સારાંશ",
        "missing_title": "તમારા શરીરમાં શું ફેરફાર થઈ રહ્યો છે",
        "recorded_val": "રિપોર્ટમાં નોંધાયેલ પ્રમાણ:",
        "what_happening": "સરળ શબ્દોમાં સમજૂતી:",
        "food_title": "ખાવા યોગ્ય યોગ્ય ખોરાક અને પરહેજ",
        "questions_title": "ડૉક્ટરને પૂછવા માટેના ખાસ પ્રશ્નો",
        "download_questions": "પ્રશ્નોની યાદી સાચવો (.txt)",
        "disclaimer": "તબીબી ડિસ્ક્લેમર: ક્લેરિટીલેબ એઆઈ ફક્ત દર્દીની જાણકારી માટે છે. દવા કે સારવાર બદલતા પહેલાં ફેમિલી ડૉક્ટરની સલાહ લેવી અનિવાર્ય છે.",
        "pill_normal": "સામાન્ય", "pill_high": "વધુ", "pill_low": "ઓછું",
        "stat_total": "કુલ પેરામીટર", "stat_normal": "સામાન્ય મર્યાદામાં", "stat_flagged": "ધ્યાન આપો",
        "range_low": "ન્યૂનતમ", "range_high": "મહત્તમ",
        "tab_biomarkers": "બાયોમાર્કર", "tab_food": "આહાર", "tab_doctor": "ડૉક્ટરને પ્રશ્નો",
        "questions_hint": "અસામાન્ય પેરામીટર પહેલા બતાવ્યા છે. પ્રશ્નો જોવા માટે પેરામીટર પર ટેપ કરો.",
        "no_results": "આ ફાઇલમાંથી કોઈ મેડિકલ પેરામીટર વાંચી શકાયા નહીં. કૃપા કરીને સ્પષ્ટ સ્કેન અપલોડ કરો.",
        "step": "પગલું", "general_questions": "સામાન્ય પ્રશ્નો",
    }
}
L = TEXTS[st.session_state.selected_lang]

# ---------------------------------------------------------
# Document Text Extraction
# ---------------------------------------------------------
def extract_raw_file_text(file_bytes, filename, mime_type):
    extracted_text = ""
    is_pdf = "pdf" in mime_type.lower() or filename.lower().endswith(".pdf")

    # Tell pytesseract exactly where the Tesseract program is installed
    if pytesseract is not None:
        if sys.platform.startswith('win'):
            # Local Windows path
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        else:
            # On Streamlit Cloud (Linux), Tesseract installs to the system path automatically
            pass

    if is_pdf and pypdf is not None:
        try:
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page in pdf_reader.pages:
                t = page.extract_text()
                if t: extracted_text += t + "\n"
        except Exception:
            pass

    if not extracted_text.strip():
        if is_pdf and pdf2image is not None and pytesseract is not None:
            try:
                for img in pdf2image.convert_from_bytes(file_bytes):
                    extracted_text += pytesseract.image_to_string(img) + "\n"
            except Exception as e:
                print(f"PDF OCR Error: {e}") # Prints error to your terminal
        elif not is_pdf and pytesseract is not None:
            try:
                extracted_text = pytesseract.image_to_string(Image.open(io.BytesIO(file_bytes)))
            except Exception as e:
                print(f"Image OCR Error: {e}") # Prints error to your terminal

    return extracted_text

# ---------------------------------------------------------
# GROQ AI LPU ENGINE (1,000+ daily runs, sub-second speed)
# ---------------------------------------------------------
def analyze_report_with_groq(file_bytes, filename, mime_type, target_lang, target_diet, api_key):
    try:
        if Groq is None:
            return None, "groq library not installed. Run: pip install groq"

        extracted_text = extract_raw_file_text(file_bytes, filename, mime_type)
        if not extracted_text.strip():
            return None, "Could not extract text from document. Please ensure it is a clear scan."

        client = Groq(api_key=api_key.strip())

        prompt = f"""
You are an expert clinical laboratory analyst and medical AI consultant.
Analyze this medical lab report text with maximum clinical precision:

--- REPORT TEXT ---
{extracted_text}
--- END REPORT ---

Requirements:
- Target Language: {target_lang} (ALL text fields MUST be in {target_lang})
- Dietary Profile: {target_diet}

STRICT CLINICAL RULES:
1. Ignore Lab IDs, doctor registration numbers, invoice numbers, and patient address details.
2. Extract all clinical biomarkers (Fasting Glucose, HbA1c, Cholesterol, Triglycerides, Hemoglobin, Creatinine, Bilirubin, TSH, etc.).
3. For each biomarker:
   - "name": Clean parameter title translated to {target_lang}.
   - "category": Short category (e.g. Metabolic, Lipid, Thyroid, Blood Count, Liver, Kidney) translated to {target_lang}.
   - "value": Observed measured value with unit and reference range.
   - "numeric_value": Float value, or null.
   - "unit": Unit string, or "".
   - "ref_low": Lower bound float, or null.
   - "ref_high": Upper bound float, or null.
   - "status_code": "normal" | "high" | "low".
   - "status": Translated status word.
   - "badge": "badge-attention" if High/Low, or "badge-normal" if Normal.
   - "explanation": Simple human language biological explanation in {target_lang}.
   - "food_remedies": Specific Indian food remedies aligned with {target_diet} in {target_lang}.
   - "questions_for_doctor": 2-3 specific clinical questions in {target_lang}.

4. "summary": 2-3 sentence overview of overall report in {target_lang}.

Return ONLY a valid JSON object matching this schema:
{{
  "summary": "Full summary in {target_lang}",
  "parameters": [
    {{
      "name": "string",
      "category": "string",
      "value": "string",
      "numeric_value": 0,
      "unit": "string",
      "ref_low": 0,
      "ref_high": 0,
      "status_code": "normal | high | low",
      "status": "string",
      "badge": "badge-attention OR badge-normal",
      "explanation": "string",
      "food_remedies": "string",
      "questions_for_doctor": ["string", "string"]
    }}
  ]
}}
"""
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are a clinical diagnostic analysis engine. Respond strictly in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        parsed_data = json.loads(response.choices[0].message.content)
        return parsed_data, None

    except Exception as e:
        return None, f"Groq Execution Error: {str(e)}"

# ---------------------------------------------------------
# Normalization & UI Builders
# ---------------------------------------------------------
NUM_RE = r"-?\d+(?:\.\d+)?"

def to_float(v):
    try:
        return float(v) if v is not None and v != "" else None
    except (TypeError, ValueError):
        return None

def status_code_of(param) -> str:
    code = str(param.get("status_code", "")).strip().lower()
    if code in ("normal", "high", "low"):
        return code
    text = str(param.get("status", "")).lower()
    if any(w in text for w in ("low", "कम", "ઓછું", "below")):
        return "low"
    if any(w in text for w in ("high", "अधिक", "વધુ", "above", "elevated")):
        return "high"
    return "normal"

def normalise(param) -> dict:
    raw_value = str(param.get("value", "") or "")
    value = to_float(param.get("numeric_value"))
    low = to_float(param.get("ref_low"))
    high = to_float(param.get("ref_high"))
    unit = str(param.get("unit", "") or "")

    if value is None:
        m = re.search(NUM_RE, raw_value)
        value = float(m.group()) if m else None

    if low is None and high is None:
        ref_part = raw_value.split("(", 1)[1] if "(" in raw_value else ""
        rng = re.search(rf"({NUM_RE})\s*(?:-|–|to)\s*({NUM_RE})", ref_part)
        if rng:
            low, high = float(rng.group(1)), float(rng.group(2))

    questions = param.get("questions_for_doctor") or []
    if isinstance(questions, str):
        questions = [q.strip() for q in questions.split("\n") if q.strip()]

    return {
        "name": param.get("name", "Biomarker"),
        "category": param.get("category", ""),
        "raw_value": raw_value,
        "value": value,
        "unit": unit,
        "low": low,
        "high": high,
        "code": status_code_of(param),
        "explanation": param.get("explanation", ""),
        "food": param.get("food_remedies", ""),
        "questions": questions,
    }

def fmt_num(n: float) -> str:
    return f"{n:g}" if abs(n) < 1e6 else f"{n:.3g}"

def status_pill(code: str) -> str:
    icon = ICON_UP if code == "high" else ICON_DOWN if code == "low" else ""
    label = esc(L[f"pill_{code}"])
    return (
        f'<span class="pill pill-{code}" role="status" aria-label="{label}">'
        f'<span class="pill-dot" aria-hidden="true"></span>{label}{icon}</span>'
    )

def range_bar(b: dict) -> str:
    value, low, high = b["value"], b["low"], b["high"]
    if value is None or high is None:
        return ""
    low = low if low is not None else 0.0
    span = (high - low) or max(abs(high), 1.0)
    lo_edge = max(0.0, low - span * 0.5) if low >= 0 else low - span * 0.5
    hi_edge = high + span * 0.5

    def pct(n):
        return min(100.0, max(0.0, (n - lo_edge) / (hi_edge - lo_edge) * 100))

    return f"""
    <div class="range" aria-hidden="true">
        <div class="range-track">
            <div class="range-safe" style="left:{pct(low):.1f}%;width:{pct(high) - pct(low):.1f}%"></div>
            <div class="range-marker" style="left:{pct(value):.1f}%"></div>
        </div>
        <div class="range-labels"><span>{esc(L['range_low'])} {fmt_num(low)}</span><span>{esc(L['range_high'])} {fmt_num(high)}</span></div>
    </div>
    """

def metric_card(b: dict, index: int) -> str:
    state_cls = {"high": "is-flagged", "low": "is-low"}.get(b["code"], "")
    flag_bar = '<span class="flag-bar" aria-hidden="true"></span>' if b["code"] != "normal" else ""
    category = f'<p class="metric-cat">{esc(b["category"])}</p>' if b["category"] else ""

    if b["value"] is not None:
        value_html = f'<span class="metric-number">{fmt_num(b["value"])}</span><span class="metric-unit">{esc(b["unit"])}</span>'
    else:
        value_html = f'<span class="metric-raw">{esc(b["raw_value"])}</span>'

    explain = ""
    if b["explanation"]:
        explain = f'<p class="metric-explain"><strong>{esc(L["what_happening"])}</strong>{esc(b["explanation"])}</p>'

    return f"""
    <article class="metric-card {state_cls}" style="animation-delay:{index * 120}ms">
        {flag_bar}
        <header class="metric-head">
            <div>{category}<h3 class="metric-name">{esc(b["name"])}</h3></div>
            {status_pill(b["code"])}
        </header>
        <p class="metric-value">{value_html}</p>
        {range_bar(b)}
        {explain}
    </article>
    """

def summary_panel(summary: str, biomarkers: list) -> str:
    total = len(biomarkers)
    flagged = [b for b in biomarkers if b["code"] != "normal"]
    normal = total - len(flagged)
    tags = "".join(f'<span class="cl-flag-tag">{esc(b["name"])}</span>' for b in flagged)
    tag_row = f'<div class="cl-flag-list">{tags}</div>' if tags else ""

    return f"""
    <section class="cl-summary">
        <div>
            <p class="cl-eyebrow">{esc(L['summary_title'])}</p>
            <p class="cl-summary-text">{esc(summary)}</p>
        </div>
        <div class="cl-stats">
            <div class="cl-stat"><span class="cl-stat-label">{esc(L['stat_total'])}</span><span class="cl-stat-value">{total}</span></div>
            <div class="cl-stat cl-stat-normal"><span class="cl-stat-label">{esc(L['stat_normal'])}</span><span class="cl-stat-value">{normal}</span></div>
            <div class="cl-stat cl-stat-flagged"><span class="cl-stat-label">{esc(L['stat_flagged'])}</span><span class="cl-stat-value">{len(flagged)}</span></div>
        </div>
        {tag_row}
    </section>
    """

def question_accordion(title: str, questions: list, code, is_open: bool, index: int) -> str:
    items = "".join(f"<li>{esc(q)}</li>" for q in questions)
    pill = status_pill(code) if code else ""
    return f"""
    <details class="dq" {'open' if is_open else ''} style="animation-delay:{index * 100}ms">
        <summary>
            <span class="dq-left"><span class="dq-count">{len(questions)}</span><span class="dq-name">{esc(title)}</span></span>
            <span class="dq-right">{pill}{ICON_CHEV}</span>
        </summary>
        <div class="dq-body"><ol>{items}</ol></div>
    </details>
    """

# ---------------------------------------------------------
# STEP 1: ONBOARDING MODAL 1 - LANGUAGE
# ---------------------------------------------------------
LANG_OPTIONS = ["English", "हिंदी", "ગુજરાતી"]

if st.session_state.onboarding_step == 1:
    _, center, _ = st.columns([1, 1.8, 1])
    with center:
        render_html(f"""
        <div class="ob-card">
            <div class="cl-logo">{ICON_LOGO}</div>
            <span class="ob-step">{esc(L['step'])} 1 / 2</span>
            <h2 class="ob-title">{esc(L['lang_modal_title'])}</h2>
            <p class="ob-desc">{esc(L['lang_modal_desc'])}</p>
        </div>
        """)
        selected_l = st.radio(
            L["radio_lang_label"],
            LANG_OPTIONS,
            index=LANG_OPTIONS.index(st.session_state.selected_lang),
            label_visibility="collapsed",
        )
        if st.button(L["lang_modal_btn"], use_container_width=True):
            st.session_state.selected_lang = selected_l
            st.session_state.onboarding_step = 2
            st.rerun()

# ---------------------------------------------------------
# STEP 2: ONBOARDING MODAL 2 - DIET
# ---------------------------------------------------------
elif st.session_state.onboarding_step == 2:
    _, center, _ = st.columns([1, 1.8, 1])
    with center:
        render_html(f"""
        <div class="ob-card">
            <div class="cl-logo">{ICON_LOGO}</div>
            <span class="ob-step">{esc(L['step'])} 2 / 2</span>
            <h2 class="ob-title">{esc(L['diet_modal_title'])}</h2>
            <p class="ob-desc">{esc(L['diet_modal_desc'])}</p>
        </div>
        """)
        selected_d = st.radio(
            L["radio_diet_label"],
            [L["veg_opt"], L["nonveg_opt"]],
            index=0 if st.session_state.selected_diet == "Vegetarian" else 1,
            label_visibility="collapsed",
        )
        if st.button(L["diet_modal_btn"], use_container_width=True):
            st.session_state.selected_diet = "Vegetarian" if selected_d == L["veg_opt"] else "Non-Vegetarian"
            st.session_state.onboarding_step = 3
            st.rerun()

# ---------------------------------------------------------
# STEP 3: MAIN MEDICAL DASHBOARD
# ---------------------------------------------------------
else:
    head_col, action_col = st.columns([4, 1], vertical_alignment="center")
    with head_col:
        render_html(f"""
        <header class="cl-header">
            <div class="cl-brand">
                <span class="cl-logo">{ICON_LOGO}</span>
                <div>
                    <h1 class="cl-title">{esc(L['title'])}</h1>
                    <p class="cl-tagline">{esc(L['tagline'])}</p>
                </div>
            </div>
            <span class="cl-chip"><span class="cl-chip-dot" aria-hidden="true"></span>{esc(L['system_status'])}</span>
        </header>
        """)
    with action_col:
        if st.button(L["change_prefs"], key="change_prefs", use_container_width=True):
            st.session_state.onboarding_step = 1
            st.rerun()

    translated_diet = L["veg_opt"] if st.session_state.selected_diet == "Vegetarian" else L["nonveg_opt"]
    render_html(f"""
    <div class="cl-prefs">
        <span>{esc(L['selected_lang_label'])} <strong>{esc(st.session_state.selected_lang)}</strong></span>
        <span>{esc(L['diet_profile_label'])} <strong>{esc(translated_diet)}</strong></span>
    </div>
    """)

    # Secure Automatic Groq Key Pipeline (Reads from secrets.toml or environment)
    groq_api_key = ""
    try:
        groq_api_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass
    groq_api_key = groq_api_key or os.environ.get("GROQ_API_KEY", "")

    render_html(f"""
    <div style="margin-top:20px; animation: cinematicReveal 1s var(--ease-cinematic) 0.15s both;">
        <p class="cl-eyebrow">01</p>
        <h2 class="cl-h2">{esc(L['upload_header'])}</h2>
        <p class="cl-sub" style="margin-bottom:16px; color: rgba(255,255,255,0.6);">{esc(L['upload_desc'])}</p>
    </div>
    """)
    uploaded_file = st.file_uploader(L["upload_label"], type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed")

    parsed_report_data = None
    error_notice = None

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "application/pdf"
        cache_key = (
            hashlib.sha256(file_bytes).hexdigest(),
            st.session_state.selected_lang,
            st.session_state.selected_diet,
        )
        parsed_report_data = st.session_state.analysis_cache.get(cache_key)

        if parsed_report_data is None:
            with st.spinner("Analyzing report biomarkers and clinical values with Groq..."):
                parsed_report_data, error_notice = analyze_report_with_groq(
                    file_bytes, uploaded_file.name, mime_type,
                    st.session_state.selected_lang, st.session_state.selected_diet,
                    groq_api_key
                )

            if parsed_report_data:
                st.session_state.analysis_cache[cache_key] = parsed_report_data

        if error_notice and not parsed_report_data:
            st.error(error_notice)
        elif not parsed_report_data:
            render_html(f'<div class="cl-empty" style="margin-top:20px;">{esc(L["no_results"])}</div>')

    # -----------------------------------------------------
    # Render Diagnostic Results
    # -----------------------------------------------------
    if parsed_report_data:
        biomarkers = [normalise(p) for p in parsed_report_data.get("parameters", [])]
        order = {"high": 0, "low": 1, "normal": 2}
        biomarkers_sorted = sorted(biomarkers, key=lambda b: order[b["code"]])

        render_html(summary_panel(parsed_report_data.get("summary", ""), biomarkers))

        tab_bio, tab_food, tab_doc = st.tabs([
            f"{L['tab_biomarkers']} ({len(biomarkers)})",
            L["tab_food"],
            L["tab_doctor"],
        ])

        with tab_bio:
            cards = "".join(metric_card(b, i) for i, b in enumerate(biomarkers_sorted))
            render_html(f"""
            <section aria-label="{esc(L['missing_title'])}">
                <h2 class="cl-h2" style="margin-top:16px; animation: cinematicReveal 1s var(--ease-cinematic) both;">{esc(L['missing_title'])}</h2>
                <div class="metric-grid">{cards}</div>
            </section>
            """)

        with tab_food:
            food_cards = "".join(
                f"""
                <article class="food-card" style="animation-delay:{i * 120}ms">
                    <header class="food-head"><h3 class="food-title">{esc(b['name'])}</h3>{status_pill(b['code'])}</header>
                    <p class="food-body">{esc(b['food'])}</p>
                </article>
                """
                for i, b in enumerate(biomarkers_sorted) if b["food"]
            )
            render_html(f"""
            <section aria-label="{esc(L['food_title'])}">
                <h2 class="cl-h2" style="margin-top:16px; animation: cinematicReveal 1s var(--ease-cinematic) both;">{esc(L['food_title'])}</h2>
                <div class="metric-grid">{food_cards}</div>
            </section>
            """)

        with tab_doc:
            groups = [(b["name"], b["questions"], b["code"]) for b in biomarkers_sorted if b["questions"]]
            top_level = parsed_report_data.get("questions") or []
            if not groups and top_level:
                groups = [(L["general_questions"], top_level, None)]

            if groups:
                accordions = "".join(
                    question_accordion(title, qs, code, is_open=(i == 0), index=i)
                    for i, (title, qs, code) in enumerate(groups)
                )
                render_html(f"""
                <section aria-label="{esc(L['questions_title'])}">
                    <h2 class="cl-h2" style="margin-top:16px; animation: cinematicReveal 1s var(--ease-cinematic) both;">{esc(L['questions_title'])}</h2>
                    <p class="cl-tagline" style="margin-bottom:24px; animation: cinematicReveal 1s var(--ease-cinematic) 0.1s both;">{esc(L['questions_hint'])}</p>
                    <div class="dq-list">{accordions}</div>
                </section>
                """)

                q_text = "\n\n".join(
                    f"{title}\n" + "\n".join(f"  {n}. {q}" for n, q in enumerate(qs, 1))
                    for title, qs, _ in groups
                )
                st.download_button(
                    label=L["download_questions"],
                    data=q_text,
                    file_name=f"doctor_questions_{st.session_state.selected_lang.lower()}.txt",
                    mime="text/plain",
                )

    render_html(f'<footer class="cl-footer">{esc(L["disclaimer"])}</footer>')
