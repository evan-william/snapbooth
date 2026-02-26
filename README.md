<div align="center">

<!-- Replace with your generated logo -->
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

SnapBooth is a browser-based virtual photobooth built with Streamlit. It captures a series of photos from the user's webcam, lets them apply filters and emoji stickers (with face detection), composes everything into a classic vertical strip, and exports it as a high-resolution JPG or a print-ready PDF.

---

## Features

- **5 frame styles** — Classic, Retro, Minimalist, Neon, Pastel
- **6 image filters** — Original, Black & White, Sepia, Retro, Cool Tone, Vivid
- **Face-tracked stickers** — Sunglasses, crown, cat ears, and more (powered by MediaPipe)
- **Strip compositor** — Photos assembled into a polished vertical strip with branding
- **Dual export** — Download as JPEG (social share) or PDF (print-ready, A4)
- **All in-memory** — No files written to disk; camera data never leaves the session

---

## Quick Start

### Run locally

```bash
# Clone
git clone https://github.com/your-username/snapbooth.git
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
[ Frame Selection ] → [ Camera Capture ] → [ Preview & Effects ] → [ Download ]
```

Each stage is an independent render function. All state transitions go through
`core/session.py`, which is the single source of truth for reads and writes to
`st.session_state`.

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
│   └── settings.py             # Constants, frame/filter/sticker configs
├── core/
│   ├── validation.py           # Magic-byte image validation
│   ├── filters.py              # OpenCV + PIL filter pipeline
│   ├── stickers.py             # MediaPipe face detection + emoji overlay
│   ├── compositor.py           # PIL strip layout engine
│   ├── exporter.py             # JPG + ReportLab PDF export
│   └── session.py              # Streamlit session state helpers
├── ui/
│   ├── styles.py               # CSS injection
│   ├── template_page.py        # Stage 1 — frame selection
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
| Image processing | OpenCV, Pillow |
| Face detection | MediaPipe |
| PDF generation | ReportLab |
| Testing | pytest, pytest-cov |

---

## Security Notes

- **Magic-byte validation** — camera images are validated by their actual bytes, not file extension, before entering any processing pipeline.
- **Size cap** — each captured frame is rejected if it exceeds 10 MB.
- **No disk writes** — all image data lives exclusively in `st.session_state` (in-memory bytes). Nothing is persisted between sessions.
- **No user data stored** — the app has no database, no authentication, and no logging of image content.

---

## Roadmap

- [ ] Background removal (via `rembg`)
- [ ] Horizontal strip layout option
- [ ] Timer countdown before each shot
- [ ] Custom text overlay on the strip header
- [ ] Streamlit Cloud deployment

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

Built with Streamlit

</div>