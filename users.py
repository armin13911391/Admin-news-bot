import json
import os
from datetime import datetime

from storage import users_path


def load_users():
    path = users_path()
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as file:
            json.dump({}, file, ensure_ascii=False, indent=4)
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            users = json.load(file)
            return users if isinstance(users, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_users(users):
    path = users_path()
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=4)


def user_exists(user_id):
    return str(user_id) in load_users()


def add_user(user_id, first_name, username=None):
    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {
            "first_name": first_name,
            "username": username,
            "join_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "wallet": 0,
            "channels": [],
            "subscription": {
                "type": None,
                "expire": None,
            },
            "invited_by": None,
            "invite_count": 0,
            "is_admin": False,
        }
        save_users(users)


def get_user(user_id):
    return load_users().get(str(user_id))


def update_user(user_id, data):
    users = load_users()
    user_id = str(user_id)
    if user_id in users:
        users[user_id].update(data)
        save_users(users)


def add_channel(user_id, channel):
    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return False

    channels = users[user_id].setdefault("channels", [])
    if len(channels) >= 3:
        return False

    for item in channels:
        if item.get("id") == channel:
            return False

    channels.append({
        "id": channel,
        "status": "active",
        "send_image": True,
        "show_emoji": True,
        "footer_text": "",
        "interval": 10,
        "last_send": 0,
        "categories": ["همه"],
    })
    save_users(users)
    return True


def delete_channel(user_id, channel_id):
    users = load_users()
    user_id = str(user_id)
    if user_id not in users:
        return False

    channels = users[user_id].get("channels", [])
    for channel in list(channels):
        if channel.get("id") == channel_id:
            channels.remove(channel)
            save_users(users)
            return True
    return False


def _toggle_flag(user_id, channel_id, key, default=True):
    users = load_users()
    user_id = str(user_id)
    if user_id not in users:
        return None

    for channel in users[user_id].get("channels", []):
        if channel.get("id") == channel_id:
            channel[key] = not channel.get(key, default)
            save_users(users)
            return channel[key]
    return None


def toggle_channel_image(user_id, channel_id):
    return _toggle_flag(user_id, channel_id, "send_image", True)


def toggle_channel_emoji(user_id, channel_id):
    return _toggle_flag(user_id, channel_id, "show_emoji", True)


def update_footer_text(user_id, channel_id, text):
    users = load_users()
    user_id = str(user_id)
    if user_id not in users:
        return False

    for channel in users[user_id].get("channels", []):
        if channel.get("id") == channel_id:
            channel["footer_text"] = text
            save_users(users)
            return True
    return False


def update_categories(user_id, channel_id, categories):
    users = load_users()
    user_id = str(user_id)
    if user_id not in users:
        return False

    if not categories:
        categories = ["همه"]

    for channel in users[user_id].get("channels", []):
        if channel.get("id") == channel_id:
            channel["categories"] = categories
            save_users(users)
            return True
    return False


def update_send_time(user_id, channel_id, interval):
    users = load_users()
    user_id = str(user_id)
    if user_id not in users:
        return False

    for channel in users[user_id].get("channels", []):
        if channel.get("id") == channel_id:
            channel["interval"] = int(interval)
            save_users(users)
            return True
    return False


def update_last_send(user_id, channel_id, last_send):
    users = load_users()
    user_id = str(user_id)
    if user_id not in users:
        return False

    for channel in users[user_id].get("channels", []):
        if channel.get("id") == channel_id:
            channel["last_send"] = last_send
            save_users(users)
            return True
    return False
