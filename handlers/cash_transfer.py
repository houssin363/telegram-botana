from telebot import types
from config import ADMIN_MAIN_ID
from services.wallet_service import get_balance, deduct_balance, register_user_if_not_exist
from handlers import keyboards

user_states = {}
pending_cash_requests = {}

COMMISSION_PER_50000 = 3500

def calculate_commission(amount):
    blocks = amount // 50000
    remainder = amount % 50000
    commission = blocks * COMMISSION_PER_50000
    if remainder > 0:
        commission += int(COMMISSION_PER_50000 * (remainder / 50000))
    return commission

def start_cash_transfer(bot, message, history=None):
    user_id = message.from_user.id
    register_user_if_not_exist(user_id)
    if history is not None:
        history.setdefault(user_id, []).append("cash_menu")

    bot.send_message(
        message.chat.id,
        "📤 اختر نوع التحويل من محفظتك:",
        reply_markup=keyboards.cash_transfer_menu()
    )

def make_inline_buttons(*buttons):
    kb = types.InlineKeyboardMarkup()
    for text, data in buttons:
        kb.add(types.InlineKeyboardButton(text, callback_data=data))
    return kb

def register(bot, history):
    @bot.message_handler(func=lambda msg: msg.text in ["💵 شراء رصيد كاش", "🧧 تحويل كاش من محفظتك"])
    def open_cash_menu(msg):
        start_cash_transfer(bot, msg, history)

    @bot.message_handler(func=lambda msg: msg.text in ["سيرياتيل كاش", "أم تي إن كاش", "شام كاش"])
    def handle_cash_type(msg):
        user_id = msg.from_user.id
        cash_type = msg.text
        user_states[user_id] = {"step": "show_commission", "cash_type": cash_type}
        history.setdefault(user_id, []).append("cash_menu")

        text = (
            "⚠️ تنويه:\n"
            f"العمولة لكل 50000 ل.س هي {COMMISSION_PER_50000} ل.س.\n"
            "اضغط موافق للمتابعة."
        )
        kb = make_inline_buttons(
            ("✅ موافق", "commission_confirm"),
            ("❌ إلغاء", "commission_cancel")
        )
        bot.send_message(msg.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "commission_cancel")
    def commission_cancel(call):
        user_id = call.from_user.id
        bot.edit_message_text("❌ تم إلغاء العملية.", call.message.chat.id, call.message.message_id)
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data == "commission_confirm")
    def commission_confirmed(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_number"
        label = "الرقم" if user_states[user_id]["cash_type"] != "شام كاش" else "الكود"
        bot.edit_message_text(f"📲 أكتب {label} المراد التحويل له:", call.message.chat.id, call.message.message_id)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_number")
    def get_target_number(msg):
        user_id = msg.from_user.id
        user_states[user_id]["number"] = msg.text
        user_states[user_id]["step"] = "awaiting_amount"
        bot.send_message(msg.chat.id, "💰 اكتب المبلغ الذي تريد صرفه من المحفظة:")

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_amount")
    def get_amount_and_confirm(msg):
        user_id = msg.from_user.id
        try:
            amount = int(msg.text)
        except ValueError:
            bot.send_message(msg.chat.id, "⚠️ الرجاء إدخال مبلغ صحيح بالأرقام.")
            return

        if amount <= 0:
            bot.send_message(msg.chat.id, "⚠️ يجب أن يكون المبلغ أكبر من صفر.")
            return

        state = user_states[user_id]
        commission = calculate_commission(amount)
        total = amount + commission
        balance = get_balance(user_id)
        if balance < total:
            bot.send_message(msg.chat.id, f"❌ رصيدك الحالي لا يكفي لإتمام العملية.\nرصيدك: {balance:,} ل.س\nالمطلوب: {total:,} ل.س")
            user_states.pop(user_id, None)
            return

        label = "الرقم" if state["cash_type"] != "شام كاش" else "الكود"
        summary = (
            f"📤 تأكيد العملية:\n"
            f"💼 العملية: {state['cash_type']}\n"
            f"📲 {label}: {state['number']}\n"
            f"💸 المبلغ المطلوب: {amount:,} ل.س\n"
            f"🧾 العمولة: {commission:,} ل.س\n"
            f"✅ سيتم خصم: {total:,} ل.س من محفظتك\n\n"
            f"هل أنت متأكد من متابعة العملية؟"
        )

        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("✔️ تأكيد", callback_data="cash_confirm"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="cash_cancel")
        )
        bot.send_message(msg.chat.id, summary, reply_markup=kb)
        state["amount"] = amount
        state["commission"] = commission
        state["total"] = total
        state["step"] = "confirming"

    @bot.callback_query_handler(func=lambda call: call.data == "cash_cancel")
    def cancel_transfer(call):
        user_id = call.from_user.id
        bot.edit_message_text("🚫 تم إلغاء الطلب.", call.message.chat.id, call.message.message_id)
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data == "cash_confirm")
    def confirm_transfer(call):
        user_id = call.from_user.id
        data = user_states[user_id]
        # لا تخصم هنا - خصم بعد تأكيد الأدمن
        pending_cash_requests[user_id] = {
            **data,
            "chat_id": call.message.chat.id,
            "message_id": call.message.message_id,
            "user_full_name": call.from_user.full_name,
            "username": call.from_user.username
        }
        label = "الرقم" if data["cash_type"] != "شام كاش" else "الكود"
        bot.edit_message_text(
            "✅ تم إرسال طلبك للإدارة. الوقت المتوقع من 1 إلى 3 دقائق.",
            call.message.chat.id, call.message.message_id
        )
        # رسالة للأدمن
        admin_keyboard = types.InlineKeyboardMarkup(row_width=2)
        admin_keyboard.add(
            types.InlineKeyboardButton("✅ تأكيد العملية", callback_data=f"admin_cash_ok_{user_id}"),
            types.InlineKeyboardButton("❌ رفض", callback_data=f"admin_cash_reject_{user_id}")
        )
        msg_admin = (
            f"🆕 طلب تحويل كاش:\n"
            f"👤 المستخدم: {data['user_full_name']} (@{data['username']})\n"
            f"🆔 آيدي: `{user_id}`\n"
            f"💼 العملية: {data['cash_type']}\n"
            f"📲 {label}: {data['number']}\n"
            f"💸 المبلغ المطلوب: {data['amount']:,} ل.س\n"
            f"🧾 العمولة: {data['commission']:,} ل.س\n"
            f"✅ سيتم الخصم: {data['total']:,} ل.س\n\n"
            "أرفق صورة التحويل قبل التأكيد أو اكتب سبب الرفض."
        )
        bot.send_message(ADMIN_MAIN_ID, msg_admin, parse_mode="Markdown", reply_markup=admin_keyboard)
        data["step"] = "pending_admin"

    # الأدمن: رفض الطلب
    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_cash_reject_"))
    def admin_reject(call):
        user_id = int(call.data.split("_")[-1])
        if user_id not in pending_cash_requests:
            bot.answer_callback_query(call.id, "❌ الطلب غير موجود أو انتهى بالفعل.")
            return
        msg = bot.send_message(call.message.chat.id, "📝 اكتب سبب الرفض ليتم إرساله للعميل:")
        bot.register_next_step_handler(msg, lambda m: process_admin_reject(m, user_id, call))

    def process_admin_reject(msg, user_id, call):
        reason = msg.text
        req = pending_cash_requests.pop(user_id, None)
        if req:
            bot.send_message(
                req["chat_id"],
                f"❌ تم رفض طلبك.\n📝 السبب: {reason}",
                reply_markup=keyboards.main_menu()
            )
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    # الأدمن: قبول الطلب وإرفاق صورة تحويل
    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_cash_ok_"))
    def admin_ok(call):
        user_id = int(call.data.split("_")[-1])
        if user_id not in pending_cash_requests:
            bot.answer_callback_query(call.id, "❌ الطلب غير موجود أو انتهى بالفعل.")
            return
        msg = bot.send_message(call.message.chat.id, "📸 أرسل صورة التحويل للعميل (أو اكتب تخطي لإكمال الطلب بدون صورة):")
        bot.register_next_step_handler(msg, lambda m: finish_cash_transfer(m, user_id, call))

    def finish_cash_transfer(msg, user_id, call):
        req = pending_cash_requests.pop(user_id, None)
        if not req:
            bot.send_message(call.message.chat.id, "❌ الطلب غير موجود أو انتهى بالفعل.")
            return

        # خصم الرصيد فعليا بعد موافقة الأدمن
        total = req["total"]
        balance = get_balance(user_id)
        if balance < total:
            bot.send_message(call.message.chat.id, f"⚠️ لم يعد لدى العميل رصيد كافٍ. الطلب ملغي تلقائياً.")
            bot.send_message(req["chat_id"], "❌ فشل تنفيذ الطلب بسبب نقص الرصيد.", reply_markup=keyboards.main_menu())
            return

        deduct_balance(user_id, total, f"تحويل كاش {req['cash_type']} إلى {req['number']} (خصم بعد تنفيذ الأدمن)")

        caption = (
            f"✅ تم تنفيذ عملية تحويل الكاش:\n"
            f"💸 المبلغ المطلوب: {req['amount']:,} ل.س\n"
            f"🧾 العمولة: {req['commission']:,} ل.س\n"
            f"✅ تم خصم: {req['total']:,} ل.س من محفظتك"
        )
        # أرسل صورة التحويل أو رسالة نصية
        if msg.content_type == "photo":
            bot.send_photo(req["chat_id"], msg.photo[-1].file_id, caption=caption, reply_markup=keyboards.main_menu())
        else:
            bot.send_message(req["chat_id"], caption, reply_markup=keyboards.main_menu())
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
