import time

from bale import CallbackQuery, Message

from client import bot
from ui import edit_message
from states import set_state, get_state, clear_state
from keyboards import plans_menu, pay_method_menu, card_pay_menu, admin_pay_menu, home_inline_menu
from subscription import (
    PLANS,
    CARD_NUMBER,
    ADMIN_IDS,
    load_payments,
    save_payments,
    create_license,
    redeem_license,
)
from sender import send_message, send_photo
from handlers.home import home_components, home_text


@bot.event
async def on_callback(callback: CallbackQuery):
    data = callback.data or ""
    user_id = callback.from_user.id

    if data.startswith("plan_"):
        plan_id = data.replace("plan_", "", 1)
        plan = PLANS.get(plan_id)
        if not plan:
            return
        set_state(user_id, "choose_pay", {"plan_id": plan_id})
        await edit_message(
            callback,
            f"اشتراک {plan['title']}\nمبلغ: {plan['price']:,} تومن\n\nروش پرداخت را انتخاب کنید.".replace(",", "٬"),
            pay_method_menu(),
        )
        return

    if data == "pay_card":
        state = get_state(user_id)
        plan = PLANS.get((state.get("data") or {}).get("plan_id"), {})
        set_state(user_id, "card_info", state.get("data") or {})
        await edit_message(
            callback,
            f"مبلغ {plan.get('price', 0):,} تومن برای اشتراک {plan.get('title', '')} را به شماره کارت زیر واریز کنید.\n\n{CARD_NUMBER}\n\nبعد روی واریز کردم بزنید.".replace(",", "٬"),
            card_pay_menu(),
        )
        return

    if data == "pay_gift":
        state = get_state(user_id)
        set_state(user_id, "gift_code", state.get("data") or {})
        await edit_message(callback, "کد یا پیام پاکت هدیه را بفرستید.")
        return

    if data == "pay_paid":
        state = get_state(user_id)
        set_state(user_id, "wait_receipt", state.get("data") or {})
        await edit_message(callback, "عکس واریزی را بفرستید. اگر توضیحی دارید زیر عکس بنویسید.")
        return

    if data.startswith("adm_ok_"):
        if callback.from_user.id not in ADMIN_IDS:
            return
        req_id = data.replace("adm_ok_", "", 1)
        payments = load_payments()
        item = payments.get(req_id)
        if not item or item.get("status") != "pending":
            await edit_message(callback, "این درخواست قبلاً بررسی شده است.")
            return
        days = int(item.get("days") or 0)
        code = create_license(days)
        item["status"] = "approved"
        item["license"] = code
        payments[req_id] = item
        save_payments(payments)
        send_message(
            item["user_id"],
            "کد لایسنس شما:\n\n"
            f"{code}\n\n"
            "این کد را نزد کسی ندهید. در منو روی ورود کد لایسنس بزنید و کد را بفرستید.",
        )
        await edit_message(callback, f"تایید شد.\nلایسنس: {code}")
        return

    if data.startswith("adm_no_"):
        if callback.from_user.id not in ADMIN_IDS:
            return
        req_id = data.replace("adm_no_", "", 1)
        payments = load_payments()
        item = payments.get(req_id)
        if item:
            item["status"] = "rejected"
            payments[req_id] = item
            save_payments(payments)
            send_message(item["user_id"], "واریز شما تایید نشد. اگر اشتباهی هست به پشتیبانی پیام بدهید.")
        await edit_message(callback, "درخواست رد شد.")
        return

    if data.startswith("adm_msg_"):
        if callback.from_user.id not in ADMIN_IDS:
            return
        req_id = data.replace("adm_msg_", "", 1)
        set_state(callback.from_user.id, "admin_msg", {"req_id": req_id})
        await edit_message(callback, "پیام را بفرستید تا برای کاربر ارسال شود.")
        return


@bot.event
async def on_message(message: Message):
    if message.from_user is None:
        return
    user_id = message.from_user.id
    state = get_state(user_id)
    name = state.get("state")
    text = (message.content or "").strip()

    if name == "enter_license":
        ok, result = redeem_license(user_id, text)
        clear_state(user_id)
        if ok:
            await message.reply(
                f"لایسنس فعال شد.\nاشتراک {result} روزه برای شما فعال شد.",
                components=home_inline_menu(show_free=False),
            )
        else:
            await message.reply(str(result), components=home_inline_menu(True))
        return

    if name == "admin_msg" and user_id in ADMIN_IDS:
        req_id = (state.get("data") or {}).get("req_id")
        payments = load_payments()
        item = payments.get(req_id) or {}
        if item.get("user_id"):
            send_message(item["user_id"], text)
        clear_state(user_id)
        await message.reply("پیام برای کاربر ارسال شد.")
        return

    if name in ("wait_receipt", "gift_code"):
        plan_id = (state.get("data") or {}).get("plan_id")
        plan = PLANS.get(plan_id) or {}
        req_id = str(int(time.time())) + str(user_id)
        payments = load_payments()
        payments[req_id] = {
            "user_id": user_id,
            "plan_id": plan_id,
            "days": plan.get("days"),
            "price": plan.get("price"),
            "title": plan.get("title"),
            "note": text,
            "status": "pending",
        }
        save_payments(payments)
        photo = None
        for attr in ("photos", "photo", "document"):
            value = getattr(message, attr, None)
            if value:
                photo = value
                break
        admin_text = (
            f"درخواست واریز\n"
            f"کاربر: {user_id}\n"
            f"اشتراک: {plan.get('title')}\n"
            f"مبلغ: {plan.get('price')}\n"
            f"توضیح: {text}"
        )
        for admin_id in ADMIN_IDS:
            send_message(admin_id, admin_text)
            try:
                if isinstance(photo, str) and photo.startswith("http"):
                    send_photo(admin_id, photo, admin_text)
            except Exception:
                pass
            try:
                await bot.send_message(admin_id, admin_text, components=admin_pay_menu(req_id))
            except Exception:
                send_message(admin_id, admin_text)
        clear_state(user_id)
        await message.reply(
            "عکس واریزی برای ادمین ارسال شد.\nحداکثر چند ساعت صبر کنید تا بررسی شود.",
            components=home_inline_menu(True),
        )
        return
