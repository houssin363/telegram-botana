from telebot import types
from database.models.product import Product
from services.wallet_service import has_sufficient_balance, deduct_balance
from config import ADMIN_MAIN_ID

# ✅ منتجات سيرياتيل وحدات (قابلة للتعديل بسهولة)
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

user_syr_states = {}
pending_syr_requests = {}

def start_syriatel_menu(bot, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for product in SYRIATEL_PRODUCTS:
        btn = types.KeyboardButton(f"{product.name} - {product.price:,} ل.س")
        markup.add(btn)
    markup.add(types.KeyboardButton("⬅️ رجوع"))
    bot.send_message(message.chat.id, "📦 اختر كمية وحدات سيرياتيل:", reply_markup=markup)
    user_syr_states[message.from_user.id] = {"step": "select_product"}

def register(bot, user_state):

    @bot.message_handler(func=lambda msg: msg.text == "💳 تحويل رصيد سوري")
    def open_syr_menu(msg):
        start_syriatel_menu(bot, msg)

    @bot.message_handler(func=lambda msg: msg.text in [f"{p.name} - {p.price:,} ل.س" for p in SYRIATEL_PRODUCTS])
    def select_syriatel_product(msg):
        user_id = msg.from_user.id
        selected = next(p for p in SYRIATEL_PRODUCTS if f"{p.name} - {p.price:,} ل.س" == msg.text)
        user_syr_states[user_id] = {"step": "enter_number", "product": selected}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(types.KeyboardButton("⬅️ رجوع"))
        bot.send_message(
            msg.chat.id,
            "🔹 أرقام سيرياتيل تبدأ بـ 093 أو 098 أو 099\nيمكنك أيضا إرسال كود رقمك مباشرة.",
            reply_markup=kb
        )
        bot.send_message(msg.chat.id, "📲 أدخل الرقم أو الكود المراد التحويل له:")

    @bot.message_handler(func=lambda msg: msg.text == "⬅️ رجوع")
    def go_back(msg):
        user_id = msg.from_user.id
        # إذا كان المستخدم في حالة وحدات سيرياتيل يرجع للقائمة الأولى
        if user_syr_states.get(user_id):
            start_syriatel_menu(bot, msg)
            user_syr_states[user_id] = {"step": "select_product"}

    @bot.message_handler(func=lambda msg: user_syr_states.get(msg.from_user.id, {}).get("step") == "enter_number")
    def enter_syriatel_number(msg):
        user_id = msg.from_user.id
        number = msg.text.strip()
        state = user_syr_states[user_id]
        state["number"] = number
        product = state["product"]
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("⬅️ رجوع", callback_data="syr_back"),
            types.InlineKeyboardButton("✔️ تأكيد", callback_data="syr_confirm"),
        )
        bot.send_message(
            msg.chat.id,
            f"❓ هل أنت متأكد من شراء {product.name} مقابل {product.price:,} ل.س؟\n"
            f"📲 الرقم أو الكود: `{number}`",
            parse_mode="Markdown",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "syr_back")
    def back_step(call):
        user_id = call.from_user.id
        start_syriatel_menu(bot, call.message)
        user_syr_states[user_id] = {"step": "select_product"}
        bot.edit_message_text("🔙 رجعت لاختيار كمية الوحدات.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "syr_confirm")
    def confirm_syr_order(call):
        user_id = call.from_user.id
        state = user_syr_states.get(user_id, {})
        product = state.get("product")
        number = state.get("number", "")
        if not has_sufficient_balance(user_id, product.price):
            bot.send_message(call.message.chat.id, "❌ لا يوجد رصيد كافٍ في محفظتك.")
            return
        # يرسل للأدمن
        pending_syr_requests[user_id] = state
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("✅ تنفيذ", callback_data=f"syr_admin_ok_{user_id}"),
            types.InlineKeyboardButton("❌ رفض", callback_data=f"syr_admin_reject_{user_id}")
        )
        bot.send_message(
            ADMIN_MAIN_ID,
            f"🔸 طلب وحدات سيرياتيل\n"
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

    @bot.callback_query_handler(func=lambda call: call.data.startswith("syr_admin_ok_"))
    def syr_admin_ok(call):
        user_id = int(call.data.split("_")[-1])
        req = pending_syr_requests.pop(user_id, None)
        if not req:
            bot.answer_callback_query(call.id, "❌ الطلب غير موجود أو تم معالجته بالفعل.")
            return
        product = req["product"]
        number = req["number"]
        if not has_sufficient_balance(user_id, product.price):
            bot.send_message(call.message.chat.id, "⚠️ العميل لا يملك رصيد كافٍ حالياً، الطلب ألغي تلقائياً.")
            return
        deduct_balance(user_id, product.price, f"شراء {product.name} (سيرياتيل وحدات)")
        # أرسل للعميل
        bot.send_message(
            user_id,
            f"✅ تم تنفيذ طلبك وخصم {product.price:,} ل.س من محفظتك.\n"
            f"🔸 المنتج: {product.name}\n"
            f"📲 الرقم أو الكود: {number}",
        )
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("syr_admin_reject_"))
    def syr_admin_reject(call):
        user_id = int(call.data.split("_")[-1])
        req = pending_syr_requests.pop(user_id, None)
        if not req:
            bot.answer_callback_query(call.id, "❌ الطلب غير موجود أو تم معالجته بالفعل.")
            return
        msg = bot.send_message(call.message.chat.id, "📝 اكتب سبب الرفض لإرساله للعميل:")
        bot.register_next_step_handler(msg, lambda m: process_syr_admin_reject(m, user_id, call))

    def process_syr_admin_reject(msg, user_id, call):
        bot.send_message(user_id, f"❌ تم رفض طلب شراء وحدات سيرياتيل.\n📝 السبب: {msg.text}")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

