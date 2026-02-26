"""
Stage 1 — Template selection.
The user picks a frame style before moving to the camera.
"""

import streamlit as st

from config.settings import FRAMES, FRAME_MAP
from core.session import get_frame, set_frame, set_stage
from config.settings import STAGE_CAPTURE


def render():
    st.markdown('<p class="snap-section">Choose a Frame Style</p>', unsafe_allow_html=True)
    st.markdown(
        "Pick the look for your strip. You can switch later on the preview screen.",
        unsafe_allow_html=True,
    )
    st.markdown("")

    current = get_frame()
    cols = st.columns(len(FRAMES))

    for col, frame in zip(cols, FRAMES):
        with col:
            bg_hex   = "#{:02x}{:02x}{:02x}".format(*frame.bg_color)
            bdr_hex  = "#{:02x}{:02x}{:02x}".format(*frame.border_color)
            selected = "selected" if frame.key == current else ""

            st.markdown(
                f"""
                <div class="frame-card {selected}" style="background:{bg_hex}">
                    <div class="frame-swatch"
                         style="background:{bg_hex};
                                border:{frame.border_width}px solid {bdr_hex};
                                box-shadow: inset 0 0 0 2px {bdr_hex}40;">
                    </div>
                    <div class="frame-label" style="color:{'#fff' if frame.key == current else '#aaa'}">
                        {frame.label}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Select" if frame.key != current else "Selected ✓",
                key=f"frame_btn_{frame.key}",
                type="primary" if frame.key == current else "secondary",
            ):
                set_frame(frame.key)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    col_l, col_r = st.columns([3, 1])
    with col_r:
        if st.button("Start Shooting →", type="primary", use_container_width=True):
            set_stage(STAGE_CAPTURE)
            st.rerun()