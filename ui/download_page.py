"""
Stage 4 — Download.
"""

import streamlit as st

from config.settings import STAGE_TEMPLATE, STAGE_PREVIEW
from core.session import (
    get_strip_bytes, get_strip_pdf,
    set_stage, reset_session,
)

_PAGE_CSS = """<style>
/* ── Download buttons — force readable text in ALL states ── */
[data-testid="stDownloadButton"] > button {
    width: 100% !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
}

/* JPG = primary yellow */
[data-testid="stDownloadButton"] > button[kind="primary"] {
    background: #e0ff60 !important;
    color: #111111 !important;
    border: none !important;
}
[data-testid="stDownloadButton"] > button[kind="primary"]:hover {
    background: #cff040 !important;
    color: #111111 !important;
}

/* PDF = secondary — white text on dark border, always visible */
[data-testid="stDownloadButton"] > button[kind="secondary"] {
    background: #1e1e1e !important;
    color: #f0f0f0 !important;
    border: 1px solid #555 !important;
}
[data-testid="stDownloadButton"] > button[kind="secondary"]:hover {
    background: #2a2a2a !important;
    color: #ffffff !important;
    border-color: #888 !important;
}

/* Footer */
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


def render():
    st.markdown(_PAGE_CSS, unsafe_allow_html=True)

    jpg = get_strip_bytes()
    pdf = get_strip_pdf()

    if not jpg:
        st.warning("No strip found. Please go back and generate one.")
        if st.button("← Back to Preview", type="secondary"):
            set_stage(STAGE_PREVIEW)
            st.rerun()
        return

    st.markdown('<p class="snap-section">Your Photobooth Strip</p>', unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.image(jpg, width='stretch', caption="Your strip is ready!")

    st.markdown("---")
    st.markdown("**Download**")

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
                type="secondary",
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

    _render_footer()


def _render_footer():
    st.markdown(
        """
        <div class="snap-footer">
            <div class="snap-footer-name">Evan Wollian</div>
            <div class="snap-footer-copy">© 2025 Evan Wollian · SnapBooth · All rights reserved</div>
        </div>
        """,
        unsafe_allow_html=True,
    )