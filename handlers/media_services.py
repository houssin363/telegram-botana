from telebot import types
from config import ADMIN_MAIN_ID
from handlers.wallet_service import has_sufficient_balance, deduct_balance

user_media_state = {}

# سعر الدولار للمنتجات المتعلقة بالتصميم (يتم تعديله لاحقًا من config أو ديناميكياً)
USD_RATE = 11000

# المنتجات الثابتة وأسعارها بالدولار (يمكن تعديلها)
MEDIA_PRODUCTS = {
    "🖼️ تصميم لوغو احترافي": 300,
    "📱 إدارة ونشر يومي": 300,
    "📢 إطلاق حملة إعلانية": 300,
    "🧾 باقة متكاملة شهرية": 300,
    "✏️ طلب مخصص": 0  # يتم تحديد السعر لاحقاً
}

def show_media_services(bot, message, user_state):
    user_state[message.from_user.id] = "media_services"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for name in MEDIA_PRODUCTS.keys():
        markup.add(types.KeyboardButton(name))
    markup.add(types.KeyboardButton("⬅️ رجوع"))
    bot.send_message(message.chat.id, "🎨 اختر الخدمة المطلوبة:", reply_markup=markup)

def register(bot, user_state):

    @bot.message_handler(func=lambda msg: msg.text in MEDIA_PRODUCTS)
    def handle_selected_service(msg):
        user_id = msg.from_user.id
        service = msg.text
        user_media_state[user_id] = {
            "step": "details",
            "service": service
        }

        if MEDIA_PRODUCTS[service] == 0:
            bot.send_message(msg.chat.id, f"✏️ يرجى كتابة تفاصيل الطلب المخصص بشكل كامل:")
        else:
            price_usd = MEDIA_PRODUCTS[service]
            price_lbp = price_usd * USD_RATE
            user_media_state[user_id]["price"] = price_lbp
            bot.send_message(msg.chat.id,
                f"🔧 تفاصيل الطلب: {service}\n"
                f"💵 السعر المقدر: {price_lbp:,} ل.س\n"
                f"📝 يرجى الآن كتابة أي تفاصيل تريد إضافتها (مثلاً: اسم الصفحة، المجال، أفكار التصميم...)")

    @bot.message_handler(func=lambda msg: user_media_state.get(msg.from_user.id, {}).get("step") == "details")
    def handle_media_details(msg):
        user_id = msg.from_user.id
        state = user_media_state[user_id]
        service = state["service"]
        details = msg.text.strip()
        price_lbp = state.get("price", 0)

        text = (
            f"❓ هل تريد طلب خدمة:\n"
            f"📦 {service}\n"
            f"💬 التفاصيل: {details}\n"
        )

        if price_lbp:
            text += f"💰 السعر: {price_lbp:,} ل.س"

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✔️ تأكيد", callback_data="media_confirm"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="media_cancel")
        )

        user_media_state[user_id]["details"] = details
        user_state[user_id] = "media_services"
        bot.send_message(msg.chat.id, text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data in ["media_cancel", "media_confirm"])
    def process_media_action(call):
        user_id = call.from_user.id
        state = user_media_state.get(user_id)
        if not state:
            return

        if call.data == "media_cancel":
            bot.edit_message_text("🚫 تم إلغاء الطلب.", call.message.chat.id, call.message.message_id)
            user_media_state.pop(user_id, None)
            return

        service = state["service"]
        details = state["details"]
        price = state.get("price", 0)

        if price > 0 and not has_sufficient_balance(user_id, price):
            bot.send_message(call.message.chat.id, "❌ لا يوجد رصيد كافٍ في محفظتك.")
            return

        if price > 0:
            deduct_balance(user_id, price)

        text = (
            f"📥 طلب خدمة جديدة:\n"
            f"👤 المستخدم: {user_id}\n"
            f"📦 الخدمة: {service}\n"
            f"💬 التفاصيل: {details}\n"
        )
        if price > 0:
            text += f"💰 تم خصم: {price:,} ل.س من محفظته."

        bot.send_message(ADMIN_MAIN_ID, text)
        bot.edit_message_text("✅ تم إرسال طلبك للإدارة، سيتم التواصل معك قريبًا.",
                              call.message.chat.id, call.message.message_id)
        user_media_state.pop(user_id, None)
