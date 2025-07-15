from telebot import types
from config import ADMIN_MAIN_ID
from services.wallet_service import get_balance, deduct_balance, register_user_if_not_exist
from handlers import keyboards

user_states = {}

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
    # يدعم الزرين من المنتجات أو المحفظة
    @bot.message_handler(func=lambda msg: msg.text in ["💵 شراء رصيد كاش", "🧧 تحويل كاش من محفظتك"])
    def open_cash_menu(msg):
        start_cash_transfer(bot, msg, history)

    # نوع التحويل
    @bot.message_handler(func=lambda msg: msg.text in ["سيرياتيل كاش", "أم تي إن كاش", "شام كاش"])
    def handle_cash_type(msg):
        user_id = msg.from_user.id
        cash_type = msg.text
        user_states[user_id] = {"step": "show_commission", "cash_type": cash_type}
        history.setdefault(user_id, []).append("cash_menu")

        text = (
            "⚠️ تنويه:\n"
            f"العمولة لكل 50000 ل.س هي {COMMISSION_PER_50000} ل.س.\n"
            "هل تريد المتابعة وكتابة الرقم أو الكود المراد التحويل له؟"
        )
        kb = make_inline_buttons(
            ("✅ موافق", "commission_confirm"),
            ("❌ إلغاء", "commission_cancel")
        )
        bot.send_message(msg.chat.id, text, reply_markup=kb)

    # إلغاء الخطوة بعد العمولة
    @bot.callback_query_handler(func=lambda call: call.data == "commission_cancel")
    def commission_cancel(call):
        user_id = call.from_user.id
        bot.edit_message_text("❌ تم إلغاء العملية.", call.message.chat.id, call.message.message_id)
        user_states.pop(user_id, None)

    # موافق - اكتب الرقم/الكود
    @bot.callback_query_handler(func=lambda call: call.data == "commission_confirm")
    def commission_confirmed(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_number"
        bot.edit_message_text("📲 أكتب الرقم أو الكود المراد التحويل له:",
                              call.message.chat.id, call.message.message_id)

    # اكتب الرقم/الكود
    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_number")
    def get_target_number(msg):
        user_id = msg.from_user.id
        user_states[user_id]["number"] = msg.text
        user_states[user_id]["step"] = "awaiting_amount"
        bot.send_message(msg.chat.id, "💰 اكتب المبلغ الذي تريد تحويله:")

    # اكتب المبلغ
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

        summary = (
            f"📤 تأكيد العملية:\n"
            f"📲 الرقم: {state['number']}\n"
            f"💸 المبلغ: {amount:,} ل.س\n"
            f"🧾 العمولة: {commission:,} ل.س\n"
            f"✅ الإجمالي: {total:,} ل.س\n"
            f"💼 الطريقة: {state['cash_type']}"
        )

        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("✔️ تأكيد", callback_data="cash_confirm"),
            types.InlineKeyboardButton("✏️ تعديل", callback_data="cash_edit"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="cash_cancel")
        )
        bot.send_message(msg.chat.id, summary, reply_markup=kb)
        state["amount"] = amount
        state["commission"] = commission
        state["total"] = total
        state["step"] = "confirming"

    # إلغاء نهائي
    @bot.callback_query_handler(func=lambda call: call.data == "cash_cancel")
    def cancel_transfer(call):
        user_id = call.from_user.id
        bot.edit_message_text("🚫 تم إلغاء الطلب.", call.message.chat.id, call.message.message_id)
        user_states.pop(user_id, None)

    # تعديل المبلغ
    @bot.callback_query_handler(func=lambda call: call.data == "cash_edit")
    def edit_amount(call):
        user_id = call.from_user.id
        state = user_states.get(user_id)
        if state:
            state["step"] = "awaiting_amount"
            bot.edit_message_text("💰 اكتب المبلغ الجديد الذي تريد تحويله:", call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text("حدث خطأ. الرجاء البدء من جديد.", call.message.chat.id, call.message.message_id)

    # تأكيد نهائي - تنفيذ العملية
    @bot.callback_query_handler(func=lambda call: call.data == "cash_confirm")
    def confirm_transfer(call):
        user_id = call.from_user.id
        data = user_states.pop(user_id, {})
        total = data.get("total", 0)
        balance = get_balance(user_id)
        if balance < total:
            bot.edit_message_text(f"❌ رصيدك الحالي لا يكفي لإتمام العملية.\nرصيدك: {balance:,} ل.س\nالمطلوب: {total:,} ل.س",
                                  call.message.chat.id, call.message.message_id)
            return

        # خصم الرصيد مباشرة
        deduct_balance(user_id, total, f"تحويل كاش ({data.get('cash_type')}) إلى {data.get('number')}")
        message = (
            f"📤 طلب تحويل كاش جديد:\n"
            f"👤 المستخدم: {user_id}\n"
            f"📲 الرقم: {data.get('number')}\n"
            f"💰 المبلغ: {data.get('amount'):,} ل.س\n"
            f"💼 الطريقة: {data.get('cash_type')}\n"
            f"🧾 العمولة: {data.get('commission'):,} ل.س\n"
            f"✅ الإجمالي: {data.get('total'):,} ل.س"
        )
        bot.edit_message_text("✅ تم إرسال الطلب بنجاح، بانتظار المعالجة من الإدارة.",
                              call.message.chat.id, call.message.message_id)
        bot.send_message(ADMIN_MAIN_ID, message)
