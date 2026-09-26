from bale import CallbackQuery, Message

from client import bot
from ui import edit_message
from users import get_user, add_user, user_exists, set_channel_status
from keyboards import (
    home_inline_menu,
    channel_inline_menu,
    channel_pick_menu,
    plans_menu,
    main_menu,
)
from states import set_state, clear_state
from subscription import (
    subscription_info,
    has_subscription,
    max_channels_for,
    activate_subscription,
    FREE_DAYS,
    is_free_user,
)


def _need_sub_text():
    return (
        "شما اشتراک فعال ندارید.\n\n"
        "اول اشتراک رایگان ۳ روزه را بگیرید یا اشتراک بخرید."
    )


def home_text(user_id):
    user = get_user(user_id) or {}
    info = subscription_info(user_id)
    channels = user.get("channels") or []
    limit = max_channels_for(user_id) or (1 if info["type"] == "free" else 3)
    if not info["active"]:
        limit = 1
        remain_line = "مدت اشتراک باقی‌مانده: ۰"
        sub_line = "اشتراک شما: ندارد"
    else:
        total = info["total"] or info["remaining"]
        remain_line = f"مدت اشتراک باقی‌مانده: {info['remaining']}/{total}"
        sub_line = f"اشتراک شما: {info['label']}"
    return (
        f"{sub_line}\n"
        f"{remain_line}\n"
        f"کانال‌های شما: {len(channels)}/{limit}\n\n"
        "یکی از دکمه‌ها را انتخاب کنید."
    )


def home_components(user_id):
    info = subscription_info(user_id)
    user = get_user(user_id) or {}
    show_free = (not info["active"]) and (not user.get("free_claimed"))
    return home_inline_menu(show_free=show_free)


async def show_home(target, user_id, reply=False):
    text = home_text(user_id)
    components = home_components(user_id)
    if reply:
        message = getattr(target, "reply", None)
        if callable(message):
            await target.reply(text, components=components)
            return
    await edit_message(target, text, components)


@bot.event
async def on_message(message: Message):
    if message.from_user is None:
        return
    text = (message.content or "").strip()
    if text in ("/start", "🏠 منوی اصلی", "🔙 بازگشت"):
        user = message.from_user
        if not user_exists(user.id):
            add_user(user.id, user.first_name, user.username)
        user_data = get_user(user.id) or {}
        await message.reply(
            home_text(user.id),
            components=home_components(user.id),
        )
        try:
            await message.reply("—", components=main_menu(is_admin=user_data.get("is_admin", False)))
        except Exception:
            pass


@bot.event
async def on_callback(callback: CallbackQuery):
    data = callback.data or ""
    user_id = callback.from_user.id
    user = get_user(user_id) or {}
    channels = user.get("channels") or []

    if data == "m_home":
        await show_home(callback, user_id)
        return

    if data == "m_settings":
        if not has_subscription(user_id):
            await edit_message(callback, _need_sub_text(), home_components(user_id))
            return
        if not channels:
            await edit_message(callback, "هنوز کانالی ثبت نشده. اول کانال اضافه کنید.", home_components(user_id))
            return
        await edit_message(callback, "کانال موردنظر را انتخاب کنید.", channel_inline_menu(channels))
        return

    if data == "m_add":
        if not has_subscription(user_id):
            await edit_message(callback, _need_sub_text(), home_components(user_id))
            return
        limit = max_channels_for(user_id)
        if len(channels) >= limit:
            await edit_message(callback, f"سقف کانال اشتراک شما {limit} تاست.", home_components(user_id))
            return
        set_state(user_id, "add_channel", {})
        await edit_message(callback, "آیدی کانال را بفرستید.\nمثال: @mychannel")
        return

    if data == "m_pause":
        if not has_subscription(user_id):
            await edit_message(callback, _need_sub_text(), home_components(user_id))
            return
        if not channels:
            await edit_message(callback, "کانالی ثبت نشده است.", home_components(user_id))
            return
        if len(channels) == 1:
            channel_id = channels[0]["id"]
            set_channel_status(user_id, channel_id, "paused")
            await edit_message(
                callback,
                f"ربات از الان متوقف شد و دیگر در کانال {channel_id} خبری نمی‌گذارد.",
                home_components(user_id),
            )
            return
        await edit_message(callback, "کدام کانال متوقف شود؟", channel_pick_menu(channels, "pause_"))
        return

    if data.startswith("pause_"):
        channel_id = data.replace("pause_", "", 1)
        set_channel_status(user_id, channel_id, "paused")
        await edit_message(
            callback,
            f"ربات از الان متوقف شد و دیگر در کانال {channel_id} خبری نمی‌گذارد.",
            home_components(user_id),
        )
        return

    if data == "m_resume":
        if not has_subscription(user_id):
            await edit_message(callback, _need_sub_text(), home_components(user_id))
            return
        if not channels:
            await edit_message(callback, "کانالی ثبت نشده است.", home_components(user_id))
            return
        if len(channels) == 1:
            channel = channels[0]
            if channel.get("status") == "active":
                await edit_message(
                    callback,
                    f"ربات از قبل در کانال {channel['id']} فعال است.",
                    home_components(user_id),
                )
                return
            set_channel_status(user_id, channel["id"], "active")
            await edit_message(
                callback,
                f"ربات از الان در کانال {channel['id']} شروع به فعالیت کرد.\nوضعیت: فعال",
                home_components(user_id),
            )
            return
        await edit_message(callback, "کدام کانال شروع شود؟", channel_pick_menu(channels, "resume_"))
        return

    if data.startswith("resume_"):
        channel_id = data.replace("resume_", "", 1)
        current = next((item for item in channels if item.get("id") == channel_id), None)
        if current and current.get("status") == "active":
            await edit_message(callback, f"ربات از قبل در کانال {channel_id} فعال است.", home_components(user_id))
            return
        set_channel_status(user_id, channel_id, "active")
        await edit_message(
            callback,
            f"ربات از الان در کانال {channel_id} شروع به فعالیت کرد.\nوضعیت: فعال",
            home_components(user_id),
        )
        return

    if data == "m_buy":
        await edit_message(callback, "تعرفه اشتراک را انتخاب کنید.", plans_menu())
        return

    if data == "m_license":
        set_state(user_id, "enter_license", {})
        await edit_message(callback, "کد لایسنس را بفرستید.")
        return

    if data == "m_free":
        if has_subscription(user_id):
            await edit_message(callback, "اشتراک فعال دارید.", home_components(user_id))
            return
        if user.get("free_claimed"):
            await edit_message(callback, "اشتراک رایگان قبلاً گرفته شده است.", home_components(user_id))
            return
        from users import update_user
        activate_subscription(user_id, "free", FREE_DAYS)
        update_user(user_id, {"free_claimed": True})
        await edit_message(
            callback,
            f"اشتراک رایگان {FREE_DAYS} روزه فعال شد.\nفقط ۱ کانال می‌توانید ثبت کنید.",
            home_components(user_id),
        )
        return

    if data == "m_support":
        await edit_message(callback, "برای پشتیبانی به ادمین پیام بدهید.", home_components(user_id))
        return
