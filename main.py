import time

from rss_reader import get_news
from storage import load_users, is_news_sent, mark_news_sent
from users import update_last_send
from sender import send_message, send_photo
from utils import add_emoji
from category_engine import detect_category_advanced, news_matches_channel
from ai import translate_news


CHECK_INTERVAL = 20


def get_all_channels():
    users = load_users()
    channels = []

    for user_id, user_data in users.items():
        if not isinstance(user_data, dict):
            continue

        for channel in user_data.get("channels", []):
            if not isinstance(channel, dict):
                continue
            if channel.get("status") != "active":
                continue
            if not channel.get("id"):
                continue

            channel = dict(channel)
            channel["user_id"] = user_id
            channel.setdefault("interval", 10)
            channel.setdefault("last_send", 0)
            channel.setdefault("categories", ["همه"])
            channel.setdefault("send_image", True)
            channel.setdefault("show_emoji", True)
            channel.setdefault("footer_text", "")
            channels.append(channel)

    return channels


def build_message(news, channel):
    title = (news.get("title") or "").strip()

    try:
        title = translate_news(title)
    except Exception:
        pass

    if channel.get("show_emoji", True):
        try:
            title = add_emoji(title)
        except Exception:
            pass

    message = title
    footer = (channel.get("footer_text") or "").strip()
    if footer:
        message += f"\n\n{footer}"

    return message


def can_send(channel):
    now = time.time()
    last_send = float(channel.get("last_send") or 0)
    interval_minutes = int(channel.get("interval") or 10)
    interval_seconds = max(interval_minutes, 1) * 60
    return (now - last_send) >= interval_seconds


def send_news_to_channel(channel, news):
    message = build_message(news, channel)
    image = news.get("image")

    if channel.get("send_image", True) and image:
        return send_photo(channel["id"], image, message)

    return send_message(channel["id"], message)


def run():
    print("🚀 AutoNewsBot MultiChannel Started...")

    while True:
        try:
            news_list = get_news()
            channels = get_all_channels()

            if not news_list:
                print("⚠️ خبری پیدا نشد")
                time.sleep(CHECK_INTERVAL)
                continue

            if not channels:
                print("ℹ️ کانال فعالی برای ارسال نیست")
                time.sleep(CHECK_INTERVAL)
                continue

            for channel in channels:
                if not can_send(channel):
                    continue

                sent_this_round = False

                for latest_news in news_list:
                    link = (latest_news.get("link") or "").strip()
                    title = (latest_news.get("title") or "").strip()

                    if not link or not title:
                        continue

                    if is_news_sent(channel["id"], link):
                        continue

                    categories = channel.get("categories") or ["همه"]
                    if not news_matches_channel(
                        title,
                        latest_news.get("source", ""),
                        categories,
                    ):
                        continue

                    try:
                        result = send_news_to_channel(channel, latest_news)
                    except Exception as send_error:
                        print("❌ خطا در ارسال:", send_error)
                        result = False

                    if not result:
                        print(f"❌ ارسال ناموفق بود: {channel['id']}")
                        continue

                    mark_news_sent(channel["id"], link)
                    update_last_send(
                        channel["user_id"],
                        channel["id"],
                        time.time(),
                    )

                    category_name = detect_category_advanced(
                        title,
                        latest_news.get("source", ""),
                    )
                    next_send = channel.get("interval", 10)
                    print(
                        f"✅ ارسال شد به {channel['id']}\n"
                        f"📂 دسته خبر: {category_name}\n"
                        f"🏷 فیلتر کانال: {', '.join(categories)}\n"
                        f"⏰ ارسال بعدی: {next_send} دقیقه دیگر"
                    )
                    sent_this_round = True
                    break

            time.sleep(CHECK_INTERVAL)

        except Exception as error:
            print("❌ خطای اصلی:", error)
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()
