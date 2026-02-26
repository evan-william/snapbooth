"""
Stage 2 — Camera capture with freeze-frame confirmation + auto-timer.
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
    set_processed,
)
from core.validation import validate_image_bytes, safe_open_image
from core.filters import apply_filter
from core.stickers import apply_sticker


def _mirror_image(data: bytes) -> bytes:
    try:
        img = Image.open(io.BytesIO(data))
        flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
        buf = io.BytesIO()
        flipped.save(buf, format="JPEG", quality=97, optimize=True)
        return buf.getvalue()
    except Exception:
        return data


def _build_processed_as_bytes() -> list:
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


def _get_timer_js(seconds: int) -> str:
    """
    Full self-contained timer JS:
    - Counts down from N to 0, updating the big number each second
    - Disables all timer pill buttons and the take-photo button while running
    - Auto-clicks the shutter when it hits 0
    - Re-enables everything after shutter click (Streamlit will rerun anyway)
    """
    return f"""
<script>
(function() {{
  // Kill any existing timer
  if (window._snapTimer) {{ clearInterval(window._snapTimer); window._snapTimer = null; }}

  var total   = {seconds};
  var remaining = total;

  // --- Find / create the countdown display ---
  var display = document.getElementById('snap-countdown-num');
  if (!display) return;

  // --- Disable timer pill buttons ---
  var timerBtns = document.querySelectorAll('[data-snap-timer-btn]');
  timerBtns.forEach(function(b) {{ b.disabled = true; b.style.opacity = '0.35'; }});

  // --- Disable the camera shutter button ---
  function getShutter() {{
    return document.querySelector('[data-testid="stCameraInputButton"]');
  }}
  var shutter = getShutter();
  if (shutter) {{ shutter.disabled = true; shutter.style.opacity = '0.3'; }}

  // --- Show the countdown overlay ---
  var overlay = document.getElementById('snap-timer-overlay');
  if (overlay) overlay.style.display = 'flex';

  // --- Tick ---
  window._snapTimer = setInterval(function() {{
    remaining--;
    var d = document.getElementById('snap-countdown-num');
    if (d) d.textContent = remaining;

    if (remaining <= 0) {{
      clearInterval(window._snapTimer);
      window._snapTimer = null;

      // Re-enable shutter briefly, click it, then it's Streamlit's turn
      var s = getShutter();
      if (s) {{
        s.disabled = false;
        s.style.opacity = '1';
        s.click();
      }}

      // Re-enable timer pills too
      var btns = document.querySelectorAll('[data-snap-timer-btn]');
      btns.forEach(function(b) {{ b.disabled = false; b.style.opacity = '1'; }});

      // Hide overlay
      var ov = document.getElementById('snap-timer-overlay');
      if (ov) ov.style.display = 'none';
    }}
  }}, 1000);
}})();
</script>
"""


_BASE_CSS = """<style>
[data-testid="stCameraInput"] video { transform: scaleX(-1) !important; }
[data-testid="stCameraInput"] img   { transform: scaleX(-1) !important; }

/* Timer overlay — sits on top of camera widget */
#snap-timer-overlay {{
    display: none;
    position: fixed;
    inset: 0;
    z-index: 99999;
    align-items: center;
    justify-content: center;
    background: rgba(0,0,0,0.55);
    backdrop-filter: blur(2px);
    flex-direction: column;
    gap: 0.5rem;
    pointer-events: none;
}}
.snap-timer-label-big {{
    color: #aaa;
    font-size: 1rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    font-family: 'DM Sans', sans-serif;
}}
#snap-countdown-num {{
    font-size: 9rem;
    font-weight: 900;
    color: #e0ff60;
    text-shadow: 0 0 60px #e0ff6099, 0 0 20px #e0ff6066;
    line-height: 1;
    font-family: 'DM Serif Display', serif;
    animation: snapPulse 1s ease-in-out infinite;
}}
@keyframes snapPulse {{
    0%   {{ transform: scale(1);    opacity: 1; }}
    50%  {{ transform: scale(1.12); opacity: 0.8; }}
    100% {{ transform: scale(1);    opacity: 1; }}
}}
.snap-timer-sublabel {{
    color: #666;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}}

/* Footer */
.snap-footer {{
    margin-top: 3rem;
    padding-top: 1.2rem;
    border-top: 1px solid #1e1e1e;
    text-align: center;
}}
.snap-footer-name {{
    font-size: 0.78rem;
    font-weight: 600;
    color: #555;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}}
.snap-footer-copy {{
    font-size: 0.68rem;
    color: #333;
    margin-top: 0.2rem;
    letter-spacing: 0.06em;
}}
</style>"""


def render():
    st.markdown(_BASE_CSS, unsafe_allow_html=True)

    # Global timer overlay — always present in DOM, shown/hidden by JS
    st.markdown("""
        <div id="snap-timer-overlay">
            <div class="snap-timer-label-big">📷 &nbsp; Get ready…</div>
            <div id="snap-countdown-num">3</div>
            <div class="snap-timer-sublabel">seconds</div>
        </div>
    """, unsafe_allow_html=True)

    max_photos = get_max_photos()
    layout     = get_layout()
    count      = photos_count()
    pending    = get_pending_photo()

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
        # Reset timer selection for next shot
        timer_key = f"timer_choice_{count}"
        st.session_state[timer_key] = 0

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
                    with st.spinner("✨ Preparing your strip…"):
                        processed_bytes = _build_processed_as_bytes()
                        if processed_bytes:
                            set_processed(processed_bytes)
                    set_stage(STAGE_PREVIEW)
                    st.rerun()
                else:
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back", type="secondary"):
            clear_photos()
            set_pending_photo(None)
            set_stage(STAGE_TEMPLATE)
            st.rerun()

        _render_footer()
        return

    # ══════════════════════════════════════════════════════════════════════
    # BRANCH B — Live camera + Timer selector
    # ══════════════════════════════════════════════════════════════════════
    st.markdown(
        f'<p class="snap-section">Take Photo {count + 1}</p>',
        unsafe_allow_html=True,
    )

    # Timer state — per shot, reset after photo taken
    timer_key     = f"timer_choice_{count}"
    timer_active  = f"timer_active_{count}"
    if timer_key not in st.session_state:
        st.session_state[timer_key]    = 0
        st.session_state[timer_active] = False

    chosen_timer = st.session_state[timer_key]
    is_active    = st.session_state.get(timer_active, False)

    # ── Timer pill selector (disabled while timer is running) ─────────────
    st.markdown("**⏱ Timer**")
    timer_options = [(0, "Off"), (3, "3s"), (6, "6s"), (10, "10s"), (15, "15s")]
    pill_cols = st.columns(5, gap="small")

    for col, (secs, label) in zip(pill_cols, timer_options):
        selected = chosen_timer == secs
        with col:
            btn_label = f"✓ {label}" if selected else label
            if st.button(
                btn_label,
                key=f"timer_pill_{count}_{secs}",
                type="primary" if selected else "secondary",
                disabled=is_active,          # locked while countdown running
                use_container_width=True,
            ):
                st.session_state[timer_key]    = secs
                st.session_state[timer_active] = False
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Camera hint
    st.markdown(
        '<div style="background:#1a1a1a;border:1px solid #333;border-radius:8px;'
        'padding:10px 14px;margin-bottom:10px;font-size:0.78rem;color:#888;">'
        '📷 &nbsp;If you see a black screen: '
        '<strong style="color:#ccc;">allow camera access in your browser</strong>, '
        'then press <strong style="color:#e0ff60;">↺ Refresh</strong>.'
        '</div>',
        unsafe_allow_html=True,
    )

    col_cam, col_refresh = st.columns([5, 1])
    with col_refresh:
        if st.button("↺ Refresh", key=f"cam_refresh_{count}", type="secondary",
                     use_container_width=True, disabled=is_active):
            st.rerun()

    # ── Start Timer button (only if timer > 0 and not yet active) ─────────
    if chosen_timer > 0 and not is_active:
        st.markdown("<br>", unsafe_allow_html=True)
        col_tl, col_tc, col_tr = st.columns([1, 2, 1])
        with col_tc:
            if st.button(
                f"▶ Start {chosen_timer}s Timer",
                key=f"start_timer_{count}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state[timer_active] = True
                st.rerun()

    # ── Camera widget ─────────────────────────────────────────────────────
    camera_img = st.camera_input(
        label="Point your camera and click Take Photo",
        key=f"cam_{count}",
    )

    # ── Inject timer JS AFTER camera widget so shutter button exists in DOM ─
    if is_active and chosen_timer > 0:
        st.markdown(_get_timer_js(chosen_timer), unsafe_allow_html=True)

    if camera_img is not None:
        # Photo captured (either manual or by timer auto-click)
        st.session_state[timer_active] = False
        st.session_state[timer_key]    = 0   # reset timer choice for next shot
        raw = camera_img.getvalue()
        err = validate_image_bytes(raw)
        if err:
            st.error(f"Could not use that image: {err}")
        else:
            mirrored = _mirror_image(raw)
            set_pending_photo(mirrored)
            st.rerun()

    _render_progress_dots(count, max_photos)

    # Navigation
    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_mid, col_next = st.columns([1, 2, 1])

    with col_back:
        if st.button("← Back", type="secondary", disabled=is_active):
            clear_photos()
            set_pending_photo(None)
            set_stage(STAGE_TEMPLATE)
            st.rerun()

    with col_next:
        if st.button(
            "Preview →",
            type="primary",
            disabled=(count < max_photos) or is_active,
            use_container_width=True,
        ):
            set_stage(STAGE_PREVIEW)
            st.rerun()

    if 0 < count < max_photos:
        remaining = max_photos - count
        st.caption(f"{remaining} more photo{'s' if remaining > 1 else ''} to go.")

    _render_footer()


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
                'background:#555;"></div>'
            )
        else:
            dots_html += '<div style="width:10px;height:10px;border-radius:50%;background:#333;"></div>'
    dots_html += "</div>"
    st.markdown(dots_html, unsafe_allow_html=True)


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