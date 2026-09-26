from bale import Message

from client import bot
from states import get_state, clear_state
from users import add_channel
from subscription import has_subscription, max_channels_for
from handlers.home import home_components


@bot.event
async def on_message(message: Message):
    if message.from_user is None:
        return
    user_id = message.from_user.id
    if get_state(user_id).get("state") != "add_channel":
        return
    if not has_subscription(user_id):
        clear_state(user_id)
        await message.reply(
            "🔒 اشتراک فعال نداری.\nاول اشتراک رایگان یا خرید اشتراک را انتخاب کن.",
            components=home_components(user_id),
        )
        return
    channel = (message.content or "").strip()
    if not channel.startswith("@"):
        await message.reply("⚠️ آیدی کانال باید با @ شروع شود.\nمثال: @mychannel")
        return
    limit = max_channels_for(user_id)
    if add_channel(user_id, channel, max_channels=limit):
        clear_state(user_id)
        await message.reply(
            f"✅ کانال {channel} ثبت شد.\nالان از تنظیمات می‌تونی دسته و فاصله ارسال را تغییر بدی.",
            components=home_components(user_id),
        )
    else:
        await message.reply(
            "⚠️ این کانال قبلاً هست یا سقف کانال پر است.",
            components=home_components(user_id),
        )
