from __future__ import annotations

import html

import streamlit as st

from ui.history_store import (
    delete_all,
    load_chats,
    new_id,
)

from ui.compat import stretch
from ui.theme import ACCENTS

from ui.verdict import LEVELS


def render():
    """
    Render the main sidebar controls.

    Returns:
        (mode, response_style, accent)
    """

    st.session_state.setdefault(
        "dark",
        True,
    )

    st.session_state.setdefault(
        "messages",
        [],
    )

    with st.sidebar:

        # -----------------------------------------------------
        # BRANDING
        # -----------------------------------------------------

        st.markdown(
            """
            <div class="sidebar-brand">

                <div class="sidebar-brand-logo">
                    🛡️
                </div>

                <div class="sidebar-brand-text">
                    <div class="sidebar-brand-name">
                        ScamHunter <span>AI</span>
                    </div>

                    <div class="sidebar-brand-subtitle">
                        Evidence-first investigation
                    </div>
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # -----------------------------------------------------
        # INVESTIGATION MODE
        # -----------------------------------------------------

        mode = st.selectbox(
            "INVESTIGATION MODE",
            [
                "Quick Check",
                "Deep Investigation",
            ],
            index=0,
            key="mode",
        )

        # -----------------------------------------------------
        # RESPONSE STYLE
        # -----------------------------------------------------

        style = st.selectbox(
            "RESPONSE STYLE",
            [
                "Concise",
                "Balanced",
                "Detailed",
            ],
            index=1,
            key="style",
        )

        # -----------------------------------------------------
        # RESPONSE LANGUAGE
        # -----------------------------------------------------

        st.selectbox(
            "RESPONSE LANGUAGE",
            [
                "English",
                "Urdu (اردو)",
                "Roman Urdu",
            ],
            index=0,
            key="language",
        )

        # -----------------------------------------------------
        # ACCENT
        # -----------------------------------------------------

        accent_names = list(ACCENTS.keys())

        default_accent = (
            accent_names.index("Amber")
            if "Amber" in accent_names
            else 0
        )

        accent = st.selectbox(
            "ACCENT COLOR",
            accent_names,
            index=default_accent,
            key="accent",
        )

        # -----------------------------------------------------
        # THEME
        # -----------------------------------------------------

        st.markdown(
            '<div class="sidebar-section-title">THEME</div>',
            unsafe_allow_html=True,
        )

        light_col, dark_col = st.columns(
            2,
            gap="small",
        )

        with light_col:

            if st.button(
                "☀ Light",
                **stretch(st.button),
                key="btn_light",
                type=(
                    "primary"
                    if not st.session_state.dark
                    else "secondary"
                ),
            ):

                st.session_state.dark = False
                st.rerun()

        with dark_col:

            if st.button(
                "🌙 Dark",
                **stretch(st.button),
                key="btn_dark",
                type=(
                    "primary"
                    if st.session_state.dark
                    else "secondary"
                ),
            ):

                st.session_state.dark = True
                st.rerun()

        active_theme = (
            "Dark"
            if st.session_state.dark
            else "Light"
        )

        st.markdown(
            f"""
            <div class="sidebar-active-theme">
                Active theme:
                <strong>{html.escape(active_theme)}</strong>
                <span>·</span>
                <strong>{html.escape(accent)}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return mode, style, accent


def _last_dot(chat: dict) -> str:
    """Return verdict indicator for a saved chat."""

    for message in reversed(
        chat.get("messages", [])
    ):

        verdict = (
            message.get("verdict")
            or {}
        )

        level = verdict.get("level")

        if level in LEVELS:
            return LEVELS[level]["emoji"]

    return "⚪"


def render_footer(
    uid: str,
    kb_status: str,
):
    """
    Render the lower sidebar content.

    This function is intentionally kept separate from render()
    so the chat list is refreshed after an investigation.
    """

    with st.sidebar:

        st.divider()

        # -----------------------------------------------------
        # KNOWLEDGE BASE STATUS
        # -----------------------------------------------------

        st.markdown(
            '<div class="sidebar-section-title">'
            'KNOWLEDGE BASE'
            '</div>',
            unsafe_allow_html=True,
        )

        safe_status = html.escape(
            str(kb_status)
        )

        st.markdown(
            f"""
            <div class="sidebar-status-card">
                <div class="sidebar-status-dot"></div>
                <div>{safe_status}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # -----------------------------------------------------
        # RECENT INVESTIGATIONS
        # -----------------------------------------------------

        st.markdown(
            '<div class="sidebar-section-title">'
            'RECENT INVESTIGATIONS'
            '</div>',
            unsafe_allow_html=True,
        )

        chats = load_chats(uid)

        if chats:

            current = st.session_state.get(
                "chat_id"
            )

            for chat in chats[:10]:

                chat_id = chat.get(
                    "id",
                    "",
                )

                title = chat.get(
                    "title",
                    "Chat",
                )

                title = " ".join(
                    str(title).split()
                )

                label = (
                    f"{_last_dot(chat)} "
                    f"{title}"
                )

                if chat_id == current:
                    label = "▸ " + label

                if st.button(
                    label,
                    key=f"open_{chat_id}",
                    **stretch(st.button),
                ):

                    st.session_state.load_chat_id = (
                        chat_id
                    )

                    st.rerun()

            st.caption(
                "Saved investigations are linked "
                "to this browser."
            )

        else:

            st.caption(
                "No investigations yet."
            )

        # -----------------------------------------------------
        # CLEAR CURRENT CHAT
        # -----------------------------------------------------

        if st.button(
            "Clear Chat",
            **stretch(st.button),
            key="btn_clear",
        ):

            st.session_state.messages = []
            st.session_state.chat_id = new_id()
            st.session_state.last_result = None

            st.rerun()

        # -----------------------------------------------------
        # DELETE SAVED HISTORY
        # -----------------------------------------------------

        with st.popover(
            "Delete saved history",
            **stretch(st.popover),
        ):

            st.caption(
                "This permanently deletes all saved "
                "investigations for this browser."
            )

            if st.button(
                "Yes, delete everything",
                key="btn_delete_all",
                **stretch(st.button),
            ):

                delete_all(uid)

                st.session_state.messages = []
                st.session_state.chat_id = new_id()
                st.session_state.last_result = None

                st.rerun()
