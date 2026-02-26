"""
Stage 2 — Camera capture with freeze-frame confirmation.

Flow per shot:
  1. Camera widget shown → user clicks shutter
  2. Frame is IMMEDIATELY frozen and stored as pending_photo
  3. Camera hides, frozen preview shown
  4. User clicks "Use this photo" → saved, move to next shot
     OR "Retake" → discard, camera shown again
"""

import streamlit as st

from config.settings import STAGE_PREVIEW, STAGE_TEMPLATE
from core.session import (
    add_photo, photos_count,
    set_stage, clear_photos,
    get_pending_photo, set_pending_photo,
    get_max_photos, get_min_photos, get_layout,
)
from core.validation import validate_image_bytes


def render():
    max_photos = get_max_photos()
    layout     = get_layout()
    count      = photos_count()

    # Auto-advance when quota full
    if count >= max_photos:
        set_pending_photo(None)
        set_stage(STAGE_PREVIEW)
        st.rerun()
        return

    st.markdown(
        f'<div class="photo-counter">Shot {count + 1} of {max_photos} '
        f'&nbsp;·&nbsp; {layout.cols}×{layout.rows} layout</div>',
        unsafe_allow_html=True,
    )

    pending = get_pending_photo()

    if pending is not None:
        # ── Freeze-frame confirmation ─────────────────────────────────────
        st.markdown('<p class="snap-section">Use this photo?</p>', unsafe_allow_html=True)

        col_l, col_m, col_r = st.columns([1, 3, 1])
        with col_m:
            st.image(pending, use_container_width=True)

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
                    set_stage(STAGE_PREVIEW)
                st.rerun()

    else:
        # ── Live camera ───────────────────────────────────────────────────
        st.markdown(
            f'<p class="snap-section">Take Photo {count + 1}</p>',
            unsafe_allow_html=True,
        )

        # Camera permission helper — shown above the widget
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
                set_pending_photo(raw)
                st.rerun()

        _render_progress_dots(count, max_photos)

    # ── Navigation ───────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_mid, col_next = st.columns([1, 2, 1])

    with col_back:
        if st.button("← Back", type="secondary"):
            clear_photos()
            set_pending_photo(None)
            set_stage(STAGE_TEMPLATE)
            st.rerun()

    with col_next:
        can_proceed = count >= max_photos and pending is None
        if st.button(
            "Preview →",
            type="primary",
            disabled=not can_proceed,
            use_container_width=True,
        ):
            set_stage(STAGE_PREVIEW)
            st.rerun()

    if 0 < count < max_photos and pending is None:
        remaining = max_photos - count
        st.caption(f"{remaining} more photo{'s' if remaining > 1 else ''} to go.")


def _render_progress_dots(done: int, total: int):
    # Cap displayed dots at 12 for very large layouts, show number instead
    if total > 12:
        pct = int(done / total * 100)
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