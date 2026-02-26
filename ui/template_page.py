"""
Stage 1 — Template selection with live frame preview thumbnails.
"""

import io
import streamlit as st

from config.settings import FRAMES, FRAME_MAP, STAGE_CAPTURE
from core.session import get_frame, set_frame, set_stage
from core.compositor import compose_preview_strip


@st.cache_data(show_spinner=False)
def _cached_preview(frame_key: str) -> bytes:
    """
    Generate and cache a small strip preview for a given frame.
    Cached so we don't regenerate on every interaction.
    """
    frame = FRAME_MAP[frame_key]
    thumb = compose_preview_strip(frame, scale=0.30)
    buf   = io.BytesIO()
    thumb.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


def render():
    st.markdown('<p class="snap-section">Choose a Frame</p>', unsafe_allow_html=True)
    st.markdown(
        "Pick the look for your strip — you can change it again on the preview screen.",
    )
    st.markdown("")

    current = get_frame()

    # Two rows of 4
    rows = [FRAMES[:4], FRAMES[4:]]

    for row in rows:
        cols = st.columns(len(row), gap="small")
        for col, frame in zip(cols, row):
            with col:
                is_selected = frame.key == current

                # Actual rendered preview image
                try:
                    preview_bytes = _cached_preview(frame.key)
                    border_style  = "3px solid #e0ff60" if is_selected else "2px solid #333"
                    st.markdown(
                        f'<div style="border:{border_style};border-radius:8px;'
                        f'overflow:hidden;margin-bottom:4px;">',
                        unsafe_allow_html=True,
                    )
                    st.image(preview_bytes, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                except Exception:
                    # Fallback colour swatch
                    bg_hex  = "#{:02x}{:02x}{:02x}".format(*frame.bg_color)
                    bdr_hex = "#{:02x}{:02x}{:02x}".format(*frame.border_color)
                    st.markdown(
                        f'<div style="background:{bg_hex};border:4px solid {bdr_hex};'
                        f'border-radius:8px;height:80px;margin-bottom:4px;"></div>',
                        unsafe_allow_html=True,
                    )

                if st.button(
                    f"✓ {frame.label}" if is_selected else frame.label,
                    key=f"frame_btn_{frame.key}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True,
                ):
                    set_frame(frame.key)
                    st.rerun()

        st.markdown("")  # spacer between rows

    st.markdown("---")
    col_l, col_r = st.columns([3, 1])
    with col_r:
        if st.button("Start Shooting →", type="primary", use_container_width=True):
            set_stage(STAGE_CAPTURE)
            st.rerun()