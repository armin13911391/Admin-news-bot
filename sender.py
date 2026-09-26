import requests

from config import BOT_TOKEN


BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"


def _is_ok(response):
    if response is None:
        return False

    if response.status_code != 200:
        return False

    try:
        payload = response.json()
    except ValueError:
        return False

    return bool(payload.get("ok"))


def send_message(channel_id, text):
    try:
        response = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": channel_id,
                "text": text,
            },
            timeout=15,
        )

        if not _is_ok(response):
            print(
                f"❌ خطا در ارسال متن به {channel_id}: "
                f"{response.status_code} {response.text[:200]}"
            )
            return False

        return True

    except requests.RequestException as error:
        print(f"❌ خطای شبکه در ارسال متن به {channel_id}:", error)
        return False


def send_photo(channel_id, photo_url, caption):
    if not isinstance(photo_url, str) or not photo_url.startswith("http"):
        return send_message(channel_id, caption)

    try:
        response = requests.post(
            f"{BASE_URL}/sendPhoto",
            json={
                "chat_id": channel_id,
                "photo": photo_url,
                "caption": caption,
            },
            timeout=15,
        )

        if _is_ok(response):
            return True

        print(
            f"⚠️ ارسال عکس به {channel_id} ناموفق بود "
            f"({response.status_code})؛ متن فرستاده می‌شود."
        )
        return send_message(channel_id, caption)

    except requests.RequestException as error:
        print(f"❌ خطای شبکه در ارسال عکس به {channel_id}:", error)
        return send_message(channel_id, caption)
