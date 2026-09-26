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


def send_message(channel_id, text):
    try:
        response = requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": channel_id, "text": text},
            timeout=15,
        )
        result = _parse_response(response)
        if not result["ok"]:
            print(f"❌ خطا در ارسال متن به {channel_id}: {result['code']} {result.get('description', '')[:160]}")
        return result
    except requests.RequestException as error:
        print(f"❌ خطای شبکه در ارسال متن به {channel_id}:", error)
        return {"ok": False, "code": 0, "forbidden": False}


def send_photo(channel_id, photo_url, caption):
    if not isinstance(photo_url, str) or not photo_url.startswith("http"):
        return send_message(channel_id, caption)
    try:
        response = requests.post(
            f"{BASE_URL}/sendPhoto",
            json={"chat_id": channel_id, "photo": photo_url, "caption": caption},
            timeout=15,
        )
        result = _parse_response(response)
        if result["ok"]:
            return result
        if result["forbidden"]:
            print(f"❌ ربات در {channel_id} دسترسی ارسال ندارد. این کانال موقتاً نادیده می‌شود.")
            return result
        print(f"⚠️ ارسال عکس به {channel_id} ناموفق بود ({result['code']})؛ متن فرستاده می‌شود.")
        return send_message(channel_id, caption)
    except requests.RequestException as error:
        print(f"❌ خطای شبکه در ارسال عکس به {channel_id}:", error)
        return send_message(channel_id, caption)
