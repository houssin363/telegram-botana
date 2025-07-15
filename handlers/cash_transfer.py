from telebot import types
from config import ADMIN_MAIN_ID
from services.wallet_service import register_user_if_not_exist, get_balance, deduct_balance
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

def register(bot, user_state):
    @bot.message_handler(func=lambda msg: msg.text == "💵 شراء رصيد كاش")
    def open_cash_menu(msg):
        user_id = msg.from_user.id
        register_user_if_not_exist(user_id)
        user_state.setdefault(user_id, []).append("cash_menu")
        bot.send_message(msg.chat.id, "📤 اختر نوع التحويل من محفظتك:", reply_markup=keyboards.cash_transfer_menu())

    @bot.message_handler(func=lambda msg: msg.text in ["📲 سيرياتيل كاش", "📲 أم تي إن كاش", "📲 شام كاش"])
    def select_cash_type(msg):
        user_id = msg.from_user.id
        cash_type = msg.text
        user_states[user_id] = {"step": "commission_notice", "cash_type": cash_type}
        text = (
            f"⚠️ العمولة لكل 50000 ل.س هي {COMMISSION_PER_50000} ل.س.\n"
            "هل تريد المتابعة؟"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ موافق", callback_data="commission_confirm"))
        kb.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="commission_cancel"))
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
        bot.edit_message_text("📲 أكتب الرقم أو الكود المراد التحويل له:", call.message.chat.id, call.message.message_id)

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
            amount = int(msg.text.strip())
        except ValueError:
            bot.send_message(msg.chat.id, "⚠️ الرجاء إدخال مبلغ صحيح بالأرقام.")
            return

        balance = get_balance(user_id)
        commission = calculate_commission(amount)
        total = amount + commission

        if balance < total:
            bot.send_message(msg.chat.id, f"❌ رصيدك غير كافٍ، تحتاج إلى {total:,} ل.س، ورصيدك الحالي {balance:,} ل.س.")
            user_states.pop(user_id, None)
            return

        state = user_states[user_id]
        summary = (
            f"📤 تأكيد العملية:\n"
            f"📲 الرقم: {state['number']}\n"
            f"💸 المبلغ: {amount:,} ل.س\n"
            f"🧾 العمولة: {commission:,} ل.س\n"
            f"✅ الإجمالي: {total:,} ل.س\n"
            f"💼 الطريقة: {state['cash_type']}"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✔️ تأكيد", callback_data="cash_confirm"))
        kb.add(types.InlineKeyboardButton("✏️ تعديل", callback_data="cash_edit"))
        kb.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cash_cancel"))
        bot.send_message(msg.chat.id, summary, reply_markup=kb)
        state["amount"] = amount
        state["commission"] = commission
        state["total"] = total
        state["step"] = "confirming"

    @bot.callback_query_handler(func=lambda call: call.data == "cash_edit")
    def edit_cash(call):
        user_id = call.from_user.id
        if user_states.get(user_id, {}).get("step") == "confirming":
            user_states[user_id]["step"] = "awaiting_amount"
            bot.edit_message_text("💰 أعد كتابة المبلغ الجديد الذي تريد تحويله:", call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text("❌ لا يمكن تعديل العملية في هذه الخطوة.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "cash_cancel")
    def cancel_transfer(call):
        user_id = call.from_user.id
        bot.edit_message_text("🚫 تم إلغاء الطلب.", call.message.chat.id, call.message.message_id)
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data == "cash_confirm")
    def confirm_transfer(call):
        user_id = call.from_user.id
        data = user_states.pop(user_id, {})
        message = (
            f"📤 طلب تحويل كاش جديد:\n"
            f"👤 المستخدم: {user_id}\n"
            f"📲 الرقم: {data.get('number')}\n"
            f"💰 المبلغ: {data.get('amount'):,} ل.س\n"
            f"💼 الطريقة: {data.get('cash_type')}\n"
            f"🧾 العمولة: {data.get('commission'):,} ل.س\n"
            f"✅ الإجمالي: {data.get('total'):,} ل.س"
        )
        bot.edit_message_text("✅ تم إرسال الطلب بنجاح، بانتظار المعالجة من الإدارة.", call.message.chat.id, call.message.message_id)
        bot.send_message(ADMIN_MAIN_ID, message)
