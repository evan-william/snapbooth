"""
Stage 3 — Preview & customise.
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


_FOOTER_CSS = """<style>
.choice-title {
    font-size: 0.78rem;
    color: #8b8b8b;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 0 0 0.45rem;
}
.choice-card {
    border: 1px solid #292929;
    background: #111;
    border-radius: 8px;
    padding: 0.45rem 0.5rem;
    min-height: 46px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: #d8d8d8;
    font-size: 0.78rem;
    font-weight: 650;
    line-height: 1.2;
    margin-bottom: 0.25rem;
}
.choice-card.selected {
    border-color: #e0ff60;
    background: linear-gradient(135deg, #1d2308, #111);
    color: #e0ff60;
    box-shadow: 0 0 12px #e0ff6030;
}
.choice-card .choice-sub {
    display: block;
    color: #686868;
    font-size: 0.62rem;
    font-weight: 500;
    margin-top: 0.15rem;
}
.choice-card.selected .choice-sub { color: #9faf46; }
.stButton > button {
    white-space: normal !important;
    min-height: 2.45rem;
    line-height: 1.15;
}
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


def _bytes_to_pil(processed: list) -> list:
    """Convert bytes→PIL if camera_page stored bytes. If already PIL, return as-is."""
    result = []
    for item in processed:
        if isinstance(item, (bytes, bytearray)):
            try:
                img = Image.open(io.BytesIO(item))
                img.load()
                result.append(img.convert("RGB"))
            except Exception:
                pass
        else:
            result.append(item)
    return result


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
    frame_cfg  = FRAME_MAP[get_frame()]
    layout_cfg = get_layout()
    strip      = compose_strip(processed, frame_cfg, layout=layout_cfg)
    buf        = io.BytesIO()
    strip.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _render_option_grid(title: str, options: list, current_key: str,
                        key_prefix: str, columns: int = 3) -> str:
    st.markdown(f'<p class="choice-title">{title}</p>', unsafe_allow_html=True)
    selected = current_key

    for row_start in range(0, len(options), columns):
        row = options[row_start:row_start + columns]
        cols = st.columns(len(row), gap="small")
        for col, option in zip(cols, row):
            opt_key = option.key
            label = option.label
            is_selected = opt_key == current_key
            card_class = "choice-card selected" if is_selected else "choice-card"
            button_label = f"✓ {label}" if is_selected else label
            with col:
                st.markdown(
                    f'<div class="{card_class}"><span>{label}</span></div>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    button_label,
                    key=f"{key_prefix}_{opt_key}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True,
                ):
                    selected = opt_key

    return selected


def render():
    st.markdown(_FOOTER_CSS, unsafe_allow_html=True)

    processed = get_processed()
    if processed:
        processed = _bytes_to_pil(processed)

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

    layout_cfg = get_layout()
    col_ctrl, col_preview = st.columns([3, 2], gap="large")

    with col_ctrl:
        st.markdown('<p class="snap-section">Your Photos</p>', unsafe_allow_html=True)
        n_cols   = min(4, len(processed))
        th_cols  = st.columns(n_cols)
        for i, img in enumerate(processed):
            th_cols[i % n_cols].image(
                generate_thumbnail(img, width=100), width='stretch'
            )

        st.markdown("---")

        current_filter = get_filter()
        filter_choice = _render_option_grid(
            "Filter",
            FILTERS,
            current_filter,
            "filter_choice",
            columns=3,
        )
        if filter_choice != current_filter:
            set_filter(filter_choice)
            set_processed([])
            st.rerun()

        st.markdown("")

        current_sticker = get_sticker()
        sticker_choice = _render_option_grid(
            "Sticker",
            STICKERS,
            current_sticker,
            "sticker_choice",
            columns=3,
        )
        if sticker_choice != current_sticker:
            set_sticker(sticker_choice)
            set_processed([])
            st.rerun()

        st.markdown("---")

        current_frame = get_frame()
        frame_choice = _render_option_grid(
            "Frame",
            list(FRAME_MAP.values()),
            current_frame,
            "frame_choice",
            columns=3,
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
                _generate_strip(processed)

    with col_preview:
        st.markdown('<p class="snap-section">Preview</p>', unsafe_allow_html=True)
        try:
            st.image(
                _strip_preview_bytes(processed),
                width='stretch',
                caption=f"{FRAME_MAP[get_frame()].label} · {layout_cfg.cols}×{layout_cfg.rows}",
            )
        except Exception as exc:
            st.warning(f"Preview unavailable: {exc}")

    _render_footer()


def _generate_strip(photos: list):
    frame_cfg  = FRAME_MAP[get_frame()]
    layout_cfg = get_layout()
    with st.spinner("Composing your strip…"):
        try:
            strip = compose_strip(photos, frame_cfg, layout=layout_cfg)
            set_strip_bytes(export_jpg(strip))
            set_strip_pdf(export_pdf(strip))
            set_stage(STAGE_DOWNLOAD)
            st.rerun()
        except Exception as exc:
            st.error(f"Strip generation failed: {exc}")


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
