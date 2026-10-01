"""Saved chat history, one JSON file per browser id (no accounts needed)."""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "data" / "chat_history"
MAX_CHATS = 50
_UID = re.compile(r"^[a-f0-9]{32}$")


def new_id() -> str:
    return uuid.uuid4().hex


def valid_uid(uid) -> bool:
    return bool(uid) and isinstance(uid, str) and bool(_UID.match(uid))


def _path(uid: str) -> Path:
    return BASE / f"{uid}.json"


def load_chats(uid: str) -> list:
    if not valid_uid(uid):
        return []
    try:
        data = json.loads(_path(uid).read_text(encoding="utf-8"))
        chats = data.get("chats", [])
    except (FileNotFoundError, ValueError, OSError, AttributeError):
        return []
    return sorted(chats, key=lambda c: c.get("updated", 0), reverse=True)


def _write(uid: str, chats: list) -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    tmp = _path(uid).with_suffix(".tmp")
    tmp.write_text(json.dumps({"chats": chats}, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, _path(uid))


def _title(messages: list) -> str:
    for m in messages:
        if m.get("role") == "user":
            text = " ".join(str(m.get("content", "")).split())
            return (text[:45] + "…") if len(text) > 45 else (text or "New chat")
    return "New chat"


def save_chat(uid: str, chat_id: str, messages: list) -> None:
    if not valid_uid(uid) or not messages:
        return
    chats = load_chats(uid)
    now = time.time()
    for chat in chats:
        if chat.get("id") == chat_id:
            chat["messages"] = messages
            chat["updated"] = now
            break
    else:
        chats.append(
            {
                "id": chat_id,
                "title": _title(messages),
                "created": now,
                "updated": now,
                "messages": messages,
            }
        )
    chats.sort(key=lambda c: c.get("updated", 0), reverse=True)
    try:
        _write(uid, chats[:MAX_CHATS])
    except OSError:
        pass  # history is best-effort; never break the app


def delete_all(uid: str) -> None:
    if valid_uid(uid):
        try:
            _path(uid).unlink(missing_ok=True)
        except OSError:
            pass
