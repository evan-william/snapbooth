"""
Stage 2 — Camera capture with freeze-frame confirmation.

Root-cause fixes:
  FLASH BUG:
    CSS mirrors both <video> and <img> inside camera widget so no flip flash.

  FLICKER ON LAST PHOTO:
    After accepting the last photo, pre-process and store as JPEG bytes
    (not PIL Image objects — those can't survive session state serialization
    reliably and cause the preview page to fall back to cold rebuild, which
    causes the flicker). Bytes survive perfectly.

  MISSING MEDIAFILE ERROR:
    Caused by stale PIL Image objects in session state being passed to
    st.image(). Now thumbnails on preview page come from stored bytes.

  use_container_width DEPRECATION:
    Replaced all use_container_width=True  → width='stretch'
    Replaced all use_container_width=False → width='content'
"""

import io
import streamlit as st
from PIL import Image

from config.settings import STAGE_PREVIEW, STAGE_TEMPLATE, STICKER_MAP
from core.session import (
    add_photo, photos_count,
    set_stage, clear_photos,
    get_pending_photo, set_pending_photo,
    get_max_photos, get_layout,
    get_photos, get_filter, get_sticker,
    set_processed, get_processed,
)
from core.validation import validate_image_bytes, safe_open_image
from core.filters import apply_filter
from core.stickers import apply_sticker


def _mirror_image(data: bytes) -> bytes:
    """Horizontally flip the captured JPEG to match the mirrored live preview."""
    try:
        img = Image.open(io.BytesIO(data))
        flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
        buf = io.BytesIO()
        flipped.save(buf, format="JPEG", quality=97, optimize=True)
        return buf.getvalue()
    except Exception:
        return data


def _build_processed_as_bytes() -> list:
    """
    Process all stored photos with current filter/sticker.
    Returns list of JPEG bytes (NOT PIL Image objects).
    Bytes survive st.session_state serialization perfectly;
    PIL Images do not and cause MediaFileHandler errors + flicker.
    """
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
        # Serialize to bytes immediately — safe for session state
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95, subsampling=0)
        result.append(buf.getvalue())
    return result


_CAMERA_CSS = """<style>
/* Mirror live video feed → selfie feel */
[data-testid="stCameraInput"] video {
    transform: scaleX(-1) !important;
}
/*
 * KEY FIX: After capture, Streamlit shows the raw captured frame as an <img>
 * inside the widget BEFORE Python reacts. That img is unflipped → user sees
 * the jarring flip for a split second.
 * By also flipping the img, the preview looks identical to the video feed,
 * so the transition is invisible. Python-side we still flip the bytes normally.
 */
[data-testid="stCameraInput"] img {
    transform: scaleX(-1) !important;
}
</style>"""


def render():
    # Inject CSS at the very top, every render
    st.markdown(_CAMERA_CSS, unsafe_allow_html=True)

    max_photos = get_max_photos()
    layout     = get_layout()
    count      = photos_count()
    pending    = get_pending_photo()

    # ── Hard guard: if already full and not confirming, go straight to preview
    if count >= max_photos and pending is None:
        set_stage(STAGE_PREVIEW)
        st.rerun()
        return

    st.markdown(
        f'<div class="photo-counter">Shot {count + 1} of {max_photos} '
        f'&nbsp;·&nbsp; {layout.cols}×{layout.rows} layout</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════════════
    # BRANCH A — Freeze-frame confirmation
    # ══════════════════════════════════════════════════════════════════════
    if pending is not None:
        st.markdown('<p class="snap-section">Use this photo?</p>', unsafe_allow_html=True)

        col_l, col_m, col_r = st.columns([1, 3, 1])
        with col_m:
            st.image(pending, width='stretch')

        st.markdown("<br>", unsafe_allow_html=True)
        col_ret, col_use = st.columns(2, gap="small")

        with col_ret:
            if st.button("↩ Retake", type="secondary", use_container_width=True):
                set_pending_photo(None)
                st.rerun()

        with col_use:
            if st.button("✓ Use this photo", type="primary", use_container_width=True):
                add_photo(pending)
                set_pending_photo(None)
                new_count = photos_count()

                if new_count >= max_photos:
                    # ── GLITCH FIX: pre-process photos HERE before switching ──
                    # Store as JPEG bytes (not PIL Images) to avoid
                    # MediaFileHandler errors and session state serialization issues.
                    with st.spinner("✨ Preparing your strip…"):
                        processed_bytes = _build_processed_as_bytes()
                        if processed_bytes:
                            set_processed(processed_bytes)
                    set_stage(STAGE_PREVIEW)
                    # Single clean rerun → preview page renders immediately
                    st.rerun()
                else:
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back", type="secondary"):
            clear_photos()
            set_pending_photo(None)
            set_stage(STAGE_TEMPLATE)
            st.rerun()

        return  # ← early return: don't render camera widget while confirming

    # ══════════════════════════════════════════════════════════════════════
    # BRANCH B — Live camera
    # ══════════════════════════════════════════════════════════════════════
    st.markdown(
        f'<p class="snap-section">Take Photo {count + 1}</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="background:#1a1a1a;border:1px solid #333;border-radius:8px;'
        'padding:10px 14px;margin-bottom:10px;font-size:0.78rem;color:#888;">'
        '📷 &nbsp;If you see a black screen or permission prompt: '
        '<strong style="color:#ccc;">click the camera icon in your browser\'s address bar</strong> '
        'and allow camera access, then press the <strong style="color:#e0ff60;">↺ Refresh</strong> button below.'
        '</div>',
        unsafe_allow_html=True,
    )

    col_cam, col_refresh = st.columns([5, 1])
    with col_refresh:
        if st.button("↺ Refresh", key=f"cam_refresh_{count}", type="secondary",
                     use_container_width=True):
            st.rerun()

    camera_img = st.camera_input(
        label="Point your camera and click Take Photo",
        key=f"cam_{count}",
    )

    if camera_img is not None:
        raw = camera_img.getvalue()
        err = validate_image_bytes(raw)
        if err:
            st.error(f"Could not use that image: {err}")
        else:
            # Flip bytes to match what user saw (video was mirrored via CSS)
            mirrored = _mirror_image(raw)
            set_pending_photo(mirrored)
            st.rerun()

    _render_progress_dots(count, max_photos)

    # ── Navigation ────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_mid, col_next = st.columns([1, 2, 1])

    with col_back:
        if st.button("← Back", type="secondary"):
            clear_photos()
            set_pending_photo(None)
            set_stage(STAGE_TEMPLATE)
            st.rerun()

    with col_next:
        # Disabled (black, unclickable) until ALL photos are taken
        # Only becomes active (yellow) when count >= max_photos
        photos_full = count >= max_photos
        if st.button(
            "Preview →",
            type="primary",
            disabled=not photos_full,
            use_container_width=True,
        ):
            set_stage(STAGE_PREVIEW)
            st.rerun()

    if 0 < count < max_photos:
        remaining = max_photos - count
        st.caption(f"{remaining} more photo{'s' if remaining > 1 else ''} to go.")


def _render_progress_dots(done: int, total: int):
    if total > 12:
        st.markdown(
            f'<div style="text-align:center;margin-top:1rem;color:#888;font-size:0.8rem;">'
            f'{done} / {total} photos taken</div>',
            unsafe_allow_html=True,
        )
        st.progress(done / total)
        return

    dots_html = '<div style="display:flex;gap:6px;justify-content:center;margin-top:1rem;">'
    for i in range(total):
        if i < done:
            dots_html += '<div style="width:10px;height:10px;border-radius:50%;background:#e0ff60;"></div>'
        elif i == done:
            dots_html += (
                '<div style="width:10px;height:10px;border-radius:50%;'
                'background:#555;animation:pulse 1s infinite;"></div>'
            )
        else:
            dots_html += '<div style="width:10px;height:10px;border-radius:50%;background:#333;"></div>'
    dots_html += "</div>"
    st.markdown(dots_html, unsafe_allow_html=True)