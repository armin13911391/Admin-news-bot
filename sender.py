import json
import requests

from config import BOT_TOKEN


BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"


def _parse_response(response):
    if response is None:
        return {"ok": False, "code": 0, "forbidden": False}
    code = response.status_code
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    api_ok = bool(payload.get("ok")) and code == 200
    description = str(payload.get("description", ""))
    forbidden = code == 403 or "permission_denied" in description or "Forbidden" in description
    return {"ok": api_ok, "code": code, "forbidden": forbidden, "description": description}


def inline_keyboard(rows):
    return {
        "inline_keyboard": [
            [{"text": text, "callback_data": data} for text, data in row]
            for row in rows
        ]
    }


def send_message(channel_id, text, reply_markup=None):
    try:
        payload = {"chat_id": channel_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        response = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=15)
        result = _parse_response(response)
        if not result["ok"]:
            print(f"❌ خطا در ارسال متن به {channel_id}: {result['code']} {result.get('description', '')[:160]}")
        return result
    except requests.RequestException as error:
        print(f"❌ خطای شبکه در ارسال متن به {channel_id}:", error)
        return {"ok": False, "code": 0, "forbidden": False}


def send_photo(channel_id, photo, caption, reply_markup=None):
    payload = {"chat_id": channel_id, "photo": photo, "caption": caption or ""}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if not isinstance(photo, str) or not photo:
        return send_message(channel_id, caption, reply_markup)
    try:
        response = requests.post(f"{BASE_URL}/sendPhoto", json=payload, timeout=20)
        result = _parse_response(response)
        if result["ok"]:
            return result
        if result["forbidden"]:
            print(f"❌ ربات در {channel_id} دسترسی ارسال ندارد.")
            return result
        print(f"⚠️ ارسال عکس به {channel_id} ناموفق بود ({result['code']})")
        return send_message(channel_id, caption, reply_markup)
    except requests.RequestException as error:
        print(f"❌ خطای شبکه در ارسال عکس به {channel_id}:", error)
        return send_message(channel_id, caption, reply_markup)


def send_photo_file(chat_id, path, caption="", reply_markup=None):
    try:
        with open(path, "rb") as file:
            data = {"chat_id": str(chat_id), "caption": caption or ""}
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
            response = requests.post(
                f"{BASE_URL}/sendPhoto",
                data=data,
                files={"photo": file},
                timeout=30,
            )
        result = _parse_response(response)
        if not result["ok"]:
            print("send_photo_file failed:", result)
            return send_message(chat_id, caption, reply_markup)
        return result
    except Exception as error:
        print("send_photo_file error:", error)
        return send_message(chat_id, caption, reply_markup)


def copy_message(to_chat, from_chat, message_id):
    try:
        response = requests.post(
            f"{BASE_URL}/copyMessage",
            json={
                "chat_id": to_chat,
                "from_chat_id": from_chat,
                "message_id": message_id,
            },
            timeout=15,
        )
        return _parse_response(response)
    except requests.RequestException:
        return {"ok": False}
