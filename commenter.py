import time

import requests

from config import BOT_TOKEN
from users import _patch_channel

BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"
_LINKED = {}


def _call(method, payload):
    try:
        response = requests.post(f"{BASE_URL}/{method}", json=payload, timeout=10)
        try:
            data = response.json()
        except ValueError:
            data = {}
        result = data.get("result")
        message_id = None
        if isinstance(result, dict):
            message_id = result.get("message_id") or result.get("id")
        elif isinstance(result, int):
            message_id = result
        return {
            "ok": bool(data.get("ok")) and response.status_code == 200,
            "code": response.status_code,
            "description": str(data.get("description") or ""),
            "message_id": int(message_id) if message_id else None,
            "raw": data,
        }
    except Exception as error:
        return {"ok": False, "description": str(error), "message_id": None}


def extract_message_id(result):
    if not isinstance(result, dict):
        return None
    mid = result.get("message_id")
    if mid:
        try:
            return int(mid)
        except Exception:
            return None
    raw = result.get("raw") or {}
    body = raw.get("result") if isinstance(raw, dict) else None
    if isinstance(body, dict):
        mid = body.get("message_id") or body.get("id")
        try:
            return int(mid) if mid else None
        except Exception:
            return None
    return None


def get_linked_chat(channel_id):
    if channel_id in _LINKED and time.time() - _LINKED[channel_id][0] < 300:
        return _LINKED[channel_id][1]
    data = _call("getChat", {"chat_id": channel_id})
    result = (data.get("raw") or {}).get("result") or {}
    linked = result.get("linked_chat_id") or result.get("linked_chat")
    if isinstance(linked, dict):
        linked = linked.get("id")
    _LINKED[channel_id] = (time.time(), linked)
    return linked


def _try_send(chat_id, text, reply_to=None, extra=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_to:
        payload["reply_to_message_id"] = int(reply_to)
    if extra:
        payload.update(extra)
    result = _call("sendMessage", payload)
    if result.get("ok"):
        return result
    form = {"chat_id": str(chat_id), "text": text}
    if reply_to:
        form["reply_to_message_id"] = str(int(reply_to))
    try:
        response = requests.post(f"{BASE_URL}/sendMessage", data=form, timeout=10)
        data = response.json()
        if data.get("ok"):
            body = data.get("result") or {}
            mid = body.get("message_id") if isinstance(body, dict) else body
            return {"ok": True, "message_id": mid, "description": ""}
        return {"ok": False, "description": data.get("description") or ""}
    except Exception as error:
        return {"ok": False, "description": str(error)}


def post_comment(channel_id, text, reply_to=None):
    text = (text or "").strip()
    if not text:
        return {"ok": False, "description": "empty"}
    last_error = ""
    if reply_to:
        result = _try_send(channel_id, text, reply_to)
        if result.get("ok"):
            print(f"💬 دیدگاه روی پست {channel_id} نوشته شد")
            return result
        last_error = result.get("description") or ""
        linked = get_linked_chat(channel_id)
        if linked:
            result = _try_send(linked, text, reply_to)
            if result.get("ok"):
                print(f"💬 دیدگاه در گروه لینک {channel_id} نوشته شد")
                return result
            result = _try_send(
                linked,
                text,
                extra={"reply_parameters": {"message_id": int(reply_to), "chat_id": channel_id}},
            )
            if result.get("ok"):
                print(f"💬 دیدگاه با reply_parameters نوشته شد")
                return result
            last_error = result.get("description") or last_error
    result = _try_send(channel_id, text, reply_to)
    if result.get("ok"):
        print(f"💬 کامنت بدون ریپلای روی {channel_id} رفت")
        return result
    print(f"⚠️ کامنت {channel_id} نرفت: {result.get('description') or last_error}")
    return result


def remember_post(user_id, channel_id, message_id):
    if user_id and channel_id and message_id:
        try:
            _patch_channel(user_id, channel_id, {"last_post_id": int(message_id)})
        except Exception:
            pass
