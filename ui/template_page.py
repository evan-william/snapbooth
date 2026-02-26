"""
Stage 1 — Layout + Template selection.

Users pick:
  1. Photo count / layout (1×3, 1×4, 2×2, 2×3, …)
  2. Frame style (from 20+ options)
"""

import io
import streamlit as st

from config.settings import FRAMES, FRAME_MAP, LAYOUTS, LAYOUT_MAP, STAGE_CAPTURE
from core.session import get_frame, set_frame, set_stage, get_layout_key, set_layout, get_layout
from core.compositor import compose_preview_strip


@st.cache_data(show_spinner=False)
def _cached_preview(frame_key: str, layout_key: str) -> bytes:
    frame  = FRAME_MAP[frame_key]
    layout = LAYOUT_MAP[layout_key]
    thumb  = compose_preview_strip(frame, layout=layout, scale=0.28)
    buf    = io.BytesIO()
    thumb.save(buf, format="JPEG", quality=78)
    return buf.getvalue()


def render():
    current_layout = get_layout_key()
    current_frame  = get_frame()

    # ── Step 1: Layout Picker ──────────────────────────────────────────────
    st.markdown('<p class="snap-section">Choose Layout</p>', unsafe_allow_html=True)
    st.markdown(
        "How many photos do you want in your strip or grid?",
    )
    st.markdown("")

    layout_cols = st.columns(len(LAYOUTS), gap="small")
    for col, layout in zip(layout_cols, LAYOUTS):
        with col:
            is_sel   = layout.key == current_layout
            btn_type = "primary" if is_sel else "secondary"
            # Keep label short — no ✓ prefix to avoid Streamlit line-wrapping
            label    = f"{layout.cols}×{layout.rows}"
            dot_html = (
                '<div style="text-align:center;font-size:0.7rem;'
                f'color:{"#e0ff60" if is_sel else "#666"};margin-bottom:2px;">'
                f'{"●" if is_sel else "○"} {layout.total} photos</div>'
            )
            st.markdown(dot_html, unsafe_allow_html=True)
            if st.button(label, key=f"layout_{layout.key}", type=btn_type,
                         use_container_width=True):
                set_layout(layout.key)
                st.rerun()

    st.markdown("---")

    # ── Step 2: Frame Picker ───────────────────────────────────────────────
    st.markdown('<p class="snap-section">Choose a Frame</p>', unsafe_allow_html=True)
    st.markdown(
        "Pick the look for your strip — you can change it again on the preview screen.",
    )
    st.markdown("")

    # Render frames in rows of 4
    chunk_size = 4
    for row_start in range(0, len(FRAMES), chunk_size):
        row_frames = FRAMES[row_start : row_start + chunk_size]
        cols       = st.columns(len(row_frames), gap="small")
        for col, frame in zip(cols, row_frames):
            with col:
                is_selected  = frame.key == current_frame
                border_style = "3px solid #e0ff60" if is_selected else "2px solid #333"

                try:
                    preview_bytes = _cached_preview(frame.key, current_layout)
                    st.markdown(
                        f'<div style="border:{border_style};border-radius:8px;'
                        f'overflow:hidden;margin-bottom:4px;">',
                        unsafe_allow_html=True,
                    )
                    st.image(preview_bytes, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                except Exception:
                    bg_hex  = "#{:02x}{:02x}{:02x}".format(*frame.bg_color)
                    bdr_hex = "#{:02x}{:02x}{:02x}".format(*frame.border_color)
                    st.markdown(
                        f'<div style="background:{bg_hex};border:4px solid {bdr_hex};'
                        f'border-radius:8px;height:80px;margin-bottom:4px;"></div>',
                        unsafe_allow_html=True,
                    )

                if st.button(
                    frame.label,
                    key=f"frame_btn_{frame.key}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True,
                ):
                    set_frame(frame.key)
                    st.rerun()

        st.markdown("")  # spacer between rows

    # ── CTA ───────────────────────────────────────────────────────────────
    st.markdown("---")
    layout_obj = get_layout()
    col_l, col_r = st.columns([3, 1])
    with col_r:
        if st.button(
            f"Start Shooting ({layout_obj.total} photos) →",
            type="primary",
            use_container_width=True,
        ):
            set_stage(STAGE_CAPTURE)
            st.rerun()
            