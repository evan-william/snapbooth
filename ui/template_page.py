"""
Stage 1 — Layout + Template selection.
Redesigned: compact layout picker + frame grid with hover previews.
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
    thumb  = compose_preview_strip(frame, layout=layout, scale=0.80)
    buf    = io.BytesIO()
    thumb.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


_PAGE_CSS = """<style>

/* ── Layout pills ── */
.layout-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}
.layout-pill {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    padding: 0.5rem 0.9rem;
    border-radius: 10px;
    border: 1.5px solid #2a2a2a;
    background: #111;
    cursor: pointer;
    transition: all 0.15s ease;
    min-width: 72px;
    text-align: center;
}
.layout-pill:hover { border-color: #555; background: #1a1a1a; }
.layout-pill.active {
    border-color: #e0ff60;
    background: #1a1f0a;
    box-shadow: 0 0 10px #e0ff6033;
}
.layout-pill-key {
    font-size: 0.9rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.02em;
}
.layout-pill.active .layout-pill-key { color: #e0ff60; }
.layout-pill-sub {
    font-size: 0.62rem;
    color: #555;
    letter-spacing: 0.04em;
}
.layout-pill.active .layout-pill-sub { color: #8a9e30; }

/* ── Frame cards ── */
.frame-card-wrap {
    position: relative;
    border-radius: 10px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    margin-bottom: 6px;
}
.frame-card-wrap:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}

/* ── Section label ── */
.snap-section-sm {
    font-family: 'DM Serif Display', serif;
    font-size: 1.15rem;
    color: #fff;
    margin: 0 0 0.5rem;
}

/* ── Footer ── */
.snap-footer {
    margin-top: 3rem;
    padding-top: 1.2rem;
    border-top: 1px solid #1e1e1e;
    text-align: center;
}
.snap-footer-name {
    font-size: 0.78rem;
    font-weight: 600;
    color: #555;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.snap-footer-copy {
    font-size: 0.68rem;
    color: #333;
    margin-top: 0.2rem;
    letter-spacing: 0.06em;
}
</style>"""


# Group frames into named categories for compact tabbed display
_FRAME_GROUPS = {
    "Classic":   ["classic", "film", "vintage", "gold_foil", "black_gold"],
    "Cute":      ["pink_heart", "garden", "cherry_blossom", "sakura", "lavender",
                     "pastel_dream", "rose_gold", "mint_fresh", "bows"],
    "Aesthetic": ["blue_sky", "ocean", "ice", "autumn", "warm_sunset"],
    "Dark":      ["neon", "midnight", "galaxy", "electric", "purple_rain"],
}


def render():
    st.markdown(_PAGE_CSS, unsafe_allow_html=True)

    current_layout = get_layout_key()
    current_frame  = get_frame()

    # ══════════════════════════════════════════════════════════════════════
    # STEP 1 — Layout (compact pills, no scroll)
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<p class="snap-section">Choose Layout</p>', unsafe_allow_html=True)

    # Two rows of pills rendered via Streamlit columns
    row1 = LAYOUTS[:5]
    row2 = LAYOUTS[5:]

    for row in [row1, row2]:
        cols = st.columns(len(row), gap="small")
        for col, layout in zip(cols, row):
            is_sel = layout.key == current_layout
            border = "2px solid #e0ff60" if is_sel else "1.5px solid #2a2a2a"
            bg     = "#1a1f0a" if is_sel else "#111"
            key_color = "#e0ff60" if is_sel else "#fff"
            sub_color = "#8a9e30" if is_sel else "#555"
            with col:
                st.markdown(
                    f'<div style="border:{border};border-radius:10px;background:{bg};'
                    f'padding:0.45rem 0.3rem;text-align:center;margin-bottom:2px;'
                    f'{"box-shadow:0 0 10px #e0ff6033;" if is_sel else ""}">'
                    f'<div style="font-size:0.9rem;font-weight:700;color:{key_color};">'
                    f'{layout.cols}×{layout.rows}</div>'
                    f'<div style="font-size:0.6rem;color:{sub_color};letter-spacing:0.04em;">'
                    f'{layout.total} photos</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    "✓" if is_sel else "Select",
                    key=f"layout_btn_{layout.key}",
                    type="primary" if is_sel else "secondary",
                    use_container_width=True,
                ):
                    set_layout(layout.key)
                    st.rerun()

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════
    # STEP 2 — Frame (tabbed by category, 5 per row)
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<p class="snap-section">Choose a Frame</p>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#666;font-size:0.82rem;margin-top:-0.5rem;margin-bottom:1rem;">'
        'You can change this later on the preview screen.</p>',
        unsafe_allow_html=True,
    )

    tab_labels = list(_FRAME_GROUPS.keys())
    tabs = st.tabs(tab_labels)

    for tab, (group_label, frame_keys) in zip(tabs, _FRAME_GROUPS.items()):
        with tab:
            group_frames = [FRAME_MAP[k] for k in frame_keys if k in FRAME_MAP]
            chunk = 5
            for row_start in range(0, len(group_frames), chunk):
                row_frames = group_frames[row_start:row_start + chunk]
                cols = st.columns(len(row_frames), gap="small")
                for col, frame in zip(cols, row_frames):
                    is_sel = frame.key == current_frame
                    border = "3px solid #e0ff60" if is_sel else "2px solid #222"
                    shadow = "box-shadow:0 0 14px #e0ff6055;" if is_sel else ""
                    with col:
                        try:
                            preview_bytes = _cached_preview(frame.key, current_layout)
                            st.markdown(
                                f'<div style="border:{border};border-radius:8px;'
                                f'overflow:hidden;margin-bottom:4px;{shadow}">',
                                unsafe_allow_html=True,
                            )
                            st.image(preview_bytes, use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                        except Exception:
                            bg_hex  = "#{:02x}{:02x}{:02x}".format(*frame.bg_color)
                            bdr_hex = "#{:02x}{:02x}{:02x}".format(*frame.border_color)
                            st.markdown(
                                f'<div style="background:{bg_hex};border:3px solid {bdr_hex};'
                                f'border-radius:8px;height:70px;margin-bottom:4px;{shadow}"></div>',
                                unsafe_allow_html=True,
                            )
                        if st.button(
                            "✓" if is_sel else frame.label,
                            key=f"frame_btn_{frame.key}",
                            type="primary" if is_sel else "secondary",
                            use_container_width=True,
                        ):
                            set_frame(frame.key)
                            st.rerun()

    # ── CTA ──────────────────────────────────────────────────────────────
    st.markdown("---")
    layout_obj   = get_layout()
    current_name = FRAME_MAP.get(current_frame)
    frame_label  = current_name.label if current_name else current_frame

    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.markdown(
            f'<div style="padding:0.6rem 0;color:#666;font-size:0.82rem;">'
            f'Layout: <strong style="color:#e0ff60;">{layout_obj.cols}×{layout_obj.rows} '
            f'({layout_obj.total} photos)</strong>'
            f' &nbsp;·&nbsp; Frame: <strong style="color:#e0ff60;">{frame_label}</strong>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_btn:
        if st.button(
            f"Start Shooting →",
            type="primary",
            use_container_width=True,
        ):
            set_stage(STAGE_CAPTURE)
            st.rerun()

    _render_footer()


def _render_footer():
    st.markdown(
        """
        <div class="snap-footer">
            <div class="snap-footer-name">Evan William</div>
            <div class="snap-footer-copy">© 2026 Evan William · SnapBooth · All rights reserved</div>
        </div>
        """,
        unsafe_allow_html=True,
    )