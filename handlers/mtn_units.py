# handlers/mtn_units.py
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
]

# حالة المستخدم في سير عمل MTN
user_mtn_states = {}

def start_mtn_menu(bot, message):
    """عرض قائمة منتجات MTN للمستخدم"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for product in MTN_PRODUCTS:
        markup.add(types.KeyboardButton(f"{product.name} - {product.price:,} ل.س"))
    markup.add(types.KeyboardButton("⬅️ رجوع"))
    bot.send_message(message.chat.id, "📲 اختر كمية الوحدات من MTN:", reply_markup=markup)
    user_mtn_states[message.from_user.id] = {"step": "select_product"}

def register(bot, user_state):
    """ربط أزرار تحويل رصيد MTN ببوت تيليجرام"""
    @bot.message_handler(func=lambda msg: msg.text == "💳 تحويل رصيد ام تي ان")
    def open_mtn_menu(msg):
        user_id = msg.from_user.id
        user_state[user_id] = "mtn_transfer"           # تعيين الحالة الرئيسية
        start_mtn_menu(bot, msg)

    @bot.message_handler(func=lambda msg: user_mtn_states.get(msg.from_user.id, {}).get("step") == "select_product")
    def select_mtn_product(msg):
        user_id = msg.from_user.id
        for product in MTN_PRODUCTS:
            if f"{product.name} - {product.price:,} ل.س" == msg.text:
                user_mtn_states[user_id] = {"step": "enter_number", "product": product}
                bot.send_message(msg.chat.id, "📲 أدخل الرقم أو الكود الذي يبدأ بـ 094 أو 095 أو 096:")
                return
        bot.send_message(msg.chat.id, "⚠️ الرجاء اختيار منتج من القائمة.")

    @bot.message_handler(func=lambda msg: user_mtn_states.get(msg.from_user.id, {}).get("step") == "enter_number")
    def enter_mtn_number(msg):
        user_id = msg.from_user.id
        number = msg.text.strip()
        state = user_mtn_states[user_id]
        product = state["product"]

        if not has_sufficient_balance(user_id, product.price):
            bot.send_message(msg.chat.id, "❌ لا يوجد رصيد كافٍ في محفظتك.")
            user_mtn_states.pop(user_id, None)
            return

        # خصم الرصيد
        deduct_balance(user_id, product.price)

        # تحضير رسالة للإدارة
        admin_msg = (
            f"📥 طلب جديد من المستخدم {user_id}\n"
            f"👤 المنتج: {product.name} ({product.price:,} ل.س)\n"
            f"📞 الرقم: {number}\n"
            f"📦 النوع: رصيد MTN وحدات"
        )
        bot.send_message(ADMIN_MAIN_ID, admin_msg)

        # تأكيد للمستخدم
        bot.send_message(msg.chat.id, "✅ تم إرسال الطلب إلى الإدارة، بانتظار المعالجة.")

        # تنظيف الحالة وإرجاع المستخدم للقائمة الرئيسية للمنتجات
        user_mtn_states.pop(user_id, None)
        user_state[user_id] = "products_menu"
