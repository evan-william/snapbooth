"""
Mobile device detection + full-page block screen.

Uses st.components.v1.html() — the ONLY way to run real JavaScript in Streamlit.
st.markdown(<script>) silently strips all script tags, so it never worked.

The component injects JS into the PARENT window (via window.parent) which
overlays the entire Streamlit app with a "use desktop" screen.
"""

import streamlit as st
import streamlit.components.v1 as components


_MOBILE_BLOCK_JS = """
<script>
(function() {
  var ua = navigator.userAgent || navigator.vendor || window.opera;

  // Detect mobile: UA string + touchpoints + narrow viewport
  var isMobile = (
    /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini|mobile|tablet|silk|kindle/i.test(ua)
    || (navigator.maxTouchPoints > 1 && /Macintosh/i.test(ua))
    || window.parent.innerWidth < 768
  );

  if (!isMobile) return;

  // ── Work on the PARENT document (actual Streamlit page) ──────────────────
  var doc = window.parent.document;
  var win = window.parent;

  // Prevent flash of Streamlit app
  var appRoot = doc.querySelector('[data-testid="stAppViewContainer"]')
             || doc.querySelector('.main')
             || doc.getElementById('root');
  if (appRoot) appRoot.style.cssText = 'display:none!important';

  // Inject global CSS into parent
  if (!doc.getElementById('mb-style')) {
    var style = doc.createElement('style');
    style.id = 'mb-style';
    style.textContent = [
      '#snapbooth-mobile-block{',
        'position:fixed;inset:0;z-index:2147483647;',
        'display:flex;align-items:center;justify-content:center;',
        'padding:24px;box-sizing:border-box;',
        'font-family:"DM Sans",-apple-system,BlinkMacSystemFont,sans-serif;',
      '}',
      '.mb-bg{',
        'position:absolute;inset:0;',
        'background:radial-gradient(ellipse at 60% 20%,#1a1a2e 0%,#0e0e0e 70%);',
      '}',
      '.mb-bg::after{',
        'content:"";position:absolute;inset:0;',
        'background-image:radial-gradient(circle,rgba(255,255,255,.06) 1px,transparent 1px);',
        'background-size:28px 28px;',
      '}',
      '.mb-card{',
        'position:relative;background:#131320;',
        'border:1px solid #2a2a3a;border-radius:24px;',
        'padding:44px 36px 36px;max-width:420px;width:100%;',
        'text-align:center;',
        'box-shadow:0 32px 80px rgba(0,0,0,.8),0 0 0 1px rgba(255,255,255,.04) inset;',
      '}',
      '.mb-pulse{animation:mb-pulse-anim 2s ease-in-out infinite;}',
      '@keyframes mb-pulse-anim{0%,100%{filter:drop-shadow(0 0 8px #e0ff6033);}50%{filter:drop-shadow(0 0 24px #e0ff6088);}}',
      '.mb-badge{',
        'display:inline-block;background:#e0ff6018;color:#e0ff60;',
        'border:1px solid #e0ff6044;border-radius:20px;',
        'font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;',
        'padding:4px 12px;margin-bottom:18px;',
      '}',
      '.mb-title{font-size:1.85rem;font-weight:700;color:#fff;margin:0 0 8px;letter-spacing:-.02em;}',
      '.mb-sub{font-size:.92rem;color:#777;margin:0 0 24px;line-height:1.6;}',
      '.mb-divider{height:1px;background:linear-gradient(90deg,transparent,#2a2a3a,transparent);margin:0 0 24px;}',
      '.mb-reasons{display:flex;flex-direction:column;gap:8px;text-align:left;margin-bottom:24px;}',
      '.mb-reason{',
        'display:flex;align-items:flex-start;gap:10px;',
        'background:#0e0e18;border-radius:10px;padding:10px 14px;',
        'font-size:.82rem;color:#aaa;line-height:1.45;',
        'border:1px solid #1e1e2e;',
      '}',
      '.mb-icon-sm{font-size:1rem;flex-shrink:0;margin-top:1px;}',
      '.mb-url-box{',
        'background:#0a0a14;border:1px solid #1e1e2e;border-radius:12px;',
        'padding:14px 16px;margin-bottom:20px;',
        'display:flex;flex-direction:column;gap:8px;align-items:center;',
      '}',
      '.mb-url-label{font-size:.68rem;color:#444;text-transform:uppercase;letter-spacing:.1em;}',
      '.mb-url{font-size:.78rem;color:#e0ff60;word-break:break-all;line-height:1.5;}',
      '.mb-copy{',
        'background:#1a1a28;color:#ccc;border:1px solid #2a2a3a;',
        'border-radius:20px;padding:7px 20px;font-size:.78rem;',
        'cursor:pointer;transition:all .2s;font-family:inherit;',
      '}',
      '.mb-copy:hover{background:#252538;border-color:#555;color:#fff;}',
      '.mb-copy.copied{background:#e0ff60;color:#111;border-color:#e0ff60;}',
      '.mb-footer{font-size:.65rem;color:#2a2a3a;margin:0;letter-spacing:.06em;text-transform:uppercase;}',
    ].join('');
    doc.head.appendChild(style);
  }

  // Inject overlay into parent body
  if (!doc.getElementById('snapbooth-mobile-block')) {
    var div = doc.createElement('div');
    div.id = 'snapbooth-mobile-block';
    div.innerHTML = [
      '<div class="mb-bg"></div>',
      '<div class="mb-card">',
        '<div class="mb-pulse" style="margin-bottom:20px;">',
          '<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">',
            // Monitor body
            '<rect x="4" y="6" width="42" height="30" rx="3" stroke="#e0ff60" stroke-width="2.5" fill="none"/>',
            // Monitor stand
            '<line x1="25" y1="36" x2="25" y2="44" stroke="#e0ff60" stroke-width="2.5" stroke-linecap="round"/>',
            '<line x1="15" y1="44" x2="35" y2="44" stroke="#e0ff60" stroke-width="2.5" stroke-linecap="round"/>',
            // Screen content lines (decorative)
            '<line x1="11" y1="16" x2="35" y2="16" stroke="#e0ff6055" stroke-width="1.5" stroke-linecap="round"/>',
            '<line x1="11" y1="21" x2="29" y2="21" stroke="#e0ff6033" stroke-width="1.5" stroke-linecap="round"/>',
            // Phone outline (greyed, crossed)
            '<rect x="45" y="18" width="14" height="24" rx="2.5" stroke="#333" stroke-width="2" fill="none"/>',
            // Cross
            '<line x1="41" y1="15" x2="63" y2="46" stroke="#ff4455" stroke-width="2.5" stroke-linecap="round"/>',
          '</svg>',
        '</div>',
        '<div class="mb-badge">Desktop Only</div>',
        '<h1 class="mb-title">Open on a Computer</h1>',
        '<p class="mb-sub">SnapBooth uses your webcam and needs a desktop browser to work properly.</p>',
        '<div class="mb-divider"></div>',
        '<div class="mb-reasons">',
          '<div class="mb-reason"><span class="mb-icon-sm">📷</span><span>Webcam capture requires a real desktop browser</span></div>',
          '<div class="mb-reason"><span class="mb-icon-sm">🖥️</span><span>Designed and optimised for laptop and PC screens</span></div>',
          '<div class="mb-reason"><span class="mb-icon-sm">⬇️</span><span>Photo strip downloads work best on desktop</span></div>',
        '</div>',
        '<div class="mb-url-box">',
          '<span class="mb-url-label">Copy link &amp; open on your computer</span>',
          '<span class="mb-url" id="mb-url-text"></span>',
          '<button class="mb-copy" id="mb-copy-btn" onclick="',
            'var btn=document.getElementById(\'mb-copy-btn\');',
            'navigator.clipboard.writeText(window.location.href).then(function(){',
              'btn.textContent=\'✓ Copied!\';btn.classList.add(\'copied\');',
              'setTimeout(function(){btn.textContent=\'Copy Link\';btn.classList.remove(\'copied\');},2000);',
            '});',
          '">Copy Link</button>',
        '</div>',
        '<p class="mb-footer">snapbooth.app &nbsp;·&nbsp; Virtual Photobooth</p>',
      '</div>',
    ].join('');
    doc.body.appendChild(div);
    doc.getElementById('mb-url-text').textContent = win.location.href;
  }

  // Keep Streamlit app hidden as it re-renders
  var obs = new MutationObserver(function() {
    var r = doc.querySelector('[data-testid="stAppViewContainer"]');
    if (r && r.style.display !== 'none') r.style.cssText = 'display:none!important';
  });
  obs.observe(doc.body, { childList: true, subtree: false });

})();
</script>
"""


def inject_mobile_block():
    """
    Call once near the top of app.py, AFTER st.set_page_config().

    Uses st.components.v1.html() — the only Streamlit API that actually
    executes JavaScript. st.markdown(<script>) is silently stripped.

    height=0 makes the iframe invisible; JS works via window.parent.
    """
    components.html(_MOBILE_BLOCK_JS, height=0, scrolling=False)