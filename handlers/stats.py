import os

from bale import CallbackQuery

from client import bot
from ui import edit_message
from users import get_user
from keyboards import channel_pick_menu
from subscription import has_subscription
from analytics import build_report
from chart_builder import render_stats_image, render_stats_text
from sender import send_photo_file, send_message, inline_keyboard
from handlers.home import home_components


def _need_sub():
    return "🔒 اول اشتراک را فعال کن تا آمار کانال را ببینی."


async def send_channel_stats(user_id, channel_id, callback=None):
    report = build_report(channel_id)
    text = render_stats_text(report)
    path = os.path.join("data", "charts", f"{str(channel_id).replace('@', '')}.png")
    image_path = None
    try:
        image_path = render_stats_image(report, path)
    except Exception as error:
        print("stats image error:", error)
    markup = inline_keyboard([[("🏠 منوی اصلی", "m_home")]])
    if image_path:
        send_photo_file(user_id, image_path, text, markup)
    else:
        send_message(user_id, text, markup)
    if callback:
        await edit_message(callback, f"📊 آمار {channel_id} آماده شد.", home_components(user_id))


@bot.event
async def on_callback(callback: CallbackQuery):
    data = callback.data or ""
    user_id = callback.from_user.id
    user = get_user(user_id) or {}
    channels = user.get("channels") or []

    if data == "m_stats":
        if not has_subscription(user_id):
            await edit_message(callback, _need_sub(), home_components(user_id))
            return
        if not channels:
            await edit_message(callback, "📢 اول یک کانال ثبت کن.", home_components(user_id))
            return
        if len(channels) == 1:
            await send_channel_stats(user_id, channels[0]["id"], callback)
            return
        await edit_message(callback, "📊 آمار کدام کانال را می‌خوای؟", channel_pick_menu(channels, "stats_"))
        return

    if data.startswith("stats_"):
        if not has_subscription(user_id):
            await edit_message(callback, _need_sub(), home_components(user_id))
            return
        await send_channel_stats(user_id, data.replace("stats_", "", 1), callback)
