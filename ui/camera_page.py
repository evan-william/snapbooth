"""
Stage 2 — Camera capture.
Guides the user through taking MAX_PHOTOS sequential shots.
"""

import streamlit as st

from config.settings import MAX_PHOTOS, MIN_PHOTOS, STAGE_PREVIEW, STAGE_TEMPLATE
from core.session import (
    get_photos, add_photo, photos_count, photos_remaining,
    set_stage, clear_photos,
)
from core.validation import validate_image_bytes


def render():
    count     = photos_count()
    remaining = photos_remaining()

    st.markdown(
        f'<div class="photo-counter">Shot {count + 1} of {MAX_PHOTOS}</div>',
        unsafe_allow_html=True,
    )

    if remaining > 0:
        st.markdown(
            f'<p class="snap-section">Take Photo {count + 1}</p>',
            unsafe_allow_html=True,
        )

        # --- Camera widget --------------------------------------------------
        camera_img = st.camera_input(
            label="Look at the camera and click the capture button",
            key=f"cam_{count}",       # unique key forces a fresh widget each shot
        )

        if camera_img is not None:
            raw = camera_img.getvalue()
            err = validate_image_bytes(raw)

            if err:
                st.error(f"Could not use that image: {err}")
            else:
                add_photo(raw)
                # Show a quick success flash
                if photos_remaining() > 0:
                    st.success(f"Got it! {photos_remaining()} more to go.")
                else:
                    st.success("All shots taken! Moving to preview…")
                st.rerun()

        # Progress dots
        _render_progress_dots(count, MAX_PHOTOS)

    # --- Navigation ---------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_mid, col_next = st.columns([1, 2, 1])

    with col_back:
        if st.button("← Back", type="secondary"):
            clear_photos()
            set_stage(STAGE_TEMPLATE)
            st.rerun()

    with col_next:
        can_proceed = photos_count() >= MIN_PHOTOS
        if st.button(
            "Preview →",
            type="primary",
            disabled=not can_proceed,
            use_container_width=True,
        ):
            set_stage(STAGE_PREVIEW)
            st.rerun()

    if not can_proceed and photos_count() > 0:
        st.caption(f"Take at least {MIN_PHOTOS} photos to continue.")


def _render_progress_dots(done: int, total: int):
    dots_html = '<div style="display:flex;gap:6px;justify-content:center;margin-top:1rem;">'
    for i in range(total):
        if i < done:
            color = "#e0ff60"
        elif i == done:
            color = "#555"
            # Pulsing dot for "current"
            dots_html += (
                f'<div style="width:10px;height:10px;border-radius:50%;'
                f'background:{color};animation:pulse 1s infinite;"></div>'
            )
            continue
        else:
            color = "#333"
        dots_html += (
            f'<div style="width:10px;height:10px;border-radius:50%;background:{color};"></div>'
        )
    dots_html += "</div>"
    st.markdown(dots_html, unsafe_allow_html=True)