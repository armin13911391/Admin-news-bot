from bale import Message

from client import bot
from users import user_exists, add_user
from force_join import is_force_join_enabled, is_user_joined
from force_join_keyboard import force_join_keyboard


@bot.event
async def on_message(message: Message):
    if message.content != "/start":
        return
    user = message.from_user
    if user is None:
        return
    if not user_exists(user.id):
        add_user(user.id, user.first_name, user.username)
    if is_force_join_enabled() and not is_user_joined(user.id):
        await message.reply(
            "اول در کانال اطلاع‌رسانی عضو شوید و بعد روی عضو شدم بزنید.",
            components=force_join_keyboard(),
        )
