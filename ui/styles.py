"""
CSS injection for Streamlit.

Using a single CSS block loaded once in app.py keeps styling centralised
and avoids scattering st.markdown('<style>') calls everywhere.
"""

GLOBAL_CSS = """
<style>
/* ── Google Font import ── */
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Reset & base ── */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0e0e0e;
    color: #f0f0f0;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── App container ── */
[data-testid="stAppViewContainer"] > .main > .block-container {
    max-width: 780px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

/* ── Page header ── */
.snap-header {
    text-align: center;
    padding: 2rem 0 1.2rem;
}
.snap-header h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 3rem;
    letter-spacing: -0.02em;
    color: #ffffff;
    margin: 0;
}
.snap-header p {
    font-size: 0.95rem;
    color: #888;
    margin: 0.4rem 0 0;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ── Stage breadcrumb ── */
.snap-steps {
    display: flex;
    justify-content: center;
    gap: 0.4rem;
    margin: 0.6rem 0 2rem;
    font-size: 0.78rem;
    color: #555;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.snap-step-active { color: #e0ff60; font-weight: 600; }

/* ── Section heading ── */
.snap-section {
    font-family: 'DM Serif Display', serif;
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: #fff;
}

/* ── Frame card grid ── */
.frame-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 0.8rem;
    margin-bottom: 2rem;
}
.frame-card {
    border-radius: 10px;
    padding: 1rem 0.5rem;
    text-align: center;
    cursor: pointer;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    border: 2px solid transparent;
}
.frame-card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.4); }
.frame-card.selected { border-color: #e0ff60; }
.frame-swatch {
    width: 48px; height: 68px;
    border-radius: 6px;
    margin: 0 auto 0.5rem;
}
.frame-label { font-size: 0.8rem; color: #ccc; }

/* ── Counter badge ── */
.photo-counter {
    background: #1a1a1a;
    border-radius: 30px;
    padding: 0.5rem 1.2rem;
    display: inline-block;
    font-size: 0.85rem;
    color: #e0ff60;
    margin-bottom: 1rem;
    border: 1px solid #333;
}

/* ── Filter pills ── */
.filter-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin: 0.5rem 0 1.5rem;
}
.filter-pill {
    border-radius: 20px;
    padding: 0.35rem 0.9rem;
    font-size: 0.8rem;
    cursor: pointer;
    border: 1px solid #333;
    background: #1a1a1a;
    color: #aaa;
    transition: all 0.15s ease;
}
.filter-pill.active {
    background: #e0ff60;
    color: #111;
    border-color: #e0ff60;
    font-weight: 600;
}

/* ── Preview strip ── */
.strip-preview {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #222;
    margin: 1rem auto;
    display: block;
    max-width: 300px;
}

/* ── Download buttons ── */
[data-testid="stDownloadButton"] > button {
    width: 100%;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    letter-spacing: 0.03em;
    transition: opacity 0.15s ease;
}
[data-testid="stDownloadButton"] > button:hover { opacity: 0.88; }

/* ── Primary action button ── */
.stButton > button[kind="primary"] {
    background: #e0ff60;
    color: #111;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    letter-spacing: 0.03em;
    padding: 0.55rem 1.5rem;
}
.stButton > button[kind="primary"]:hover { background: #cff040; }

/* ── Secondary button ── */
.stButton > button[kind="secondary"] {
    background: transparent;
    color: #888;
    border: 1px solid #333;
    border-radius: 8px;
}
.stButton > button[kind="secondary"]:hover { border-color: #666; color: #ccc; }

/* ── Alert / info boxes ── */
[data-testid="stInfo"] { background: #1a1a2e; border-left-color: #e0ff60; }

/* ── Divider ── */
hr { border-color: #222; }
</style>
"""


def inject_css():
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)