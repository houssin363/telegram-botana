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
        # ... your existing code for university_name step

    @bot.message_handler(func=lambda msg: user_uni_state.get(msg.from_user.id, {}).get("step") == "national_id")
    def enter_national_id(msg):
        # ... your existing code for national_id step

    @bot.message_handler(func=lambda msg: user_uni_state.get(msg.from_user.id, {}).get("step") == "university_id")
    def enter_university_id(msg):
        # ... your existing code for university_id step

    @bot.message_handler(func=lambda msg: user_uni_state.get(msg.from_user.id, {}).get("step") == "amount")
    def enter_amount(msg):
        # ... your existing code for amount step

    @bot.callback_query_handler(func=lambda call: call.data == "uni_cancel")
    def cancel_uni(call):
        # ... your existing code for uni_cancel

    @bot.callback_query_handler(func=lambda call: call.data == "uni_confirm")
    def confirm_uni_order(call):
        # ... your existing code for uni_confirm
