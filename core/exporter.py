"""
Export the composed strip image to downloadable byte buffers.

Outputs:
  - High-quality JPEG (social share)
  - Print-ready PDF via ReportLab (centred on A4)

Neither function writes to disk; everything stays in memory.
"""

import io
import logging
from typing import Tuple

from PIL import Image

from config.settings import PDF_PAGE_W, PDF_PAGE_H

logger = logging.getLogger(__name__)


def export_jpg(strip: Image.Image, quality: int = 92) -> bytes:
    """
    Encode the strip as a JPEG byte string.

    quality=92 is a good balance between file size and visible detail.
    """
    buf = io.BytesIO()
    strip.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def export_pdf(strip: Image.Image) -> bytes:
    """
    Render the strip centred on an A4 page and return the PDF as bytes.
    Uses ReportLab for generation; falls back to a JPEG-embedded PDF if
    ReportLab is unavailable (rare but handled gracefully).
    """
    try:
        return _export_pdf_reportlab(strip)
    except ImportError:
        logger.warning("ReportLab not available; falling back to minimal PDF.")
        return _export_pdf_fallback(strip)


def _export_pdf_reportlab(strip: Image.Image) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.utils import ImageReader

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)

    page_w, page_h = A4  # in points

    # Scale strip to fit the page with margins (15 pt each side)
    margin = 15
    available_w = page_w - 2 * margin
    available_h = page_h - 2 * margin

    img_w, img_h = strip.size
    scale = min(available_w / img_w, available_h / img_h)

    draw_w = img_w * scale
    draw_h = img_h * scale

    # Centre on page
    x = (page_w - draw_w) / 2
    y = (page_h - draw_h) / 2

    # ReportLab reads from a PIL-compatible buffer
    img_buf = io.BytesIO()
    strip.convert("RGB").save(img_buf, format="PNG")
    img_buf.seek(0)

    c.drawImage(ImageReader(img_buf), x, y, width=draw_w, height=draw_h)
    c.save()

    return buf.getvalue()


def _export_pdf_fallback(strip: Image.Image) -> bytes:
    """
    Minimal valid PDF that embeds a JPEG image.
    Used only when ReportLab is missing.
    """
    jpeg_buf = io.BytesIO()
    strip.convert("RGB").save(jpeg_buf, format="JPEG", quality=90)
    jpeg_bytes = jpeg_buf.getvalue()

    w, h = strip.size
    # Scale to A4 points
    scale = min(PDF_PAGE_W / w, PDF_PAGE_H / h)
    dw = int(w * scale)
    dh = int(h * scale)
    ox = (PDF_PAGE_W - dw) // 2
    oy = (PDF_PAGE_H - dh) // 2

    img_len = len(jpeg_bytes)

    xobj = (
        f"3 0 obj\n<< /Type /XObject /Subtype /Image "
        f"/Width {w} /Height {h} /ColorSpace /DeviceRGB "
        f"/BitsPerComponent 8 /Filter /DCTDecode /Length {img_len} >>\n"
        f"stream\n"
    ).encode() + jpeg_bytes + b"\nendstream\nendobj\n"

    content_stream = f"q {dw} 0 0 {dh} {ox} {oy} cm /Im1 Do Q"
    content = (
        f"4 0 obj\n<< /Length {len(content_stream)} >>\nstream\n"
        f"{content_stream}\nendstream\nendobj\n"
    ).encode()

    header   = b"%PDF-1.4\n"
    catalog  = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    pages    = (
        f"2 0 obj\n<< /Type /Pages /Kids [5 0 R] /Count 1 >>\nendobj\n"
    ).encode()
    page_obj = (
        f"5 0 obj\n<< /Type /Page /Parent 2 0 R "
        f"/MediaBox [0 0 {PDF_PAGE_W} {PDF_PAGE_H}] "
        f"/Contents 4 0 R /Resources << /XObject << /Im1 3 0 R >> >> >>\nendobj\n"
    ).encode()

    body = header + catalog + pages + xobj + content + page_obj
    xref_offset = len(body)

    xref = b"xref\n0 6\n0000000000 65535 f \n"
    trailer = (
        f"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()

    return body + xref + trailer