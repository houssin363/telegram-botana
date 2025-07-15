# handlers/internet_providers.py
from telebot import types
from database.models.product import Product
from services.wallet_service import has_sufficient_balance, deduct_balance
from config import ADMIN_MAIN_ID

INTERNET_PROVIDERS = [
    "تراسل", "أم تي أن", "سيرياتيل", "آية", "سوا", "رن نت", "سما نت", "أمنية",
    "ناس", "هايبر نت", "MTS", "يارا", "دنيا", "آينت"
]

INTERNET_SPEEDS = [
    {"label": "1 ميغا", "price": 19500},
    {"label": "2 ميغا", "price": 25000},
    {"label": "4 ميغا", "price": 39000},
    {"label": "8 ميغا", "price": 65000},
    {"label": "16 ميغا", "price": 84000},
]

COMMISSION_PER_5000 = 600
user_net_state = {}

def start_internet_provider_menu(bot, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for name in INTERNET_PROVIDERS:
        markup.add(types.KeyboardButton(f"🌐 مزود انترنت {name}"))
    markup.add(types.KeyboardButton("⬅️ رجوع"))
    bot.send_message(
        message.chat.id,
        "⚠️ اختر أحد مزودات الإنترنت:\n💸 العمولة لكل 5000 ل.س = 600 ل.س",
        reply_markup=markup
    )
    user_net_state[message.from_user.id] = {"step": "choose_provider"}

def calculate_commission(amount):
    blocks = amount // 5000
    remainder = amount % 5000
    commission = blocks * COMMISSION_PER_5000
    if remainder > 0:
        commission += int(COMMISSION_PER_5000 * (remainder / 5000))
    return commission

def register(bot):
    @bot.message_handler(func=lambda msg: msg.text == "🌐 دفع مزودات الإنترنت ADSL")
    def open_net_menu(msg):
        start_internet_provider_menu(bot, msg)

    @bot.message_handler(func=lambda msg: user_net_state.get(msg.from_user.id, {}).get("step") == "choose_provider")
    def handle_provider_choice(msg):
        user_id = msg.from_user.id
        provider = msg.text.replace("🌐 مزود انترنت ", "")
        if provider not in INTERNET_PROVIDERS:
            return bot.send_message(msg.chat.id, "⚠️ يرجى اختيار مزود صحيح من القائمة.")
        user_net_state[user_id]["provider"] = provider
        user_net_state[user_id]["step"] = "choose_speed"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for speed in INTERNET_SPEEDS:
            markup.add(types.KeyboardButton(f"{speed['label']} - {speed['price']:,} ل.س"))
        markup.add(types.KeyboardButton("⬅️ رجوع"))
        bot.send_message(
            msg.chat.id,
            "⚡ اختر السرعة المطلوبة:\n💸 العمولة لكل 5000 ل.س = 600 ل.س",
            reply_markup=markup
        )

    # ... (rest of your existing handlers for choose_speed, enter_phone, confirm, etc.)
