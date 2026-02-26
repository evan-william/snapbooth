"""
Stage 4 — Download.
Shows the final strip and offers JPG + PDF download buttons.
"""

import streamlit as st

from config.settings import STAGE_TEMPLATE, STAGE_PREVIEW
from core.session import (
    get_strip_bytes, get_strip_pdf,
    set_stage, reset_session,
)


def render():
    jpg = get_strip_bytes()
    pdf = get_strip_pdf()

    if not jpg:
        st.warning("No strip found. Please go back and generate one.")
        if st.button("← Back to Preview", type="secondary"):
            set_stage(STAGE_PREVIEW)
            st.rerun()
        return

    st.markdown('<p class="snap-section">Your Photobooth Strip</p>', unsafe_allow_html=True)

    # Display the strip centred
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.image(jpg, use_container_width=True, caption="Your strip is ready!")

    st.markdown("---")
    st.markdown("**Download**")

    # Force black text on the primary (yellow) download button
    st.markdown(
        """<style>
        [data-testid="stDownloadButton"] > button {
            color: #111111 !important;
            font-weight: 700 !important;
        }
        [data-testid="stDownloadButton"] > button[kind="primary"] {
            background: #e0ff60 !important;
            color: #111111 !important;
            border: none !important;
        }
        [data-testid="stDownloadButton"] > button[kind="secondary"] {
            color: #111111 !important;
            border: 1px solid #555 !important;
        }
        </style>""",
        unsafe_allow_html=True,
    )

    col_jpg, col_pdf = st.columns(2)
    with col_jpg:
        st.download_button(
            label="⬇ Download JPG",
            data=jpg,
            file_name="snapbooth_strip.jpg",
            mime="image/jpeg",
            type="primary",
            use_container_width=True,
        )

    with col_pdf:
        if pdf:
            st.download_button(
                label="⬇ Download PDF",
                data=pdf,
                file_name="snapbooth_strip.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.info("PDF generation requires ReportLab.")

    st.markdown("---")
    col_back, _, col_new = st.columns([1, 2, 1])

    with col_back:
        if st.button("← Edit", type="secondary"):
            set_stage(STAGE_PREVIEW)
            st.rerun()

    with col_new:
        if st.button("New Session", type="primary", use_container_width=True):
            reset_session()
            st.rerun()