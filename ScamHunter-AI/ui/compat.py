"""Streamlit version helpers.

`use_container_width` is deprecated in newer Streamlit in favour of
`width="stretch"`. `stretch(fn)` returns whichever keyword the installed
version understands, so the same code runs on old and new releases.
"""
from __future__ import annotations

import inspect


def stretch(widget) -> dict:
    try:
        params = inspect.signature(widget).parameters
    except (TypeError, ValueError):
        return {"use_container_width": True}
    if "width" in params:
        return {"width": "stretch"}
    return {"use_container_width": True}
