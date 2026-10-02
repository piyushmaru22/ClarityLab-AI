import base64
import hashlib
import html
import io
import json
import os
import re
import sys
import textwrap
import time

import streamlit as st
from PIL import Image

# ---------------------------------------------------------
# Third-Party Parsers & AI Clients
# ---------------------------------------------------------
try:
    from groq import Groq
except ImportError:
    Groq = None

# Primary Table-Aware PDF Reader
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# Secondary PDF Reader Fallback
try:
    import pypdf
except ImportError:
    pypdf = None

# OCR Fallbacks
try:
    import pytesseract
    if sys.platform.startswith('win'):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except ImportError:
    pytesseract = None

try:
    import pdf2image
except ImportError:
    pdf2image = None

# ---------------------------------------------------------
# Page Configuration
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
# Theme: Apple/Linear-Grade Glassmorphism 2.0 UI
# ---------------------------------------------------------
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
    --bg-deep: #050914;
    --surface-glass: rgba(15, 21, 35, 0.45);
    --surface-glass-hover: rgba(20, 28, 45, 0.65);
    --border-glass: rgba(255, 255, 255, 0.08);
    --text-main: #ffffff;
    --text-muted: #8b9bb4;
    --neon-cyan: #00e5ff;
    --neon-emerald: #00e676;
    --neon-coral: #ff1744;
    --neon-amber: #ffc400;
    --ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
    --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
}

html, body, .stApp, [class*="css"], .stMarkdown, button, input, label {
    font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp { 
    background: var(--bg-deep) !important; 
    color: var(--text-main); 
}
.stApp::before { 
    content: ""; 
    position: fixed; 
    inset: 0; 
    background: radial-gradient(circle at 15% 0%, rgba(0, 229, 255, 0.06) 0%, transparent 40%), 
                radial-gradient(circle at 85% 100%, rgba(0, 230, 118, 0.04) 0%, transparent 40%); 
    z-index: -1; 
    pointer-events: none; 
}

header[data-testid="stHeader"] { background: transparent !important; }
.block-container { max-width: 1200px; padding-top: 2rem !important; padding-bottom: 4rem !important; }

@keyframes cardRise { 
    from { opacity: 0; transform: translateY(24px) scale(0.98); } 
    to { opacity: 1; transform: translateY(0) scale(1); } 
}
@keyframes floatSlow { 
    0%, 100% { transform: translateY(0); } 
    50% { transform: translateY(-8px); } 
}
@keyframes breatheCoral { 
    0%, 100% { box-shadow: 0 0 12px rgba(255, 23, 68, 0.25); border-color: rgba(255, 23, 68, 0.4); } 
    50% { box-shadow: 0 0 28px rgba(255, 23, 68, 0.6); border-color: rgba(255, 23, 68, 0.9); } 
}
@keyframes breatheAmber { 
    0%, 100% { box-shadow: 0 0 12px rgba(255, 196, 0, 0.25); border-color: rgba(255, 196, 0, 0.4); } 
    50% { box-shadow: 0 0 28px rgba(255, 196, 0, 0.6); border-color: rgba(255, 196, 0, 0.9); } 
}
@keyframes scanline { 
    0% { top: 0; opacity: 0; } 
    15% { opacity: 1; } 
    85% { opacity: 1; } 
    100% { top: 100%; opacity: 0; } 
}
@keyframes dotPulse { 
    0% { box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.5); } 
    70% { box-shadow: 0 0 0 12px rgba(0, 229, 255, 0); } 
    100% { box-shadow: 0 0 0 0 rgba(0, 229, 255, 0); } 
}

.cl-title { font-size: 2.2rem; font-weight: 700; letter-spacing: -0.04em; margin: 0; background: linear-gradient(135deg, #ffffff 0%, #a3b1c6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.cl-tagline { font-size: 1.05rem; color: var(--text-muted); margin-top: 4px; font-weight: 500; }
.cl-h2 { font-size: 1.6rem; font-weight: 700; letter-spacing: -0.03em; color: var(--text-main); margin-bottom: 8px; }
.cl-eyebrow { font: 600 12px/1 'JetBrains Mono', monospace; letter-spacing: 0.2em; text-transform: uppercase; color: var(--neon-cyan); margin-bottom: 8px; }

.cl-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 24px; border-bottom: 1px solid var(--border-glass); margin-bottom: 24px; flex-wrap: wrap; gap: 20px; }
.cl-brand { display: flex; align-items: center; gap: 20px; }

.cl-logo { 
    width: 60px; height: 60px; 
    display: flex; align-items: center; justify-content: center; 
    background: rgba(0, 10, 20, 0.5); 
    border: 1px solid rgba(0, 229, 255, 0.4); 
    border-radius: 18px; 
    box-shadow: 0 8px 30px rgba(0, 229, 255, 0.25), inset 0 0 20px rgba(0,229,255,0.1); 
    backdrop-filter: blur(12px);
}
.cl-logo img, .cl-logo svg { width: 44px; height: 44px; }

.cl-chip { display: inline-flex; align-items: center; gap: 10px; padding: 8px 18px; border-radius: 999px; background: rgba(0, 229, 255, 0.05); border: 1px solid rgba(0, 229, 255, 0.3); font: 500 13px 'JetBrains Mono', monospace; color: var(--neon-cyan); box-shadow: 0 0 20px rgba(0, 229, 255, 0.1); backdrop-filter: blur(8px); }
.cl-chip-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--neon-cyan); animation: dotPulse 2s infinite; }

.cl-prefs { display: flex; gap: 24px; flex-wrap: wrap; margin: 16px 0 8px; font-size: 0.95rem; color: var(--text-muted); }
.cl-prefs strong { color: var(--text-main); font-weight: 600; padding: 4px 10px; background: rgba(255,255,255,0.05); border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); }

[data-testid="stFileUploaderDropzone"] { 
    position: relative; overflow: hidden; background: var(--surface-glass) !important; 
    border: 1px dashed rgba(0, 229, 255, 0.4) !important; border-radius: 20px !important; 
    transition: all 0.3s var(--ease-out) !important; backdrop-filter: blur(12px); 
}
[data-testid="stFileUploaderDropzone"]:hover { 
    border-color: var(--neon-cyan) !important; background: var(--surface-glass-hover) !important; 
    box-shadow: 0 0 40px rgba(0, 229, 255, 0.15) !important; 
}

.metric-card, .food-card, .cl-summary, .ob-card, details.dq { 
    background: var(--surface-glass); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); 
    border: 1px solid var(--border-glass); border-radius: 24px; box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3); 
    animation: cardRise 0.7s var(--ease-spring) both; 
    transition: transform 0.4s var(--ease-out), box-shadow 0.4s var(--ease-out), border-color 0.4s var(--ease-out); 
}
.metric-card:hover, .food-card:hover { 
    transform: translateY(-8px) scale(1.015); border-color: rgba(255, 255, 255, 0.2); 
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), 0 0 30px rgba(0, 229, 255, 0.08); 
}

.metric-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; margin-top: 12px; }
.metric-card { padding: 26px; position: relative; overflow: hidden; display: flex; flex-direction: column; justify-content: space-between; }
.metric-card.is-flagged { border-color: rgba(255, 23, 68, 0.35); background: linear-gradient(180deg, rgba(255, 23, 68, 0.04) 0%, transparent 100%), var(--surface-glass); }
.metric-card.is-flagged:hover { box-shadow: 0 20px 50px rgba(255, 23, 68, 0.15); border-color: rgba(255, 23, 68, 0.7); }
.metric-card.is-low { border-color: rgba(255, 196, 0, 0.35); background: linear-gradient(180deg, rgba(255, 196, 0, 0.04) 0%, transparent 100%), var(--surface-glass); }
.metric-card.is-low:hover { box-shadow: 0 20px 50px rgba(255, 196, 0, 0.15); border-color: rgba(255, 196, 0, 0.7); }

.flag-bar { position: absolute; top: 0; left: 0; right: 0; height: 4px; background: var(--neon-coral); box-shadow: 0 0 15px var(--neon-coral); }
.metric-card.is-low .flag-bar { background: var(--neon-amber); box-shadow: 0 0 15px var(--neon-amber); }

.metric-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; gap: 12px; }
.metric-cat { font: 600 11px/1.2 'JetBrains Mono', monospace; letter-spacing: 0.18em; text-transform: uppercase; color: var(--text-muted); margin: 0 0 6px; }
.metric-name { font-size: 1.15rem; font-weight: 600; margin: 0; color: var(--text-main); }
.metric-value { display: flex; align-items: baseline; gap: 8px; margin: 0 0 4px; }

.metric-number { font: 700 3.6rem/1 'JetBrains Mono', monospace; color: var(--text-main); text-shadow: 0 4px 24px rgba(255,255,255,0.15); }
.metric-card.is-flagged .metric-number { color: var(--neon-coral); text-shadow: 0 4px 24px rgba(255, 23, 68, 0.4); }
.metric-card.is-low .metric-number { color: var(--neon-amber); text-shadow: 0 4px 24px rgba(255, 196, 0, 0.4); }
.metric-unit { font: 500 1.1rem 'JetBrains Mono', monospace; color: var(--text-muted); }
.metric-raw { font: 600 1.2rem/1.5 'JetBrains Mono', monospace; color: var(--text-main); }

.range { margin-top: 24px; display: flex; flex-direction: column; gap: 10px; }
.range-track { height: 8px; background: rgba(255,255,255,0.06); border-radius: 999px; position: relative; overflow: visible; }
.range-safe { position: absolute; top: 0; bottom: 0; background: rgba(0, 230, 118, 0.25); border-radius: 999px; border: 1px solid rgba(0, 230, 118, 0.5); }
.range-marker { position: absolute; top: 50%; width: 18px; height: 18px; transform: translate(-50%, -50%); border-radius: 50%; background: var(--neon-emerald); box-shadow: 0 0 16px var(--neon-emerald), inset 0 0 0 4px var(--bg-deep); z-index: 2; }
.metric-card.is-flagged .range-marker { background: var(--neon-coral); box-shadow: 0 0 16px var(--neon-coral), inset 0 0 0 4px var(--bg-deep); }
.metric-card.is-low .range-marker { background: var(--neon-amber); box-shadow: 0 0 16px var(--neon-amber), inset 0 0 0 4px var(--bg-deep); }
.range-labels { display: flex; justify-content: space-between; font: 500 12px 'JetBrains Mono', monospace; color: var(--text-muted); }

.metric-explain { padding-top: 18px; margin-top: 18px; border-top: 1px dashed rgba(255,255,255,0.1); font-size: 0.98rem; line-height: 1.6; color: rgba(255,255,255,0.85); margin-bottom: 0; }
.metric-explain strong { color: var(--text-main); font-weight: 600; display: block; margin-bottom: 6px; }

.pill { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px; font: 700 11px/1 'JetBrains Mono', monospace; letter-spacing: 0.12em; text-transform: uppercase; white-space: nowrap; border: 1px solid transparent; }
.pill svg { width: 14px; height: 14px; }
.pill-dot { position: relative; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.pill-normal { background: rgba(0, 230, 118, 0.12); color: var(--neon-emerald); border-color: rgba(0, 230, 118, 0.4); box-shadow: 0 0 15px rgba(0, 230, 118, 0.15); }
.pill-high { background: rgba(255, 23, 68, 0.12); color: var(--neon-coral); animation: breatheCoral 2.5s ease-in-out infinite; }
.pill-low { background: rgba(255, 196, 0, 0.12); color: var(--neon-amber); animation: breatheAmber 2.5s ease-in-out infinite; }

.cl-summary { padding: 36px; display: grid; gap: 28px; margin: 32px 0 16px; border-radius: 28px; }
.cl-summary-text { font-size: 1.15rem; line-height: 1.7; color: rgba(255,255,255,0.95); margin: 0; }
.cl-stats { display: flex; gap: 16px; flex-wrap: wrap; }
.cl-stat { flex: 1; min-width: 150px; background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); padding: 22px; border-radius: 18px; display: flex; flex-direction: column; gap: 10px; }
.cl-stat-label { font: 600 12px 'JetBrains Mono', monospace; letter-spacing: 0.18em; text-transform: uppercase; color: var(--text-muted); }
.cl-stat-value { font: 700 2.8rem/1 'JetBrains Mono', monospace; color: var(--text-main); }
.cl-stat-normal .cl-stat-value { color: var(--neon-emerald); text-shadow: 0 0 20px rgba(0,230,118,0.3); }
.cl-stat-flagged .cl-stat-value { color: var(--neon-coral); text-shadow: 0 0 20px rgba(255,23,68,0.3); }
.cl-flag-tag { background: rgba(255,23,68,0.15); color: var(--neon-coral); padding: 8px 14px; border-radius: 10px; font-weight: 600; font-size: 0.9rem; border: 1px solid rgba(255,23,68,0.3); }
.cl-flag-list { display: flex; gap: 12px; flex-wrap: wrap; }

.food-card { padding: 28px; display: flex; flex-direction: column; gap: 18px; }
.food-head { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.food-title { font-size: 1.25rem; font-weight: 600; margin: 0; color: var(--text-main); }
.food-body { font-size: 1.05rem; line-height: 1.8; color: rgba(255,255,255,0.85); margin: 0; white-space: pre-line; }

.dq-list { display: flex; flex-direction: column; gap: 14px; margin-top: 16px; }
details.dq { margin-bottom: 0; }
details.dq > summary { padding: 22px 26px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; list-style: none; gap: 16px; }
details.dq > summary::-webkit-details-marker { display: none; }
details.dq[open] { border-color: rgba(0, 229, 255, 0.4); box-shadow: 0 12px 32px rgba(0, 229, 255, 0.15); background: rgba(0, 229, 255, 0.03); }
.dq-left { display: flex; align-items: center; gap: 16px; }
.dq-count { background: rgba(0, 229, 255, 0.15); color: var(--neon-cyan); border: 1px solid rgba(0,229,255,0.3); width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 10px; font: 700 15px 'JetBrains Mono', monospace; }
.dq-name { font-size: 1.15rem; font-weight: 600; color: var(--text-main); }
.dq-right { display: flex; align-items: center; gap: 16px; }
.dq-chev { width: 22px; height: 22px; color: var(--text-muted); }
.dq-body { padding: 0 26px 26px; }
.dq-body ol { list-style: none; counter-reset: q; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 14px; }
.dq-body li { counter-increment: q; background: rgba(0,0,0,0.3); border: 1px solid var(--border-glass); padding: 18px 20px; border-radius: 14px; font-size: 1.05rem; color: rgba(255,255,255,0.9); display: flex; gap: 18px; line-height: 1.6; }
.dq-body li::before { content: counter(q, decimal-leading-zero); font: 700 15px/1.5 'JetBrains Mono', monospace; color: var(--neon-cyan); flex-shrink: 0; }

.stTabs [data-baseweb="tab-list"] { background: var(--surface-glass); backdrop-filter: blur(24px); border-radius: 18px; padding: 8px; gap: 10px; border: 1px solid var(--border-glass); display: inline-flex; margin-bottom: 32px; }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 12px; padding: 12px 28px; border: none; color: var(--text-muted); font-weight: 600; font-size: 1.05rem; }
.stTabs [aria-selected="true"] { background: rgba(255, 255, 255, 0.12) !important; color: var(--text-main) !important; }
.stTabs [data-baseweb="tab-highlight"] { display: none; }

.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, var(--neon-cyan), #00b0ff) !important; color: #000 !important;
    border: none !important; border-radius: 14px !important; font-weight: 700 !important;
    padding: 0.7rem 1.4rem !important; font-size: 1.05rem !important;
    box-shadow: 0 6px 20px rgba(0, 229, 255, 0.35) !important;
}
.ob-card { animation: cardRise 0.7s var(--ease-spring) both, floatSlow 6s ease-in-out infinite; padding: 56px 40px; text-align: center; border: 1px solid rgba(0, 229, 255, 0.25); margin-top: 48px; }
.ob-step { display: inline-block; font: 700 12px 'JetBrains Mono', monospace; letter-spacing: 0.25em; text-transform: uppercase; color: var(--neon-cyan); margin-bottom: 16px; background: rgba(0,229,255,0.12); padding: 6px 16px; border-radius: 999px; }
.ob-title { font-size: 2.4rem; font-weight: 700; color: var(--text-main); margin: 0 0 18px; }
.ob-desc { font-size: 1.15rem; line-height: 1.6; color: var(--text-muted); margin: 0 auto; max-width: 520px; }
.cl-footer { margin-top: 60px; padding-top: 24px; border-top: 1px dashed var(--border-glass); text-align: center; font-size: 0.85rem; color: #5e6b82; }
</style>
"""
render_html(THEME_CSS)

RAW_SVG = """<svg width="100%" height="100%" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="46" fill="#00e5ff"/>
    <path d="M 10 52 L 28 52 L 38 22 L 55 88 L 68 42 L 76 52 L 90 52" fill="none" stroke="#ffffff" stroke-width="6" stroke-linecap="round"/>
</svg>"""
B64_LOGO = base64.b64encode(RAW_SVG.encode('utf-8')).decode('utf-8')
ICON_LOGO = f'<img src="data:image/svg+xml;base64,{B64_LOGO}" alt="Logo" />'

ICON_UP = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M12 19V5M5 12l7-7 7 7"/></svg>'
ICON_DOWN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>'

# Session state initialization
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
        "title": "ClarityLab AI", "tagline": "Personalized Diagnostic Medical Interpreter", "system_status": "Diagnostic AI Engine Active",
        "lang_modal_title": "Choose Your Language", "lang_modal_desc": "Select the language you feel most comfortable reading your medical report analysis in:",
        "lang_modal_btn": "Proceed to Diet Selection →", "diet_modal_title": "Choose Dietary Preference",
        "diet_modal_desc": "Select your diet profile for tailored food solutions:", "diet_modal_btn": "Launch Health Workspace →",
        "radio_lang_label": "Preferred Language", "radio_diet_label": "Diet Preference", "veg_opt": "Vegetarian", "nonveg_opt": "Non-Vegetarian",
        "change_prefs": "Adjust Settings", "selected_lang_label": "Language:", "diet_profile_label": "Diet Plan:",
        "upload_header": "Upload Medical Lab Report", "upload_desc": "Upload lab test reports in PDF or image format. Evaluates biomarkers instantly.",
        "upload_label": "Upload PDF or Image File", "summary_title": "Diagnostic Health Overview", "missing_title": "Biological Breakdown of Your Biomarkers",
        "what_happening": "What this means for your body:", "food_title": "Evidence-Based Food Suggestions", "questions_title": "Important Questions for Your Next Doctor Visit",
        "download_questions": "Save Doctor Questions (.txt)", "disclaimer": "Clinical Disclaimer: ClarityLab AI is designed for informational support only. Consult a physician for medical advice.",
        "pill_normal": "Normal", "pill_high": "High", "pill_low": "Low", "stat_total": "Biomarkers", "stat_normal": "In range", "stat_flagged": "Needs attention",
        "range_low": "Low", "range_high": "High", "tab_biomarkers": "Biomarkers", "tab_food": "Nutrition", "tab_doctor": "Doctor questions",
        "questions_hint": "Flagged biomarkers are listed first. Tap a biomarker to view questions.", "no_results": "No medical biomarkers could be extracted from this document.",
        "step": "Step", "general_questions": "General questions"
    },
    "हिंदी": {
        "title": "क्लैरिटीलैब एआई", "tagline": "सरल और सटीक मेडिकल रिपोर्ट विश्लेषक", "system_status": "डायग्नोस्टिक एआई इंजन सक्रिय है",
        "lang_modal_title": "अपनी भाषा चुनें", "lang_modal_desc": "रिपोर्ट समझने के लिए भाषा चुनें:",
        "lang_modal_btn": "आहार चयन के लिए आगे बढ़ें →", "diet_modal_title": "खान-पान की आदत चुनें",
        "diet_modal_desc": "अपनी जीवनशैली के अनुसार आहार चुनें:", "diet_modal_btn": "डैशबोर्ड खोलें →",
        "radio_lang_label": "पसंदीदा भाषा", "radio_diet_label": "आहार विकल्प", "veg_opt": "शाकाहारी (Vegetarian)", "nonveg_opt": "मांसाहारी (Non-Vegetarian)",
        "change_prefs": "भाषा / आहार बदलें", "selected_lang_label": "भाषा:", "diet_profile_label": "आहार शैली:",
        "upload_header": "अपनी मेडिकल लैब रिपोर्ट अपलोड करें", "upload_desc": "PDF या फोटो अपलोड करें।",
        "upload_label": "PDF या इमेज फाइल अपलोड करें", "summary_title": "स्वास्थ्य रिपोर्ट का मुख्य सारांश", "missing_title": "बायोमार्कर का विवरण",
        "what_happening": "सरल शब्दों में अर्थ:", "food_title": "आहार और परहेज", "questions_title": "डॉक्टर से पूछने योग्य जरूरी सवाल",
        "download_questions": "सवालों की सूची डाउनलोड करें (.txt)", "disclaimer": "चिकित्सा अस्वीकरण: यह केवल सूचनात्मक उद्देश्य के लिए है। योग्य डॉक्टर से परामर्श लें।",
        "pill_normal": "सामान्य", "pill_high": "अधिक", "pill_low": "कम", "stat_total": "कुल पैरामीटर", "stat_normal": "सामान्य सीमा में", "stat_flagged": "ध्यान दें",
        "range_low": "न्यूनतम", "range_high": "अधिकतम", "tab_biomarkers": "बायोमार्कर", "tab_food": "आहार", "tab_doctor": "डॉक्टर से सवाल",
        "questions_hint": "असामान्य पैरामीटर पहले दिखाए गए हैं।", "no_results": "कोई पैरामीटर नहीं मिला।", "step": "चरण", "general_questions": "सामान्य सवाल"
    },
    "ગુજરાતી": {
        "title": "ક્લેરિટીલેબ એઆઈ", "tagline": "તબીબી લેબ રિપોર્ટનું સરળ વિશ્લેષણ", "system_status": "ડાયગ્નોસ્ટિક એઆઈ સિસ્ટમ કાર્યરત છે",
        "lang_modal_title": "તમારી ભાષા પસંદ કરો", "lang_modal_desc": "ભાષા પસંદ કરો:",
        "lang_modal_btn": "ખોરાક પસંદ કરો →", "diet_modal_title": "ખોરાકની પસંદગી",
        "diet_modal_desc": "યોગ્ય આહાર સૂચવવા માટે પસંદગી કરો:", "diet_modal_btn": "ડેશબોર્ડ શરૂ કરો →",
        "radio_lang_label": "ભાષા", "radio_diet_label": "ખોરાક", "veg_opt": "શાકાહારી", "nonveg_opt": "માસાહારી",
        "change_prefs": "સેટિંગ્સ બદલો", "selected_lang_label": "ભાષા:", "diet_profile_label": "આહાર:",
        "upload_header": "લેબ રિપોર્ટ અપલોડ કરો", "upload_desc": "PDF અથવા ફોટો અપલોડ કરો.",
        "upload_label": "ફાઇલ અપલોડ કરો", "summary_title": "આરોગ્ય સારાંશ", "missing_title": "બાયોમાર્કર વિશ્લેષણ",
        "what_happening": "સરળ સમજૂતી:", "food_title": "આહાર સલાહ", "questions_title": "ડૉક્ટરને પૂછવાના પ્રશ્નો",
        "download_questions": "પ્રશ્નો સાચવો (.txt)", "disclaimer": "ડિસ્ક્લેમર: ફક્ત દર્દીની જાણકારી માટે છે.",
        "pill_normal": "સામાન્ય", "pill_high": "વધુ", "pill_low": "ઓછું", "stat_total": "કુલ પેરામીટર", "stat_normal": "સામાન્ય", "stat_flagged": "ધ્યાન આપો",
        "range_low": "ન્યૂનતમ", "range_high": "મહત્તમ", "tab_biomarkers": "બાયોમાર્કર", "tab_food": "આહાર", "tab_doctor": "ડૉક્ટરને પ્રશ્નો",
        "questions_hint": "અસામાન્ય પેરામીટર પહેલા બતાવ્યા છે.", "no_results": "કોઈ પરિણામ નથી મળ્યું.", "step": "પગલું", "general_questions": "સામાન્ય પ્રશ્નો"
    }
}
L = TEXTS[st.session_state.selected_lang]

# ---------------------------------------------------------
# Reliable Raw Document Extractor (Preserves Tables)
# ---------------------------------------------------------
def extract_pages_text(file_bytes: bytes, filename: str, mime_type: str) -> list[str]:
    pages_text = []
    is_pdf = "pdf" in mime_type.lower() or filename.lower().endswith(".pdf")

    if is_pdf:
        if pdfplumber is not None:
            try:
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    for idx, page in enumerate(pdf.pages):
                        page_text = page.extract_text(layout=True) or ""
                        tables = page.extract_tables()
                        if tables:
                            table_lines = []
                            for tbl in tables:
                                for row in tbl:
                                    if any(row):
                                        cleaned = [str(c).strip().replace("\n", " ") if c else "" for c in row]
                                        table_lines.append(" | ".join(cleaned))
                            if table_lines:
                                page_text += "\n" + "\n".join(table_lines)

                        if len(page_text.strip()) < 80 and pdf2image is not None and pytesseract is not None:
                            try:
                                images = pdf2image.convert_from_bytes(file_bytes, first_page=idx+1, last_page=idx+1)
                                if images:
                                    ocr_txt = pytesseract.image_to_string(images[0], config="--psm 6")
                                    if len(ocr_txt.strip()) > len(page_text.strip()):
                                        page_text = ocr_txt
                            except Exception:
                                pass

                        if page_text.strip():
                            pages_text.append(page_text.strip())
            except Exception as e:
                print(f"pdfplumber error: {e}")

        if not pages_text and pypdf is not None:
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                for page in reader.pages:
                    t = page.extract_text() or ""
                    if t.strip():
                        pages_text.append(t.strip())
            except Exception:
                pass

        if not pages_text and pdf2image is not None and pytesseract is not None:
            try:
                all_images = pdf2image.convert_from_bytes(file_bytes)
                for img in all_images:
                    t = pytesseract.image_to_string(img, config="--psm 6")
                    if t.strip():
                        pages_text.append(t.strip())
            except Exception:
                pass

    else:
        if pytesseract is not None:
            try:
                img = Image.open(io.BytesIO(file_bytes))
                txt = pytesseract.image_to_string(img, config="--psm 6")
                if txt.strip():
                    pages_text.append(txt.strip())
            except Exception:
                pass

    return pages_text

# ---------------------------------------------------------
# Dynamic Model Caller
# ---------------------------------------------------------
def clean_json_response(content: str) -> dict:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            return json.loads(cleaned[start:end+1])
        raise

def call_ai_safe(client, messages, response_format=None, temperature=0.1):
    """
    Calls Groq using currently live, verified production models.
    Catches 413, 400 decommissioned, and 404 models gracefully with backoff.
    """
    candidate_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192"
    ]
    last_err = None
    for model_name in candidate_models:
        for attempt in range(2):
            try:
                kwargs = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                }
                if response_format:
                    kwargs["response_format"] = response_format
                return client.chat.completions.create(**kwargs)
            except Exception as e:
                last_err = e
                err_msg = str(e).lower()
                if "rate" in err_msg or "tpm" in err_msg or "413" in err_msg:
                    time.sleep(2.0)  # Wait for token minute bucket reset
                    continue
                if any(k in err_msg for k in ["not exist", "decommissioned", "model_not_found", "404", "400"]):
                    break  # Jump to next model
                break
    raise last_err or RuntimeError("Unable to communicate with the Diagnostic AI Engine.")

# ---------------------------------------------------------
# Two-Stage Extraction & Micro-Batched Enrichment
# ---------------------------------------------------------
def analyze_report_with_ai(file_bytes, filename, mime_type, target_lang, target_diet, api_key):
    try:
        if Groq is None:
            return None, "groq package not installed. Run: pip install groq"

        pages = extract_pages_text(file_bytes, filename, mime_type)
        if not pages:
            return None, "Could not extract readable text from document. Ensure scans are clear."

        client = Groq(api_key=api_key.strip())

        # STAGE 1: Page-by-page extraction (prevents prompt token overflow)
        stage1_prompt = """
You are a medical laboratory data extractor.
Extract EVERY clinical test, value, and reference range from the text into this exact JSON schema:
{
  "parameters": [
    {
      "name": "Hemoglobin",
      "category": "Complete Blood Count",
      "raw_value": "11.2 g/dL (13.0 - 17.0)",
      "numeric_value": 11.2,
      "unit": "g/dL",
      "ref_low": 13.0,
      "ref_high": 17.0
    }
  ]
}
If interval is "< 150", set ref_low: 0, ref_high: 150. If non-numeric (e.g. Negative/Positive), set numeric_value: null.
"""
        all_extracted_params = []
        for idx, page_text in enumerate(pages):
            if len(page_text.strip()) < 20:
                continue
            try:
                response = call_ai_safe(
                    client=client,
                    messages=[
                        {"role": "system", "content": "You are a clinical extraction engine. Respond strictly in valid JSON."},
                        {"role": "user", "content": f"{stage1_prompt}\n\n--- DOCUMENT PAGE {idx+1} ---\n{page_text}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                parsed = clean_json_response(response.choices[0].message.content)
                params = parsed.get("parameters", [])
                if isinstance(params, list):
                    all_extracted_params.extend(params)
            except Exception as e:
                print(f"Error extracting page {idx+1}: {e}")
            time.sleep(0.5)

        if not all_extracted_params:
            return None, "No medical parameters could be found. Please ensure the document contains clinical test rows."

        # Deduplicate
        unique_params = {}
        for p in all_extracted_params:
            name = str(p.get("name", "")).strip()
            if not name:
                continue
            k = name.lower()
            if k not in unique_params:
                unique_params[k] = p

        # Python Mathematical Range Validation
        processed_params = []
        flagged_params = []

        for p in unique_params.values():
            val = to_float(p.get("numeric_value"))
            low = to_float(p.get("ref_low"))
            high = to_float(p.get("ref_high"))
            
            code = "normal"
            if val is not None:
                if low is not None and val < low:
                    code = "low"
                elif high is not None and val > high:
                    code = "high"
            else:
                raw_lower = str(p.get("raw_value", "")).lower()
                if any(w in raw_lower for w in ["positive", "reactive", "detected", "high"]):
                    code = "high"
                elif any(w in raw_lower for w in ["low", "deficient"]):
                    code = "low"

            p["status_code"] = code
            p["numeric_value"] = val
            p["ref_low"] = low
            p["ref_high"] = high
            processed_params.append(p)
            if code in ("high", "low"):
                flagged_params.append(p)

        # STAGE 2: Micro-Batched Enrichment
        # Enriching abnormal biomarkers in chunks of 3 guarantees output tokens never cap out
        flagged_enriched = {}
        batch_size = 3
        for i in range(0, len(flagged_params), batch_size):
            batch = flagged_params[i:i + batch_size]
            prompt = f"""
Translate and explain these abnormal biomarkers for a patient:
- Language: {target_lang}
- Diet Preference: {target_diet}

Biomarkers:
{json.dumps([{"name": b["name"], "observed": b.get("raw_value") or b.get("numeric_value"), "status": b["status_code"]} for b in batch], ensure_ascii=False)}

Return JSON:
{{
  "details": [
    {{
      "name": "biomarker name translated to {target_lang}",
      "original_key": "original name from input",
      "explanation": "clear biological meaning in {target_lang}",
      "food_remedies": "realistic Indian {target_diet} food solution in {target_lang}",
      "questions_for_doctor": ["question 1 in {target_lang}", "question 2 in {target_lang}"]
    }}
  ]
}}
"""
            try:
                enrich_resp = call_ai_safe(
                    client=client,
                    messages=[
                        {"role": "system", "content": "You are a clinical dietitian and consultant. Respond strictly in valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2
                )
                edata = clean_json_response(enrich_resp.choices[0].message.content)
                for item in edata.get("details", []):
                    k = item.get("original_key", item.get("name", "")).strip().lower()
                    flagged_enriched[k] = item
            except Exception as e:
                print(f"Batch enrichment error: {e}")
            time.sleep(0.6)

        # Merge enrichments back into biomarkers
        for p in processed_params:
            p_key = p["name"].strip().lower()
            matched = flagged_enriched.get(p_key)
            if not matched:
                for k, v in flagged_enriched.items():
                    if k in p_key or p_key in k:
                        matched = v
                        break

            if matched:
                p["explanation"] = matched.get("explanation", "")
                p["food_remedies"] = matched.get("food_remedies", "")
                p["questions_for_doctor"] = matched.get("questions_for_doctor", [])
            else:
                p["explanation"] = ""
                p["food_remedies"] = ""
                p["questions_for_doctor"] = []

        summary_text = (
            f"Successfully analyzed {len(processed_params)} biomarkers. "
            f"{len(flagged_params)} parameter(s) fall outside reference intervals."
        )

        return {
            "summary": summary_text,
            "parameters": processed_params,
            "questions": ["Are there any lifestyle or medication adjustments required based on these results?"]
        }, None

    except Exception as e:
        return None, f"Diagnostic AI Error: {str(e)}"

# ---------------------------------------------------------
# Normalization & UI Builders
# ---------------------------------------------------------
NUM_RE = r"-?\d+(?:\.\d+)?"

def to_float(v):
    try:
        return float(v) if v is not None and v != "" else None
    except (TypeError, ValueError):
        return None

def normalise(param) -> dict:
    raw_value = str(param.get("raw_value") or param.get("value") or "")
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
        "code": param.get("status_code", "normal"),
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
    <article class="metric-card {state_cls}" style="animation-delay:{index * 40}ms">
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
    <details class="dq" {'open' if is_open else ''} style="animation-delay:{index * 40}ms">
        <summary>
            <span class="dq-left"><span class="dq-count">{len(questions)}</span><span class="dq-name">{esc(title)}</span></span>
            <span class="dq-right">{pill}</span>
        </summary>
        <div class="dq-body"><ol>{items}</ol></div>
    </details>
    """

# ---------------------------------------------------------
# STEP 1: Language Selection
# ---------------------------------------------------------
LANG_OPTIONS = ["English", "हिंदी", "ગુજરાતી"]

if st.session_state.onboarding_step == 1:
    _, center, _ = st.columns([1, 1.6, 1])
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
# STEP 2: Dietary Preference
# ---------------------------------------------------------
elif st.session_state.onboarding_step == 2:
    _, center, _ = st.columns([1, 1.6, 1])
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
# STEP 3: Main Dashboard
# ---------------------------------------------------------
else:
    head_col, action_col = st.columns([4, 1], vertical_alignment="center")
    with head_col:
        render_html(f"""
        <header class="cl-header">
            <div class="cl-brand">
                <div class="cl-logo">{ICON_LOGO}</div>
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

    groq_api_key = ""
    try:
        groq_api_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass
    groq_api_key = groq_api_key or os.environ.get("GROQ_API_KEY", "")

    render_html(f"""
    <div style="margin-top:20px">
        <p class="cl-eyebrow">01</p>
        <h2 class="cl-h2">{esc(L['upload_header'])}</h2>
        <p class="cl-sub" style="margin-bottom:12px">{esc(L['upload_desc'])}</p>
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
            with st.spinner("Analyzing laboratory document with Groq LPU engine..."):
                parsed_report_data, error_notice = analyze_report_with_ai(
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
        biomarkers_sorted = sorted(biomarkers, key=lambda b: order.get(b["code"], 2))

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
                <h2 class="cl-h2" style="margin-top:8px">{esc(L['missing_title'])}</h2>
                <div class="metric-grid">{cards}</div>
            </section>
            """)

        with tab_food:
            food_cards = "".join(
                f"""
                <article class="food-card" style="animation-delay:{i * 50}ms">
                    <header class="food-head"><h3 class="food-title">{esc(b['name'])}</h3>{status_pill(b['code'])}</header>
                    <p class="food-body">{esc(b['food'])}</p>
                </article>
                """
                for i, b in enumerate(biomarkers_sorted) if b["food"]
            )
            render_html(f"""
            <section aria-label="{esc(L['food_title'])}">
                <h2 class="cl-h2" style="margin-top:8px">{esc(L['food_title'])}</h2>
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
                    <h2 class="cl-h2" style="margin-top:8px">{esc(L['questions_title'])}</h2>
                    <p class="cl-tagline" style="margin-bottom:20px;">{esc(L['questions_hint'])}</p>
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
