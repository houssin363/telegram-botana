# handlers/media_services.py
from telebot import types
from config import ADMIN_MAIN_ID
from services.wallet_service import has_sufficient_balance, deduct_balance
from handlers.keyboards import media_services_menu

user_media_state = {}
USD_RATE = 11000
MEDIA_PRODUCTS = {
    "🖼️ تصميم لوغو احترافي": 300,
    "📱 إدارة ونشر يومي": 300,
    "📢 إطلاق حملة إعلانية": 300,
    "🧾 باقة متكاملة شهرية": 300,
    "✏️ طلب مخصص": 0,
}

def register(bot, user_state):
    @bot.message_handler(func=lambda msg: msg.text == "🖼️ خدمات إعلانية وتصميم")
    def open_media_menu(msg):
        user_state[msg.from_user.id] = "media_services"
        bot.send_message(
            msg.chat.id,
            "🖌️ اختر خدمة الإعلان أو التصميم التي تريدها:",
            reply_markup=media_services_menu()
        )

    @bot.message_handler(func=lambda msg: msg.text in MEDIA_PRODUCTS)
    def handle_selected_service(msg):
        # ... your existing code for details step, pricing, callbacks, etc.
