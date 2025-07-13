from telebot import types
from config import ADMIN_MAIN_ID
from handlers import keyboards  # ✅ الكيبورد الموحد

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

        # فقط أرقام صحيحة بدون أي فواصل أو رموز
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

        caption = (
            f"💳 طلب شحن محفظة جديد:\n"
            f"👤 المستخدم: {msg.from_user.first_name} (@{msg.from_user.username})\n"
            f"🆔 ID: `{user_id}`\n"
            f"💵 المبلغ: {amount:,} ل.س\n"
            f"💳 الطريقة: {data['method']}\n"
            f"🔢 رقم الإشعار: `{data['ref']}`"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ قبول الشحن", callback_data=f"confirm_add_{user_id}_{amount}"),
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
            msg.chat.id,
            "📨 تم إرسال طلبك إلى الإدارة، الرجاء الانتظار.",
            reply_markup=keyboards.recharge_menu()
        )
        recharge_pending.add(user_id)

    # لم تعد هذه الدالة مطلوبة إذا كنت تستعمل معالج القبول/الرفض في ملف admin.py
    # يمكنك حذفها أو تركها معطلة (لا تؤثر)
