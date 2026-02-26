"""
Stage 3 — Preview & customise.

Photos may already be pre-processed as JPEG bytes (stored by camera_page
to avoid the flicker/MediaFileHandler glitch). If not (e.g. user came back
to change filter/sticker), rebuild them.

Key change: processed photos are now stored as JPEG bytes in session state,
NOT as PIL Image objects. PIL Images are not reliably serializable across
Streamlit reruns and cause MediaFileHandler missing-file errors.

We convert bytes → PIL only when we actually need to compose the strip.
"""

import io
import streamlit as st
from PIL import Image

from config.settings import (
    FILTERS, STICKERS, STICKER_MAP, FRAME_MAP,
    STAGE_CAPTURE, STAGE_DOWNLOAD,
)
from core.session import (
    get_photos, get_frame, set_frame, get_filter, set_filter,
    get_sticker, set_sticker, get_processed, set_processed,
    set_strip_bytes, set_strip_pdf, set_stage, clear_photos,
    get_layout,
)
from core.validation import safe_open_image
from core.filters import apply_filter, generate_thumbnail
from core.stickers import apply_sticker
from core.compositor import compose_strip
from core.exporter import export_jpg, export_pdf


def _build_processed_bytes() -> list:
    """Build processed photos and return as list of JPEG bytes."""
    filter_key  = get_filter()
    sticker_cfg = STICKER_MAP.get(get_sticker())
    result = []
    for raw in get_photos():
        img = safe_open_image(raw)
        if img is None:
            continue
        img = apply_filter(img, filter_key)
        if sticker_cfg and sticker_cfg.key != "none":
            img = apply_sticker(img, sticker_cfg)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95, subsampling=0)
        result.append(buf.getvalue())
    return result


def _bytes_to_pil(processed_bytes: list) -> list:
    """Convert list of JPEG bytes back to PIL Images for compositing."""
    result = []
    for b in processed_bytes:
        try:
            img = Image.open(io.BytesIO(b))
            img.load()
            result.append(img.convert("RGB"))
        except Exception:
            pass
    return result


def _strip_preview_bytes(processed_bytes: list) -> bytes:
    pil_images = _bytes_to_pil(processed_bytes)
    frame_cfg  = FRAME_MAP[get_frame()]
    layout_cfg = get_layout()
    strip      = compose_strip(pil_images, frame_cfg, layout=layout_cfg)
    buf        = io.BytesIO()
    strip.save(buf, format="JPEG", quality=92, subsampling=0)
    return buf.getvalue()


def render():
    # Processed photos are stored as JPEG bytes (not PIL Images).
    # If missing or empty, rebuild from raw photos.
    processed_bytes = get_processed()

    # Validate that stored data is actually bytes (not stale PIL objects)
    if processed_bytes and not isinstance(processed_bytes[0], (bytes, bytearray)):
        processed_bytes = []
        set_processed([])

    if not processed_bytes:
        with st.spinner("Applying effects…"):
            built = _build_processed_bytes()
            set_processed(built)
            processed_bytes = built

    if not processed_bytes:
        st.error("No valid photos found. Please retake your shots.")
        if st.button("← Retake", type="secondary"):
            clear_photos()
            set_processed([])
            set_stage(STAGE_CAPTURE)
            st.rerun()
        return

    layout_cfg = get_layout()
    col_ctrl, col_preview = st.columns([3, 2], gap="large")

    with col_ctrl:
        # --- Photo thumbnails ---
        st.markdown('<p class="snap-section">Your Photos</p>', unsafe_allow_html=True)
        n_cols  = min(4, len(processed_bytes))
        th_cols = st.columns(n_cols)
        for i, img_bytes in enumerate(processed_bytes):
            # Open from bytes for thumbnail — this is fine, it's immediate
            try:
                img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                thumb = generate_thumbnail(img, width=120)
                th_cols[i % n_cols].image(thumb, width='stretch')
            except Exception:
                pass

        st.markdown("---")

        # --- Filter (split into Classic + Aesthetic groups) ---
        st.markdown("**Filter**")
        current_filter = get_filter()

        CLASSIC_KEYS   = {"none","bw","sepia","retro","cool","vivid","soft","warm","fade"}
        classic_list   = [f for f in FILTERS if f.key in CLASSIC_KEYS]
        aesthetic_list = [f for f in FILTERS if f.key not in CLASSIC_KEYS]

        st.caption("Classic")
        classic_choice = st.radio(
            "filter_classic",
            options=[f.key for f in classic_list],
            format_func=lambda k: next(f.label for f in FILTERS if f.key == k),
            index=next((i for i,f in enumerate(classic_list) if f.key == current_filter), 0),
            horizontal=True,
            label_visibility="collapsed",
        )

        st.caption("✨ Aesthetic")
        aesthetic_choice = st.radio(
            "filter_aesthetic",
            options=[f.key for f in aesthetic_list],
            format_func=lambda k: next(f.label for f in FILTERS if f.key == k),
            index=next((i for i,f in enumerate(aesthetic_list) if f.key == current_filter), 0),
            horizontal=True,
            label_visibility="collapsed",
        )

        # Detect which group the user just changed
        new_filter = current_filter
        if classic_choice != current_filter and classic_choice in CLASSIC_KEYS:
            new_filter = classic_choice
        if aesthetic_choice != current_filter and aesthetic_choice not in CLASSIC_KEYS:
            new_filter = aesthetic_choice

        if new_filter != current_filter:
            set_filter(new_filter)
            set_processed([])
            st.rerun()

        st.markdown("")

        # --- Sticker ---
        st.markdown("**Sticker**")
        current_sticker = get_sticker()
        sticker_choice  = st.radio(
            "sticker_select",
            options=[s.key for s in STICKERS],
            format_func=lambda k: next(s.label for s in STICKERS if s.key == k),
            index=next(i for i,s in enumerate(STICKERS) if s.key == current_sticker),
            horizontal=True,
            label_visibility="collapsed",
        )
        if sticker_choice != current_sticker:
            set_sticker(sticker_choice)
            set_processed([])
            st.rerun()

        st.markdown("---")

        # --- Frame ---
        st.markdown("**Frame**")
        current_frame = get_frame()
        frame_keys    = list(FRAME_MAP.keys())
        frame_choice  = st.radio(
            "frame_radio",
            options=frame_keys,
            format_func=lambda k: FRAME_MAP[k].label,
            index=frame_keys.index(current_frame) if current_frame in frame_keys else 0,
            horizontal=True,
            label_visibility="collapsed",
        )
        if frame_choice != current_frame:
            set_frame(frame_choice)
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
                _generate_strip(processed_bytes)

    # ── Live strip preview ──────────────────────────────────────────────────
    with col_preview:
        st.markdown('<p class="snap-section">Preview</p>', unsafe_allow_html=True)
        try:
            st.image(
                _strip_preview_bytes(processed_bytes),
                width='stretch',
                caption=f"{FRAME_MAP[get_frame()].label} · {layout_cfg.cols}×{layout_cfg.rows}",
            )
        except Exception as exc:
            st.warning(f"Preview unavailable: {exc}")


def _generate_strip(processed_bytes: list):
    pil_images = _bytes_to_pil(processed_bytes)
    frame_cfg  = FRAME_MAP[get_frame()]
    layout_cfg = get_layout()
    with st.spinner("Composing your HD strip…"):
        try:
            strip = compose_strip(pil_images, frame_cfg, layout=layout_cfg)
            set_strip_bytes(export_jpg(strip))
            set_strip_pdf(export_pdf(strip))
            set_stage(STAGE_DOWNLOAD)
            st.rerun()
        except Exception as exc:
            st.error(f"Strip generation failed: {exc}")