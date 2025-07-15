# handlers/syr_units.py
from telebot import types
from database.models.product import Product
from services.wallet_service import has_sufficient_balance, deduct_balance
from config import ADMIN_MAIN_ID
from handlers.keyboards import syrian_balance_menu

# منتجات سيرياتيل وحدات
SYRIATEL_PRODUCTS = [
    Product(1001, "1000 وحدة", "سيرياتيل", 1200),
    Product(1002, "1500 وحدة", "سيرياتيل", 1800),
    Product(1003, "2013 وحدة", "سيرياتيل", 2400),
    Product(1004, "3068 وحدة", "سيرياتيل", 3682),
    Product(1005, "4506 وحدة", "سيرياتيل", 5400),
    Product(1006, "5273 وحدة", "سيرياتيل", 6285),
    Product(1007, "7190 وحدة", "سيرياتيل", 8628),
    Product(1008, "9587 وحدة", "سيرياتيل", 11500),
    Product(1009, "13039 وحدة", "سيرياتيل", 15500),
]
user_syr_states = {}

def register(bot, user_state):
    @bot.message_handler(func=lambda msg: msg.text == "💳 تحويل رصيد سوري")
    def open_syr_menu(msg):
        user_state[msg.from_user.id] = "syrian_transfer"
        bot.send_message(
            msg.chat.id,
            "📲 اختر كمية الوحدات من سيرياتيل:",
            reply_markup=syrian_balance_menu()
        )

    @bot.message_handler(func=lambda msg: msg.text in [f"{p.name} - {p.price:,} ل.س" for p in SYRIATEL_PRODUCTS])
    def select_syriatel_product(msg):
        user_id = msg.from_user.id
        selected = next(p for p in SYRIATEL_PRODUCTS if f"{p.name} - {p.price:,} ل.س" == msg.text)
        user_syr_states[user_id] = {"step": "enter_number", "product": selected}
        bot.send_message(msg.chat.id, "📲 أدخل الرقم أو الكود الذي يبدأ بـ 093 أو 098 أو 099:")

    @bot.message_handler(func=lambda msg: user_syr_states.get(msg.from_user.id, {}).get("step") == "enter_number")
    def enter_syriatel_number(msg):
        user_id = msg.from_user.id
        number = msg.text.strip()
        state = user_syr_states[user_id]
        state["number"] = number
        product = state["product"]
        balance = has_sufficient_balance(user_id, product.price)
        if not balance:
            bot.send_message(msg.chat.id, "❌ لا يوجد رصيد كافٍ في محفظتك.")
            user_syr_states.pop(user_id, None)
            return
        deduct_balance(user_id, product.price)
        admin_msg = (
            f"📥 طلب جديد من {user_id}\n"
            f"👤 المنتج: {product.name} ({product.price:,} ل.س)\n"
            f"📞 الرقم: {number}\n"
            f"📦 النوع: رصيد سيرياتيل وحدات"
        )
        bot.send_message(ADMIN_MAIN_ID, admin_msg)
        bot.send_message(msg.chat.id, "✅ تم إرسال الطلب إلى الإدارة، بانتظار المعالجة.")
        user_syr_states.pop(user_id, None)
        user_state[user_id] = "products_menu"
