from telebot import types
from database.models.product import Product
from services.wallet_service import has_sufficient_balance, deduct_balance
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

user_mtn_states = {}

def start_mtn_units_menu(bot, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for product in MTN_PRODUCTS:
        btn = types.KeyboardButton(f"{product.name} - {product.price:,} ل.س")
        markup.add(btn)
    markup.add(types.KeyboardButton("⬅️ رجوع"))
    bot.send_message(message.chat.id, "📦 اختر الكمية:", reply_markup=markup)
    user_mtn_states[message.from_user.id] = {"step": "select_product"}

def register(bot, user_state):
    @bot.message_handler(func=lambda msg: msg.text == "رصيد أم تي إن وحدات")
    def menu_handler(msg):
        start_mtn_units_menu(bot, msg)

    @bot.message_handler(func=lambda msg: msg.text in [f"{p.name} - {p.price:,} ل.س" for p in MTN_PRODUCTS])
    def select_mtn_product(msg):
        user_id = msg.from_user.id
        selected = next(p for p in MTN_PRODUCTS if f"{p.name} - {p.price:,} ل.س" == msg.text)
        user_mtn_states[user_id] = {"step": "enter_number", "product": selected}
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="mtn_back"))
        bot.send_message(msg.chat.id, "📲 أدخل الرقم أو الكود (يبدأ بـ 094 أو 095 أو 096):", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "mtn_back")
    def back_to_menu(call):
        start_mtn_units_menu(bot, call.message)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    @bot.message_handler(func=lambda msg: user_mtn_states.get(msg.from_user.id, {}).get("step") == "enter_number")
    def enter_mtn_number(msg):
        user_id = msg.from_user.id
        number = msg.text.strip()
        state = user_mtn_states[user_id]
        state["number"] = number
        product = state["product"]
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✔️ تأكيد", callback_data="mtn_confirm"))
        kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="mtn_back"))
        bot.send_message(
            msg.chat.id,
            f"❓ هل أنت متأكد من شراء {product.name} مقابل {product.price:,} ل.س؟\nالرقم: {number}",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "mtn_confirm")
    def confirm_mtn_order(call):
        user_id = call.from_user.id
        state = user_mtn_states.pop(user_id, {})
        product = state.get("product")
        number = state.get("number", "")
        if not has_sufficient_balance(user_id, product.price):
            bot.send_message(call.message.chat.id, "❌ لا يوجد رصيد كافٍ في محفظتك.")
            return
        deduct_balance(user_id, product.price)
        bot.send_message(
            ADMIN_MAIN_ID,
            f"📥 طلب جديد من {user_id}\n"
            f"👤 المنتج: {product.name} ({product.price:,} ل.س)\n"
            f"📞 الرقم: {number}\n"
            f"📦 النوع: رصيد أم تي إن وحدات"
        )
        bot.edit_message_text(
            "✅ تم إرسال الطلب إلى الإدارة، بانتظار المعالجة.",
            call.message.chat.id, call.message.message_id
        )

    # تحديث حالة العودة
    user_state.update({uid: "products_menu" for uid in user_mtn_states})
