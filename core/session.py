"""
Centralised session-state helpers.

All reads/writes to st.session_state go through these functions,
which keeps the rest of the UI code clean and prevents key-name typos.
"""

import streamlit as st
from typing import Any, List, Optional
from PIL.Image import Image

from config.settings import (
    KEY_STAGE, KEY_FRAME, KEY_PHOTOS, KEY_FILTER,
    KEY_STICKER, KEY_PROCESSED, KEY_STRIP_BYTES, KEY_STRIP_PDF,
    STAGE_TEMPLATE, MAX_PHOTOS,
)


def init_session():
    """Ensure all required session keys exist with safe defaults."""
    defaults = {
        KEY_STAGE:       STAGE_TEMPLATE,
        KEY_FRAME:       "classic",
        KEY_PHOTOS:      [],
        KEY_FILTER:      "none",
        KEY_STICKER:     "none",
        KEY_PROCESSED:   [],
        KEY_STRIP_BYTES: None,
        KEY_STRIP_PDF:   None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# --- Stage navigation -------------------------------------------------------

def get_stage() -> str:
    return st.session_state[KEY_STAGE]

def set_stage(stage: str):
    st.session_state[KEY_STAGE] = stage


# --- Frame ------------------------------------------------------------------

def get_frame() -> str:
    return st.session_state[KEY_FRAME]

def set_frame(key: str):
    st.session_state[KEY_FRAME] = key


# --- Photos -----------------------------------------------------------------

def get_photos() -> List[bytes]:
    return st.session_state[KEY_PHOTOS]

def add_photo(data: bytes):
    photos = st.session_state[KEY_PHOTOS]
    if len(photos) < MAX_PHOTOS:
        photos.append(data)

def photos_remaining() -> int:
    return MAX_PHOTOS - len(st.session_state[KEY_PHOTOS])

def photos_count() -> int:
    return len(st.session_state[KEY_PHOTOS])

def clear_photos():
    st.session_state[KEY_PHOTOS] = []


# --- Filter / sticker -------------------------------------------------------

def get_filter() -> str:
    return st.session_state[KEY_FILTER]

def set_filter(key: str):
    # Changing filter invalidates cached processed images
    if st.session_state[KEY_FILTER] != key:
        st.session_state[KEY_FILTER] = key
        st.session_state[KEY_PROCESSED] = []

def get_sticker() -> str:
    return st.session_state[KEY_STICKER]

def set_sticker(key: str):
    if st.session_state[KEY_STICKER] != key:
        st.session_state[KEY_STICKER] = key
        st.session_state[KEY_PROCESSED] = []


# --- Processed photos + strip -----------------------------------------------

def get_processed() -> List[Any]:
    return st.session_state[KEY_PROCESSED]

def set_processed(images: List[Any]):
    st.session_state[KEY_PROCESSED] = images

def get_strip_bytes() -> Optional[bytes]:
    return st.session_state[KEY_STRIP_BYTES]

def set_strip_bytes(data: bytes):
    st.session_state[KEY_STRIP_BYTES] = data

def get_strip_pdf() -> Optional[bytes]:
    return st.session_state[KEY_STRIP_PDF]

def set_strip_pdf(data: bytes):
    st.session_state[KEY_STRIP_PDF] = data


# --- Full reset -------------------------------------------------------------

def reset_session():
    """Clear everything and go back to the start."""
    for key in [KEY_PHOTOS, KEY_PROCESSED, KEY_STRIP_BYTES, KEY_STRIP_PDF]:
        st.session_state[key] = [] if key in (KEY_PHOTOS, KEY_PROCESSED) else None
    st.session_state[KEY_STAGE]   = STAGE_TEMPLATE
    st.session_state[KEY_FRAME]   = "classic"
    st.session_state[KEY_FILTER]  = "none"
    st.session_state[KEY_STICKER] = "none"