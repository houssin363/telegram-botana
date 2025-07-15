# handlers/cash_transfer.py
from telebot import types
from config import ADMIN_MAIN_ID
from handlers.wallet import register_user_if_not_exist
from handlers import keyboards

user_states = {}
pending_cash_requests = set()

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
        history[user_id] = "cash_menu"
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
    @bot.message_handler(func=lambda msg: msg.text == "💵 شراء رصيد كاش")
    def open_cash_menu(msg):
        start_cash_transfer(bot, msg, history)

    @bot.message_handler(func=lambda msg: msg.text in ["📲 سيرياتيل كاش", "📲 أم تي إن كاش", "📲 شام كاش"])
    def handle_cash_type(msg):
        user_id = msg.from_user.id
        user_states[user_id] = {"step": "show_commission", "cash_type": msg.text}
        history[user_id] = "cash_menu"
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

    @bot.callback_query_handler(func=lambda call: call.data == "commission_cancel")
    def commission_cancel(call):
        user_id = call.from_user.id
        bot.edit_message_text(
            "❌ تم إلغاء العملية.",
            call.message.chat.id,
            call.message.message_id
        )
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data == "commission_confirm")
    def commission_confirmed(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_number"
        bot.edit_message_text(
            "📲 أكتب الرقم أو الكود المراد التحويل له:",
            call.message.chat.id,
            call.message.message_id
        )

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_number")
    def get_target_number(msg):
        user_id = msg.from_user.id
        user_states[user_id]["number"] = msg.text
        user_states[user_id]["step"] = "awaiting_amount"
        bot.send_message(msg.chat.id, "💰 اكتب المبلغ الذي تريد تحويله:")

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_amount")
    def get_amount_and_confirm(msg):
        user_id = msg.from_user.id
        try:
            amount = int(msg.text)
        except ValueError:
            return bot.send_message(msg.chat.id, "⚠️ الرجاء إدخال مبلغ صحيح بالأرقام.")
        commission = calculate_commission(amount)
        total = amount + commission
        user_states[user_id].update({
            "amount": amount,
            "commission": commission,
            "total": total,
            "step": "confirming"
        })
        summary = (
            f"📤 تأكيد العملية:\n"
            f"📲 الرقم: {user_states[user_id]['number']}\n"
            f"💸 المبلغ: {amount:,} ل.س\n"
            f"💼 الطريقة: {user_states[user_id]['cash_type']}\n"
            f"🧾 العمولة: {commission:,} ل.س\n"
            f"✅ الإجمالي: {total:,} ل.س"
        )
        kb = make_inline_buttons(
            ("✅ تأكيد", "cash_confirm"),
            ("❌ إلغاء", "cash_cancel")
        )
        bot.send_message(msg.chat.id, summary, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "cash_cancel")
    def cancel_transfer(call):
        user_id = call.from_user.id
        bot.edit_message_text(
            "🚫 تم إلغاء الطلب.",
            call.message.chat.id,
            call.message.message_id
        )
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data == "cash_confirm")
    def confirm_transfer(call):
        user_id = call.from_user.id
        data = user_states.pop(user_id, {})
        admin_msg = (
            f"📤 طلب تحويل كاش جديد:\n"
            f"👤 المستخدم: {user_id}\n"
            f"📲 الرقم: {data.get('number')}\n"
            f"💰 المبلغ: {data.get('amount'):,} ل.س\n"
            f"💼 الطريقة: {data.get('cash_type')}\n"
            f"🧾 العمولة: {data.get('commission'):,} ل.س\n"
            f"✅ الإجمالي: {data.get('total'):,} ل.س"
        )
        bot.edit_message_text(
            "✅ تم إرسال الطلب بنجاح، بانتظار المعالجة من الإدارة.",
            call.message.chat.id,
            call.message.message_id
        )
        bot.send_message(ADMIN_MAIN_ID, admin_msg)
