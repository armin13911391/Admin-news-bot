from bale import Message

from client import bot
from states import set_state, get_state, clear_state
from keyboards import home_inline_menu
from users import add_channel, get_user
from subscription import has_subscription, max_channels_for
from handlers.home import home_text, home_components

BTN_ADD_CHANNEL = "➕ افزودن کانال جدید"


@bot.event
async def on_message(message: Message):
    if message.from_user is None:
        return
    user_id = message.from_user.id

    if get_state(user_id)["state"] == "add_channel":
        if not has_subscription(user_id):
            clear_state(user_id)
            await message.reply(
                "اشتراک فعال ندارید. اول اشتراک رایگان یا خرید اشتراک را انتخاب کنید.",
                components=home_components(user_id),
            )
            return
        channel = (message.content or "").strip()
        if not channel.startswith("@"):
            await message.reply("آیدی کانال باید با @ شروع شود.")
            return
        limit = max_channels_for(user_id)
        if add_channel(user_id, channel, max_channels=limit):
            clear_state(user_id)
            await message.reply("کانال ثبت شد.", components=home_components(user_id))
        else:
            await message.reply("این کانال قبلاً هست یا سقف کانال پر است.")
        return

    if message.content != BTN_ADD_CHANNEL:
        return
    if not has_subscription(user_id):
        await message.reply(
            "اشتراک فعال ندارید. اول اشتراک رایگان یا خرید اشتراک را انتخاب کنید.",
            components=home_components(user_id),
        )
        return
    set_state(user_id, "add_channel", {})
    await message.reply("آیدی کانال را بفرستید.\nمثال: @mychannel")
