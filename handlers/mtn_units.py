from telebot import types
from database.models.product import Product
from services.wallet_service import has_sufficient_balance, deduct_balance
from config import ADMIN_MAIN_ID

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

def register(bot, user_state):
    @bot.message_handler(func=lambda msg: msg.text == "رصيد أم تي إن وحدات")
    def start_mtn_menu(msg):
        user_id = msg.from_user.id
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for product in MTN_PRODUCTS:
            btn = types.KeyboardButton(f"{product.name} - {product.price:,} ل.س")
            markup.add(btn)
        markup.add(types.KeyboardButton("⬅️ رجوع"))
        bot.send_message(msg.chat.id, "📦 اختر الكمية:", reply_markup=markup)
        user_mtn_states[user_id] = {"step": "select_product"}

    @bot.message_handler(func=lambda msg: user_mtn_states.get(msg.from_user.id, {}).get("step") == "select_product" and "MTN" in msg.text)
    def select_mtn_product(msg):
        user_id = msg.from_user.id
        selected = next(p for p in MTN_PRODUCTS if f"{p.name} - {p.price:,} ل.س" == msg.text)
        user_mtn_states[user_id] = {"step": "enter_number", "product": selected}
        bot.send_message(msg.chat.id, "📲 أدخل الرقم أو الكود الذي يبدأ بـ 094 أو 095 أو 096:")

    @bot.message_handler(func=lambda msg: user_mtn_states.get(msg.from_user.id, {}).get("step") == "enter_number")
    def enter_mtn_number(msg):
        user_id = msg.from_user.id
        number = msg.text.strip()
        state = user_mtn_states[user_id]
        state["number"] = number
        product = state["product"]
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✔️ تأكيد", callback_data="mtn_confirm"))
        kb.add(types.InlineKeyboardButton("✏️ تعديل", callback_data="mtn_edit"))
        kb.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="mtn_cancel"))
        bot.send_message(
            msg.chat.id,
            f"❓ هل أنت متأكد من شراء {product.name} مقابل {product.price:,} ل.س؟\nالرقم: {number}",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "mtn_edit")
    def edit_mtn(call):
        user_id = call.from_user.id
        user_mtn_states[user_id]["step"] = "enter_number"
        bot.edit_message_text("📲 أعد إدخال الرقم أو الكود الجديد:", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "mtn_cancel")
    def cancel_mtn_order(call):
        user_mtn_states.pop(call.from_user.id, None)
        bot.edit_message_text("🚫 تم إلغاء العملية.", call.message.chat.id, call.message.message_id)

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
            f"📥 طلب جديد من {call.from_user.full_name} (`{user_id}`)\n"
            f"👤 المنتج: {product.name} ({product.price:,} ل.س)\n"
            f"📞 الرقم: {number}\n"
            f"📦 النوع: رصيد أم تي إن وحدات",
            parse_mode="Markdown"
        )
        bot.edit_message_text(
            "✅ تم إرسال الطلب إلى الإدارة، بانتظار المعالجة.",
            call.message.chat.id, call.message.message_id
        )
