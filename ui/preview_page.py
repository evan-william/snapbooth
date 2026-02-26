"""
Stage 3 — Preview & customise.
User applies filters and stickers, then generates the strip.
"""

import streamlit as st

from config.settings import (
    FILTERS, STICKERS, FRAME_MAP,
    STAGE_CAPTURE, STAGE_DOWNLOAD,
)

# All session helpers imported at module level — never inside the function.
# Importing inside a function body causes Python to treat the name as a local
# variable throughout the entire function, leading to UnboundLocalError when
# the name is referenced before the inner import runs.
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
    """
    (Re)build the list of processed PIL Images from raw session bytes.
    Only called when the filter or sticker selection changes.
    """
    filter_key  = get_filter()
    sticker_key = get_sticker()
    result      = []

    for raw in get_photos():
        img = safe_open_image(raw)
        if img is None:
            continue
        img = apply_filter(img, filter_key)
        img = apply_sticker(img, sticker_key)
        result.append(img)

    return result


def render():
    # --- Build processed images if not cached -----------------------------
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

    # --- Thumbnails row ---------------------------------------------------
    st.markdown('<p class="snap-section">Your Photos</p>', unsafe_allow_html=True)
    thumb_cols = st.columns(len(processed))
    for col, img in zip(thumb_cols, processed):
        col.image(generate_thumbnail(img, width=160), use_container_width=True)

    st.markdown("---")

    # --- Filter picker ----------------------------------------------------
    st.markdown("**Filter**")
    current_filter = get_filter()
    filter_cols = st.columns(len(FILTERS))

    for col, f in zip(filter_cols, FILTERS):
        is_active = f.key == current_filter
        if col.button(
            f.label,
            key=f"filter_{f.key}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            set_filter(f.key)
            st.rerun()

    st.markdown("")

    # --- Sticker picker ---------------------------------------------------
    st.markdown("**Sticker**")
    current_sticker = get_sticker()
    sticker_cols = st.columns(len(STICKERS))

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

    # --- Generate strip button --------------------------------------------
    col_back, _, col_gen = st.columns([1, 2, 1])

    with col_back:
        if st.button("← Retake", type="secondary"):
            clear_photos()
            set_processed([])
            set_stage(STAGE_CAPTURE)
            st.rerun()

    with col_gen:
        if st.button("Generate Strip →", type="primary", use_container_width=True):
            _generate_strip(processed)


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