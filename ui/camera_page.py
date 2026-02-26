"""
Stage 2 — Camera capture with freeze-frame confirmation + auto-timer.

Fixes:
  - Mirror CSS on both video and img (no flip flash)
  - Store processed photos as JPEG bytes (no MediaFileHandler errors)
  - Pre-process on last photo before stage switch (no flicker)
  - Auto-timer: 3 / 6 / 10 / 15 seconds countdown before auto-capture
  - Professional footer with copyright
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


_CAMERA_CSS = """<style>
[data-testid="stCameraInput"] video { transform: scaleX(-1) !important; }
[data-testid="stCameraInput"] img   { transform: scaleX(-1) !important; }

/* Timer countdown display */
.snap-timer-ring {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    margin: 0.5rem 0 1rem;
}
.snap-timer-number {
    font-size: 5rem;
    font-weight: 800;
    color: #e0ff60;
    text-shadow: 0 0 30px #e0ff6088;
    line-height: 1;
    font-family: 'DM Serif Display', serif;
    animation: timerPulse 1s ease-in-out infinite;
}
@keyframes timerPulse {
    0%   { transform: scale(1);    opacity: 1; }
    50%  { transform: scale(1.08); opacity: 0.85; }
    100% { transform: scale(1);    opacity: 1; }
}
.snap-timer-label {
    text-align: center;
    color: #888;
    font-size: 0.8rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

/* Timer option pills */
.timer-pills {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
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

# Timer JS — injected once per shot, auto-submits camera after N seconds
_TIMER_JS = """
<script>
(function() {{
  var seconds = {seconds};
  var displayEl = document.getElementById('snap-countdown');
  if (!displayEl) return;

  var interval = setInterval(function() {{
    seconds--;
    if (displayEl) displayEl.textContent = seconds;
    if (seconds <= 0) {{
      clearInterval(interval);
      // Trigger the camera shutter button automatically
      var shutterBtn = document.querySelector('[data-testid="stCameraInputButton"]');
      if (shutterBtn) {{
        shutterBtn.click();
      }}
    }}
  }}, 1000);

  // Store interval ID so we can clear it if user clicks Retake
  window._snapTimerInterval = interval;
}})();
</script>
"""


def render():
    st.markdown(_CAMERA_CSS, unsafe_allow_html=True)

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

    # ── Timer selector ────────────────────────────────────────────────────
    timer_key = f"timer_choice_{count}"
    if timer_key not in st.session_state:
        st.session_state[timer_key] = 0   # 0 = off

    st.markdown("**⏱ Timer**")
    timer_cols = st.columns(5, gap="small")
    timer_options = [
        (0,  "Off"),
        (3,  "3s"),
        (6,  "6s"),
        (10, "10s"),
        (15, "15s"),
    ]
    for col, (secs, label) in zip(timer_cols, timer_options):
        selected = st.session_state[timer_key] == secs
        with col:
            if st.button(
                f"{'✓ ' if selected else ''}{label}",
                key=f"timer_btn_{count}_{secs}",
                type="primary" if selected else "secondary",
                use_container_width=True,
            ):
                st.session_state[timer_key] = secs
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Camera permission tip ─────────────────────────────────────────────
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
                     use_container_width=True):
            st.rerun()

    # ── Active timer countdown display ────────────────────────────────────
    chosen_timer = st.session_state.get(timer_key, 0)
    active_timer_key = f"timer_started_{count}"

    if chosen_timer > 0:
        # Show START button if timer not yet running
        if not st.session_state.get(active_timer_key, False):
            st.markdown("<br>", unsafe_allow_html=True)
            col_tl, col_tc, col_tr = st.columns([1, 2, 1])
            with col_tc:
                if st.button(
                    f"▶ Start {chosen_timer}s Timer",
                    key=f"start_timer_{count}",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state[active_timer_key] = True
                    st.rerun()
        else:
            # Timer is running — show big animated countdown
            st.markdown(
                f'<div class="snap-timer-label">Get ready…</div>'
                f'<div class="snap-timer-ring">'
                f'<div class="snap-timer-number" id="snap-countdown">{chosen_timer}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            # Inject JS countdown that auto-clicks the shutter
            st.markdown(
                _TIMER_JS.format(seconds=chosen_timer),
                unsafe_allow_html=True,
            )

    # ── Camera widget ─────────────────────────────────────────────────────
    camera_img = st.camera_input(
        label="Point your camera and click Take Photo",
        key=f"cam_{count}",
    )

    if camera_img is not None:
        # Reset timer state for this shot
        st.session_state[active_timer_key] = False
        raw = camera_img.getvalue()
        err = validate_image_bytes(raw)
        if err:
            st.error(f"Could not use that image: {err}")
        else:
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
        if st.button(
            "Preview →",
            type="primary",
            disabled=(count < max_photos),
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
                'background:#555;animation:pulse 1s infinite;"></div>'
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