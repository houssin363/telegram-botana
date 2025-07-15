# handlers/cash_transfer.py

from telebot import types
from config import ADMIN_MAIN_ID
from services.wallet_service import has_sufficient_balance, deduct_balance
from handlers.wallet import register_user_if_not_exist
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

def make_inline_buttons(*buttons):
    kb = types.InlineKeyboardMarkup()
    for text, data in buttons:
        kb.add(types.InlineKeyboardButton(text, callback_data=data))
    return kb

def start_cash_transfer(bot, message, history=None):
    user_id = message.from_user.id
    register_user_if_not_exist(user_id)
    if history is not None:
        history.setdefault(user_id, []).append("cash_menu")
    bot.send_message(message.chat.id, "📤 اختر نوع التحويل من محفظتك:", reply_markup=keyboards.cash_transfer_menu())

def register(bot, history):
    @bot.message_handler(func=lambda msg: msg.text == "🧧 تحويل كاش من محفظتك")
    def open_cash_menu(msg):
        start_cash_transfer(bot, msg, history)

    @bot.message_handler(func=lambda msg: msg.text in [
        "تحويل إلى سيرياتيل كاش",
        "تحويل إلى شام كاش",
        "تحويل إلى أم تي إن كاش"
    ])
    def handle_cash_type(msg):
        user_id = msg.from_user.id
        if "سيرياتيل" in msg.text:
            cash_type = "سيرياتيل كاش"
        elif "شام" in msg.text:
            cash_type = "شام كاش"
        elif "أم تي إن" in msg.text:
            cash_type = "أم تي إن كاش"
        else:
            cash_type = msg.text
        user_states[user_id] = {"step": "awaiting_number", "cash_type": cash_type}
        bot.send_message(msg.chat.id, "📲 أكتب الرقم أو الكود المراد التحويل له:")

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
            bot.send_message(msg.chat.id, "⚠️ الرجاء إدخال مبلغ صحيح بالأرقام.")
            return

        state = user_states[user_id]
        commission = calculate_commission(amount)
        total = amount + commission

        summary = (
            f"📤 تأكيد العملية:\n"
            f"📲 الرقم: {state['number']}\n"
            f"💸 المبلغ: {amount:,} ل.س\n"
            f"🧾 العمولة: {commission:,} ل.س\n"
            f"✅ الإجمالي: {total:,} ل.س\n"
            f"💼 الطريقة: {state['cash_type']}"
        )

        kb = make_inline_buttons(
            ("✔️ تأكيد", "cash_confirm"),
            ("✏️ تعديل", "cash_edit"),
            ("❌ إلغاء", "cash_cancel")
        )
        bot.send_message(msg.chat.id, summary, reply_markup=kb)
        state["amount"] = amount
        state["commission"] = commission
        state["total"] = total
        state["step"] = "confirming"

    @bot.callback_query_handler(func=lambda call: call.data == "cash_edit")
    def edit_transfer(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_number"
        bot.edit_message_text("✏️ أعد إدخال الرقم أو الكود المراد التحويل له:",
                              call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "cash_cancel")
    def cancel_transfer(call):
        user_id = call.from_user.id
        bot.edit_message_text("🚫 تم إلغاء الطلب.", call.message.chat.id, call.message.message_id)
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data == "cash_confirm")
    def confirm_transfer(call):
        user_id = call.from_user.id
        state = user_states.get(user_id, {})
        total = state.get("total")
        # تحقق من الرصيد
        if not has_sufficient_balance(user_id, total):
            kb = make_inline_buttons(
                ("💳 شحن المحفظة", "recharge_wallet"),
                ("⬅️ رجوع", "cash_cancel")
            )
            bot.send_message(call.message.chat.id, f"❌ لا يوجد رصيد كافٍ في محفظتك.\n💡 الرجاء شحن المحفظة بمبلغ {total:,} ل.س أو أكثر لإتمام العملية.", reply_markup=kb)
            return

        # خصم الرصيد من المحفظة فورًا
        deduct_balance(user_id, total)
        # رسالة ملخص للعميل
        bot.edit_message_text("✅ تم إرسال طلبك بانتظار موافقة الإدارة.", call.message.chat.id, call.message.message_id)
        # رسالة للإدارة مع أزرار قبول/رفض
        kb_admin = make_inline_buttons(
            ("✅ قبول", f"admin_cash_accept_{user_id}"),
            ("❌ رفض", f"admin_cash_reject_{user_id}")
        )
        message = (
            f"📤 طلب تحويل كاش جديد:\n"
            f"👤 المستخدم: {user_id}\n"
            f"📲 الرقم: {state.get('number')}\n"
            f"💰 المبلغ: {state.get('amount'):,} ل.س\n"
            f"💼 الطريقة: {state.get('cash_type')}\n"
            f"🧾 العمولة: {state.get('commission'):,} ل.س\n"
            f"✅ الإجمالي: {state.get('total'):,} ل.س"
        )
        bot.send_message(ADMIN_MAIN_ID, message, reply_markup=kb_admin)
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data == "recharge_wallet")
    def show_recharge_methods(call):
        bot.send_message(call.message.chat.id, "💳 اختر طريقة شحن المحفظة:", reply_markup=keyboards.recharge_menu())

    # يمكنك لاحقًا إضافة منطق القبول والرفض للإدارة عبر callback_data "admin_cash_accept_*" و"admin_cash_reject_*"

