import json
import requests

from config import BOT_TOKEN


BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"


def _parse_response(response):
    if response is None:
        return {"ok": False, "code": 0, "forbidden": False, "message_id": None}
    code = response.status_code
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    api_ok = bool(payload.get("ok")) and code == 200
    description = str(payload.get("description", ""))
    forbidden = code == 403 or "permission_denied" in description or "Forbidden" in description
    result_body = payload.get("result")
    message_id = None
    if isinstance(result_body, dict):
        message_id = result_body.get("message_id")
    return {
        "ok": api_ok,
        "code": code,
        "forbidden": forbidden,
        "description": description,
        "message_id": message_id,
    }


def inline_keyboard(rows):
    return {
        "inline_keyboard": [
            [{"text": text, "callback_data": data} for text, data in row]
            for row in rows
        ]
    }


def send_message(channel_id, text, reply_markup=None, reply_to_message_id=None):
    try:
        payload = {"chat_id": channel_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        response = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=8)
        return _parse_response(response)
    except requests.RequestException:
        return {"ok": False, "code": 0, "forbidden": False, "message_id": None}


def send_photo(channel_id, photo, caption, reply_markup=None):
    payload = {"chat_id": channel_id, "photo": photo, "caption": caption or ""}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if not isinstance(photo, str) or not photo:
        return send_message(channel_id, caption, reply_markup)
    try:
        response = requests.post(f"{BASE_URL}/sendPhoto", json=payload, timeout=12)
        result = _parse_response(response)
        if result["ok"] or result["forbidden"]:
            return result
        return send_message(channel_id, caption, reply_markup)
    except requests.RequestException:
        return send_message(channel_id, caption, reply_markup)


def send_comment(channel_id, text, reply_to_message_id):
    if not text or not reply_to_message_id:
        return {"ok": False}
    return send_message(channel_id, text, reply_to_message_id=reply_to_message_id)


def send_photo_file(chat_id, path, caption="", reply_markup=None):
    try:
        with open(path, "rb") as file:
            data = {"chat_id": str(chat_id), "caption": caption or ""}
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
            response = requests.post(f"{BASE_URL}/sendPhoto", data=data, files={"photo": file}, timeout=20)
        result = _parse_response(response)
        if not result["ok"]:
            return send_message(chat_id, caption, reply_markup)
        return result
    except Exception:
        return send_message(chat_id, caption, reply_markup)


def copy_message(to_chat, from_chat, message_id):
    try:
        response = requests.post(
            f"{BASE_URL}/copyMessage",
            json={"chat_id": to_chat, "from_chat_id": from_chat, "message_id": message_id},
            timeout=8,
        )
        return _parse_response(response)
    except requests.RequestException:
        return {"ok": False}


def forward_message(to_chat, from_chat, message_id):
    try:
        response = requests.post(
            f"{BASE_URL}/forwardMessage",
            json={"chat_id": to_chat, "from_chat_id": from_chat, "message_id": message_id},
            timeout=8,
        )
        return _parse_response(response)
    except requests.RequestException:
        return {"ok": False}


def deliver_broadcast(to_chat, from_chat, message_id, text="", forwarded=False):
    if forwarded and message_id:
        result = forward_message(to_chat, from_chat, message_id)
        if result.get("ok"):
            return result
        result = copy_message(to_chat, from_chat, message_id)
        if result.get("ok"):
            return result
    if text:
        return send_message(to_chat, text)
    if message_id:
        return copy_message(to_chat, from_chat, message_id)
    return {"ok": False}


def deliver_as_is(to_chat, from_chat, message_id, fallback_text=""):
    return deliver_broadcast(to_chat, from_chat, message_id, fallback_text, forwarded=True)
