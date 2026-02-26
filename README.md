<div align="center">

<img src="assets/snapbooth-logo.jpg" alt="SnapBooth" width="600"/>

# SnapBooth

**A virtual photobooth — take shots, apply effects, download your strip**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-pytest-6d28d9?style=for-the-badge)](tests/)

</div>

---

## What is SnapBooth?

SnapBooth is a browser-based virtual photobooth built with Streamlit. It captures a series of photos from the user's webcam, lets them choose a layout, apply filters and stickers, composes everything into a polished strip or grid, and exports it as a high-resolution JPG or print-ready PDF.

---

## Features

- **9 layout options** — 1×3, 1×4, 1×6 strips and 2×2, 2×3, 2×4, 3×2, 3×3, 4×2 grids
- **23 frame styles** — Classic, Film Strip, Pink Heart, Garden, Blue Sky, Vintage, Neon Glow, Lavender, Midnight, Cherry Blossom, Gold Foil, Ocean Wave, Galaxy, Rose Gold, Pastel Dream, Autumn, Mint Fresh, Black & Gold, Sakura, Electric Blue, Warm Sunset, Ice Crystal, Purple Rain
- **23 image filters** — Original, B&W, Sepia, Retro, Cool, Vivid, Soft, Warm, Fade, ✨ Golden, 🌸 Cherry, 🎞️ Film, ⚡ Neon, 🍬 Pastel, 🌑 Moody, 💿 Y2K, 🍵 Matcha, 💜 Lavender, 🔍 Crisp, 🌆 Dusk, 🗼 Tokyo, 🩷 Candy, 📷 Polaroid
- **12 sticker themes** — Hearts, Stars, Flowers, Sparkles, Clovers, Butterflies, Diamonds, Bows, Crowns, Bubbles, Confetti (all PIL-drawn, no dependencies)
- **HD strip compositor** — renders at 2× resolution internally, downscaled for crisp anti-aliased output
- **Dual export** — download as JPEG (quality 96, 4:4:4 chroma) or PDF (ReportLab A4, print-ready)
- **Mobile block** — detects phones/tablets via JS and shows a polished "use desktop" overlay
- **All in-memory** — no files written to disk; camera data never leaves the session

---

## Quick Start

### Run locally

```bash
# Clone
git clone https://github.com/evan-william/snapbooth.git
cd snapbooth

# Install dependencies (Python 3.10+ recommended)
pip install -r requirements.txt

# Launch
streamlit run app.py
```

### Run tests

```bash
chmod +x run_tests.sh
./run_tests.sh              # standard run
./run_tests.sh --coverage   # with HTML coverage report
```

---

## How It Works

The app is a four-stage flow managed by Streamlit's session state:

```
[ Layout + Frame ] → [ Camera Capture ] → [ Preview & Effects ] → [ Download ]
```

Each stage is an independent render function. All state transitions go through
`core/session.py`, which is the single source of truth for reads and writes to
`st.session_state`.

**Key technical detail — processed photos are stored as JPEG bytes, not PIL Image objects.**
PIL objects expire from Streamlit's in-memory media cache between reruns, causing
`MediaFileHandler` errors and visible flickering. Bytes survive `st.session_state`
serialization perfectly and are converted back to PIL only when compositing is needed.

---

## Project Structure

```
snapbooth/
├── app.py                      # Entry point & stage router
├── requirements.txt
├── run_tests.sh                # Test runner script
├── .streamlit/
│   └── config.toml             # Theme configuration
├── config/
│   └── settings.py             # Constants, layout/frame/filter/sticker configs
├── core/
│   ├── validation.py           # Magic-byte image validation
│   ├── filters.py              # PIL + NumPy filter pipeline (23 filters)
│   ├── stickers.py             # PIL-drawn themed sticker overlays
│   ├── compositor.py           # HD strip/grid layout engine (2× render)
│   ├── exporter.py             # JPG + ReportLab PDF export
│   └── session.py              # Streamlit session state helpers
├── ui/
│   ├── styles.py               # Global CSS injection
│   ├── mobile_block.py         # JS mobile detection + block overlay
│   ├── template_page.py        # Stage 1 — layout + frame selection
│   ├── camera_page.py          # Stage 2 — sequential photo capture
│   ├── preview_page.py         # Stage 3 — filter/sticker/frame tuning
│   └── download_page.py        # Stage 4 — strip display + download
└── tests/
    ├── test_validation.py
    ├── test_filters.py
    ├── test_compositor.py
    └── test_exporter.py
```

---

## Technical Stack

| Layer | Technology |
|---|---|
| UI framework | Streamlit |
| Image processing | Pillow, NumPy |
| PDF generation | ReportLab |
| Testing | pytest, pytest-cov |

---

## Layouts

| Key | Name | Photos |
|---|---|---|
| `1x3` | 1 × 3 Strip | 3 |
| `1x4` | 1 × 4 Strip | 4 |
| `1x6` | 1 × 6 Strip | 6 |
| `2x2` | 2 × 2 Grid | 4 |
| `2x3` | 2 × 3 Grid | 6 |
| `2x4` | 2 × 4 Grid | 8 |
| `3x2` | 3 × 2 Grid | 6 |
| `3x3` | 3 × 3 Grid | 9 |
| `4x2` | 4 × 2 Grid | 8 |

---

## Security Notes

- **Magic-byte validation** — camera images are validated by their actual bytes, not file extension, before entering any processing pipeline.
- **Size cap** — each captured frame is rejected if it exceeds 10 MB.
- **No disk writes** — all image data lives exclusively in `st.session_state` (in-memory bytes). Nothing is persisted between sessions.
- **No user data stored** — the app has no database, no authentication, and no logging of image content.

---

## Roadmap

- [x] Multiple layout options (strips + grids)
- [x] Aesthetic filter collection (23 filters)
- [x] Themed sticker overlays (12 themes, PIL-drawn)
- [x] HD output (2× internal render + sharpness pass)
- [x] Mobile block screen
- [ ] Timer countdown before each shot
- [ ] Custom text overlay on strip header/footer

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push and open a Pull Request

Please ensure `run_tests.sh` passes before submitting.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ by **Evan William** · © 2026 SnapBooth · All rights reserved

</div>