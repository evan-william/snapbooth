"""
Stage 3 — Preview & customise.
"""

import io
import streamlit as st

from config.settings import (
    FILTERS, STICKERS, STICKER_MAP, FRAME_MAP,
    STAGE_CAPTURE, STAGE_DOWNLOAD,
)
from core.session import (
    get_photos, get_frame, set_frame, get_filter, set_filter,
    get_sticker, set_sticker, get_processed, set_processed,
    set_strip_bytes, set_strip_pdf, set_stage, clear_photos,
)
from core.validation import safe_open_image
from core.filters import apply_filter, generate_thumbnail
from core.stickers import apply_sticker
from core.compositor import compose_strip
from core.exporter import export_jpg, export_pdf


def _build_processed_photos() -> list:
    filter_key  = get_filter()
    sticker_cfg = STICKER_MAP.get(get_sticker())
    result      = []
    for raw in get_photos():
        img = safe_open_image(raw)
        if img is None:
            continue
        img = apply_filter(img, filter_key)
        if sticker_cfg and sticker_cfg.key != "none":
            img = apply_sticker(img, sticker_cfg)
        result.append(img)
    return result


def _strip_preview_bytes(processed: list) -> bytes:
    """Render the current strip and return as JPEG bytes for display."""
    frame_cfg = FRAME_MAP[get_frame()]
    strip     = compose_strip(processed, frame_cfg)
    buf       = io.BytesIO()
    strip.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def render():
    # Build processed images
    processed = get_processed()
    if not processed:
        with st.spinner("Applying effects…"):
            built = _build_processed_photos()
            set_processed(built)
            processed = built

    if not processed:
        st.error("No valid photos found. Please retake your shots.")
        if st.button("← Retake", type="secondary"):
            set_stage(STAGE_CAPTURE)
            st.rerun()
        return

    # ── Layout: left column = controls, right column = live strip preview ──
    col_ctrl, col_preview = st.columns([3, 2], gap="large")

    with col_ctrl:
        # --- Photo row ---
        st.markdown('<p class="snap-section">Your Photos</p>', unsafe_allow_html=True)
        thumb_cols = st.columns(len(processed))
        for col, img in zip(thumb_cols, processed):
            col.image(generate_thumbnail(img, width=120), use_container_width=True)

        st.markdown("---")

        # --- Filter ---
        st.markdown("**Filter**")
        current_filter = get_filter()
        f_cols = st.columns(len(FILTERS))
        for col, f in zip(f_cols, FILTERS):
            if col.button(
                f.label,
                key=f"f_{f.key}",
                type="primary" if f.key == current_filter else "secondary",
                use_container_width=True,
            ):
                set_filter(f.key)
                set_processed([])
                st.rerun()

        st.markdown("")

        # --- Sticker ---
        st.markdown("**Sticker**")
        current_sticker = get_sticker()
        s_cols = st.columns(len(STICKERS))
        for col, s in zip(s_cols, STICKERS):
            label = s.label
            if col.button(
                label,
                key=f"s_{s.key}",
                type="primary" if s.key == current_sticker else "secondary",
                use_container_width=True,
            ):
                set_sticker(s.key)
                set_processed([])
                st.rerun()

        st.markdown("---")

        # --- Frame ---
        st.markdown("**Frame**")
        current_frame = get_frame()
        frame_keys    = list(FRAME_MAP.keys())
        selected_idx  = frame_keys.index(current_frame) if current_frame in frame_keys else 0

        choice = st.radio(
            "frame_radio",
            options=frame_keys,
            format_func=lambda k: FRAME_MAP[k].label,
            index=selected_idx,
            horizontal=True,
            label_visibility="collapsed",
        )
        if choice != current_frame:
            set_frame(choice)
            st.rerun()

        st.markdown("---")

        col_back, _, col_gen = st.columns([1, 1, 2])
        with col_back:
            if st.button("← Retake", type="secondary"):
                clear_photos()
                set_processed([])
                set_stage(STAGE_CAPTURE)
                st.rerun()
        with col_gen:
            if st.button("Generate Strip →", type="primary", use_container_width=True):
                _generate_strip(processed)

    # ── Live strip preview ─────────────────────────────────────────────────
    with col_preview:
        st.markdown('<p class="snap-section">Preview</p>', unsafe_allow_html=True)
        try:
            preview_bytes = _strip_preview_bytes(processed)
            st.image(preview_bytes, use_container_width=True, caption=f"Frame: {FRAME_MAP[get_frame()].label}")
        except Exception as exc:
            st.warning(f"Preview unavailable: {exc}")


def _generate_strip(photos: list):
    frame_cfg = FRAME_MAP[get_frame()]
    with st.spinner("Composing your strip…"):
        try:
            strip = compose_strip(photos, frame_cfg)
            set_strip_bytes(export_jpg(strip))
            set_strip_pdf(export_pdf(strip))
            set_stage(STAGE_DOWNLOAD)
            st.rerun()
        except Exception as exc:
            st.error(f"Strip generation failed: {exc}")