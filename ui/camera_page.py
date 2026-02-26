"""
Stage 2 — Camera capture with freeze-frame confirmation.

Root-cause fixes:
  FLASH BUG:
    Also apply scaleX(-1) to [data-testid="stCameraInput"] img so the
    captured still matches the mirrored video — no jarring flip visible.

  GLITCH ON LAST PHOTO + MediaFileHandler errors:
    Previously stored PIL Image objects in session state. PIL objects expire
    from Streamlit's in-memory media cache between reruns → MediaFileHandler
    "Missing file" errors + flickering as preview_page tries to re-render stale refs.
    Fix: serialize processed photos to JPEG bytes immediately. Bytes are plain
    Python data that survive session state perfectly across all reruns.
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
    """Membalik gambar secara horizontal agar sesuai dengan preview selfie."""
    try:
        img = Image.open(io.BytesIO(data))
        flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
        buf = io.BytesIO()
        flipped.save(buf, format="JPEG", quality=97, optimize=True)
        return buf.getvalue()
    except Exception:
        return data

def _build_processed_now() -> list:
    """Proses semua foto dengan filter/stiker sebelum pindah stage."""
    filter_key = get_filter()
    sticker_cfg = STICKER_MAP.get(get_sticker())
    result = []
    for raw in get_photos():
        img = safe_open_image(raw)
        if img is None: continue
        img = apply_filter(img, filter_key)
        if sticker_cfg and sticker_cfg.key != "none":
            img = apply_sticker(img, sticker_cfg)
        result.append(img)
    return result

_CAMERA_CSS = """<style>
[data-testid="stCameraInput"] video { transform: scaleX(-1) !important; }
[data-testid="stCameraInput"] img { transform: scaleX(-1) !important; }
</style>"""

def render():
    st.markdown(_CAMERA_CSS, unsafe_allow_html=True)

    max_photos = get_max_photos()
    layout = get_layout()
    count = photos_count()
    pending = get_pending_photo()

    # 1. Navigasi Otomatis (Hanya jika benar-benar sudah selesai)
    if count >= max_photos and pending is None:
        set_stage(STAGE_PREVIEW)
        st.rerun()
        return

    st.markdown(
        f'<div class="photo-counter">Shot {count + 1} of {max_photos} '
        f'&nbsp;·&nbsp; {layout.cols}×{layout.rows} layout</div>',
        unsafe_allow_html=True,
    )

    # 2. Logika Konfirmasi Foto
    if pending is not None:
        st.markdown('<p class="snap-section">Use this photo?</p>', unsafe_allow_html=True)
        col_m = st.columns([1, 3, 1])[1]
        with col_m:
            st.image(pending, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_ret, col_use = st.columns(2, gap="small")

        with col_ret:
            if st.button("↩ Retake", use_container_width=True):
                set_pending_photo(None)
                st.rerun()

        with col_use:
            if st.button("✓ Use this photo", type="primary", use_container_width=True):
                add_photo(pending)
                set_pending_photo(None)
                
                # Cek jika ini foto terakhir
                if photos_count() >= max_photos:
                    with st.spinner("✨ Finishing your strip..."):
                        processed = _build_processed_now()
                        set_processed(processed)
                    set_stage(STAGE_PREVIEW)
                st.rerun()
        return

    # 3. Logika Live Camera
    st.markdown(f'<p class="snap-section">Take Photo {count + 1}</p>', unsafe_allow_html=True)
    
    # Tooltip helper agar user tidak bingung jika kamera mati
    st.info("📷 Klik icon kamera di address bar jika layar hitam, lalu Refresh.")

    # FIX: Jangan render camera_input jika sedang memproses pending (sudah dihandle return di atas)
    camera_img = st.camera_input(
        label="Point your camera and click Take Photo",
        key=f"cam_widget_{count}", # Key unik per shot
    )

    if camera_img is not None:
        raw = camera_img.getvalue()
        if not validate_image_bytes(raw):
            mirrored = _mirror_image(raw)
            set_pending_photo(mirrored)
            # PENTING: Segera hapus value widget agar tidak loop saat rerun
            st.rerun()

    _render_progress_dots(count, max_photos)

    # Navigasi Back
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Frames", type="secondary"):
        clear_photos()
        set_pending_photo(None)
        set_stage(STAGE_TEMPLATE)
        st.rerun()

def _render_progress_dots(done: int, total: int):
    if total > 12:
        st.progress(done / total)
        return
    dots_html = '<div style="display:flex;gap:6px;justify-content:center;margin-top:1rem;">'
    for i in range(total):
        color = "#e0ff60" if i < done else ("#555" if i == done else "#333")
        dots_html += f'<div style="width:10px;height:10px;border-radius:50%;background:{color};"></div>'
    dots_html += "</div>"
    st.markdown(dots_html, unsafe_allow_html=True)