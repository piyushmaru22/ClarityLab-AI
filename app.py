import hashlib
import html
import io
import json
import os
import re
import textwrap
import sys
import time
import base64
from concurrent.futures import ThreadPoolExecutor

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
# Theme: Ultra-Premium Glassmorphism 3.0 UI w/ Animations
# ---------------------------------------------------------
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');

:root {
    --bg-deep: #03050a;
    --surface-glass: rgba(13, 18, 30, 0.4);
    --surface-glass-hover: rgba(18, 25, 42, 0.65);
    --border-glass: rgba(255, 255, 255, 0.08);
    --border-glass-glow: rgba(255, 255, 255, 0.2);
    --text-main: #ffffff;
    --text-muted: #8b9bb4;
    --text-bright: #e2e8f0;
    --neon-cyan: #00e5ff;
    --neon-emerald: #00e676;
    --neon-coral: #ff2a55;
    --neon-amber: #ffc400;
    --ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
    --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
    --ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Base Adjustments & Scrollbar */
html, body, .stApp, [class*="css"], .stMarkdown, button, input, label {
    font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--bg-deep); border-left: 1px solid var(--border-glass); }
::-webkit-scrollbar-thumb { background: rgba(0, 229, 255, 0.2); border-radius: 10px; border: 2px solid var(--bg-deep); }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 229, 255, 0.5); }

/* Remove Streamlit Default Elements */
#MainMenu, header[data-testid="stHeader"], footer { visibility: hidden !important; height: 0 !important; }
.block-container { max-width: 1250px; padding-top: 1rem !important; padding-bottom: 4rem !important; animation: pageLoad 1s var(--ease-out); }

/* Ambient Aurora Background */
.stApp { background: var(--bg-deep) !important; color: var(--text-main); overflow-x: hidden; }
.stApp::before { 
    content: ""; position: fixed; inset: -20%; z-index: -1; pointer-events: none;
    background: 
        radial-gradient(circle at 15% 10%, rgba(0, 229, 255, 0.07) 0%, transparent 40%), 
        radial-gradient(circle at 85% 80%, rgba(0, 230, 118, 0.05) 0%, transparent 40%),
        radial-gradient(circle at 50% 50%, rgba(255, 42, 85, 0.03) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(255, 196, 0, 0.02) 0%, transparent 30%);
    animation: ambientShift 25s ease-in-out infinite alternate;
    filter: blur(40px);
}
.stApp::after {
    content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
    background: url('data:image/svg+xml;utf8,<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"><filter id="noise"><feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/></filter><rect width="100%" height="100%" filter="url(%23noise)" opacity="0.04"/></svg>');
}

/* Animations */
@keyframes ambientShift { 0% { transform: scale(1) translate(0, 0) rotate(0deg); } 50% { transform: scale(1.1) translate(3%, -3%) rotate(2deg); } 100% { transform: scale(1) translate(-2%, 4%) rotate(-1deg); } }
@keyframes pageLoad { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
@keyframes cardRise { from { opacity: 0; transform: translateY(30px) scale(0.95); } to { opacity: 1; transform: translateY(0) scale(1); } }
@keyframes floatSlow { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-12px); box-shadow: 0 30px 60px rgba(0,0,0,0.6), inset 0 0 50px rgba(0,229,255,0.1); } }
@keyframes breatheCoral { 0%, 100% { box-shadow: 0 0 12px rgba(255, 42, 85, 0.3); border-color: rgba(255, 42, 85, 0.5); } 50% { box-shadow: 0 0 28px rgba(255, 42, 85, 0.7); border-color: rgba(255, 42, 85, 1); } }
@keyframes breatheAmber { 0%, 100% { box-shadow: 0 0 12px rgba(255, 196, 0, 0.3); border-color: rgba(255, 196, 0, 0.5); } 50% { box-shadow: 0 0 28px rgba(255, 196, 0, 0.7); border-color: rgba(255, 196, 0, 1); } }
@keyframes scanline { 0% { top: -10%; opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { top: 110%; opacity: 0; } }
@keyframes dotPulse { 0% { transform: scale(0.8); opacity: 1; } 100% { transform: scale(2.5); opacity: 0; } }
@keyframes pingMarker { 0% { transform: scale(1); opacity: 0.8; } 100% { transform: scale(2); opacity: 0; } }
@keyframes popIn { 0% { transform: scale(0); opacity: 0; } 80% { transform: scale(1.1); opacity: 1; } 100% { transform: scale(1); } }

/* Headings & Typography */
.cl-title { font-size: 2.8rem; font-weight: 800; letter-spacing: -0.05em; margin: 0; background: linear-gradient(135deg, #ffffff 0%, #8b9bb4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; drop-shadow: 0 4px 20px rgba(255,255,255,0.1); }
.cl-tagline { font-size: 1.15rem; color: var(--neon-cyan); margin-top: 6px; font-weight: 500; letter-spacing: 0.02em; }
.cl-h2 { font-size: 1.8rem; font-weight: 700; letter-spacing: -0.03em; color: var(--text-main); margin-bottom: 8px; text-shadow: 0 2px 10px rgba(0,0,0,0.5); }
.cl-eyebrow { font: 700 13px/1 'JetBrains Mono', monospace; letter-spacing: 0.25em; text-transform: uppercase; color: var(--neon-cyan); margin-bottom: 8px; display: inline-block; padding: 4px 12px; background: rgba(0,229,255,0.1); border-radius: 100px; border: 1px solid rgba(0,229,255,0.2); }

/* Header & Status Ribbon */
.cl-header { display: flex; justify-content: space-between; align-items: center; padding: 24px 32px; background: var(--surface-glass); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); border: 1px solid var(--border-glass); border-radius: 28px; margin-bottom: 32px; box-shadow: 0 20px 40px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1); flex-wrap: wrap; gap: 20px; }
.cl-brand { display: flex; align-items: center; gap: 24px; }
.cl-logo { width: 68px; height: 68px; display: flex; align-items: center; justify-content: center; background: radial-gradient(circle at top left, rgba(0, 30, 60, 0.8), rgba(0, 10, 20, 0.9)); border: 1px solid rgba(0, 229, 255, 0.5); border-radius: 22px; box-shadow: 0 12px 30px rgba(0, 229, 255, 0.3), inset 0 2px 20px rgba(0,229,255,0.2), inset 0 0 0 1px rgba(255,255,255,0.2); backdrop-filter: blur(12px); transform-style: preserve-3d; transition: transform 0.5s var(--ease-spring); }
.cl-logo:hover { transform: rotateY(15deg) rotateX(10deg) scale(1.05); box-shadow: 0 20px 40px rgba(0, 229, 255, 0.4), inset 0 2px 20px rgba(0,229,255,0.3); }
.cl-logo img, .cl-logo svg { width: 50px; height: 50px; filter: drop-shadow(0 4px 8px rgba(0,229,255,0.5)); }

/* Status Chip */
.cl-chip { display: inline-flex; align-items: center; gap: 12px; padding: 10px 22px; border-radius: 999px; background: rgba(0, 229, 255, 0.08); border: 1px solid rgba(0, 229, 255, 0.4); font: 600 14px 'JetBrains Mono', monospace; color: var(--neon-cyan); box-shadow: 0 0 25px rgba(0, 229, 255, 0.15), inset 0 0 10px rgba(0,229,255,0.1); backdrop-filter: blur(10px); }
.cl-chip-dot { position: relative; width: 10px; height: 10px; border-radius: 50%; background: var(--neon-cyan); box-shadow: 0 0 10px var(--neon-cyan); }
.cl-chip-dot::after { content: ''; position: absolute; inset: -4px; border-radius: 50%; background: var(--neon-cyan); animation: dotPulse 2s cubic-bezier(0,0,0.2,1) infinite; }

/* Preferences Ribbon */
.cl-prefs { display: flex; gap: 24px; flex-wrap: wrap; margin: 0 0 24px 0; font-size: 1rem; color: var(--text-muted); background: linear-gradient(90deg, var(--surface-glass), transparent); padding: 12px 24px; border-radius: 16px; border-left: 3px solid var(--neon-cyan); }
.cl-prefs strong { color: var(--text-bright); font-weight: 600; padding: 4px 12px; background: rgba(255,255,255,0.05); border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); letter-spacing: 0.02em; }

/* Sci-Fi Laser Uploader */
[data-testid="stFileUploaderDropzone"] { 
    position: relative; overflow: hidden; background: rgba(10, 15, 25, 0.6) !important; 
    border: 2px dashed rgba(0, 229, 255, 0.3) !important; border-radius: 24px !important; 
    transition: all 0.4s var(--ease-out) !important; backdrop-filter: blur(16px); min-height: 200px;
    display: flex; align-items: center; justify-content: center; box-shadow: inset 0 0 40px rgba(0,0,0,0.5);
}
[data-testid="stFileUploaderDropzone"]:hover { 
    border-color: var(--neon-cyan) !important; background: rgba(15, 25, 45, 0.7) !important; 
    box-shadow: 0 0 50px rgba(0, 229, 255, 0.15), inset 0 0 30px rgba(0,229,255,0.1) !important; transform: scale(1.01);
}
[data-testid="stFileUploaderDropzone"]::after { 
    content: ""; position: absolute; left: -10%; right: -10%; height: 3px; 
    background: linear-gradient(90deg, transparent, var(--neon-cyan), #fff, var(--neon-cyan), transparent); 
    box-shadow: 0 0 20px var(--neon-cyan), 0 0 40px var(--neon-cyan); 
    animation: scanline 4s linear infinite; pointer-events: none; opacity: 0.8;
}

/* Glass Cards Master Class & 3D Hover */
.metric-card, .food-card, .cl-summary, .ob-card, details.dq { 
    background: var(--surface-glass); backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px); 
    border: 1px solid var(--border-glass); border-radius: 28px; box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255,255,255,0.1); 
    animation: cardRise 0.8s var(--ease-spring) both; 
    transition: transform 0.5s var(--ease-spring), box-shadow 0.5s var(--ease-out), border-color 0.5s var(--ease-out); 
    position: relative; overflow: hidden; transform-style: preserve-3d;
}
/* Sweeping Glare Reflection */
.metric-card::before, .food-card::before, .ob-card::before {
    content: ""; position: absolute; top: 0; left: -150%; width: 100%; height: 100%;
    background: linear-gradient(120deg, transparent, rgba(255,255,255,0.08), transparent);
    transform: skewX(-25deg); transition: 0.7s var(--ease-smooth); pointer-events: none; z-index: 10;
}
.metric-card:hover::before, .food-card:hover::before, .ob-card:hover::before { left: 150%; }

.metric-card:hover, .food-card:hover { 
    transform: translateY(-10px) scale(1.02); border-color: var(--border-glass-glow); 
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.6), 0 0 40px rgba(0, 229, 255, 0.1), inset 0 1px 2px rgba(255,255,255,0.2); 
    z-index: 2;
}

/* Metric Cards specific */
.metric-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 24px; margin-top: 16px; margin-bottom: 40px; }
.metric-card { padding: 32px; display: flex; flex-direction: column; justify-content: space-between; isolation: isolate; }
.metric-card.is-flagged { border-color: rgba(255, 42, 85, 0.4); background: linear-gradient(180deg, rgba(255, 42, 85, 0.05) 0%, transparent 100%), var(--surface-glass); }
.metric-card.is-flagged:hover { box-shadow: 0 25px 60px rgba(255, 42, 85, 0.2); border-color: rgba(255, 42, 85, 0.8); }
.metric-card.is-low { border-color: rgba(255, 196, 0, 0.4); background: linear-gradient(180deg, rgba(255, 196, 0, 0.05) 0%, transparent 100%), var(--surface-glass); }
.metric-card.is-low:hover { box-shadow: 0 25px 60px rgba(255, 196, 0, 0.2); border-color: rgba(255, 196, 0, 0.8); }

.flag-bar { position: absolute; top: 0; left: 0; right: 0; height: 5px; background: var(--neon-coral); box-shadow: 0 0 20px var(--neon-coral); z-index: 5; transition: height 0.3s; }
.metric-card:hover .flag-bar { height: 8px; }
.metric-card.is-low .flag-bar { background: var(--neon-amber); box-shadow: 0 0 20px var(--neon-amber); }

.metric-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; gap: 16px; position: relative; z-index: 2; }
.metric-cat { font: 700 11px/1.2 'JetBrains Mono', monospace; letter-spacing: 0.25em; text-transform: uppercase; color: var(--text-muted); margin: 0 0 8px; opacity: 0.8; }
.metric-name { font-size: 1.3rem; font-weight: 700; margin: 0; color: var(--text-main); letter-spacing: -0.01em; }

/* Large High-Contrast Numbers */
.metric-value { display: flex; align-items: baseline; gap: 10px; margin: 0 0 8px; position: relative; z-index: 2; }
.metric-number { font: 800 4rem/1 'JetBrains Mono', monospace; color: var(--text-main); text-shadow: 0 8px 30px rgba(255,255,255,0.2); letter-spacing: -0.04em; }
.metric-card.is-flagged .metric-number { color: var(--neon-coral); text-shadow: 0 8px 30px rgba(255, 42, 85, 0.5); }
.metric-card.is-low .metric-number { color: var(--neon-amber); text-shadow: 0 8px 30px rgba(255, 196, 0, 0.5); }
.metric-unit { font: 600 1.25rem 'JetBrains Mono', monospace; color: var(--text-muted); background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 8px; }
.metric-raw { font: 700 1.5rem/1.5 'JetBrains Mono', monospace; color: var(--text-bright); }

/* Animated Range Track */
.range { margin-top: 32px; display: flex; flex-direction: column; gap: 12px; position: relative; z-index: 2; }
.range-track { height: 10px; background: rgba(0,0,0,0.4); border-radius: 999px; position: relative; overflow: visible; box-shadow: inset 0 2px 5px rgba(0,0,0,0.5), 0 1px 0 rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.05); }
.range-safe { position: absolute; top: 0; bottom: 0; background: linear-gradient(90deg, rgba(0, 230, 118, 0.2), rgba(0, 230, 118, 0.5), rgba(0, 230, 118, 0.2)); border-radius: 999px; border: 1px solid rgba(0, 230, 118, 0.6); box-shadow: 0 0 15px rgba(0, 230, 118, 0.2); }
.range-marker { position: absolute; top: 50%; width: 22px; height: 22px; transform: translate(-50%, -50%); border-radius: 50%; background: var(--neon-emerald); box-shadow: 0 0 20px var(--neon-emerald), inset 0 0 0 5px var(--bg-deep); z-index: 3; transition: left 1.5s var(--ease-spring); }
.range-marker::after { content: ''; position: absolute; inset: -6px; border-radius: 50%; border: 2px solid var(--neon-emerald); animation: pingMarker 2s cubic-bezier(0, 0, 0.2, 1) infinite; pointer-events: none; }
.metric-card.is-flagged .range-marker { background: var(--neon-coral); box-shadow: 0 0 20px var(--neon-coral), inset 0 0 0 5px var(--bg-deep); }
.metric-card.is-flagged .range-marker::after { border-color: var(--neon-coral); }
.metric-card.is-low .range-marker { background: var(--neon-amber); box-shadow: 0 0 20px var(--neon-amber), inset 0 0 0 5px var(--bg-deep); }
.metric-card.is-low .range-marker::after { border-color: var(--neon-amber); }
.range-labels { display: flex; justify-content: space-between; font: 600 12px 'JetBrains Mono', monospace; color: var(--text-muted); padding: 0 4px; }

/* Detailed Explanations */
.metric-explain { padding-top: 20px; margin-top: 24px; border-top: 1px dashed rgba(255,255,255,0.15); font-size: 1.05rem; line-height: 1.7; color: rgba(255,255,255,0.9); margin-bottom: 0; position: relative; z-index: 2; }
.metric-explain strong { color: var(--neon-cyan); font-weight: 700; display: block; margin-bottom: 8px; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.1em; }

/* Glowing Neon Pills */
.pill { display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 999px; font: 800 12px/1 'JetBrains Mono', monospace; letter-spacing: 0.15em; text-transform: uppercase; white-space: nowrap; border: 1px solid transparent; box-shadow: inset 0 1px 1px rgba(255,255,255,0.2); }
.pill svg { width: 16px; height: 16px; }
.pill-dot { position: relative; width: 8px; height: 8px; border-radius: 50%; background: currentColor; box-shadow: 0 0 8px currentColor; }
.pill-normal { background: rgba(0, 230, 118, 0.15); color: var(--neon-emerald); border-color: rgba(0, 230, 118, 0.5); box-shadow: 0 0 20px rgba(0, 230, 118, 0.2), inset 0 1px 1px rgba(255,255,255,0.2); animation: popIn 0.5s var(--ease-spring) backwards; }
.pill-high { background: rgba(255, 42, 85, 0.15); color: var(--neon-coral); border-color: rgba(255, 42, 85, 0.5); animation: breatheCoral 2.5s ease-in-out infinite, popIn 0.5s var(--ease-spring) backwards; }
.pill-low { background: rgba(255, 196, 0, 0.15); color: var(--neon-amber); border-color: rgba(255, 196, 0, 0.5); animation: breatheAmber 2.5s ease-in-out infinite, popIn 0.5s var(--ease-spring) backwards; }

/* Dashboard Summary Panel */
.cl-summary { padding: 40px; display: grid; gap: 32px; margin: 16px 0 32px; border-radius: 32px; background: linear-gradient(145deg, rgba(20, 28, 45, 0.6), rgba(10, 15, 25, 0.4)); border: 1px solid rgba(0, 229, 255, 0.2); box-shadow: 0 20px 50px rgba(0,0,0,0.5), inset 0 0 40px rgba(0,229,255,0.05); }
.cl-summary-text { font-size: 1.25rem; line-height: 1.8; color: var(--text-bright); margin: 0; font-weight: 400; }
.cl-stats { display: flex; gap: 20px; flex-wrap: wrap; }
.cl-stat { flex: 1; min-width: 160px; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.08); padding: 24px; border-radius: 20px; display: flex; flex-direction: column; gap: 12px; box-shadow: inset 0 2px 15px rgba(255,255,255,0.03); position: relative; overflow: hidden; transition: transform 0.3s, border-color 0.3s; }
.cl-stat:hover { transform: translateY(-4px); border-color: rgba(255,255,255,0.2); }
.cl-stat::after { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 60%); opacity: 0; transition: opacity 0.3s; pointer-events: none; }
.cl-stat:hover::after { opacity: 1; }
.cl-stat-label { font: 700 13px 'JetBrains Mono', monospace; letter-spacing: 0.2em; text-transform: uppercase; color: var(--text-muted); z-index: 2; }
.cl-stat-value { font: 800 3.2rem/1 'JetBrains Mono', monospace; color: var(--text-main); z-index: 2; }
.cl-stat-normal .cl-stat-value { color: var(--neon-emerald); text-shadow: 0 0 30px rgba(0,230,118,0.4); }
.cl-stat-flagged .cl-stat-value { color: var(--neon-coral); text-shadow: 0 0 30px rgba(255,42,85,0.4); }

.cl-flag-tag { background: rgba(255,42,85,0.15); color: #fff; padding: 10px 18px; border-radius: 12px; font-weight: 600; font-size: 1rem; border: 1px solid rgba(255,42,85,0.4); box-shadow: 0 4px 15px rgba(255,42,85,0.2); display: inline-flex; align-items: center; gap: 8px; backdrop-filter: blur(5px); }
.cl-flag-tag::before { content: ''; display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--neon-coral); box-shadow: 0 0 10px var(--neon-coral); }
.cl-flag-list { display: flex; gap: 14px; flex-wrap: wrap; margin-top: 8px; }

/* Nutrition & Doctor Consultation */
.food-card { padding: 32px; display: flex; flex-direction: column; gap: 20px; }
.food-head { display: flex; justify-content: space-between; align-items: center; gap: 16px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 16px; }
.food-title { font-size: 1.4rem; font-weight: 700; margin: 0; color: var(--text-main); }
.food-body { font-size: 1.1rem; line-height: 1.9; color: rgba(255,255,255,0.9); margin: 0; white-space: pre-line; }
.food-body li { margin-bottom: 10px; }

/* Smooth Accordion Details */
.dq-list { display: flex; flex-direction: column; gap: 16px; margin-top: 20px; }
details.dq { margin-bottom: 0; transition: all 0.4s var(--ease-smooth); overflow: hidden; }
details.dq > summary { padding: 24px 30px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; list-style: none; gap: 16px; user-select: none; }
details.dq > summary::-webkit-details-marker { display: none; }
details.dq[open] { border-color: var(--neon-cyan); box-shadow: 0 16px 40px rgba(0, 229, 255, 0.2); background: rgba(0, 229, 255, 0.05); }

.dq-left { display: flex; align-items: center; gap: 20px; }
.dq-count { background: rgba(0, 229, 255, 0.2); color: var(--neon-cyan); border: 1px solid rgba(0,229,255,0.4); width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; border-radius: 12px; font: 800 16px 'JetBrains Mono', monospace; box-shadow: 0 0 20px rgba(0,229,255,0.3); }
.dq-name { font-size: 1.3rem; font-weight: 700; color: var(--text-main); }
.dq-right { display: flex; align-items: center; gap: 20px; }
.dq-chev { width: 26px; height: 26px; color: var(--text-muted); transition: transform 0.5s var(--ease-spring); }
details.dq[open] .dq-chev { transform: rotate(180deg); color: var(--neon-cyan); filter: drop-shadow(0 0 8px var(--neon-cyan)); }

.dq-body { max-height: 0; opacity: 0; transition: max-height 0.6s var(--ease-out), opacity 0.5s var(--ease-out), padding 0.5s var(--ease-out); padding: 0 30px; }
details.dq[open] .dq-body { max-height: 1200px; opacity: 1; padding: 0 30px 30px; }
.dq-body ol { list-style: none; counter-reset: q; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 16px; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 24px; }
.dq-body li { counter-increment: q; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.05); padding: 22px 26px; border-radius: 16px; font-size: 1.1rem; color: rgba(255,255,255,0.95); display: flex; gap: 20px; line-height: 1.7; transition: transform 0.3s, background 0.3s; }
.dq-body li:hover { transform: translateX(8px); background: rgba(0,229,255,0.05); border-color: rgba(0,229,255,0.2); }
.dq-body li::before { content: counter(q, decimal-leading-zero); font: 800 16px/1.5 'JetBrains Mono', monospace; color: var(--neon-cyan); flex-shrink: 0; background: rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 6px; height: fit-content; }

/* Streamlit Tabs Overrides */
.stTabs [data-baseweb="tab-list"] { background: var(--surface-glass); backdrop-filter: blur(30px); border-radius: 20px; padding: 10px; gap: 12px; border: 1px solid var(--border-glass); display: inline-flex; margin-bottom: 40px; box-shadow: 0 16px 40px rgba(0,0,0,0.4), inset 0 1px 2px rgba(255,255,255,0.1); }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 14px; padding: 14px 32px; transition: all 0.4s var(--ease-spring); border: none; color: var(--text-muted); font-weight: 700; font-size: 1.1rem; letter-spacing: 0.02em; }
.stTabs [data-baseweb="tab"]:hover { color: var(--text-bright); background: rgba(255,255,255,0.05); }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.05)) !important; color: var(--text-main) !important; box-shadow: 0 8px 25px rgba(0,0,0,0.3), inset 0 1px 1px rgba(255,255,255,0.2), inset 0 0 0 1px rgba(255,255,255,0.1); }
.stTabs [data-baseweb="tab-highlight"] { display: none; }

/* Buttons & Inputs */
.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, var(--neon-cyan), #0077ff) !important; color: #fff !important;
    border: none !important; border-radius: 16px !important; font-weight: 800 !important;
    padding: 0.8rem 1.6rem !important; font-size: 1.1rem !important; letter-spacing: 0.02em;
    box-shadow: 0 8px 25px rgba(0, 229, 255, 0.4), inset 0 2px 2px rgba(255,255,255,0.4) !important; transition: all 0.4s var(--ease-spring) !important; text-shadow: 0 1px 3px rgba(0,0,0,0.3);
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-5px) scale(1.03) !important; box-shadow: 0 15px 40px rgba(0, 229, 255, 0.6), inset 0 2px 2px rgba(255,255,255,0.5) !important;
}
.stButton > button:active { transform: translateY(2px) scale(0.98) !important; }

.st-key-change_prefs button { background: rgba(255,255,255,0.05) !important; color: var(--text-main) !important; border: 1px solid rgba(255,255,255,0.1) !important; box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important; backdrop-filter: blur(10px); }
.st-key-change_prefs button:hover { background: rgba(255,255,255,0.15) !important; border-color: rgba(255,255,255,0.3) !important; box-shadow: 0 8px 25px rgba(0,0,0,0.3) !important; }

/* Floating Spatial Onboarding */
.ob-card { animation: cardRise 0.8s var(--ease-spring) both, floatSlow 8s ease-in-out infinite; padding: 60px 48px; text-align: center; border: 1px solid rgba(0, 229, 255, 0.3); box-shadow: 0 30px 80px rgba(0,0,0,0.6), inset 0 0 60px rgba(0,229,255,0.1), inset 0 1px 1px rgba(255,255,255,0.2); margin-top: 60px; background: linear-gradient(180deg, rgba(15, 25, 45, 0.7), rgba(5, 10, 15, 0.9)); max-width: 600px; margin-left: auto; margin-right: auto; }
.ob-card .cl-logo { margin: 0 auto 32px; transform: scale(1.2); }
.ob-card:hover .cl-logo { transform: scale(1.3) rotateY(15deg); }
.ob-step { display: inline-block; font: 800 13px 'JetBrains Mono', monospace; letter-spacing: 0.3em; text-transform: uppercase; color: var(--neon-cyan); margin-bottom: 20px; background: rgba(0,229,255,0.15); padding: 8px 20px; border-radius: 999px; box-shadow: 0 0 20px rgba(0,229,255,0.2); }
.ob-title { font-size: 2.6rem; font-weight: 800; color: var(--text-main); margin: 0 0 20px; letter-spacing: -0.04em; text-shadow: 0 4px 20px rgba(0,0,0,0.5); }
.ob-desc { font-size: 1.2rem; line-height: 1.7; color: var(--text-bright); margin: 0 auto; max-width: 520px; opacity: 0.9; }

.cl-footer { margin-top: 80px; padding-top: 32px; border-top: 1px dashed rgba(255,255,255,0.1); text-align: center; font-size: 0.9rem; color: #5e6b82; letter-spacing: 0.02em; padding-bottom: 40px; }
</style>
"""
render_html(THEME_CSS)

# ULTRA-REALISTIC 3D GLOSSY SVG LOGO
RAW_SVG = """<svg width="100%" height="100%" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="orbGrad" cx="35%" cy="35%" r="65%">
            <stop offset="0%" stop-color="#ffffff" />
            <stop offset="20%" stop-color="#b3ffff" />
            <stop offset="50%" stop-color="#00e5ff" />
            <stop offset="85%" stop-color="#0055ff" />
            <stop offset="100%" stop-color="#00081a" />
        </radialGradient>
        <linearGradient id="glassReflection" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#ffffff" stop-opacity="0.95" />
            <stop offset="35%" stop-color="#ffffff" stop-opacity="0.25" />
            <stop offset="100%" stop-color="#ffffff" stop-opacity="0" />
        </linearGradient>
        <filter id="glowEffect" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <filter id="dropShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="#000" flood-opacity="0.6"/>
        </filter>
    </defs>
    <!-- Outer Glow -->
    <circle cx="50" cy="50" r="48" fill="rgba(0,229,255,0.1)" filter="url(#glowEffect)"/>
    <!-- 3D Orb -->
    <circle cx="50" cy="50" r="46" fill="url(#orbGrad)" filter="url(#dropShadow)"/>
    <!-- Inner Border Highlight -->
    <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.8)" stroke-width="1.5"/>
    <!-- Medical Cross Substrate -->
    <path d="M42 26 h16 v16 h16 v16 h-16 v16 h-16 v-16 h-16 v-16 h16 z" fill="rgba(255,255,255,0.15)"/>
    <!-- Bright White Heartbeat Pulse -->
    <path d="M 8 52 L 26 52 L 36 20 L 55 90 L 68 40 L 78 52 L 92 52" 
          fill="none" stroke="#ffffff" stroke-width="5.5" 
          stroke-linecap="round" stroke-linejoin="round" 
          filter="url(#glowEffect)"/>
    <!-- Top Glass Glossy Shine -->
    <ellipse cx="50" cy="22" rx="34" ry="14" fill="url(#glassReflection)"/>
</svg>"""
B64_LOGO = base64.b64encode(RAW_SVG.encode('utf-8')).decode('utf-8')
ICON_LOGO = f'<img src="data:image/svg+xml;base64,{B64_LOGO}" alt="Logo" style="filter: drop-shadow(0px 8px 12px rgba(0,229,255,0.5));" />'
ICON_UP = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>'
ICON_DOWN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>'
ICON_CHEV = '<svg class="dq-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>'

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
        "system_status": "Groq LPU Engine Active",
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
        "system_status": "ग्रोक एआई डायग्नोस्टिक सक्रिय है",
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
# Helpers shared by the pipeline and the UI
# ---------------------------------------------------------
NUM_RE = r"-?\d+(?:\.\d+)?"

def to_float(v):
    try:
        return float(v) if v is not None and v != "" else None
    except (TypeError, ValueError):
        return None

# ---------------------------------------------------------
# Document Text Extraction (page-wise, OCR only where needed)
# ---------------------------------------------------------
MODEL = "llama-3.1-8b-instant" # Safe fallback for broad access on Groq, change back to oss-120b if preferred
MAX_PAGES = 40
CHUNK_CHARS = 9000
OCR_DPI = 130
MAX_SIDE = 1600
MAX_FILE_MB = 25

def _ocr_page(file_bytes, page_no):
    """OCR a single PDF page (1-indexed). Rendering one page at a time keeps memory low."""
    try:
        imgs = pdf2image.convert_from_bytes(
            file_bytes, first_page=page_no, last_page=page_no, dpi=OCR_DPI, fmt="jpeg"
        )
        img = imgs[0]
        w, h = img.size
        if max(w, h) > MAX_SIDE:
            r = MAX_SIDE / max(w, h)
            img = img.resize((int(w * r), int(h * r)), Image.LANCZOS)
        return pytesseract.image_to_string(img)
    except Exception as e:
        print(f"OCR error p{page_no}: {e}")
        return ""

def extract_pages(file_bytes, filename, mime_type):
    if pytesseract is not None and sys.platform.startswith("win"):
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    is_pdf = "pdf" in (mime_type or "").lower() or filename.lower().endswith(".pdf")
    pages = []

    if is_pdf:
        # 1. Native text layer (fast, clean)
        if pypdf is not None:
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                for p in reader.pages[:MAX_PAGES]:
                    pages.append(p.extract_text() or "")
            except Exception:
                pages = []
        # 2. OCR only the pages that have no usable text layer
        if pdf2image is not None and pytesseract is not None:
            if not pages:   # pypdf failed entirely -> OCR blindly
                pages = [""] * MAX_PAGES
            todo = [i for i, t in enumerate(pages) if len(t.strip()) < 40]
            if todo:
                with ThreadPoolExecutor(max_workers=4) as ex:
                    results = list(ex.map(lambda i: _ocr_page(file_bytes, i + 1), todo))
                for i, txt in zip(todo, results):
                    pages[i] = txt
    elif pytesseract is not None:
        try:
            img = Image.open(io.BytesIO(file_bytes))
            w, h = img.size
            if max(w, h) > MAX_SIDE:
                r = MAX_SIDE / max(w, h)
                img = img.resize((int(w * r), int(h * r)), Image.LANCZOS)
            pages = [pytesseract.image_to_string(img)]
        except Exception as e:
            print(f"Image OCR Error: {e}")
    return pages

NOISE = re.compile(
    r"(page \d+|www\.|https?:|@|\bphone\b|\btel\b|\bfax\b|address|disclaimer|nabl|barcode|"
    r"collected|registered|printed|reported on|end of report|lab id|sample id|reg\.? no|"
    r"patient id|referred by|dr\.)", re.I)
RANGE = re.compile(r"\d+(?:\.\d+)?\s*(?:-|–|to)\s*\d+(?:\.\d+)?|[<>≤≥]\s*\d")

def condense(pages):
    """Keep only lines likely to carry results; drop duplicates, paragraphs and boilerplate."""
    seen, out = set(), []
    for text in pages:
        for line in text.splitlines():
            line = re.sub(r"\s+", " ", line).strip()
            if len(line) < 3:
                continue
            key = line.lower()
            if key in seen:
                continue
            seen.add(key)
            has_digit = any(c.isdigit() for c in line)
            if has_digit:
                if NOISE.search(line) and not RANGE.search(line):
                    continue
                out.append(line[:200])
            elif len(line) <= 40:       # likely a test / section name on its own line
                out.append(line)
    return out

def chunk_lines(lines, size=CHUNK_CHARS):
    chunks, cur, n = [], [], 0
    for ln in lines:
        if n + len(ln) > size and cur:
            chunks.append("\n".join(cur))
            cur, n = [], 0
        cur.append(ln)
        n += len(ln) + 1
    if cur:
        chunks.append("\n".join(cur))
    return chunks

# ---------------------------------------------------------
# GROQ LPU ENGINE (multi-stage, token-safe for large files)
# ---------------------------------------------------------
SYS = "You are a clinical lab analysis engine. Respond only with valid JSON."

def call_groq(client, system, user, max_tokens, retries=5):
    """One Groq call with JSON mode, low reasoning effort, and rate-limit-aware retries."""
    last = None
    for attempt in range(retries):
        try:
            r = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=max_tokens,
                # reasoning_effort="low",  # Removed if using models that don't support it directly, add back if supported
            )
            return json.loads(r.choices[0].message.content)
        except json.JSONDecodeError as e:
            last = e
        except Exception as e:
            last = e
            msg = str(e).lower()
            if "429" in msg or "rate" in msg or "413" in msg:
                m = re.search(r"try again in ([\d.]+)\s*(ms|s|m)\b", msg)
                wait = 3 * (attempt + 1)
                if m:
                    v = float(m.group(1))
                    wait = v / 1000 if m.group(2) == "ms" else v * 60 if m.group(2) == "m" else v
                time.sleep(min(wait + 1, 40))
                continue
            raise
    raise last

def _status(item):
    """Compute high/low/normal in Python from value + reference range (zero tokens)."""
    v, lo, hi = to_float(item.get("v")), to_float(item.get("lo")), to_float(item.get("hi"))
    if v is not None and (lo is not None or hi is not None):
        if hi is not None and v > hi:
            return "high"
        if lo is not None and v < lo:
            return "low"
        return "normal"
    return {"H": "high", "L": "low"}.get(str(item.get("f", "N")).upper(), "normal")

def analyze_report_with_groq(file_bytes, filename, mime_type, target_lang, target_diet, api_key):
    try:
        if Groq is None:
            return None, "groq library not installed. Run: pip install groq"
        if not api_key or not api_key.strip():
            return None, "GROQ_API_KEY not found. Add it to .streamlit/secrets.toml or set it as an environment variable."
        if len(file_bytes) > MAX_FILE_MB * 1024 * 1024:
            return None, f"File is larger than {MAX_FILE_MB} MB. Please use a lower-resolution scan."

        pages = extract_pages(file_bytes, filename, mime_type)
        lines = condense(pages)
        if not lines:
            return None, "Could not extract text from document. Please ensure it is a clear scan."

        client = Groq(api_key=api_key.strip())

        # ---- Stage 1: compact extraction, chunk by chunk ----
        found, seen = [], set()
        for chunk in chunk_lines(lines):
            prompt = f"""Extract every lab test result from this report text.
Return JSON: {{"r":[{{"n":"test name (English)","c":"category","v":number or null,"u":"unit","lo":number or null,"hi":number or null,"f":"H"|"L"|"N"}}]}}
"f" = flag printed in the report (H/L/N). For ranges like "<200" use hi=200, lo=null.
Ignore IDs, addresses, doctor names, notes. Never invent values.

TEXT:
{chunk}"""
            data = call_groq(client, SYS, prompt, max_tokens=3000)
            for it in data.get("r", []):
                key = (str(it.get("n", "")).lower(), str(it.get("v")))
                if it.get("n") and key not in seen:
                    seen.add(key)
                    found.append(it)

        if not found:
            return None, None   # UI shows the "no results" message

        for it in found:
            it["code"] = _status(it)

        # ---- Stage 2: explanations only for abnormal biomarkers ----
        abnormal = [i for i, it in enumerate(found) if it["code"] != "normal"]
        batch_size = 8 if target_lang == "English" else 4   # Indic scripts cost more tokens
        for s in range(0, len(abnormal), batch_size):
            idxs = abnormal[s:s + batch_size]
            items = [{"i": i, "n": found[i]["n"], "v": found[i].get("v"),
                      "u": found[i].get("u"), "status": found[i]["code"]} for i in idxs]
            prompt = f"""Language for ALL text values: {target_lang}. Diet: {target_diet} (Indian cuisine).
For each abnormal lab result below return JSON:
{{"items":[{{"i":<same index>,"e":"1-2 sentence simple explanation","f":"3-4 specific Indian {target_diet} food suggestions","q":["question 1","question 2"]}}]}}

RESULTS:
{json.dumps(items, ensure_ascii=False)}"""
            out = call_groq(client, SYS, prompt,
                            max_tokens=2500 if target_lang == "English" else 4000)
            for e in out.get("items", []):
                try:
                    j = int(e.get("i"))
                except (TypeError, ValueError):
                    continue
                if 0 <= j < len(found):
                    found[j]["e"] = e.get("e", "")
                    found[j]["fd"] = e.get("f", "")
                    found[j]["q"] = e.get("q", [])

        # ---- Summary (tiny call) ----
        brief = [f'{it["n"]}: {it.get("v")} {it.get("u", "")} ({it["code"]})' for it in found]
        sm = call_groq(
            client, SYS,
            f'Write a 2-3 sentence overview in {target_lang} of these lab results. '
            f'Return {{"summary":"..."}}.\n' + "\n".join(brief[:80]),
            max_tokens=600,
        )

        params = []
        for it in found:
            v, u = it.get("v"), it.get("u") or ""
            params.append({
                "name": it["n"], "category": it.get("c", ""),
                "value": f"{v} {u}".strip() if v is not None else "",
                "numeric_value": v, "unit": u,
                "ref_low": it.get("lo"), "ref_high": it.get("hi"),
                "status_code": it["code"],
                "explanation": it.get("e", ""),
                "food_remedies": it.get("fd", ""),
                "questions_for_doctor": it.get("q", []),
            })
        return {"summary": sm.get("summary", ""), "parameters": params}, None

    except Exception as e:
        return None, f"Groq Execution Error: {e}"

# ---------------------------------------------------------
# Normalization & UI Builders
# ---------------------------------------------------------
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
        "food": param.get("food", "") or param.get("food_remedies", ""),
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
    <article class="metric-card {state_cls}" style="animation-delay:{index * 80}ms">
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
    <details class="dq" {'open' if is_open else ''} style="animation-delay:{index * 60}ms">
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
    <div style="margin-top:24px">
        <p class="cl-eyebrow">01</p>
        <h2 class="cl-h2">{esc(L['upload_header'])}</h2>
        <p class="cl-sub" style="margin-bottom:16px; color: var(--text-muted); font-size: 1.1rem;">{esc(L['upload_desc'])}</p>
    </div>
    """)

    uploaded_file = st.file_uploader(L["upload_label"], type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed")

    parsed_report_data = None
    error_notice = None

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "application/pdf"

        if uploaded_file.size > 6 * 1024 * 1024:
            st.info("Large file detected. It will be processed in chunks, so this may take a minute.")

        cache_key = (
            hashlib.sha256(file_bytes).hexdigest(),
            st.session_state.selected_lang,
            st.session_state.selected_diet,
        )
        parsed_report_data = st.session_state.analysis_cache.get(cache_key)

        if parsed_report_data is None:
            with st.spinner("Decoding report structures & extracting biomarker matrix..."):
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
            render_html(f'<div class="cl-empty" style="margin-top:20px; padding: 20px; text-align: center; color: var(--neon-amber); background: rgba(255,196,0,0.1); border-radius: 12px;">{esc(L["no_results"])}</div>')

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
                <p class="cl-eyebrow" style="margin-top:16px;">02</p>
                <h2 class="cl-h2">{esc(L['missing_title'])}</h2>
                <div class="metric-grid">{cards}</div>
            </section>
            """)

        with tab_food:
            food_cards = "".join(
                f"""
                <article class="food-card" style="animation-delay:{i * 80}ms">
                    <header class="food-head"><h3 class="food-title">{esc(b['name'])}</h3>{status_pill(b['code'])}</header>
                    <div class="food-body">{b['food'].replace('-', '•')}</div>
                </article>
                """
                for i, b in enumerate(biomarkers_sorted) if b["food"]
            )
            render_html(f"""
            <section aria-label="{esc(L['food_title'])}">
                <p class="cl-eyebrow" style="margin-top:16px;">03</p>
                <h2 class="cl-h2">{esc(L['food_title'])}</h2>
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
                    <p class="cl-eyebrow" style="margin-top:16px;">04</p>
                    <h2 class="cl-h2">{esc(L['questions_title'])}</h2>
                    <p class="cl-tagline" style="margin-bottom:24px;">{esc(L['questions_hint'])}</p>
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
