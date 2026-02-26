"""
Mobile device detection + full-page block screen.

Call inject_mobile_block() at the very top of app.py (after st.set_page_config).
Uses JS to detect mobile UA + touch screen, then overlays the entire viewport
with a polished "use desktop" screen. The underlying Streamlit app is hidden.
"""

import streamlit as st


_MOBILE_BLOCK_HTML = """
<script>
(function() {
  var ua = navigator.userAgent || navigator.vendor || window.opera;
  var isMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini|mobile|tablet|silk|kindle/i.test(ua)
               || (navigator.maxTouchPoints > 1 && /Macintosh/i.test(ua))   // iPad with desktop UA
               || window.innerWidth < 768;

  if (!isMobile) return;

  // Build the full-page overlay
  var overlay = document.createElement('div');
  overlay.id  = 'snapbooth-mobile-block';
  overlay.innerHTML = `
    <div class="mb-bg"></div>
    <div class="mb-card">
      <div class="mb-icon">
        <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
          <!-- Monitor -->
          <rect x="4" y="8" width="44" height="30" rx="3" stroke="#e0ff60" stroke-width="2.5" fill="none"/>
          <line x1="26" y1="38" x2="26" y2="46" stroke="#e0ff60" stroke-width="2.5"/>
          <line x1="16" y1="46" x2="36" y2="46" stroke="#e0ff60" stroke-width="2.5"/>
          <!-- Phone (crossed) -->
          <rect x="42" y="22" width="16" height="28" rx="2.5" stroke="#555" stroke-width="2" fill="none"/>
          <line x1="38" y1="20" x2="62" y2="52" stroke="#ff5566" stroke-width="2.5" stroke-linecap="round"/>
        </svg>
      </div>
      <h1 class="mb-title">Open on Desktop</h1>
      <p class="mb-sub">SnapBooth works best on a laptop or PC.</p>
      <div class="mb-reason-list">
        <div class="mb-reason">
          <span class="mb-icon-sm">📷</span>
          <span>Webcam access requires a desktop browser</span>
        </div>
        <div class="mb-reason">
          <span class="mb-icon-sm">🖥️</span>
          <span>The photobooth experience is designed for larger screens</span>
        </div>
        <div class="mb-reason">
          <span class="mb-icon-sm">⚡</span>
          <span>Image processing and downloads work best on desktop</span>
        </div>
      </div>
      <div class="mb-url-box">
        <span class="mb-url-label">Visit on your computer:</span>
        <span class="mb-url" id="mb-url-text"></span>
        <button class="mb-copy-btn" onclick="
          navigator.clipboard.writeText(window.location.href).then(function(){
            this.textContent='Copied!'; this.style.background='#e0ff60'; this.style.color='#111';
          }.bind(this));
        ">Copy Link</button>
      </div>
      <p class="mb-footer">snapbooth.app &nbsp;·&nbsp; Virtual Photobooth</p>
    </div>
  `;

  // Inject styles
  var style = document.createElement('style');
  style.textContent = `
    #snapbooth-mobile-block {
      position: fixed; inset: 0; z-index: 999999;
      display: flex; align-items: center; justify-content: center;
      padding: 24px; box-sizing: border-box;
      font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .mb-bg {
      position: absolute; inset: 0;
      background: radial-gradient(ellipse at 60% 20%, #1a1a2e 0%, #0e0e0e 60%);
    }
    /* Subtle dot grid */
    .mb-bg::after {
      content: '';
      position: absolute; inset: 0;
      background-image: radial-gradient(circle, #ffffff0a 1px, transparent 1px);
      background-size: 28px 28px;
    }
    .mb-card {
      position: relative;
      background: #131320;
      border: 1px solid #2a2a3a;
      border-radius: 24px;
      padding: 44px 36px 36px;
      max-width: 420px;
      width: 100%;
      text-align: center;
      box-shadow: 0 32px 80px rgba(0,0,0,0.7), 0 0 0 1px #ffffff08 inset;
    }
    .mb-icon {
      margin-bottom: 20px;
      filter: drop-shadow(0 0 18px #e0ff6033);
    }
    .mb-title {
      font-size: 1.9rem;
      font-weight: 700;
      color: #ffffff;
      margin: 0 0 8px;
      letter-spacing: -0.02em;
    }
    .mb-sub {
      font-size: 0.95rem;
      color: #888;
      margin: 0 0 28px;
      line-height: 1.5;
    }
    .mb-reason-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      text-align: left;
      margin-bottom: 28px;
    }
    .mb-reason {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      background: #1a1a2a;
      border-radius: 10px;
      padding: 10px 14px;
      font-size: 0.82rem;
      color: #bbb;
      line-height: 1.4;
      border: 1px solid #252535;
    }
    .mb-icon-sm { font-size: 1.1rem; flex-shrink: 0; margin-top: 1px; }
    .mb-url-box {
      background: #0e0e18;
      border: 1px solid #2a2a3a;
      border-radius: 12px;
      padding: 14px 16px;
      margin-bottom: 24px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      align-items: center;
    }
    .mb-url-label { font-size: 0.72rem; color: #555; text-transform: uppercase; letter-spacing: 0.08em; }
    .mb-url {
      font-size: 0.78rem;
      color: #e0ff60;
      word-break: break-all;
      line-height: 1.4;
    }
    .mb-copy-btn {
      background: #1e1e30;
      color: #ccc;
      border: 1px solid #333;
      border-radius: 20px;
      padding: 6px 18px;
      font-size: 0.78rem;
      cursor: pointer;
      transition: all 0.2s;
      font-family: inherit;
    }
    .mb-copy-btn:hover { background: #2a2a40; border-color: #555; color: #fff; }
    .mb-footer {
      font-size: 0.7rem;
      color: #333;
      margin: 0;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
  `;

  document.head.appendChild(style);
  document.body.appendChild(overlay);
  document.getElementById('mb-url-text').textContent = window.location.href;

  // Hide Streamlit's root so it doesn't flash behind the overlay
  var appRoot = document.getElementById('root') || document.querySelector('[data-testid="stAppViewContainer"]');
  if (appRoot) appRoot.style.display = 'none';

  // Also keep hiding it after Streamlit re-renders
  var obs = new MutationObserver(function() {
    var r = document.querySelector('[data-testid="stAppViewContainer"]');
    if (r) r.style.display = 'none';
  });
  obs.observe(document.body, { childList: true, subtree: true });
})();
</script>
"""


def inject_mobile_block():
    """
    Call this once at the top of app.py (right after set_page_config + init_session).
    On mobile devices it renders a full-page block overlay and hides the app.
    On desktop it does nothing.
    """
    st.markdown(_MOBILE_BLOCK_HTML, unsafe_allow_html=True)