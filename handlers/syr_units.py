from telebot import types
from database.models.product import Product
from services.wallet_service import has_sufficient_balance, deduct_balance
from config import ADMIN_MAIN_ID

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
    Product(1010, "18312 وحدة", "سيرياتيل", 21790),
    Product(1011, "28763 وحدة", "سيرياتيل", 34000),
    Product(1012, "36912 وحدة", "سيرياتيل", 43925),
    Product(1013, "57526 وحدة", "سيرياتيل", 67881),
    Product(1014, "62320 وحدة", "سيرياتيل", 73538),
    Product(1015, "76701 وحدة", "سيرياتيل", 90516),
]

pending_syr_requests = {}
user_syr_states = {}

def start_syriatel_menu(bot, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for product in SYRIATEL_PRODUCTS:
        btn = types.KeyboardButton(f"{product.name} - {product.price:,} ل.س")
        markup.add(btn)
    markup.add(types.KeyboardButton("⬅️ رجوع"))
    bot.send_message(message.chat.id, "📦 اختر الكمية:", reply_markup=markup)
    user_syr_states[message.from_user.id] = {"step": "select_product"}

def register(bot, user_state):
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
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✔️ تأكيد", callback_data="syr_confirm"))
        kb.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="syr_cancel"))
        bot.send_message(
            msg.chat.id,
            f"❓ هل أنت متأكد من شراء {product.name} مقابل {product.price:,} ل.س؟\nالرقم: {number}",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "syr_cancel")
    def cancel_syr_order(call):
        user_syr_states.pop(call.from_user.id, None)
        bot.edit_message_text("🚫 تم إلغاء العملية.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "syr_confirm")
    def confirm_syr_order(call):
        user_id = call.from_user.id
        state = user_syr_states.pop(user_id, {})
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
            f"📦 النوع: رصيد سيرياتيل وحدات"
        )
        bot.edit_message_text(
            "✅ تم إرسال الطلب إلى الإدارة، بانتظار المعالجة.",
            call.message.chat.id, call.message.message_id
        )

    # تحديث حالة العودة
    user_state.update({uid: "products_menu" for uid in user_syr_states})
