"""
Centralised session-state helpers.
All reads/writes to st.session_state go through these functions.
"""

import streamlit as st
from typing import Any, List, Optional

from config.settings import (
    KEY_STAGE, KEY_FRAME, KEY_LAYOUT, KEY_PHOTOS, KEY_FILTER,
    KEY_STICKER, KEY_PROCESSED, KEY_STRIP_BYTES, KEY_STRIP_PDF,
    STAGE_TEMPLATE, DEFAULT_LAYOUT, LAYOUT_MAP, LayoutConfig,
)

KEY_PENDING_PHOTO = "pending_photo"


def init_session():
    defaults = {
        KEY_STAGE:          STAGE_TEMPLATE,
        KEY_FRAME:          "classic",
        KEY_LAYOUT:         DEFAULT_LAYOUT,
        KEY_PHOTOS:         [],
        KEY_FILTER:         "none",
        KEY_STICKER:        "none",
        KEY_PROCESSED:      [],
        KEY_STRIP_BYTES:    None,
        KEY_STRIP_PDF:      None,
        KEY_PENDING_PHOTO:  None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# --- Stage ------------------------------------------------------------------

def get_stage() -> str:
    return st.session_state[KEY_STAGE]

def set_stage(stage: str):
    st.session_state[KEY_STAGE] = stage


# --- Frame ------------------------------------------------------------------

def get_frame() -> str:
    return st.session_state[KEY_FRAME]

def set_frame(key: str):
    st.session_state[KEY_FRAME] = key


# --- Layout -----------------------------------------------------------------

def get_layout_key() -> str:
    return st.session_state.get(KEY_LAYOUT, DEFAULT_LAYOUT)

def get_layout() -> LayoutConfig:
    key = get_layout_key()
    return LAYOUT_MAP.get(key, LAYOUT_MAP[DEFAULT_LAYOUT])

def set_layout(key: str):
    if st.session_state.get(KEY_LAYOUT) != key:
        st.session_state[KEY_LAYOUT] = key
        st.session_state[KEY_PHOTOS] = []   # reset photos on layout change
        st.session_state[KEY_PROCESSED] = []

def get_max_photos() -> int:
    return get_layout().total

def get_min_photos() -> int:
    return get_layout().min_photos


# --- Photos -----------------------------------------------------------------

def get_photos() -> List[bytes]:
    return st.session_state[KEY_PHOTOS]

def add_photo(data: bytes):
    if len(st.session_state[KEY_PHOTOS]) < get_max_photos():
        st.session_state[KEY_PHOTOS].append(data)

def photos_remaining() -> int:
    return get_max_photos() - len(st.session_state[KEY_PHOTOS])

def photos_count() -> int:
    return len(st.session_state[KEY_PHOTOS])

def clear_photos():
    st.session_state[KEY_PHOTOS] = []


# --- Pending photo ----------------------------------------------------------

def get_pending_photo() -> Optional[bytes]:
    return st.session_state.get(KEY_PENDING_PHOTO)

def set_pending_photo(data: Optional[bytes]):
    st.session_state[KEY_PENDING_PHOTO] = data


# --- Filter / sticker -------------------------------------------------------

def get_filter() -> str:
    return st.session_state[KEY_FILTER]

def set_filter(key: str):
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
    for key in [KEY_PHOTOS, KEY_PROCESSED]:
        st.session_state[key] = []
    for key in [KEY_STRIP_BYTES, KEY_STRIP_PDF, KEY_PENDING_PHOTO]:
        st.session_state[key] = None
    st.session_state[KEY_STAGE]   = STAGE_TEMPLATE
    st.session_state[KEY_FRAME]   = "classic"
    st.session_state[KEY_LAYOUT]  = DEFAULT_LAYOUT
    st.session_state[KEY_FILTER]  = "none"
    st.session_state[KEY_STICKER] = "none"