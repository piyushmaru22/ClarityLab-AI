import hashlib
import html
import io
import json
import os
import re
import textwrap
import sys
import base64

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

/* Global Body & Background */
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

/* Micro-Animations */
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

/* Headings & Typography */
.cl-title { font-size: 2.2rem; font-weight: 700; letter-spacing: -0.04em; margin: 0; background: linear-gradient(135deg, #ffffff 0%, #a3b1c6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.cl-tagline { font-size: 1.05rem; color: var(--text-muted); margin-top: 4px; font-weight: 500; }
.cl-h2 { font-size: 1.6rem; font-weight: 700; letter-spacing: -0.03em; color: var(--text-main); margin-bottom: 8px; }
.cl-eyebrow { font: 600 12px/1 'JetBrains Mono', monospace; letter-spacing: 0.2em; text-transform: uppercase; color: var(--neon-cyan); margin-bottom: 8px; }

/* Header & Ribbons */
.cl-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 24px; border-bottom: 1px solid var(--border-glass); margin-bottom: 24px; flex-wrap: wrap; gap: 20px; }
.cl-brand { display: flex; align-items: center; gap: 20px; }

/* STUNNING 3D LOGO CONTAINER */
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

/* Status Chip */
.cl-chip { display: inline-flex; align-items: center; gap: 10px; padding: 8px 18px; border-radius: 999px; background: rgba(0, 229, 255, 0.05); border: 1px solid rgba(0, 229, 255, 0.3); font: 500 13px 'JetBrains Mono', monospace; color: var(--neon-cyan); box-shadow: 0 0 20px rgba(0, 229, 255, 0.1); backdrop-filter: blur(8px); }
.cl-chip-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--neon-cyan); animation: dotPulse 2s infinite; }

.cl-prefs { display: flex; gap: 24px; flex-wrap: wrap; margin: 16px 0 8px; font-size: 0.95rem; color: var(--text-muted); }
.cl-prefs strong { color: var(--text-main); font-weight: 600; padding: 4px 10px; background: rgba(255,255,255,0.05); border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); }

/* Sci-Fi Laser Uploader */
[data-testid="stFileUploaderDropzone"] { 
    position: relative; overflow: hidden; background: var(--surface-glass) !important; 
    border: 1px dashed rgba(0, 229, 255, 0.4) !important; border-radius: 20px !important; 
    transition: all 0.3s var(--ease-out) !important; backdrop-filter: blur(12px); 
}
[data-testid="stFileUploaderDropzone"]:hover { 
    border-color: var(--neon-cyan) !important; background: var(--surface-glass-hover) !important; 
    box-shadow: 0 0 40px rgba(0, 229, 255, 0.15) !important; 
}
[data-testid="stFileUploaderDropzone"]::after { 
    content: ""; position: absolute; left: 0; right: 0; top: 0; height: 2px; 
    background: var(--neon-cyan); box-shadow: 0 0 12px var(--neon-cyan), 0 0 24px var(--neon-cyan); 
    animation: scanline 3s linear infinite; pointer-events: none; 
}

/* Glass Cards Master Class */
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

/* Metric Cards specific */
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

/* Large High-Contrast Numbers for Readability */
.metric-number { font: 700 3.6rem/1 'JetBrains Mono', monospace; color: var(--text-main); text-shadow: 0 4px 24px rgba(255,255,255,0.15); }
.metric-card.is-flagged .metric-number { color: var(--neon-coral); text-shadow: 0 4px 24px rgba(255, 23, 68, 0.4); }
.metric-card.is-low .metric-number { color: var(--neon-amber); text-shadow: 0 4px 24px rgba(255, 196, 0, 0.4); }
.metric-unit { font: 500 1.1rem 'JetBrains Mono', monospace; color: var(--text-muted); }
.metric-raw { font: 600 1.2rem/1.5 'JetBrains Mono', monospace; color: var(--text-main); }

/* Apple-style Range Track */
.range { margin-top: 24px; display: flex; flex-direction: column; gap: 10px; }
.range-track { height: 8px; background: rgba(255,255,255,0.06); border-radius: 999px; position: relative; overflow: visible; }
.range-safe { position: absolute; top: 0; bottom: 0; background: rgba(0, 230, 118, 0.25); border-radius: 999px; border: 1px solid rgba(0, 230, 118, 0.5); }
.range-marker { position: absolute; top: 50%; width: 18px; height: 18px; transform: translate(-50%, -50%); border-radius: 50%; background: var(--neon-emerald); box-shadow: 0 0 16px var(--neon-emerald), inset 0 0 0 4px var(--bg-deep); z-index: 2; transition: left 1s var(--ease-spring); }
.metric-card.is-flagged .range-marker { background: var(--neon-coral); box-shadow: 0 0 16px var(--neon-coral), inset 0 0 0 4px var(--bg-deep); }
.metric-card.is-low .range-marker { background: var(--neon-amber); box-shadow: 0 0 16px var(--neon-amber), inset 0 0 0 4px var(--bg-deep); }
.range-labels { display: flex; justify-content: space-between; font: 500 12px 'JetBrains Mono', monospace; color: var(--text-muted); }

.metric-explain { padding-top: 18px; margin-top: 18px; border-top: 1px dashed rgba(255,255,255,0.1); font-size: 0.98rem; line-height: 1.6; color: rgba(255,255,255,0.85); margin-bottom: 0; }
.metric-explain strong { color: var(--text-main); font-weight: 600; display: block; margin-bottom: 6px; }

/* Neon Breathing Pills */
.pill { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px; font: 700 11px/1 'JetBrains Mono', monospace; letter-spacing: 0.12em; text-transform: uppercase; white-space: nowrap; border: 1px solid transparent; }
.pill svg { width: 14px; height: 14px; }
.pill-dot { position: relative; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.pill-dot::after { content: ""; position: absolute; inset: 0; border-radius: 50%; background: currentColor; animation: dotPulse 2.5s infinite; }
.pill-normal { background: rgba(0, 230, 118, 0.12); color: var(--neon-emerald); border-color: rgba(0, 230, 118, 0.4); box-shadow: 0 0 15px rgba(0, 230, 118, 0.15); }
.pill-high { background: rgba(255, 23, 68, 0.12); color: var(--neon-coral); animation: breatheCoral 2.5s ease-in-out infinite; }
.pill-low { background: rgba(255, 196, 0, 0.12); color: var(--neon-amber); animation: breatheAmber 2.5s ease-in-out infinite; }

/* Summary Dashboard Panel */
.cl-summary { padding: 36px; display: grid; gap: 28px; margin: 32px 0 16px; border-radius: 28px; }
.cl-summary-text { font-size: 1.15rem; line-height: 1.7; color: rgba(255,255,255,0.95); margin: 0; }
.cl-stats { display: flex; gap: 16px; flex-wrap: wrap; }
.cl-stat { flex: 1; min-width: 150px; background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); padding: 22px; border-radius: 18px; display: flex; flex-direction: column; gap: 10px; box-shadow: inset 0 2px 10px rgba(255,255,255,0.02); }
.cl-stat-label { font: 600 12px 'JetBrains Mono', monospace; letter-spacing: 0.18em; text-transform: uppercase; color: var(--text-muted); }
.cl-stat-value { font: 700 2.8rem/1 'JetBrains Mono', monospace; color: var(--text-main); }
.cl-stat-normal .cl-stat-value { color: var(--neon-emerald); text-shadow: 0 0 20px rgba(0,230,118,0.3); }
.cl-stat-flagged .cl-stat-value { color: var(--neon-coral); text-shadow: 0 0 20px rgba(255,23,68,0.3); }
.cl-flag-tag { background: rgba(255,23,68,0.15); color: var(--neon-coral); padding: 8px 14px; border-radius: 10px; font-weight: 600; font-size: 0.9rem; border: 1px solid rgba(255,23,68,0.3); box-shadow: 0 0 12px rgba(255,23,68,0.15); }
.cl-flag-list { display: flex; gap: 12px; flex-wrap: wrap; }

/* Nutrition & Doctor Consultation */
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
.dq-count { background: rgba(0, 229, 255, 0.15); color: var(--neon-cyan); border: 1px solid rgba(0,229,255,0.3); width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 10px; font: 700 15px 'JetBrains Mono', monospace; box-shadow: 0 0 15px rgba(0,229,255,0.2); }
.dq-name { font-size: 1.15rem; font-weight: 600; color: var(--text-main); }
.dq-right { display: flex; align-items: center; gap: 16px; }
.dq-chev { width: 22px; height: 22px; color: var(--text-muted); transition: transform 0.4s var(--ease-spring); }
details.dq[open] .dq-chev { transform: rotate(180deg); color: var(--neon-cyan); }
.dq-body { padding: 0 26px 26px; }
.dq-body ol { list-style: none; counter-reset: q; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 14px; }
.dq-body li { counter-increment: q; background: rgba(0,0,0,0.3); border: 1px solid var(--border-glass); padding: 18px 20px; border-radius: 14px; font-size: 1.05rem; color: rgba(255,255,255,0.9); display: flex; gap: 18px; line-height: 1.6; }
.dq-body li::before { content: counter(q, decimal-leading-zero); font: 700 15px/1.5 'JetBrains Mono', monospace; color: var(--neon-cyan); flex-shrink: 0; }

/* Linear-style Streamlit Tabs Overrides */
.stTabs [data-baseweb="tab-list"] { background: var(--surface-glass); backdrop-filter: blur(24px); border-radius: 18px; padding: 8px; gap: 10px; border: 1px solid var(--border-glass); display: inline-flex; margin-bottom: 32px; box-shadow: 0 12px 32px rgba(0,0,0,0.3); }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 12px; padding: 12px 28px; transition: all 0.3s var(--ease-out); border: none; color: var(--text-muted); font-weight: 600; font-size: 1.05rem; letter-spacing: 0.02em; }
.stTabs [aria-selected="true"] { background: rgba(255, 255, 255, 0.12) !important; color: var(--text-main) !important; box-shadow: 0 4px 20px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.1); }
.stTabs [data-baseweb="tab-highlight"] { display: none; }

/* Buttons & Inputs */
.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, var(--neon-cyan), #00b0ff) !important; color: #000 !important;
    border: none !important; border-radius: 14px !important; font-weight: 700 !important;
    padding: 0.7rem 1.4rem !important; font-size: 1.05rem !important;
    box-shadow: 0 6px 20px rgba(0, 229, 255, 0.35) !important; transition: all 0.3s var(--ease-out) !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-3px) scale(1.02) !important; box-shadow: 0 10px 30px rgba(0, 229, 255, 0.5) !important;
}
.st-key-change_prefs button { background: transparent !important; color: var(--text-main) !important; border: 1px solid var(--border-glass) !important; box-shadow: none !important; }
.st-key-change_prefs button:hover { background: rgba(255,255,255,0.08) !important; border-color: rgba(255,255,255,0.25) !important; }

/* Floating Spatial Onboarding */
.ob-card { animation: cardRise 0.7s var(--ease-spring) both, floatSlow 6s ease-in-out infinite; padding: 56px 40px; text-align: center; border: 1px solid rgba(0, 229, 255, 0.25); box-shadow: 0 20px 60px rgba(0,0,0,0.5), inset 0 0 50px rgba(0,229,255,0.06); margin-top: 48px; }
.ob-card .cl-logo { margin: 0 auto 28px; }
.ob-step { display: inline-block; font: 700 12px 'JetBrains Mono', monospace; letter-spacing: 0.25em; text-transform: uppercase; color: var(--neon-cyan); margin-bottom: 16px; background: rgba(0,229,255,0.12); padding: 6px 16px; border-radius: 999px; }
.ob-title { font-size: 2.4rem; font-weight: 700; color: var(--text-main); margin: 0 0 18px; letter-spacing: -0.03em; }
.ob-desc { font-size: 1.15rem; line-height: 1.6; color: var(--text-muted); margin: 0 auto; max-width: 520px; }

.cl-footer { margin-top: 60px; padding-top: 24px; border-top: 1px dashed var(--border-glass); text-align: center; font-size: 0.85rem; color: #5e6b82; letter-spacing: 0.02em; }
</style>
"""
render_html(THEME_CSS)

# REALISTIC 3D GLOSSY SVG LOGO (Base64 Encoded to bypass Streamlit Sanitization)
RAW_SVG = """<svg width="100%" height="100%" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="orbGrad" cx="30%" cy="30%" r="70%">
            <stop offset="0%" stop-color="#ffffff" />
            <stop offset="15%" stop-color="#aaffff" />
            <stop offset="40%" stop-color="#00e5ff" />
            <stop offset="75%" stop-color="#0066ff" />
            <stop offset="100%" stop-color="#000b22" />
        </radialGradient>
        <linearGradient id="glassReflection" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#ffffff" stop-opacity="0.9" />
            <stop offset="30%" stop-color="#ffffff" stop-opacity="0.2" />
            <stop offset="100%" stop-color="#ffffff" stop-opacity="0" />
        </linearGradient>
        <filter id="glowEffect" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
    </defs>
    <!-- 3D Orb -->
    <circle cx="50" cy="50" r="46" fill="url(#orbGrad)"/>
    
    <!-- Inner Border Highlight -->
    <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.6)" stroke-width="2"/>
    
    <!-- Medical Cross -->
    <path d="M43 25 h14 v18 h18 v14 h-18 v18 h-14 v-18 h-18 v-14 h18 z" fill="rgba(255,255,255,0.2)"/>
    
    <!-- Bright White Heartbeat Pulse -->
    <path d="M 10 52 L 28 52 L 38 22 L 55 88 L 68 42 L 76 52 L 90 52" 
          fill="none" stroke="#ffffff" stroke-width="5" 
          stroke-linecap="round" stroke-linejoin="round" 
          filter="url(#glowEffect)"/>
          
    <!-- Top Glass Glossy Shine -->
    <ellipse cx="50" cy="20" rx="32" ry="12" fill="url(#glassReflection)"/>
</svg>"""

B64_LOGO = base64.b64encode(RAW_SVG.encode('utf-8')).decode('utf-8')
ICON_LOGO = f'<img src="data:image/svg+xml;base64,{B64_LOGO}" alt="Logo" style="filter: drop-shadow(0px 4px 6px rgba(0,229,255,0.4));" />'

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
        "upload_label": "PDF या फोटो/इमेज फाइल अपलोड करें",
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
    <article class="metric-card {state_cls}" style="animation-delay:{index * 60}ms">
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
    <details class="dq" {'open' if is_open else ''} style="animation-delay:{index * 50}ms">
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
# STEP 2: ONBOARDING MODAL 2 - DIET
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
# STEP 3: MAIN MEDICAL DASHBOARD
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

    # Secure Automatic Groq Key Pipeline (Reads from secrets.toml or environment)
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
                <h2 class="cl-h2" style="margin-top:8px">{esc(L['missing_title'])}</h2>
                <div class="metric-grid">{cards}</div>
            </section>
            """)

        with tab_food:
            food_cards = "".join(
                f"""
                <article class="food-card" style="animation-delay:{i * 60}ms">
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
