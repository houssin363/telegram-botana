from telebot import types
from config import ADMIN_MAIN_ID
from handlers import keyboards
from services.wallet_service import register_user_if_not_exist, add_balance

recharge_requests: dict[int, dict] = {}
recharge_pending: set[int] = set()

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def start_recharge_menu(bot, message, history=None):
    """إظهار قائمة طرق الشحن للمستخدم."""
    if history is not None:
        history.setdefault(message.from_user.id, []).append("recharge_menu")
    bot.send_message(
        message.chat.id,
        "💳 اختر طريقة شحن محفظتك:",
        reply_markup=keyboards.recharge_menu(),
    )


# ---------------------------------------------------------------------------
# REGISTRATION FUNCTION (to be imported by main.py)
# ---------------------------------------------------------------------------

def register(bot, history):
    """تسجيل جميع هاندلرز الشحن (مستخدم وأدمن)."""

    # ============================= المستخدم ============================= #

    @bot.message_handler(func=lambda m: m.text == "💳 شحن محفظتي")
    def open_recharge(m):
        start_recharge_menu(bot, m, history)

    @bot.message_handler(
        func=lambda m: m.text in [
            "📲 سيرياتيل كاش",
            "📲 أم تي إن كاش",
            "📲 شام كاش",
            "💳 Payeer",
        ]
    )
    def choose_method(m):
        uid = m.from_user.id
        if uid in recharge_pending:
            bot.send_message(uid, "⚠️ لديك طلب قيد المعالجة. الرجاء الانتظار.")
            return
        method = m.text.replace("📲 ", "").replace("💳 ", "")
        recharge_requests[uid] = {"method": method}
        bot.send_message(uid, "📸 أرسل صورة إشعار الدفع (Screenshot)")

    @bot.message_handler(content_types=["photo"])
    def handle_photo(m):
        uid = m.from_user.id
        if uid not in recharge_requests or "photo" in recharge_requests[uid]:
            return
        recharge_requests[uid]["photo"] = m.photo[-1].file_id
        bot.send_message(uid, "🔢 أرسل رقم الإشعار / رمز العملية:")

    @bot.message_handler(
        func=lambda m: m.from_user.id in recharge_requests
        and "photo" in recharge_requests[m.from_user.id]
        and "ref" not in recharge_requests[m.from_user.id]
    )
    def handle_ref(m):
        recharge_requests[m.from_user.id]["ref"] = m.text.strip()
        bot.send_message(m.from_user.id, "💰 أرسل مبلغ الشحن (بالأرقام):")

    @bot.message_handler(
        func=lambda m: m.from_user.id in recharge_requests
        and "ref" in recharge_requests[m.from_user.id]
        and "amount" not in recharge_requests[m.from_user.id]
    )
    def handle_amount(m):
        uid = m.from_user.id
        if not m.text.isdigit():
            bot.send_message(uid, "❌ أدخل أرقامًا فقط.")
            return
        amt = int(m.text)
        recharge_requests[uid]["amount"] = amt

        data = recharge_requests[uid]
        confirm_txt = (
            f"🔎 **تأكيد معلومات الشحن**\n"
            f"💳 الطريقة: {data['method']}\n"
            f"🔢 الإشعار: `{data['ref']}`\n"
            f"💵 المبلغ: {amt:,} ل.س\n\n"
            "هل تريد إرسال الطلب للإدارة؟"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ تأكيد", callback_data="user_confirm"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="user_cancel"),
        )
        bot.send_message(uid, confirm_txt, parse_mode="Markdown", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data in {"user_confirm", "user_cancel"})
    def user_confirm_cancel(c):
        uid = c.from_user.id
        if c.data == "user_cancel":
            recharge_requests.pop(uid, None)
            bot.answer_callback_query(c.id, "تم الإلغاء.")
            return
        # confirm branch
        data = recharge_requests.get(uid)
        if not data:
            bot.answer_callback_query(c.id, "لا يوجد طلب.")
            return

        register_user_if_not_exist(uid, c.from_user.full_name or c.from_user.first_name)

        username_part = f" (@{c.from_user.username})" if c.from_user.username else ""
        caption = (
            "💳 طلب شحن محفظة جديد:\n"
            f"👤 المستخدم: {c.from_user.first_name}{username_part}\n"
            f"🆔 ID: `{uid}`\n"
            f"💵 المبلغ: {data['amount']:,} ل.س\n"
            f"💳 الطريقة: {data['method']}\n"
            f"🔢 رقم الإشعار: `{data['ref']}`"
        )
        admin_kb = types.InlineKeyboardMarkup()
        admin_kb.add(
            types.InlineKeyboardButton(
                "✅ قبول الشحن", callback_data=f"admin_confirm_{uid}_{data['amount']}"
            ),
            types.InlineKeyboardButton(
                "❌ رفض", callback_data=f"admin_reject_{uid}"
            ),
        )
        bot.send_photo(
            ADMIN_MAIN_ID,
            photo=data["photo"],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=admin_kb,
        )
        bot.send_message(uid, "📨 أُرسل طلبك، انتظر الموافقة.")
        recharge_pending.add(uid)
        bot.answer_callback_query(c.id)

    # ============================= الأدمن ============================= #

    @bot.callback_query_handler(func=lambda c: c.data.startswith("admin_"))
    def admin_actions(c):
        try:
            if c.message.chat.id != ADMIN_MAIN_ID:
                bot.answer_callback_query(c.id, "غير مصرح.")
                return

            if c.data.startswith("admin_confirm_"):
                _, _, uid, amt = c.data.split("_", 3)
                uid, amt = int(uid), int(amt)
                add_balance(uid, amt, "شحن محفظة")
                bot.edit_message_caption(
                    chat_id=c.message.chat.id,
                    message_id=c.message.message_id,
                    caption=f"{c.message.caption}\n\n✅ *تم الشحن*",
                    parse_mode="Markdown",
                )
                bot.send_message(uid, f"🎉 تم شحن محفظتك بـ {amt:,} ل.س!")
            else:  # reject
                _, _, uid = c.data.split("_", 2)
                uid = int(uid)
                bot.edit_message_caption(
                    chat_id=c.message.chat.id,
                    message_id=c.message.message_id,
                    caption=f"{c.message.caption}\n\n❌ *تم الرفض*",
                    parse_mode="Markdown",
                )
                bot.send_message(uid, "⚠️ تم رفض طلب الشحن.")

            recharge_pending.discard(uid)
            recharge_requests.pop(uid, None)
            bot.answer_callback_query(c.id)
        except Exception:
            bot.answer_callback_query(c.id, "خطأ غير متوقع.")
            raise
