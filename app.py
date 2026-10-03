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
# Theme: Glassmorphism 3.0 — aurora, orbiting borders, ECG motion
# ---------------------------------------------------------
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

@property --ang { syntax: '<angle>'; initial-value: 0deg; inherits: false; }

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
    --neon-violet: #7c4dff;
    --ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
    --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
}

/* ---------- Global ---------- */
html, body, .stApp, [class*="css"], .stMarkdown, button, input, label {
    font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp { background: var(--bg-deep) !important; color: var(--text-main); }
.stApp::before {
    content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
    background: radial-gradient(circle at 15% 0%, rgba(0, 229, 255, 0.06) 0%, transparent 40%),
                radial-gradient(circle at 85% 100%, rgba(0, 230, 118, 0.04) 0%, transparent 40%);
}
header[data-testid="stHeader"] { background: transparent !important; }
.block-container { max-width: 1200px; padding-top: 2rem !important; padding-bottom: 4rem !important; position: relative; z-index: 1; }

/* ---------- Aurora background ---------- */
.aurora { position: fixed; inset: 0; overflow: hidden; pointer-events: none; z-index: 0; }
.aurora i { position: absolute; border-radius: 50%; filter: blur(100px); will-change: transform; }
.aurora i:nth-child(1) { width: 560px; height: 560px; left: -140px; top: -120px; background: rgba(0, 229, 255, 0.16); animation: drift1 24s ease-in-out infinite alternate; }
.aurora i:nth-child(2) { width: 520px; height: 520px; right: -160px; top: 28%; background: rgba(0, 230, 118, 0.10); animation: drift2 29s ease-in-out infinite alternate; }
.aurora i:nth-child(3) { width: 480px; height: 480px; left: 30%; bottom: -220px; background: rgba(124, 77, 255, 0.13); animation: drift3 33s ease-in-out infinite alternate; }
@keyframes drift1 { to { transform: translate(220px, 160px) scale(1.2); } }
@keyframes drift2 { to { transform: translate(-260px, -120px) scale(1.15); } }
@keyframes drift3 { to { transform: translate(-200px, -140px) scale(1.25); } }

/* ---------- Keyframes ---------- */
@keyframes cardRise {
    from { opacity: 0; transform: translateY(28px) scale(0.97); filter: blur(10px); }
    to   { opacity: 1; transform: translateY(0) scale(1); filter: none; }
}
@keyframes floatSlow { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
@keyframes breatheCoral {
    0%, 100% { box-shadow: 0 0 12px rgba(255, 23, 68, 0.25); border-color: rgba(255, 23, 68, 0.4); }
    50% { box-shadow: 0 0 28px rgba(255, 23, 68, 0.6); border-color: rgba(255, 23, 68, 0.9); }
}
@keyframes breatheAmber {
    0%, 100% { box-shadow: 0 0 12px rgba(255, 196, 0, 0.25); border-color: rgba(255, 196, 0, 0.4); }
    50% { box-shadow: 0 0 28px rgba(255, 196, 0, 0.6); border-color: rgba(255, 196, 0, 0.9); }
}
@keyframes scanline { 0% { top: 0; opacity: 0; } 15% { opacity: 1; } 85% { opacity: 1; } 100% { top: 100%; opacity: 0; } }
@keyframes dotPulse {
    0% { box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.5); }
    70% { box-shadow: 0 0 0 12px rgba(0, 229, 255, 0); }
    100% { box-shadow: 0 0 0 0 rgba(0, 229, 255, 0); }
}
@keyframes gradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
@keyframes spinAng { to { --ang: 360deg; } }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes popIn { from { opacity: 0; transform: scale(0.6); } to { opacity: 1; transform: scale(1); } }
@keyframes slideIn { from { opacity: 0; transform: translateX(-16px); } to { opacity: 1; transform: translateX(0); } }
@keyframes accIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes panelIn { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
@keyframes markerIn { from { left: 0%; } }
@keyframes growX { from { transform: scaleX(0); } }
@keyframes ringFill { from { stroke-dasharray: 0 276.5; } }
@keyframes barGlow { 0%, 100% { opacity: 0.75; } 50% { opacity: 1; } }
@keyframes orbPulse { 0%, 100% { transform: scale(1); filter: drop-shadow(0 0 8px rgba(0,229,255,0.4)); } 50% { transform: scale(1.1); filter: drop-shadow(0 0 20px rgba(0,229,255,0.9)); } }
@keyframes ecgDraw { 0% { stroke-dashoffset: 420; opacity: 1; } 70% { stroke-dashoffset: 0; opacity: 1; } 100% { stroke-dashoffset: 0; opacity: 0; } }
@keyframes stepCycle {
    0% { opacity: 0; transform: translateY(10px); }
    5%, 30% { opacity: 1; transform: translateY(0); }
    35%, 100% { opacity: 0; transform: translateY(-10px); }
}
@keyframes draw { to { stroke-dashoffset: 0; } }
@keyframes shine { from { left: -60%; } to { left: 130%; } }

/* ---------- Typography ---------- */
.cl-title {
    font-size: 2.2rem; font-weight: 700; letter-spacing: -0.04em; margin: 0;
    background: linear-gradient(120deg, #ffffff 0%, #a3b1c6 35%, #00e5ff 60%, #ffffff 100%);
    background-size: 220% 220%; animation: gradientShift 9s ease infinite;
    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.cl-tagline { font-size: 1.05rem; color: var(--text-muted); margin-top: 4px; font-weight: 500; }
.cl-sub { font-size: 1.02rem; color: var(--text-muted); line-height: 1.6; }
.cl-h2 { font-size: 1.6rem; font-weight: 700; letter-spacing: -0.03em; color: var(--text-main); margin-bottom: 8px; }
.cl-eyebrow { font: 600 12px/1 'JetBrains Mono', monospace; letter-spacing: 0.2em; text-transform: uppercase; color: var(--neon-cyan); margin-bottom: 8px; }

/* ---------- Header ---------- */
.cl-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 24px; border-bottom: 1px solid var(--border-glass); margin-bottom: 24px; flex-wrap: wrap; gap: 20px; animation: cardRise 0.8s var(--ease-out) backwards; }
.cl-brand { display: flex; align-items: center; gap: 20px; }
.cl-logo {
    position: relative; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center;
    background: rgba(0, 10, 20, 0.5); border: 1px solid rgba(0, 229, 255, 0.4); border-radius: 18px;
    box-shadow: 0 8px 30px rgba(0, 229, 255, 0.25), inset 0 0 20px rgba(0,229,255,0.1); backdrop-filter: blur(12px);
}
.cl-logo::after { content: ""; position: absolute; inset: -6px; border-radius: 22px; border: 1px dashed rgba(0, 229, 255, 0.35); animation: spin 14s linear infinite; pointer-events: none; }
.cl-logo img, .cl-logo svg { width: 44px; height: 44px; }
.cl-ecg { flex: 1; min-width: 120px; max-width: 280px; height: 44px; opacity: 0.6; }
@media (max-width: 900px) { .cl-ecg { display: none; } }
.ecg-line, .cl-ecg path { fill: none; stroke: var(--neon-cyan); stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 420; stroke-dashoffset: 420; animation: ecgDraw 2.6s linear infinite; filter: drop-shadow(0 0 6px rgba(0,229,255,0.8)); }
.cl-chip { display: inline-flex; align-items: center; gap: 10px; padding: 8px 18px; border-radius: 999px; background: rgba(0, 229, 255, 0.05); border: 1px solid rgba(0, 229, 255, 0.3); font: 500 13px 'JetBrains Mono', monospace; color: var(--neon-cyan); box-shadow: 0 0 20px rgba(0, 229, 255, 0.1); backdrop-filter: blur(8px); }
.cl-chip-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--neon-cyan); animation: dotPulse 2s infinite; }
.cl-prefs { display: flex; gap: 24px; flex-wrap: wrap; margin: 16px 0 8px; font-size: 0.95rem; color: var(--text-muted); animation: slideIn 0.7s var(--ease-out) 0.15s backwards; }
.cl-prefs strong { color: var(--text-main); font-weight: 600; padding: 4px 10px; background: rgba(255,255,255,0.05); border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); }

/* ---------- Uploader ---------- */
[data-testid="stFileUploaderDropzone"] {
    position: relative; overflow: hidden; background: var(--surface-glass) !important;
    border: 1px dashed rgba(0, 229, 255, 0.4) !important; border-radius: 20px !important;
    transition: all 0.4s var(--ease-out) !important; backdrop-filter: blur(12px);
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--neon-cyan) !important; background: var(--surface-glass-hover) !important;
    box-shadow: 0 0 50px rgba(0, 229, 255, 0.2) !important; transform: scale(1.008);
}
[data-testid="stFileUploaderDropzone"]::after {
    content: ""; position: absolute; left: 0; right: 0; top: 0; height: 2px;
    background: var(--neon-cyan); box-shadow: 0 0 12px var(--neon-cyan), 0 0 24px var(--neon-cyan);
    animation: scanline 3s linear infinite; pointer-events: none;
}

/* ---------- Glass cards ---------- */
.metric-card, .food-card, .cl-summary, .ob-card, details.dq {
    position: relative;
    background: var(--surface-glass); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border-glass); border-radius: 24px; box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
    animation: cardRise 0.8s var(--ease-spring) backwards;
    transition: transform 0.45s var(--ease-out), box-shadow 0.45s var(--ease-out), border-color 0.45s var(--ease-out);
}
.metric-card:hover, .food-card:hover {
    transform: translateY(-8px) scale(1.015); border-color: rgba(255, 255, 255, 0.2);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), 0 0 30px rgba(0, 229, 255, 0.08);
}
/* light sweep on hover */
.metric-card::after, .food-card::after {
    content: ""; position: absolute; top: 0; left: -60%; width: 40%; height: 100%;
    background: linear-gradient(100deg, transparent, rgba(255,255,255,0.08), transparent);
    transform: skewX(-20deg); pointer-events: none;
}
.metric-card:hover::after, .food-card:hover::after { animation: shine 0.9s var(--ease-out); }
.food-card { overflow: hidden; }

/* rotating gradient border on hero panels */
.cl-summary::before, .ob-card::before {
    content: ""; position: absolute; inset: 0; border-radius: inherit; padding: 1.5px; pointer-events: none;
    background: conic-gradient(from var(--ang), transparent 0%, var(--neon-cyan) 10%, transparent 24%, var(--neon-emerald) 52%, transparent 68%, var(--neon-violet) 85%, transparent 100%);
    -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
    -webkit-mask-composite: xor; mask-composite: exclude;
    animation: spinAng 7s linear infinite;
}

/* ---------- Metric cards ---------- */
.metric-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; margin-top: 12px; }
.metric-card { padding: 26px; overflow: hidden; display: flex; flex-direction: column; justify-content: space-between; }
.metric-card.is-flagged { border-color: rgba(255, 23, 68, 0.35); background: linear-gradient(180deg, rgba(255, 23, 68, 0.04) 0%, transparent 100%), var(--surface-glass); }
.metric-card.is-flagged:hover { box-shadow: 0 20px 50px rgba(255, 23, 68, 0.15); border-color: rgba(255, 23, 68, 0.7); }
.metric-card.is-low { border-color: rgba(255, 196, 0, 0.35); background: linear-gradient(180deg, rgba(255, 196, 0, 0.04) 0%, transparent 100%), var(--surface-glass); }
.metric-card.is-low:hover { box-shadow: 0 20px 50px rgba(255, 196, 0, 0.15); border-color: rgba(255, 196, 0, 0.7); }
.flag-bar { position: absolute; top: 0; left: 0; right: 0; height: 4px; background: var(--neon-coral); box-shadow: 0 0 15px var(--neon-coral); animation: barGlow 2.4s ease-in-out infinite; }
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
.range-safe { position: absolute; top: 0; bottom: 0; background: rgba(0, 230, 118, 0.25); border-radius: 999px; border: 1px solid rgba(0, 230, 118, 0.5); transform-origin: left center; animation: growX 1s var(--ease-out) 0.2s backwards; }
.range-marker { position: absolute; top: 50%; width: 18px; height: 18px; transform: translate(-50%, -50%); border-radius: 50%; background: var(--neon-emerald); box-shadow: 0 0 16px var(--neon-emerald), inset 0 0 0 4px var(--bg-deep); z-index: 2; animation: markerIn 1.5s var(--ease-spring) 0.35s backwards; }
.metric-card.is-flagged .range-marker { background: var(--neon-coral); box-shadow: 0 0 16px var(--neon-coral), inset 0 0 0 4px var(--bg-deep); }
.metric-card.is-low .range-marker { background: var(--neon-amber); box-shadow: 0 0 16px var(--neon-amber), inset 0 0 0 4px var(--bg-deep); }
.range-labels { display: flex; justify-content: space-between; font: 500 12px 'JetBrains Mono', monospace; color: var(--text-muted); }
.metric-explain { padding-top: 18px; margin-top: 18px; border-top: 1px dashed rgba(255,255,255,0.1); font-size: 0.98rem; line-height: 1.6; color: rgba(255,255,255,0.85); margin-bottom: 0; }
.metric-explain strong { color: var(--text-main); font-weight: 600; display: block; margin-bottom: 6px; }

/* ---------- Pills ---------- */
.pill { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px; font: 700 11px/1 'JetBrains Mono', monospace; letter-spacing: 0.12em; text-transform: uppercase; white-space: nowrap; border: 1px solid transparent; }
.pill svg { width: 14px; height: 14px; }
.pill-dot { position: relative; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.pill-dot::after { content: ""; position: absolute; inset: 0; border-radius: 50%; background: currentColor; animation: dotPulse 2.5s infinite; }
.pill-normal { background: rgba(0, 230, 118, 0.12); color: var(--neon-emerald); border-color: rgba(0, 230, 118, 0.4); box-shadow: 0 0 15px rgba(0, 230, 118, 0.15); }
.pill-high { background: rgba(255, 23, 68, 0.12); color: var(--neon-coral); animation: breatheCoral 2.5s ease-in-out infinite; }
.pill-low { background: rgba(255, 196, 0, 0.12); color: var(--neon-amber); animation: breatheAmber 2.5s ease-in-out infinite; }

/* ---------- Summary panel ---------- */
.cl-summary { padding: 36px; display: grid; gap: 28px; margin: 32px 0 16px; border-radius: 28px; }
.cl-summary-top { display: flex; align-items: center; gap: 32px; flex-wrap: wrap; }
.cl-summary-copy { flex: 1; min-width: 260px; }
.cl-summary-text { font-size: 1.15rem; line-height: 1.7; color: rgba(255,255,255,0.95); margin: 0; }
.ring { position: relative; width: 132px; height: 132px; flex-shrink: 0; }
.ring svg { width: 100%; height: 100%; filter: drop-shadow(0 0 10px rgba(0,230,118,0.45)); }
.ring-bg { fill: none; stroke: rgba(255,255,255,0.07); stroke-width: 8; }
.ring-fg { fill: none; stroke: var(--neon-emerald); stroke-width: 8; stroke-linecap: round; animation: ringFill 1.8s var(--ease-out) 0.3s backwards; }
.ring.mid svg { filter: drop-shadow(0 0 10px rgba(255,196,0,0.45)); } .ring.mid .ring-fg { stroke: var(--neon-amber); }
.ring.low svg { filter: drop-shadow(0 0 10px rgba(255,23,68,0.45)); } .ring.low .ring-fg { stroke: var(--neon-coral); }
.ring-label { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.ring-pct { font: 700 1.9rem/1 'JetBrains Mono', monospace; color: var(--text-main); }
.ring-cap { font: 600 9px/1.3 'JetBrains Mono', monospace; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-muted); margin-top: 6px; text-align: center; max-width: 78px; }
.cl-stats { display: flex; gap: 16px; flex-wrap: wrap; }
.cl-stat { flex: 1; min-width: 150px; background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); padding: 22px; border-radius: 18px; display: flex; flex-direction: column; gap: 10px; box-shadow: inset 0 2px 10px rgba(255,255,255,0.02); animation: popIn 0.6s var(--ease-spring) backwards; transition: transform 0.35s var(--ease-out), border-color 0.35s var(--ease-out); }
.cl-stat:hover { transform: translateY(-4px); border-color: rgba(255,255,255,0.18); }
.cl-stat-label { font: 600 12px 'JetBrains Mono', monospace; letter-spacing: 0.18em; text-transform: uppercase; color: var(--text-muted); }
.cl-stat-value { font: 700 2.8rem/1 'JetBrains Mono', monospace; color: var(--text-main); }
.cl-stat-normal .cl-stat-value { color: var(--neon-emerald); text-shadow: 0 0 20px rgba(0,230,118,0.3); }
.cl-stat-flagged .cl-stat-value { color: var(--neon-coral); text-shadow: 0 0 20px rgba(255,23,68,0.3); }
.cl-flag-tag { background: rgba(255,23,68,0.15); color: var(--neon-coral); padding: 8px 14px; border-radius: 10px; font-weight: 600; font-size: 0.9rem; border: 1px solid rgba(255,23,68,0.3); box-shadow: 0 0 12px rgba(255,23,68,0.15); animation: popIn 0.5s var(--ease-spring) backwards; }
.cl-flag-list { display: flex; gap: 12px; flex-wrap: wrap; }

/* ---------- Nutrition & Doctor ---------- */
.food-card { padding: 28px; display: flex; flex-direction: column; gap: 18px; }
.food-head { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.food-title { font-size: 1.25rem; font-weight: 600; margin: 0; color: var(--text-main); }
.food-body { font-size: 1.05rem; line-height: 1.8; color: rgba(255,255,255,0.85); margin: 0; white-space: pre-line; }
.dq-list { display: flex; flex-direction: column; gap: 14px; margin-top: 16px; }
details.dq { margin-bottom: 0; }
details.dq:hover { border-color: rgba(255,255,255,0.18); }
details.dq > summary { padding: 22px 26px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; list-style: none; gap: 16px; }
details.dq > summary::-webkit-details-marker { display: none; }
details.dq[open] { border-color: rgba(0, 229, 255, 0.4); box-shadow: 0 12px 32px rgba(0, 229, 255, 0.15); background: rgba(0, 229, 255, 0.03); }
.dq-left { display: flex; align-items: center; gap: 16px; }
.dq-count { background: rgba(0, 229, 255, 0.15); color: var(--neon-cyan); border: 1px solid rgba(0,229,255,0.3); width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 10px; font: 700 15px 'JetBrains Mono', monospace; box-shadow: 0 0 15px rgba(0,229,255,0.2); }
.dq-name { font-size: 1.15rem; font-weight: 600; color: var(--text-main); }
.dq-right { display: flex; align-items: center; gap: 16px; }
.dq-chev { width: 22px; height: 22px; color: var(--text-muted); transition: transform 0.4s var(--ease-spring), color 0.3s; }
details.dq[open] .dq-chev { transform: rotate(180deg); color: var(--neon-cyan); }
.dq-body { padding: 0 26px 26px; }
details.dq[open] .dq-body { animation: accIn 0.45s var(--ease-out); }
.dq-body ol { list-style: none; counter-reset: q; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 14px; }
.dq-body li { counter-increment: q; background: rgba(0,0,0,0.3); border: 1px solid var(--border-glass); padding: 18px 20px; border-radius: 14px; font-size: 1.05rem; color: rgba(255,255,255,0.9); display: flex; gap: 18px; line-height: 1.6; animation: slideIn 0.55s var(--ease-out) backwards; transition: transform 0.3s var(--ease-out), border-color 0.3s; }
.dq-body li:hover { transform: translateX(6px); border-color: rgba(0,229,255,0.35); }
.dq-body li:nth-child(1) { animation-delay: 0.05s; } .dq-body li:nth-child(2) { animation-delay: 0.13s; }
.dq-body li:nth-child(3) { animation-delay: 0.21s; } .dq-body li:nth-child(4) { animation-delay: 0.29s; }
.dq-body li::before { content: counter(q, decimal-leading-zero); font: 700 15px/1.5 'JetBrains Mono', monospace; color: var(--neon-cyan); flex-shrink: 0; }

/* ---------- Empty states ---------- */
.cl-empty { margin-top: 20px; padding: 28px; border-radius: 20px; background: var(--surface-glass); border: 1px dashed rgba(255,196,0,0.4); color: rgba(255,255,255,0.85); animation: cardRise 0.7s var(--ease-spring) backwards; }
.cl-empty-state { display: flex; align-items: center; gap: 22px; padding: 30px 32px; border-radius: 24px; background: var(--surface-glass); backdrop-filter: blur(20px); border: 1px solid rgba(0,230,118,0.3); box-shadow: 0 0 40px rgba(0,230,118,0.08); margin-top: 12px; animation: cardRise 0.8s var(--ease-spring) backwards; }
.cl-empty-state.warn { border-color: rgba(255,196,0,0.35); box-shadow: 0 0 40px rgba(255,196,0,0.08); }
.cl-empty-state p { margin: 0; font-size: 1.08rem; line-height: 1.7; color: rgba(255,255,255,0.9); }
.es-icon { width: 54px; height: 54px; flex-shrink: 0; color: var(--neon-emerald); filter: drop-shadow(0 0 10px rgba(0,230,118,0.6)); }
.cl-empty-state.warn .es-icon { color: var(--neon-amber); filter: drop-shadow(0 0 10px rgba(255,196,0,0.6)); }
.es-icon svg { width: 100%; height: 100%; }
.es-icon circle { stroke-dasharray: 64; stroke-dashoffset: 64; animation: draw 1s var(--ease-out) forwards; }
.es-icon path { stroke-dasharray: 20; stroke-dashoffset: 20; animation: draw 0.7s var(--ease-out) 0.5s forwards; }

/* ---------- Loader ---------- */
.ld { display: flex; flex-direction: column; align-items: center; gap: 22px; padding: 48px 24px; margin-top: 24px; text-align: center; background: var(--surface-glass); border: 1px solid rgba(0,229,255,0.2); border-radius: 28px; backdrop-filter: blur(20px); box-shadow: 0 0 60px rgba(0,229,255,0.08); animation: cardRise 0.6s var(--ease-spring) backwards; }
.ld-orb { position: relative; width: 104px; height: 104px; display: flex; align-items: center; justify-content: center; }
.ld-orb::before { content: ""; position: absolute; inset: 0; border-radius: 50%; border: 2px solid transparent; border-top-color: var(--neon-cyan); border-right-color: var(--neon-emerald); animation: spin 1.1s linear infinite; }
.ld-orb::after { content: ""; position: absolute; inset: 10px; border-radius: 50%; border: 2px solid transparent; border-bottom-color: rgba(124,77,255,0.8); border-left-color: rgba(0,229,255,0.4); animation: spin 2s linear infinite reverse; }
.ld-orb img { width: 54px; height: 54px; animation: orbPulse 2s ease-in-out infinite; }
.ld-title { font-size: 1.4rem; font-weight: 700; color: var(--text-main); margin: 0; }
.ld-steps { position: relative; height: 1.5em; width: 100%; font: 500 0.95rem 'JetBrains Mono', monospace; color: var(--neon-cyan); }
.ld-steps span { position: absolute; inset: 0; opacity: 0; animation: stepCycle 9s infinite; }
.ld-steps span:nth-child(2) { animation-delay: 3s; } .ld-steps span:nth-child(3) { animation-delay: 6s; }
.ld-ecg { width: min(320px, 80%); height: 48px; }

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] { background: var(--surface-glass); backdrop-filter: blur(24px); border-radius: 18px; padding: 8px; gap: 10px; border: 1px solid var(--border-glass); display: inline-flex; margin-bottom: 32px; box-shadow: 0 12px 32px rgba(0,0,0,0.3); }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 12px; padding: 12px 28px; transition: all 0.35s var(--ease-out); border: none; color: var(--text-muted); font-weight: 600; font-size: 1.05rem; letter-spacing: 0.02em; }
.stTabs [data-baseweb="tab"]:hover { color: var(--text-main); background: rgba(255,255,255,0.05); transform: translateY(-2px); }
.stTabs [aria-selected="true"] { background: rgba(255, 255, 255, 0.12) !important; color: var(--text-main) !important; box-shadow: 0 4px 20px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.1); }
.stTabs [data-baseweb="tab-highlight"] { display: none; }
.stTabs [data-baseweb="tab-panel"] { animation: panelIn 0.55s var(--ease-out); }

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button {
    position: relative; overflow: hidden;
    background: linear-gradient(135deg, var(--neon-cyan), #00b0ff) !important; color: #000 !important;
    border: none !important; border-radius: 14px !important; font-weight: 700 !important;
    padding: 0.7rem 1.4rem !important; font-size: 1.05rem !important;
    box-shadow: 0 6px 20px rgba(0, 229, 255, 0.35) !important; transition: all 0.3s var(--ease-out) !important;
}
.stButton > button::after, .stDownloadButton > button::after {
    content: ""; position: absolute; top: 0; left: -60%; width: 40%; height: 100%;
    background: linear-gradient(100deg, transparent, rgba(255,255,255,0.55), transparent); transform: skewX(-20deg); pointer-events: none;
}
.stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-3px) scale(1.02) !important; box-shadow: 0 10px 30px rgba(0, 229, 255, 0.5) !important; }
.stButton > button:hover::after, .stDownloadButton > button:hover::after { animation: shine 0.8s var(--ease-out); }
.stButton > button:active, .stDownloadButton > button:active { transform: translateY(0) scale(0.97) !important; }
.st-key-change_prefs button { background: transparent !important; color: var(--text-main) !important; border: 1px solid var(--border-glass) !important; box-shadow: none !important; }
.st-key-change_prefs button:hover { background: rgba(255,255,255,0.08) !important; border-color: rgba(255,255,255,0.25) !important; }

/* ---------- Radio (onboarding) ---------- */
div[data-testid="stRadio"] [role="radiogroup"] { gap: 10px; }
div[data-testid="stRadio"] label { background: var(--surface-glass); border: 1px solid var(--border-glass); border-radius: 14px; padding: 14px 18px; transition: all 0.3s var(--ease-out); cursor: pointer; width: 100%; }
div[data-testid="stRadio"] label:hover { border-color: rgba(0,229,255,0.5); transform: translateX(5px); background: var(--surface-glass-hover); }
div[data-testid="stRadio"] label:has(input:checked) { border-color: var(--neon-cyan); background: rgba(0,229,255,0.06); box-shadow: 0 0 24px rgba(0,229,255,0.2); }
div[data-testid="stRadio"] label p { color: var(--text-main) !important; font-size: 1.05rem; font-weight: 600; }

/* ---------- Onboarding ---------- */
.ob-card { animation: cardRise 0.8s var(--ease-spring) backwards, floatSlow 6s ease-in-out 0.8s infinite; padding: 56px 40px; text-align: center; border: 1px solid rgba(0, 229, 255, 0.25); box-shadow: 0 20px 60px rgba(0,0,0,0.5), inset 0 0 50px rgba(0,229,255,0.06); margin-top: 48px; }
.ob-card .cl-logo { margin: 0 auto 28px; }
.ob-step { display: inline-block; font: 700 12px 'JetBrains Mono', monospace; letter-spacing: 0.25em; text-transform: uppercase; color: var(--neon-cyan); margin-bottom: 16px; background: rgba(0,229,255,0.12); padding: 6px 16px; border-radius: 999px; }
.ob-title { font-size: 2.4rem; font-weight: 700; color: var(--text-main); margin: 0 0 18px; letter-spacing: -0.03em; }
.ob-desc { font-size: 1.15rem; line-height: 1.6; color: var(--text-muted); margin: 0 auto; max-width: 520px; }
.cl-footer { margin-top: 60px; padding-top: 24px; border-top: 1px dashed var(--border-glass); text-align: center; font-size: 0.85rem; color: #5e6b82; letter-spacing: 0.02em; }

/* ---------- Accessibility ---------- */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation-duration: 0.001ms !important; animation-iteration-count: 1 !important; transition-duration: 0.001ms !important; }
}
</style>
"""
render_html(THEME_CSS)
render_html('<div class="aurora" aria-hidden="true"><i></i><i></i><i></i></div>')

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
ICON_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 12.5l2.7 2.7L16 9.5"/></svg>'
ICON_WARN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 7v6"/><path d="M12 16.5v.5"/></svg>'
ECG_PATH = "M0 30 H100 L112 30 L122 6 L136 54 L148 18 L156 30 H320"
ICON_ECG = f'<svg class="cl-ecg" viewBox="0 0 320 60" preserveAspectRatio="none" aria-hidden="true"><path d="{ECG_PATH}"/></svg>'

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
        "no_food": "All your biomarkers are within the normal range, so no specific dietary changes are needed. Keep up a balanced diet and regular activity.",
        "no_questions": "No flagged biomarkers, so there are no specific questions for your doctor. You can still share this report during your next routine check-up.",
        "ai_missing": "Explanations could not be generated for the flagged biomarkers this time. Please retry the analysis.",
        "retry": "Retry analysis",
        "load_title": "Analyzing your report",
        "load_1": "Reading document…", "load_2": "Extracting biomarkers…", "load_3": "Preparing simple explanations…",
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
        "no_food": "आपके सभी पैरामीटर सामान्य सीमा में हैं, इसलिए किसी विशेष आहार बदलाव की जरूरत नहीं है। संतुलित आहार और नियमित व्यायाम जारी रखें।",
        "no_questions": "कोई असामान्य पैरामीटर नहीं है, इसलिए डॉक्टर से पूछने के लिए कोई विशेष सवाल नहीं है। अगले रूटीन चेकअप में यह रिपोर्ट दिखा सकते हैं।",
        "ai_missing": "इस बार असामान्य पैरामीटर के लिए व्याख्या तैयार नहीं हो सकी। कृपया विश्लेषण दोबारा चलाएँ।",
        "retry": "फिर से विश्लेषण करें",
        "load_title": "आपकी रिपोर्ट का विश्लेषण हो रहा है",
        "load_1": "दस्तावेज़ पढ़ा जा रहा है…", "load_2": "बायोमार्कर निकाले जा रहे हैं…", "load_3": "सरल व्याख्या तैयार हो रही है…",
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
        "no_food": "તમારા બધા પેરામીટર સામાન્ય મર્યાદામાં છે, તેથી ખાસ આહાર ફેરફારની જરૂર નથી. સંતુલિત આહાર અને નિયમિત કસરત ચાલુ રાખો.",
        "no_questions": "કોઈ અસામાન્ય પેરામીટર નથી, તેથી ડૉક્ટરને પૂછવા માટે ખાસ પ્રશ્નો નથી. આગલા રૂટિન ચેકઅપમાં આ રિપોર્ટ બતાવી શકો છો.",
        "ai_missing": "આ વખતે અસામાન્ય પેરામીટર માટે સમજૂતી તૈયાર થઈ શકી નથી. કૃપા કરીને વિશ્લેષણ ફરી ચલાવો.",
        "retry": "ફરી વિશ્લેષણ કરો",
        "load_title": "તમારા રિપોર્ટનું વિશ્લેષણ થઈ રહ્યું છે",
        "load_1": "દસ્તાવેજ વાંચી રહ્યા છીએ…", "load_2": "બાયોમાર્કર કાઢી રહ્યા છીએ…", "load_3": "સરળ સમજૂતી તૈયાર થઈ રહી છે…",
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
MODEL = "openai/gpt-oss-120b"   # swap stage 1 to "openai/gpt-oss-20b" if you need more quota headroom
MAX_PAGES = 40                  # pages read per document
CHUNK_CHARS = 9000              # ~2.5k tokens per extraction call
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
                reasoning_effort="low",
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
    <article class="metric-card {state_cls}" style="animation-delay:{index * 70}ms">
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

def score_ring(pct: int) -> str:
    circ = 276.46
    dash = circ * pct / 100
    cls = "" if pct >= 70 else "mid" if pct >= 40 else "low"
    return (
        f'<div class="ring {cls}" aria-label="{pct}%">'
        f'<svg viewBox="0 0 100 100" aria-hidden="true">'
        f'<circle class="ring-bg" cx="50" cy="50" r="44"/>'
        f'<circle class="ring-fg" cx="50" cy="50" r="44" stroke-dasharray="{dash:.1f} 276.5" transform="rotate(-90 50 50)"/>'
        f'</svg>'
        f'<div class="ring-label"><span class="ring-pct">{pct}%</span><span class="ring-cap">{esc(L["stat_normal"])}</span></div>'
        f'</div>'
    )

def summary_panel(summary: str, biomarkers: list) -> str:
    total = len(biomarkers)
    flagged = [b for b in biomarkers if b["code"] != "normal"]
    normal = total - len(flagged)
    pct = round(normal / total * 100) if total else 0
    tags = "".join(
        f'<span class="cl-flag-tag" style="animation-delay:{0.5 + i * 0.07:.2f}s">{esc(b["name"])}</span>'
        for i, b in enumerate(flagged)
    )
    tag_row = f'<div class="cl-flag-list">{tags}</div>' if tags else ""
    return f"""
    <section class="cl-summary">
        <div class="cl-summary-top">
            {score_ring(pct)}
            <div class="cl-summary-copy">
                <p class="cl-eyebrow">{esc(L['summary_title'])}</p>
                <p class="cl-summary-text">{esc(summary)}</p>
            </div>
        </div>
        <div class="cl-stats">
            <div class="cl-stat" style="animation-delay:.25s"><span class="cl-stat-label">{esc(L['stat_total'])}</span><span class="cl-stat-value">{total}</span></div>
            <div class="cl-stat cl-stat-normal" style="animation-delay:.35s"><span class="cl-stat-label">{esc(L['stat_normal'])}</span><span class="cl-stat-value">{normal}</span></div>
            <div class="cl-stat cl-stat-flagged" style="animation-delay:.45s"><span class="cl-stat-label">{esc(L['stat_flagged'])}</span><span class="cl-stat-value">{len(flagged)}</span></div>
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

def empty_state(message: str, ok: bool = True) -> str:
    icon = ICON_CHECK if ok else ICON_WARN
    cls = "" if ok else "warn"
    return f'<div class="cl-empty-state {cls}"><span class="es-icon">{icon}</span><p>{esc(message)}</p></div>'

def loader_html() -> str:
    return f"""
    <div class="ld" role="status" aria-live="polite">
        <div class="ld-orb">{ICON_LOGO}</div>
        <h3 class="ld-title">{esc(L['load_title'])}</h3>
        <div class="ld-steps">
            <span>{esc(L['load_1'])}</span><span>{esc(L['load_2'])}</span><span>{esc(L['load_3'])}</span>
        </div>
        <svg class="ld-ecg" viewBox="0 0 320 60" preserveAspectRatio="none" aria-hidden="true"><path class="ecg-line" d="{ECG_PATH}"/></svg>
    </div>
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
            {ICON_ECG}
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
    cache_key = None

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
            loader = st.empty()
            with loader.container():
                render_html(loader_html())
            parsed_report_data, error_notice = analyze_report_with_groq(
                file_bytes, uploaded_file.name, mime_type,
                st.session_state.selected_lang, st.session_state.selected_diet,
                groq_api_key
            )
            loader.empty()
            if parsed_report_data:
                st.session_state.analysis_cache[cache_key] = parsed_report_data

        if error_notice and not parsed_report_data:
            st.error(error_notice)
        elif not parsed_report_data:
            render_html(f'<div class="cl-empty">{esc(L["no_results"])}</div>')

    # -----------------------------------------------------
    # Render Diagnostic Results
    # -----------------------------------------------------
    if parsed_report_data:
        biomarkers = [normalise(p) for p in parsed_report_data.get("parameters", [])]
        order = {"high": 0, "low": 1, "normal": 2}
        biomarkers_sorted = sorted(biomarkers, key=lambda b: order[b["code"]])
        has_flagged = any(b["code"] != "normal" for b in biomarkers)

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
            food_items = [(i, b) for i, b in enumerate(biomarkers_sorted) if b["food"]]
            if food_items:
                food_cards = "".join(
                    f"""
                    <article class="food-card" style="animation-delay:{i * 70}ms">
                        <header class="food-head"><h3 class="food-title">{esc(b['name'])}</h3>{status_pill(b['code'])}</header>
                        <p class="food-body">{esc(b['food'])}</p>
                    </article>
                    """
                    for i, b in food_items
                )
                body = f'<div class="metric-grid">{food_cards}</div>'
            elif has_flagged:
                body = empty_state(L["ai_missing"], ok=False)
            else:
                body = empty_state(L["no_food"], ok=True)
            render_html(f"""
            <section aria-label="{esc(L['food_title'])}">
                <h2 class="cl-h2" style="margin-top:8px">{esc(L['food_title'])}</h2>
                {body}
            </section>
            """)
            if not food_items and has_flagged and cache_key is not None:
                if st.button(L["retry"], key="retry_food"):
                    st.session_state.analysis_cache.pop(cache_key, None)
                    st.rerun()

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
            else:
                if has_flagged:
                    body = empty_state(L["ai_missing"], ok=False)
                else:
                    body = empty_state(L["no_questions"], ok=True)
                render_html(f"""
                <section aria-label="{esc(L['questions_title'])}">
                    <h2 class="cl-h2" style="margin-top:8px">{esc(L['questions_title'])}</h2>
                    {body}
                </section>
                """)
                if has_flagged and cache_key is not None:
                    if st.button(L["retry"], key="retry_doc"):
                        st.session_state.analysis_cache.pop(cache_key, None)
                        st.rerun()

    render_html(f'<footer class="cl-footer">{esc(L["disclaimer"])}</footer>')
