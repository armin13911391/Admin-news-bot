from bale import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from client import bot
from ui import edit_message
from users import get_user, _patch_channel
from keyboards import channel_pick_menu
from states import set_state, get_state, clear_state
from subscription import has_subscription
from handlers.home import home_components, back_only

PRESETS = [
    "به کامنت‌های یکدیگر احترام بگذارید",
    "ری‌اکشن یادت نره",
    "کامنت یادت نره",
]


def _need_sub():
    return "🔒 اول اشتراک را فعال کن."


def find_channel(user, channel_id):
    for item in user.get("channels") or []:
        if item.get("id") == channel_id:
            return item
    return None


def comment_text_view(channel):
    on = bool(channel.get("comment_on"))
    text = (channel.get("comment_text") or "").strip() or "ندارد"
    status = "🟢 روشن" if on else "🔴 خاموش"
    return (
        f"💬 کامنت {channel.get('id')}\n"
        "━━━━━━━━━━━━━━\n"
        f"وضعیت: {status}\n"
        f"متن: {text}\n\n"
        "اگر کامنت کانال باز باشد، بعد از هر خبر همین متن زیر پست نوشته می‌شود."
    )


def comment_menu(channel):
    on = bool(channel.get("comment_on"))
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🔴 خاموش کردن" if on else "🟢 روشن کردن", callback_data=f"cmt_toggle_{channel['id']}"),
        row=1,
    )
    keyboard.add(InlineKeyboardButton("✏️ متن دلخواه", callback_data=f"cmt_custom_{channel['id']}"), row=2)
    keyboard.add(InlineKeyboardButton("💬 احترام بگذارید", callback_data="cmt_pre_0"), row=3)
    keyboard.add(InlineKeyboardButton("👍 ری‌اکشن یادت نره", callback_data="cmt_pre_1"), row=4)
    keyboard.add(InlineKeyboardButton("📝 کامنت یادت نره", callback_data="cmt_pre_2"), row=5)
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="m_comment"), row=6)
    return keyboard


async def show_comment_panel(callback, user_id, channel_id):
    user = get_user(user_id) or {}
    channel = find_channel(user, channel_id)
    if not channel:
        await edit_message(callback, "کانال پیدا نشد.", home_components(user_id))
        return
    set_state(user_id, "comment_edit", {"channel_id": channel_id})
    await edit_message(callback, comment_text_view(channel), comment_menu(channel))


@bot.event
async def on_callback(callback: CallbackQuery):
    data = callback.data or ""
    user_id = callback.from_user.id
    user = get_user(user_id) or {}
    channels = user.get("channels") or []

    if data == "m_comment":
        clear_state(user_id)
        if not has_subscription(user_id):
            await edit_message(callback, _need_sub(), home_components(user_id))
            return
        if not channels:
            await edit_message(callback, "📢 اول یک کانال ثبت کن.", home_components(user_id))
            return
        if len(channels) == 1:
            await show_comment_panel(callback, user_id, channels[0]["id"])
            return
        await edit_message(callback, "💬 کامنت کدام کانال را می‌خوای؟", channel_pick_menu(channels, "cmtch_"))
        return

    if data.startswith("cmtch_"):
        await show_comment_panel(callback, user_id, data.replace("cmtch_", "", 1))
        return

    if data.startswith("cmt_toggle_"):
        channel_id = data.replace("cmt_toggle_", "", 1)
        channel = find_channel(user, channel_id)
        if not channel:
            return
        new_value = not bool(channel.get("comment_on"))
        if new_value and not (channel.get("comment_text") or "").strip():
            await edit_message(callback, "⚠️ اول یک متن برای کامنت انتخاب کن.", comment_menu(channel))
            return
        _patch_channel(user_id, channel_id, {"comment_on": new_value})
        user = get_user(user_id) or {}
        channel = find_channel(user, channel_id)
        await edit_message(callback, comment_text_view(channel), comment_menu(channel))
        return

    if data.startswith("cmt_custom_"):
        channel_id = data.replace("cmt_custom_", "", 1)
        set_state(user_id, "comment_text", {"channel_id": channel_id})
        await edit_message(callback, "✏️ متن کامنت را بفرست.\nمثال: ری‌اکشن یادت نره", back_only())
        return

    if data.startswith("cmt_pre_"):
        index = int(data.replace("cmt_pre_", ""))
        state = get_state(user_id)
        channel_id = (state.get("data") or {}).get("channel_id")
        if not channel_id and channels:
            channel_id = channels[0]["id"]
        if index < 0 or index >= len(PRESETS) or not channel_id:
            return
        _patch_channel(user_id, channel_id, {"comment_text": PRESETS[index], "comment_on": True})
        user = get_user(user_id) or {}
        channel = find_channel(user, channel_id)
        await edit_message(callback, "✅ متن ذخیره شد و کامنت روشن شد.\n\n" + comment_text_view(channel), comment_menu(channel))
        return


@bot.event
async def on_message(message: Message):
    if message.from_user is None:
        return
    user_id = message.from_user.id
    state = get_state(user_id)
    if state.get("state") != "comment_text":
        return
    channel_id = (state.get("data") or {}).get("channel_id")
    text = (message.content or "").strip()
    if not channel_id or not text:
        return
    _patch_channel(user_id, channel_id, {"comment_text": text[:400], "comment_on": True})
    clear_state(user_id)
    user = get_user(user_id) or {}
    channel = find_channel(user, channel_id) or {"id": channel_id, "comment_on": True, "comment_text": text}
    await message.reply("✅ متن کامنت ذخیره شد و فعال شد.\n\n" + comment_text_view(channel), components=comment_menu(channel))
