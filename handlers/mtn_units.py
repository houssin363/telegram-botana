from telebot import types
from database.models.product import Product
from handlers.wallet_service import has_sufficient_balance, deduct_balance
from config import ADMIN_MAIN_ID

# منتجات MTN وحدات
MTN_PRODUCTS = [
    Product(2001, "1000 وحدة", "MTN", 1200),
    Product(2002, "5000 وحدة", "MTN", 6000),
    Product(2003, "7000 وحدة", "MTN", 8400),
    Product(2004, "10000 وحدة", "MTN", 12000),
    Product(2005, "15000 وحدة", "MTN", 18000),
    Product(2006, "20000 وحدة", "MTN", 24000),
    Product(2007, "23000 وحدة", "MTN", 27600),
    Product(2008, "30000 وحدة", "MTN", 36000),
    Product(2009, "36000 وحدة", "MTN", 43200),
    Product(2010, "40000 وحدة", "MTN", 47600),
    Product(2011, "46000 وحدة", "MTN", 54740),
    Product(2012, "50000 وحدة", "MTN", 59500),
    Product(2013, "60000 وحدة", "MTN", 70800),
    Product(2014, "75000 وحدة", "MTN", 88500),
    Product(2015, "100000 وحدة", "MTN", 118000),
]

pending_mtn_requests = {}
user_mtn_states = {}

def start_mtn_menu(bot, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for product in MTN_PRODUCTS:
        btn = types.KeyboardButton(f"{product.name} - {product.price:,} ل.س")
        markup.add(btn)
    markup.add(types.KeyboardButton("⬅️ رجوع"))
    bot.send_message(message.chat.id, "📦 اختر الكمية:", reply_markup=markup)
    user_mtn_states[message.from_user.id] = {"step": "select_product"}

def register(bot):

    @bot.message_handler(func=lambda msg: user_mtn_states.get(msg.from_user.id, {}).get("step") == "select_product")
    def select_mtn_product(msg):
        user_id = msg.from_user.id
        text = msg.text
        for product in MTN_PRODUCTS:
            if product.name in text:
                user_mtn_states[user_id]["product"] = product
                user_mtn_states[user_id]["step"] = "enter_number"
                bot.send_message(msg.chat.id,
                    "📲 أدخل الرقم أو الكود الذي يبدأ بـ 094 أو 095 أو 096:")
                return
        bot.send_message(msg.chat.id, "⚠️ الرجاء اختيار منتج من القائمة.")

    @bot.message_handler(func=lambda msg: user_mtn_states.get(msg.from_user.id, {}).get("step") == "enter_number")
    def enter_mtn_number(msg):
        user_id = msg.from_user.id
        number = msg.text.strip()
        user_mtn_states[user_id]["number"] = number
        product = user_mtn_states[user_id]["product"]
        summary = f"❓ هل أنت متأكد من شراء {product.name} مقابل {product.price:,} ل.س؟\nالرقم: {number}"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✔️ تأكيد", callback_data="mtn_confirm"))
        kb.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="mtn_cancel"))
        bot.send_message(msg.chat.id, summary, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "mtn_cancel")
    def cancel_mtn_order(call):
        user_mtn_states.pop(call.from_user.id, None)
        bot.edit_message_text("🚫 تم إلغاء العملية.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "mtn_confirm")
    def confirm_mtn_order(call):
        user_id = call.from_user.id
        state = user_mtn_states.get(user_id, {})
        product = state.get("product")
        number = state.get("number")

        if not has_sufficient_balance(user_id, product.price):
            bot.send_message(call.message.chat.id, "❌ لا يوجد رصيد كافٍ في محفظتك.")
            return

        deduct_balance(user_id, product.price)

        text = (
            f"📥 طلب جديد من {user_id}\n"
            f"👤 المنتج: {product.name} ({product.price:,} ل.س)\n"
            f"📞 الرقم: {number}\n"
            f"📦 النوع: رصيد أم تي أن وحدات"
        )
        bot.send_message(ADMIN_MAIN_ID, text)
        bot.edit_message_text("✅ تم إرسال الطلب إلى الإدارة، بانتظار المعالجة.",
                              call.message.chat.id, call.message.message_id)
        user_mtn_states.pop(user_id, None)
