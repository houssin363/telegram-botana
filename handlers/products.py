from telebot import types
from config import BOT_NAME, ADMIN_MAIN_ID
from handlers.wallet import users_wallet, register_user_if_not_exist
from handlers.recharge import start_recharge_menu
from handlers import keyboards  # كيبوردات موحدة

PRODUCTS = {
    "PUBG": [
        ("60 شدة", 0.89), ("325 شدة", 4.44), ("660 شدة", 8.85),
        ("1800 شدة", 22.09), ("3850 شدة", 43.24), ("8100 شدة", 86.31)
    ],
    "FreeFire": [
        ("100 جوهرة", 0.98), ("310 جوهرة", 2.49), ("520 جوهرة", 4.13),
        ("1060 جوهرة", 9.42), ("2180 جوهرة", 18.84)
    ],
    "Jawaker": [
        ("10000 توكنز", 1.34), ("15000 توكنز", 2.01), ("20000 توكنز", 2.68),
        ("30000 توكنز", 4.02), ("60000 توكنز", 8.04), ("120000 توكنز", 16.08)
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
    for label, usd_price in options:
        callback = f"select_{label.replace(' ', '').replace('،', '')}"
        text = f"{label}\n💵 {usd_price}$"
        keyboard.add(types.InlineKeyboardButton(text, callback_data=callback))
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

    @bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
    def capture_product_selection(call):
        user_id = call.from_user.id
        label_cleaned = call.data.split("select_")[1]
        order = user_orders.get(user_id)
        if not order:
            bot.answer_callback_query(call.id, "❌ حدث خطأ، يرجى إعادة المحاولة.")
            return
        category = order["category"]
        for name, usd_price in PRODUCTS.get(category, []):
            if label_cleaned in name.replace(" ", "").replace("،", ""):
                syp_price = convert_price_usd_to_syp(usd_price)
                order.update({
                    "product": name,
                    "usd_price": usd_price,
                    "price": syp_price
                })
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("❌ إلغاء الطلب", callback_data="cancel_order"))
                bot.send_message(call.message.chat.id, "🔢 الرجاء إدخال ID اللاعب:", reply_markup=keyboard)
                return

    @bot.message_handler(func=lambda msg: msg.from_user.id in user_orders and "product" in user_orders[msg.from_user.id] and "player_id" not in user_orders[msg.from_user.id])
    def confirm_player_id(msg):
        order = user_orders[msg.from_user.id]
        order["player_id"] = msg.text
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✅ تأكيد", callback_data="confirm_order"),
            types.InlineKeyboardButton("✏️ تعديل", callback_data="edit_order"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_order")
        )
        bot.send_message(msg.chat.id, f"📌 هل هذا هو ID اللاعب؟\n`{msg.text}`", parse_mode="Markdown", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data in ["confirm_order", "edit_order", "cancel_order"])
    def handle_order_confirmation(call):
        user_id = call.from_user.id
        order = user_orders.get(user_id)

        if call.data == "cancel_order":
            user_orders.pop(user_id, None)
            bot.send_message(call.message.chat.id, "❌ تم إلغاء الطلب.")
            return

        if call.data == "edit_order":
            order.pop("player_id", None)
            bot.send_message(call.message.chat.id, "✏️ أعد إدخال ID اللاعب:")
            return

        register_user_if_not_exist(user_id)
        balance = users_wallet.get(user_id, {}).get("balance", 0)
        if balance < order["price"]:
            missing = order["price"] - balance
            bot.send_message(
                call.message.chat.id,
                f"❌ لا يوجد رصيد كافٍ.\n💰 تحتاج إلى زيادة رصيدك بمقدار `{missing:,} ل.س` لإتمام العملية.",
                parse_mode="Markdown",
                reply_markup=keyboards.recharge_menu()
            )
            return

        product = order["product"]
        price = order["price"]
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(f"✅ نعم، شراء {product} ({price:,} ل.س)", callback_data="final_confirm"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_order")
        )
        bot.send_message(call.message.chat.id, f"🛒 هل أنت متأكد من شراء {product}؟", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data == "final_confirm")
    def send_order_to_admin(call):
        user_id = call.from_user.id
        order = user_orders.get(user_id)
        if not order or user_id in pending_orders:
            bot.send_message(call.message.chat.id, "⚠️ لا يمكن تنفيذ الطلب الآن.")
            return

        msg = (
            f"📩 طلب شراء جديد:\n"
            f"👤 الاسم: {call.from_user.first_name} | @{call.from_user.username or 'بدون اسم'}\n"
            f"🆔 ID: `{user_id}`\n"
            f"🎮 اللعبة: {order['category']}\n"
            f"📦 المنتج: {order['product']}\n"
            f"🆔 ID اللاعب: `{order['player_id']}`\n"
            f"💵 السعر: {order['price']:,} ل.س"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ تم التنفيذ", callback_data=f"approve_{user_id}"),
            types.InlineKeyboardButton("❌ رفض العملية", callback_data=f"reject_{user_id}")
        )

        bot.send_message(ADMIN_MAIN_ID, msg, parse_mode="Markdown", reply_markup=markup)
        bot.send_message(call.message.chat.id, "📨 تم إرسال طلبك للإدارة.")
        pending_orders.add(user_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
    def process_admin_decision(call):
        user_id = int(call.data.split("_")[1])
        order = user_orders.get(user_id)
        if not order:
            bot.send_message(call.message.chat.id, "❌ لا يوجد طلب بهذا الرقم.")
            return

        if call.data.startswith("approve_"):
            price = order["price"]
            balance = users_wallet.get(user_id, {}).get("balance", 0)
            if balance >= price:
                users_wallet[user_id]["balance"] -= price
                if "purchases" not in users_wallet[user_id]:
                    users_wallet[user_id]["purchases"] = []
                users_wallet[user_id]["purchases"].append(order["product"])
                bot.send_message(user_id, f"✅ تم تنفيذ طلبك: {order['product']}\n💰 تم خصم {price:,} ل.س.")
            else:
                bot.send_message(user_id, "❌ رصيدك غير كافٍ لتنفيذ الطلب.")
        else:
            bot.send_message(user_id, "❌ تم رفض طلبك من قبل الإدارة.")

        pending_orders.discard(user_id)
        user_orders.pop(user_id, None)

    @bot.message_handler(func=lambda msg: msg.text == "💳 شحن محفظتي")
    def open_recharge_menu(msg):
        start_recharge_menu(bot, msg, history)
