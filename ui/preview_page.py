"""
Stage 3 — Preview & customise.
User applies filters and stickers, then generates the strip.
"""

import io
import streamlit as st
from PIL import Image

from config.settings import (
    FILTERS, STICKERS, FRAME_MAP,
    STAGE_CAPTURE, STAGE_DOWNLOAD,
)
from core.session import (
    get_photos, get_frame, get_filter, set_filter,
    get_sticker, set_sticker, get_processed, set_processed,
    set_strip_bytes, set_strip_pdf, set_stage,
)
from core.validation import safe_open_image
from core.filters import apply_filter, generate_thumbnail
from core.stickers import apply_sticker
from core.compositor import compose_strip
from core.exporter import export_jpg, export_pdf


def _build_processed_photos() -> list:
    """
    (Re)build the list of processed PIL Images from raw session bytes.
    Expensive — only called when filter/sticker choice changes.
    """
    filter_key  = get_filter()
    sticker_key = get_sticker()
    photos      = get_photos()
    result      = []

    for raw in photos:
        img = safe_open_image(raw)
        if img is None:
            continue
        img = apply_filter(img, filter_key)
        img = apply_sticker(img, sticker_key)
        result.append(img)

    return result


def render():
    # --- Ensure processed images are ready --------------------------------
    processed = get_processed()
    if not processed:
        with st.spinner("Applying effects…"):
            processed = _build_processed_photos()
            set_processed(processed)

    if not processed:
        st.error("No valid photos found. Please retake your shots.")
        if st.button("← Retake", type="secondary"):
            set_stage(STAGE_CAPTURE)
            st.rerun()
        return

    # --- Thumbnails row ---------------------------------------------------
    st.markdown('<p class="snap-section">Your Photos</p>', unsafe_allow_html=True)
    thumb_cols = st.columns(len(processed))
    for col, img in zip(thumb_cols, processed):
        thumb = generate_thumbnail(img, width=160)
        col.image(thumb, use_container_width=True)

    st.markdown("---")

    # --- Filter picker ----------------------------------------------------
    st.markdown("**Filter**")
    filter_cols = st.columns(len(FILTERS))
    current_filter = get_filter()

    for col, f in zip(filter_cols, FILTERS):
        active_style = (
            "background:#e0ff60;color:#111;border-color:#e0ff60;font-weight:600;"
            if f.key == current_filter
            else ""
        )
        col.markdown(
            f'<div class="filter-pill{"  active" if f.key == current_filter else ""}" '
            f'style="{active_style}">{f.label}</div>',
            unsafe_allow_html=True,
        )
        if col.button(f.label, key=f"filter_{f.key}", help=f.label):
            set_filter(f.key)
            st.rerun()

    st.markdown("")

    # --- Sticker picker ---------------------------------------------------
    st.markdown("**Sticker**")
    sticker_cols = st.columns(len(STICKERS))
    current_sticker = get_sticker()

    for col, s in zip(sticker_cols, STICKERS):
        label = s.emoji if s.emoji else "None"
        if col.button(
            label,
            key=f"sticker_{s.key}",
            type="primary" if s.key == current_sticker else "secondary",
            help=s.label,
        ):
            set_sticker(s.key)
            st.rerun()

    st.markdown("---")

    # --- Frame picker (quick switch) --------------------------------------
    st.markdown("**Frame**")
    current_frame = get_frame()
    frame_keys = list(FRAME_MAP.keys())
    frame_labels = [FRAME_MAP[k].label for k in frame_keys]
    selected_idx = frame_keys.index(current_frame) if current_frame in frame_keys else 0

    choice = st.radio(
        "frame_radio",
        options=frame_keys,
        format_func=lambda k: FRAME_MAP[k].label,
        index=selected_idx,
        horizontal=True,
        label_visibility="collapsed",
    )
    if choice != current_frame:
        from core.session import set_frame
        set_frame(choice)
        st.rerun()

    st.markdown("---")

    # --- Generate strip button --------------------------------------------
    col_back, _, col_gen = st.columns([1, 2, 1])

    with col_back:
        if st.button("← Retake", type="secondary"):
            from core.session import clear_photos, set_processed
            clear_photos()
            set_processed([])
            set_stage(STAGE_CAPTURE)
            st.rerun()

    with col_gen:
        if st.button("Generate Strip →", type="primary", use_container_width=True):
            _generate_strip(processed)


def _generate_strip(processed: list):
    frame_cfg = FRAME_MAP[get_frame()]
    with st.spinner("Composing your strip…"):
        try:
            strip = compose_strip(processed, frame_cfg)
            jpg   = export_jpg(strip)
            pdf   = export_pdf(strip)
            set_strip_bytes(jpg)
            set_strip_pdf(pdf)
            set_stage(STAGE_DOWNLOAD)
            st.rerun()
        except Exception as exc:
            st.error(f"Strip generation failed: {exc}")