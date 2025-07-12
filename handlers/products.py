from telebot import types
from config import BOT_NAME
from handlers import keyboards
from database.models.product import Product

# منتجات مقسمة حسب التصنيفات
PRODUCTS = {
    "PUBG": [
        Product(1, "60 شدة", "ألعاب", 0.89),
        Product(2, "325 شدة", "ألعاب", 4.44),
        Product(3, "660 شدة", "ألعاب", 8.85),
        Product(4, "1800 شدة", "ألعاب", 22.09),
        Product(5, "3850 شدة", "ألعاب", 43.24),
        Product(6, "8100 شدة", "ألعاب", 86.31),
    ],
    "FreeFire": [
        Product(7, "100 جوهرة", "ألعاب", 0.98),
        Product(8, "310 جوهرة", "ألعاب", 2.49),
        Product(9, "520 جوهرة", "ألعاب", 4.13),
        Product(10, "1060 جوهرة", "ألعاب", 9.42),
        Product(11, "2180 جوهرة", "ألعاب", 18.84),
    ],
    "Jawaker": [
        Product(12, "10000 توكنز", "ألعاب", 1.34),
        Product(13, "15000 توكنز", "ألعاب", 2.01),
        Product(14, "20000 توكنز", "ألعاب", 2.68),
        Product(15, "30000 توكنز", "ألعاب", 4.02),
        Product(16, "60000 توكنز", "ألعاب", 8.04),
        Product(17, "120000 توكنز", "ألعاب", 16.08),
    ]
}

pending_orders = set()
user_orders = {}

def convert_price_usd_to_syp(usd):
    if usd <= 5:
        return int(usd * 11800)
    elif usd <= 10:
        return int(usd * 11600)
    elif usd <= 20:
        return int(usd * 11300)
    return int(usd * 11000)

def show_products_menu(bot, message):
    bot.send_message(message.chat.id, "📍 اختر نوع المنتج:", reply_markup=keyboards.products_menu())

def show_game_categories(bot, message):
    bot.send_message(message.chat.id, "🎮 اختر اللعبة أو التطبيق:", reply_markup=keyboards.game_categories())

def show_product_options(bot, message, category):
    options = PRODUCTS.get(category, [])
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for product in options:
        price_syp = convert_price_usd_to_syp(product.price)
        label = f"{product.name}\n💵 {price_syp:,} ل.س"
        callback_data = f"select_{product.product_id}"
        keyboard.add(types.InlineKeyboardButton(label, callback_data=callback_data))
    bot.send_message(message.chat.id, f"📦 اختر الكمية لـ {category}:", reply_markup=keyboard)

def register(bot, history):
    @bot.message_handler(func=lambda msg: msg.text in ["🛒 المنتجات", "💼 المنتجات"])
    def handle_main_product_menu(msg):
        user_id = msg.from_user.id
        if user_id in pending_orders:
            bot.send_message(msg.chat.id, "⚠️ لديك طلب قيد الانتظار.")
            return
        history.setdefault(user_id, []).append("products_menu")
        show_products_menu(bot, msg)

    @bot.message_handler(func=lambda msg: msg.text == "🎮 شحن ألعاب و تطبيقات")
    def handle_games_menu(msg):
        history.setdefault(msg.from_user.id, []).append("games_menu")
        show_game_categories(bot, msg)

    @bot.message_handler(func=lambda msg: msg.text in [
        "🎯 شحن شدات ببجي العالمية", "🔥 شحن جواهر فري فاير", "🏏 تطبيق جواكر"])
    def game_handler(msg):
        category_map = {
            "🎯 شحن شدات ببجي العالمية": "PUBG",
            "🔥 شحن جواهر فري فاير": "FreeFire",
            "🏏 تطبيق جواكر": "Jawaker"
        }
        category = category_map[msg.text]
        history.setdefault(msg.from_user.id, []).append("product_options")
        show_product_options(bot, msg, category)
        user_orders[msg.from_user.id] = {"category": category}
