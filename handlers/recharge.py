from telebot import types
from config import ADMIN_MAIN_ID
from handlers import keyboards  # ✅ الكيبورد الموحد
from services.wallet_service import register_user_if_not_exist, add_balance

recharge_requests = {}
recharge_pending = set()

# ✅ عرض قائمة طرق الشحن
def start_recharge_menu(bot, message, history=None):
    if history:
        history.setdefault(message.from_user.id, []).append("recharge_menu")
    bot.send_message(
        message.chat.id,
        "💳 اختر طريقة شحن محفظتك:",
        reply_markup=keyboards.recharge_menu()
    )

def register(bot, history):

    @bot.message_handler(func=lambda msg: msg.text == "💳 شحن محفظتي")
    def open_recharge(msg):
        start_recharge_menu(bot, msg, history)

    @bot.message_handler(func=lambda msg: msg.text in [
        "📲 سيرياتيل كاش", "📲 أم تي إن كاش", "📲 شام كاش", "💳 Payeer"
    ])
    def request_invoice(msg):
        user_id = msg.from_user.id
        if user_id in recharge_pending:
            bot.send_message(msg.chat.id, "⚠️ لديك طلب قيد المعالجة. الرجاء الانتظار.")
            return

        method = msg.text.replace("📲 ", "").replace("💳 ", "")
        recharge_requests[user_id] = {"method": method}
        bot.send_message(
            msg.chat.id,
            "📸 أرسل صورة إشعار الدفع (سكرين أو لقطة شاشة):",
            reply_markup=keyboards.recharge_menu()
        )

    @bot.message_handler(content_types=["photo"])
    def handle_photo(msg):
        user_id = msg.from_user.id
        if user_id not in recharge_requests or "photo" in recharge_requests[user_id]:
            return
        photo_id = msg.photo[-1].file_id
        recharge_requests[user_id]["photo"] = photo_id
        bot.send_message(msg.chat.id, "🔢 أرسل رقم الإشعار / رمز العملية:", reply_markup=keyboards.recharge_menu())

    @bot.message_handler(
        func=lambda msg: msg.from_user.id in recharge_requests 
        and "photo" in recharge_requests[msg.from_user.id] 
        and "ref" not in recharge_requests[msg.from_user.id]
    )
    def get_reference(msg):
        recharge_requests[msg.from_user.id]["ref"] = msg.text
        bot.send_message(msg.chat.id, "💰 أرسل مبلغ الشحن (بالليرة السورية):", reply_markup=keyboards.recharge_menu())

    @bot.message_handler(
        func=lambda msg: msg.from_user.id in recharge_requests 
        and "ref" in recharge_requests[msg.from_user.id] 
        and "amount" not in recharge_requests[msg.from_user.id]
    )
    def get_amount(msg):
        user_id = msg.from_user.id
        amount_text = msg.text.strip()

        # فقط أرقام صحيحة بدون أي رموز أو نقاط
        if not amount_text.isdigit():
            bot.send_message(
                msg.chat.id,
                "❌ يرجى إدخال مبلغ صحيح بالأرقام فقط (بدون أي فواصل أو نقاط أو رموز).",
                reply_markup=keyboards.recharge_menu()
            )
            return

        amount = int(amount_text)
        data = recharge_requests[user_id]
        data["amount"] = amount

        # رسالة التأكيد للمستخدم قبل الإرسال للإدارة
        confirm_text = (
            f"🔎 **يرجى التأكد من معلومات الشحن:**\n"
            f"💳 الطريقة: {data['method']}\n"
            f"🔢 رقم الإشعار: `{data['ref']}`\n"
            f"💵 المبلغ: {amount:,} ل.س\n\n"
            f"هل أنت متأكد من إرسال هذا الطلب للإدارة؟"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ تأكيد", callback_data="user_confirm_recharge"),
            types.InlineKeyboardButton("🔁 تعديل", callback_data="user_edit_recharge"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="user_cancel_recharge")
        )

        bot.send_message(
            msg.chat.id,
            confirm_text,
            parse_mode="Markdown",
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data in ["user_confirm_recharge", "user_edit_recharge", "user_cancel_recharge"])
    def handle_user_recharge_action(call):
        user_id = call.from_user.id

        if call.data == "user_confirm_recharge":
            data = recharge_requests.get(user_id)
            if not data:
                bot.answer_callback_query(call.id, "لا يوجد طلب قيد المعالجة.")
                return

            # ⬅️ هنا ضمان تسجيل المستخدم قبل إرسال الطلب للأدمن
            name = call.from_user.full_name if hasattr(call.from_user, 'full_name') else call.from_user.first_name
            register_user_if_not_exist(user_id, name)

            caption = (
                f"💳 طلب شحن محفظة جديد:\n"
                f"👤 المستخدم: {call.from_user.first_name} (@{call.from_user.username})\n"
                f"🆔 ID: `{user_id}`\n"
                f"💵 المبلغ: {data['amount']:,} ل.س\n"
                f"💳 الطريقة: {data['method']}\n"
                f"🔢 رقم الإشعار: `{data['ref']}`"
            )

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ قبول الشحن", callback_data=f"confirm_add_{user_id}_{data['amount']}"),
                types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_add_{user_id}")
            )

            bot.send_photo(
                ADMIN_MAIN_ID,
                photo=data["photo"],
                caption=caption,
                parse_mode="Markdown",
                reply_markup=markup
            )
            bot.send_message(
                user_id,
                "📨 تم إرسال طلبك إلى الإدارة، الرجاء الانتظار.",
                reply_markup=keyboards.recharge_menu()
            )
            recharge_pending.add(user_id)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        elif call.data == "user_edit_recharge":
            # إعادة الخطوات للمستخدم لإدخال رقم الإشعار والمبلغ من جديد
            if user_id in recharge_requests:
                recharge_requests[user_id].pop("amount", None)
                recharge_requests[user_id].pop("ref", None)
                bot.send_message(
                    user_id,
                    "🔄 يمكنك الآن إدخال رقم الإشعار / رمز العملية من جديد:",
                    reply_markup=keyboards.recharge_menu()
                )
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        elif call.data == "user_cancel_recharge":
            recharge_requests.pop(user_id, None)
            recharge_pending.discard(user_id)
            bot.send_message(
                user_id,
                "❌ تم إلغاء الطلب، يمكنك البدء من جديد.",
                reply_markup=keyboards.recharge_menu()
            )
            # العودة لاختيار طريقة الشحن من جديد
            fake_msg = types.SimpleNamespace()  # اختصار لإرسال start_recharge_menu من دون رسالة حقيقية
            fake_msg.from_user = types.SimpleNamespace()
            fake_msg.from_user.id = user_id
            fake_msg.chat = types.SimpleNamespace()
            fake_msg.chat.id = user_id
            start_recharge_menu(bot, fake_msg, history)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    # ===================== هاندلر الأدمن لقبول/رفض الشحن =====================

    @bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_add_") or c.data.startswith("reject_add_"))
    def admin_recharge_action(c):
        # تأكد أن الرسالة في دردشة الأدمن الرئيسية
        if c.message.chat.id != ADMIN_MAIN_ID:
            bot.answer_callback_query(c.id, "غير مصرح.")
            return

        try:
            if c.data.startswith("confirm_add_"):
                _, _, uid_str, amt_str = c.data.split("_", 3)
                uid, amt = int(uid_str), int(amt_str)
                add_balance(uid, amt, "شحن محفظة")

                bot.edit_message_caption(
                    chat_id=c.message.chat.id,
                    message_id=c.message.message_id,
                    caption=f"{c.message.caption}

❌ *تم الرفض*",

                    parse_mode="Markdown",
                )
                bot.send_message(uid, "⚠️ تم رفض طلب شحن محفظتك.")
                bot.answer_callback_query(c.id, "❌ تم الرفض.")

            recharge_pending.discard(uid)
            recharge_requests.pop(uid, None)
        except Exception as e:
            bot.answer_callback_query(c.id, "خطأ غير متوقع.")
            raise
