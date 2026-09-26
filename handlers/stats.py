import os

from bale import CallbackQuery

from client import bot
from ui import edit_message
from users import get_user
from keyboards import channel_pick_menu, home_inline_menu
from subscription import has_subscription
from analytics import build_report
from chart_builder import render_stats_image
from sender import send_photo_file, inline_keyboard
from handlers.home import home_components


def _need_sub():
    return "🔒 اول اشتراک را فعال کن تا آمار کانال را ببینی."


async def send_channel_stats(user_id, channel_id, callback=None):
    try:
        report = build_report(channel_id)
        path = os.path.join("data", "charts", f"{str(channel_id).replace('@', '')}.png")
        render_stats_image(report, path)
    except Exception as error:
        print("stats error:", error)
        text = "⚠️ ساخت نمودار موفق نبود. matplotlib را روی سرور نصب کن."
        if callback:
            await edit_message(callback, text, home_components(user_id))
        return
    clock = report["now"].strftime("%H:%M")
    caption = (
        f"📊 آمار {channel_id}\n"
        f"⏰ از ۰۰:۰۰ تا {clock}\n\n"
        f"👥 کاربرای امروز: {report['users_today']}\n"
        f"📅 ۷ روز گذشته: {report['users_7']}\n"
        f"📆 ۳۰ روز گذشته: {report['users_30']}\n"
        f"📢 کل اعضا: {report['members']}\n"
        f"💬 پیام‌های امروز ربات: {report['messages_today']}"
    )
    send_photo_file(
        user_id,
        path,
        caption,
        inline_keyboard([[("🏠 منوی اصلی", "m_home")]]),
    )
    if callback:
        await edit_message(callback, f"📊 نمودار {channel_id} ارسال شد.", home_components(user_id))


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
