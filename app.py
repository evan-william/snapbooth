"""
SnapBooth — Virtual Photobooth
Entry point for the Streamlit application.

Run with:
    streamlit run app.py
"""

import streamlit as st

from config.settings import (
    STAGE_TEMPLATE, STAGE_CAPTURE, STAGE_PREVIEW, STAGE_DOWNLOAD,
)
from core.session import init_session, get_stage
from ui.styles import inject_css
from ui.mobile_block import inject_mobile_block
from ui import template_page, camera_page, preview_page, download_page

# ── Page config (must be the first Streamlit call) ─────────────────────────
st.set_page_config(
    page_title="SnapBooth",
    page_icon="📸",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Global state + CSS ─────────────────────────────────────────────────────
init_session()
inject_css()

# ── Mobile block (runs JS detection, shows overlay on phones/tablets) ──────
inject_mobile_block()

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="snap-header">
        <h1>SnapBooth</h1>
        <p>Virtual Photobooth</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Stage breadcrumb ────────────────────────────────────────────────────────
_STAGES = [
    (STAGE_TEMPLATE, "Frame"),
    (STAGE_CAPTURE,  "Shoot"),
    (STAGE_PREVIEW,  "Preview"),
    (STAGE_DOWNLOAD, "Download"),
]

current_stage = get_stage()
steps_html = '<div class="snap-steps">'
for i, (key, label) in enumerate(_STAGES):
    active = "snap-step-active" if key == current_stage else ""
    sep = " › " if i < len(_STAGES) - 1 else ""
    steps_html += f'<span class="{active}">{label}</span>{sep}'
steps_html += "</div>"
st.markdown(steps_html, unsafe_allow_html=True)

# ── Route to active stage ───────────────────────────────────────────────────
if current_stage == STAGE_TEMPLATE:
    template_page.render()

elif current_stage == STAGE_CAPTURE:
    camera_page.render()

elif current_stage == STAGE_PREVIEW:
    preview_page.render()

elif current_stage == STAGE_DOWNLOAD:
    download_page.render()

else:
    st.error(f"Unknown application stage: '{current_stage}'. Please refresh the page.")
    from core.session import reset_session
    reset_session()
    st.rerun()