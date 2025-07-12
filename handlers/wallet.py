from telebot import types
from config import BOT_NAME
from handlers import keyboards

# قاعدة بيانات مؤقتة
users_wallet = {}

# ✅ تسجيل مستخدم جديد
def register_user_if_not_exist(user_id):
    if user_id not in users_wallet:
        users_wallet[user_id] = {
            "balance": 0,
            "purchases": [],
            "transfers": []
        }

# ✅ تحديث الرصيد
def update_balance(user_id, amount):
    register_user_if_not_exist(user_id)
    users_wallet[user_id]["balance"] += amount

# ✅ عرض المحفظة
def show_wallet(bot, message, history=None):
    user_id = message.from_user.id
    register_user_if_not_exist(user_id)
    balance = users_wallet[user_id]["balance"]

    if history is not None:
        history.setdefault(user_id, []).append("wallet")

    balance_str = str(balance)  # حذف الفواصل

    text = f"🧾 رقم حسابك: `{user_id}`\n💰 رصيدك الحالي: {balance_str} ل.س"
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=keyboards.wallet_menu())

# ✅ عرض المشتريات
def show_purchases(bot, message, history=None):
    user_id = message.from_user.id
    register_user_if_not_exist(user_id)

    if history is not None:
        history.setdefault(user_id, []).append("wallet")

    purchases = users_wallet[user_id]["purchases"]
    if not purchases:
        bot.send_message(message.chat.id, "📦 لا يوجد مشتريات حتى الآن.", reply_markup=keyboards.wallet_menu())
    else:
        text = "🛍️ مشترياتك المقبولة:\n" + "\n".join(purchases)
        bot.send_message(message.chat.id, text, reply_markup=keyboards.wallet_menu())

# ✅ عرض سجل التحويلات
def show_transfers(bot, message, history=None):
    user_id = message.from_user.id
    register_user_if_not_exist(user_id)

    if history is not None:
        history.setdefault(user_id, []).append("wallet")

    transfers = users_wallet[user_id]["transfers"]
    if not transfers:
        bot.send_message(message.chat.id, "📄 لا يوجد عمليات تحويل بعد.", reply_markup=keyboards.wallet_menu())
    else:
        text = "📑 سجل التحويلات:\n" + "\n".join(transfers)
        bot.send_message(message.chat.id, text, reply_markup=keyboards.wallet_menu())

# ⏳ متغير لحالة التحويل
transfer_steps = {}

# ✅ تسجيل الأوامر
def register(bot, history):

    @bot.message_handler(func=lambda msg: msg.text == "💰 محفظتي")
    def handle_wallet(msg):
        show_wallet(bot, msg, history)

    @bot.message_handler(func=lambda msg: msg.text == "🛍️ مشترياتي")
    def handle_purchases(msg):
        show_purchases(bot, msg, history)

    @bot.message_handler(func=lambda msg: msg.text == "📑 سجل التحويلات")
    def handle_transfers(msg):
        show_transfers(bot, msg, history)

    @bot.message_handler(func=lambda msg: msg.text == "🔁 تحويل من محفظتك إلى محفظة عميل آخر")
    def handle_transfer_notice(msg):
        history.setdefault(msg.from_user.id, []).append("wallet")
        warning = (
            "⚠️ تنويه:\n"
            "هذه العملية خاصة بين المستخدمين فقط.\n"
            "لسنا مسؤولين عن أي خطأ يحدث عند تحويلك رصيدًا لعميل آخر.\n"
            "اتبع التعليمات جيدًا.\n\n"
            "اضغط (✅ موافق) للمتابعة أو (⬅️ رجوع) للعودة."
        )
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("✅ موافق", "⬅️ رجوع", "🔄 ابدأ من جديد")
        bot.send_message(msg.chat.id, warning, reply_markup=kb)

    @bot.message_handler(func=lambda msg: msg.text == "✅ موافق")
    def ask_for_target_id(msg):
        bot.send_message(
            msg.chat.id,
            "🔢 أدخل رقم ID الخاص بالعميل (رقم الحساب):",
            reply_markup=keyboards.hide_keyboard()
        )
        transfer_steps[msg.from_user.id] = {"step": "awaiting_id"}

    @bot.message_handler(func=lambda msg: transfer_steps.get(msg.from_user.id, {}).get("step") == "awaiting_id")
    def receive_target_id(msg):
        try:
            target_id = int(msg.text.strip())
        except:
            bot.send_message(msg.chat.id, "❌ الرجاء إدخال رقم ID صحيح.")
            return

        if target_id not in users_wallet:
            bot.send_message(msg.chat.id, "❌ هذا الرقم غير موجود.")
            transfer_steps.pop(msg.from_user.id, None)
            return

        transfer_steps[msg.from_user.id].update({"step": "awaiting_amount", "target_id": target_id})
        bot.send_message(msg.chat.id, "💵 أدخل المبلغ الذي تريد تحويله:")

    @bot.message_handler(func=lambda msg: transfer_steps.get(msg.from_user.id, {}).get("step") == "awaiting_amount")
    def receive_amount(msg):
        user_id = msg.from_user.id
        try:
            amount = int(msg.text.strip())
        except:
            bot.send_message(msg.chat.id, "❌ الرجاء إدخال مبلغ صالح.")
            return

        balance = users_wallet[user_id]["balance"]
        if amount <= 0:
            bot.send_message(msg.chat.id, "❌ لا يمكن تحويل مبلغ صفر أو أقل.")
            return

        if balance - amount < 8000:
            needed = (8000 + amount) - balance
            bot.send_message(
                msg.chat.id,
                f"❌ لا يمكنك تنفيذ العملية.\n🔔 تحتاج إلى `{needed:,} ل.س` إضافي.",
                parse_mode="Markdown",
                reply_markup=keyboards.wallet_menu()
            )
            transfer_steps.pop(user_id, None)
            return

        transfer_steps[user_id].update({"step": "awaiting_confirm", "amount": amount})
        target_id = transfer_steps[user_id]["target_id"]

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("✅ تأكيد التحويل", "⬅️ رجوع", "🔄 ابدأ من جديد")
        msg_text = f"📤 هل أنت متأكد من تحويل `{amount:,} ل.س` إلى الحساب `{target_id}`؟"
        bot.send_message(msg.chat.id, msg_text, parse_mode="Markdown", reply_markup=kb)

    @bot.message_handler(func=lambda msg: msg.text == "✅ تأكيد التحويل")
    def confirm_transfer(msg):
        user_id = msg.from_user.id
        step = transfer_steps.get(user_id)
        if not step or step.get("step") != "awaiting_confirm":
            return

        amount = step["amount"]
        target_id = step["target_id"]

        users_wallet[user_id]["balance"] -= amount
        users_wallet[target_id]["balance"] += amount

        users_wallet[user_id]["transfers"].append(f"أرسلت {amount} ل.س إلى {target_id}")
        users_wallet[target_id]["transfers"].append(f"استلمت {amount} ل.س من {user_id}")

        bot.send_message(msg.chat.id, "✅ تم تحويل المبلغ بنجاح.", reply_markup=keyboards.wallet_menu())
        transfer_steps.pop(user_id, None)

        show_wallet(bot, msg, history)
