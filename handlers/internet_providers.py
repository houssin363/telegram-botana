from telebot import types
from database.models.product import Product
from handlers.wallet_service import has_sufficient_balance, deduct_balance
from config import ADMIN_MAIN_ID

INTERNET_PROVIDERS = [
    "تراسل", "أم تي أن", "سيرياتيل", "آية", "سوا", "رن نت", "سما نت", "أمنية",
    "ناس", "هايبر نت", "MTS", "ناس", "يارا", "دنيا", "آينت"
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
    bot.send_message(message.chat.id, "⚠️ اختر أحد مزودات الانترنت التالية.\n💸 عمولة التحويل لكل 10000 ل.س = 1000 ل.س", reply_markup=markup)
    user_net_state[message.from_user.id] = {"step": "choose_provider"}

def register(bot):

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

        bot.send_message(msg.chat.id, "⚡ اختر السرعة المطلوبة:\n💸 العمولة لكل 5000 ل.س = 600 ل.س", reply_markup=markup)

    @bot.message_handler(func=lambda msg: user_net_state.get(msg.from_user.id, {}).get("step") == "choose_speed")
    def handle_speed_choice(msg):
        user_id = msg.from_user.id
        selected = msg.text.split(" - ")[0].strip()
        speed_obj = next((s for s in INTERNET_SPEEDS if s["label"] == selected), None)
        if not speed_obj:
            return bot.send_message(msg.chat.id, "⚠️ يرجى اختيار سرعة من القائمة.")
        user_net_state[user_id]["speed"] = speed_obj
        user_net_state[user_id]["step"] = "enter_phone"
        bot.send_message(msg.chat.id, "📞 أدخل رقم الدفع مرفق برمز المحافظة:")

    @bot.message_handler(func=lambda msg: user_net_state.get(msg.from_user.id, {}).get("step") == "enter_phone")
    def enter_phone_number(msg):
        user_id = msg.from_user.id
        number = msg.text.strip()
        user_net_state[user_id]["number"] = number
        speed = user_net_state[user_id]["speed"]
        commission = calculate_commission(speed["price"])
        total = speed["price"] + commission

        user_net_state[user_id]["commission"] = commission
        user_net_state[user_id]["total"] = total

        text = (
            f"❓ هل أنت متأكد من شراء اشتراك مزود انترنت؟\n"
            f"🔹 المزود: {user_net_state[user_id]['provider']}\n"
            f"⚡ السرعة: {speed['label']}\n"
            f"📞 الرقم: {number}\n"
            f"💵 السعر: {speed['price']:,} + عمولة {commission:,} = {total:,} ل.س"
        )

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✔️ تأكيد", callback_data="net_confirm"))
        kb.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="net_cancel"))
        bot.send_message(msg.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "net_cancel")
    def cancel_net_order(call):
        user_net_state.pop(call.from_user.id, None)
        bot.edit_message_text("🚫 تم إلغاء العملية.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "net_confirm")
    def confirm_net_order(call):
        user_id = call.from_user.id
        state = user_net_state.get(user_id, {})
        total = state.get("total")

        if not has_sufficient_balance(user_id, total):
            bot.send_message(call.message.chat.id, "❌ لا يوجد رصيد كافٍ في محفظتك.")
            return

        deduct_balance(user_id, total)

        msg = (
            f"🌐 طلب اشتراك مزود انترنت جديد:\n"
            f"👤 المستخدم: {user_id}\n"
            f"🏢 المزود: {state['provider']}\n"
            f"⚡ السرعة: {state['speed']['label']}\n"
            f"📞 الرقم: {state['number']}\n"
            f"💰 السعر: {state['speed']['price']:,} + عمولة {state['commission']:,} = {total:,} ل.س"
        )

        bot.send_message(ADMIN_MAIN_ID, msg)
        bot.edit_message_text("✅ تم إرسال الطلب للإدارة.", call.message.chat.id, call.message.message_id)
        user_net_state.pop(user_id, None)

def calculate_commission(amount):
    blocks = amount // 5000
    remainder = amount % 5000
    commission = blocks * COMMISSION_PER_5000
    if remainder > 0:
        commission += int(COMMISSION_PER_5000 * (remainder / 5000))
    return commission
