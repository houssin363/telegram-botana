# handlers/university_fees.py
from telebot import types
from handlers.wallet_service import has_sufficient_balance, deduct_balance
from config import ADMIN_MAIN_ID

COMMISSION_PER_50000 = 3500
user_uni_state = {}

def start_university_fee(bot, message):
    bot.send_message(message.chat.id, "🏫 اكتب اسم الجامعة أو اسم المحافظة التي تتبع لها:")
    user_uni_state[message.from_user.id] = {"step": "university_name"}

def calculate_uni_commission(amount):
    blocks = amount // 50000
    remainder = amount % 50000
    commission = blocks * COMMISSION_PER_50000
    if remainder > 0:
        commission += int(COMMISSION_PER_50000 * (remainder / 50000))
    return commission

def register(bot):
    @bot.message_handler(func=lambda msg: msg.text == "🎓 دفع رسوم جامعية")
    def open_uni_menu(msg):
        start_university_fee(bot, msg)

    @bot.message_handler(func=lambda msg: user_uni_state.get(msg.from_user.id, {}).get("step") == "university_name")
    def enter_university(msg):
        user_id = msg.from_user.id
        user_uni_state[user_id]["university"] = msg.text.strip()
        user_uni_state[user_id]["step"] = "national_id"
        bot.send_message(msg.chat.id, "🆔 أدخل الرقم الوطني:")

    @bot.message_handler(func=lambda msg: user_uni_state.get(msg.from_user.id, {}).get("step") == "national_id")
    def enter_national_id(msg):
        user_id = msg.from_user.id
        user_uni_state[user_id]["national_id"] = msg.text.strip()
        user_uni_state[user_id]["step"] = "university_id"
        bot.send_message(msg.chat.id, "🎓 أدخل الرقم الجامعي:")

    @bot.message_handler(func=lambda msg: user_uni_state.get(msg.from_user.id, {}).get("step") == "university_id")
    def enter_university_id(msg):
        user_id = msg.from_user.id
        user_uni_state[user_id]["university_id"] = msg.text.strip()
        user_uni_state[user_id]["step"] = "amount"
        bot.send_message(msg.chat.id, "💰 أدخل المبلغ المطلوب دفعه:")

    @bot.message_handler(func=lambda msg: user_uni_state.get(msg.from_user.id, {}).get("step") == "amount")
    def enter_amount(msg):
        user_id = msg.from_user.id
        try:
            amount = int(msg.text.strip())
            user_uni_state[user_id]["amount"] = amount
        except ValueError:
            return bot.send_message(msg.chat.id, "⚠️ الرجاء إدخال رقم صالح للمبلغ.")

        commission = calculate_uni_commission(amount)
        total = amount + commission

        user_uni_state[user_id]["commission"] = commission
        user_uni_state[user_id]["total"] = total

        text = (
            f"❓ هل أنت متأكد من دفع رسوم جامعية؟\n"
            f"🏫 الجامعة: {user_uni_state[user_id]['university']}\n"
            f"🆔 رقم وطني: {user_uni_state[user_id]['national_id']}\n"
            f"🎓 رقم جامعي: {user_uni_state[user_id]['university_id']}\n"
            f"💰 المبلغ: {amount:,} + عمولة {commission:,} = {total:,} ل.س"
        )

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✔️ تأكيد", callback_data="uni_confirm"))
        kb.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="uni_cancel"))
        bot.send_message(msg.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "uni_cancel")
    def cancel_uni(call):
        user_uni_state.pop(call.from_user.id, None)
        bot.edit_message_text("🚫 تم إلغاء العملية.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "uni_confirm")
    def confirm_uni_order(call):
        user_id = call.from_user.id
        state = user_uni_state.get(user_id, {})
        total = state.get("total")

        if not has_sufficient_balance(user_id, total):
            bot.send_message(call.message.chat.id, "❌ لا يوجد رصيد كافٍ في محفظتك.")
            return

        deduct_balance(user_id, total)

        msg = (
            f"📚 طلب دفع رسوم جامعية:\n"
            f"👤 المستخدم: {user_id}\n"
            f"🏫 الجامعة: {state['university']}\n"
            f"🆔 الرقم الوطني: {state['national_id']}\n"
            f"🎓 الرقم الجامعي: {state['university_id']}\n"
            f"💵 المبلغ المطلوب: {state['amount']:,} + عمولة {state['commission']:,} = {total:,} ل.س"
        )

        bot.send_message(ADMIN_MAIN_ID, msg)
        bot.edit_message_text("✅ تم إرسال طلبك للإدارة، بانتظار الموافقة.",
                              call.message.chat.id, call.message.message_id)
        user_uni_state.pop(user_id, None)
