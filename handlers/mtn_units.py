from telebot import types
from database.models.product import Product
from services.wallet_service import has_sufficient_balance, deduct_balance
from config import ADMIN_MAIN_ID

# منتجات MTN وحدات (قابلة للتعديل بسهولة)
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
pending_mtn_requests = {}

def start_mtn_units_menu(bot, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for product in MTN_PRODUCTS:
        btn = types.KeyboardButton(f"{product.name} - {product.price:,} ل.س")
        markup.add(btn)
    markup.add(types.KeyboardButton("⬅️ رجوع"))
    bot.send_message(message.chat.id, "📦 اختر كمية وحدات MTN:", reply_markup=markup)
    user_mtn_states[message.from_user.id] = {"step": "select_mtn"}

def register(bot, user_state):

    @bot.message_handler(func=lambda msg: msg.text == "💳 تحويل رصيد أم تي أن وحدات")
    def open_mtn_units_menu(msg):
        start_mtn_units_menu(bot, msg)

    @bot.message_handler(func=lambda msg: user_mtn_states.get(msg.from_user.id, {}).get("step") == "select_mtn"
                        and msg.text in [f"{p.name} - {p.price:,} ل.س" for p in MTN_PRODUCTS])
    def select_mtn_product(msg):
        user_id = msg.from_user.id
        selected = next(p for p in MTN_PRODUCTS if f"{p.name} - {p.price:,} ل.س" == msg.text)
        user_mtn_states[user_id] = {"step": "enter_number", "product": selected}
        note = (
            "🔹 أرقام MTN تبدأ بـ 094 أو 095 أو 096\n"
            "يمكنك أيضا إرسال كود رقمك مباشرة."
        )
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(types.KeyboardButton("⬅️ رجوع"))
        bot.send_message(msg.chat.id, note, reply_markup=kb)
        bot.send_message(msg.chat.id, "📲 أدخل الرقم أو الكود المراد التحويل له:")

    @bot.message_handler(func=lambda msg: user_mtn_states.get(msg.from_user.id, {}).get("step") == "enter_number")
    def enter_mtn_number(msg):
        user_id = msg.from_user.id
        state = user_mtn_states[user_id]
        number = msg.text.strip()
        product = state["product"]
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("⬅️ رجوع", callback_data="mtn_back"),
            types.InlineKeyboardButton("✔️ تأكيد", callback_data="mtn_confirm"),
        )
        bot.send_message(
            msg.chat.id,
            f"❓ هل أنت متأكد من شراء {product.name} مقابل {product.price:,} ل.س؟\n"
            f"📲 الرقم أو الكود: `{number}`",
            parse_mode="Markdown",
            reply_markup=kb
        )
        state["number"] = number

    @bot.callback_query_handler(func=lambda call: call.data == "mtn_back")
    def mtn_back(call):
        user_id = call.from_user.id
        start_mtn_units_menu(bot, call.message)
        bot.edit_message_text("🔙 رجعت لاختيار كمية الوحدات.", call.message.chat.id, call.message.message_id)
        user_mtn_states[user_id] = {"step": "select_mtn"}

    @bot.callback_query_handler(func=lambda call: call.data == "mtn_confirm")
    def mtn_confirm(call):
        user_id = call.from_user.id
        state = user_mtn_states.get(user_id, {})
        product = state.get("product")
        number = state.get("number", "")
        if not has_sufficient_balance(user_id, product.price):
            bot.send_message(call.message.chat.id, "❌ لا يوجد رصيد كافٍ في محفظتك.")
            return
        pending_mtn_requests[user_id] = state
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("✅ تنفيذ", callback_data=f"mtn_admin_ok_{user_id}"),
            types.InlineKeyboardButton("❌ رفض", callback_data=f"mtn_admin_reject_{user_id}")
        )
        bot.send_message(
            ADMIN_MAIN_ID,
            f"🔸 طلب وحدات MTN\n"
            f"👤 المستخدم: {call.from_user.full_name} (@{call.from_user.username})\n"
            f"🆔 آيدي: `{user_id}`\n"
            f"📦 المنتج: {product.name}\n"
            f"💰 السعر: {product.price:,} ل.س\n"
            f"📲 الرقم أو الكود: `{number}`",
            parse_mode="Markdown",
            reply_markup=kb
        )
        bot.edit_message_text(
            "✅ تم إرسال الطلب للإدارة، بانتظار المعالجة.",
            call.message.chat.id, call.message.message_id
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("mtn_admin_ok_"))
    def mtn_admin_ok(call):
        user_id = int(call.data.split("_")[-1])
        req = pending_mtn_requests.pop(user_id, None)
        if not req:
            bot.answer_callback_query(call.id, "❌ الطلب غير موجود أو تم معالجته بالفعل.")
            return
        product = req["product"]
        number = req["number"]
        if not has_sufficient_balance(user_id, product.price):
            bot.send_message(call.message.chat.id, "⚠️ العميل لا يملك رصيد كافٍ حالياً، الطلب ألغي تلقائياً.")
            return
        deduct_balance(user_id, product.price, f"شراء {product.name} (MTN وحدات)")
        # أرسل للعميل
        bot.send_message(
            user_id,
            f"✅ تم تنفيذ طلبك وخصم {product.price:,} ل.س من محفظتك.\n"
            f"🔸 المنتج: {product.name} (MTN)\n"
            f"📲 الرقم أو الكود: {number}",
        )
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("mtn_admin_reject_"))
    def mtn_admin_reject(call):
        user_id = int(call.data.split("_")[-1])
        req = pending_mtn_requests.pop(user_id, None)
        if not req:
            bot.answer_callback_query(call.id, "❌ الطلب غير موجود أو تم معالجته بالفعل.")
            return
        msg = bot.send_message(call.message.chat.id, "📝 اكتب سبب الرفض لإرساله للعميل:")
        bot.register_next_step_handler(msg, lambda m: process_mtn_admin_reject(m, user_id, call))

    def process_mtn_admin_reject(msg, user_id, call):
        bot.send_message(user_id, f"❌ تم رفض طلب شراء الوحدات.\n📝 السبب: {msg.text}")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

