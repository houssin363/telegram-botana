from telebot import types
from datetime import datetime
from config import ADMINS, ADMIN_MAIN_ID
from handlers.wallet import update_balance, register_user_if_not_exist
import json
import os

SECRET_CODES_FILE = "data/secret_codes.json"
os.makedirs("data", exist_ok=True)

if not os.path.isfile(SECRET_CODES_FILE):
    with open(SECRET_CODES_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def load_code_operations():
    with open(SECRET_CODES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_code_operations(data):
    with open(SECRET_CODES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

VALID_SECRET_CODES = [
    "363836369", "36313251", "646460923",
    "91914096", "78708501", "06580193"
]

def register(bot, history):

    @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_add_"))
    def confirm_wallet_add(call):
        try:
            data_parts = call.data.split("_")
            user_id = int(data_parts[2])
            amount = float(data_parts[3])

            register_user_if_not_exist(user_id)
            update_balance(user_id, amount)

            bot.send_message(user_id, f"✅ تم إضافة {amount:,} ل.س إلى محفظتك بنجاح.")
            bot.answer_callback_query(call.id, "✅ تمت الموافقة")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(call.message.chat.id, f"✅ تم تأكيد العملية وإضافة الرصيد لليوزر `{user_id}`", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reject_add_"))
    def reject_wallet_add(call):
        user_id = int(call.data.split("_")[-1])
        bot.send_message(call.message.chat.id, "📝 اكتب سبب الرفض:")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: process_rejection(m, user_id, call))

    def process_rejection(msg, user_id, call):
        reason = msg.text.strip()
        bot.send_message(user_id, f"❌ تم رفض عملية الشحن.\n📝 السبب: {reason}")
        bot.answer_callback_query(call.id, "❌ تم رفض العملية")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    @bot.message_handler(commands=["تقرير_الوكلاء"])
    def generate_report(msg):
        if msg.from_user.id != ADMIN_MAIN_ID:
            return
        data = load_code_operations()
        if not data:
            bot.send_message(msg.chat.id, "📭 لا توجد أي عمليات تحويل عبر الأكواد بعد.")
            return

        report = "📊 تقرير عمليات الأكواد:\n"
        for code, operations in data.items():
            report += f"\n🔐 الكود: `{code}`\n"
            for entry in operations:
                user = entry["user"]
                amount = entry["amount"]
                date = entry["date"]
                report += f"▪️ {amount:,} ل.س | {date} | {user}\n"
        bot.send_message(msg.chat.id, report, parse_mode="Markdown")

    @bot.message_handler(func=lambda msg: msg.text == "🏪 وكلائنا")
    def handle_agents_entry(msg):
        history.setdefault(msg.from_user.id, []).append("agents_page")
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("⬅️ رجوع", "✅ متابعة")
        text = (
            "🏪 وكلاؤنا:\n\n"
            "📍 دمشق - ريف دمشق – قدسيا – صالة الببجي الاحترافية - 090000000\n"
            "📍 دمشق - الزاهرة الجديدة – محل الورد - 09111111\n"
            "📍 قدسيا – الساحة - 092000000\n"
            "📍 يعفور – محل الايهم - 093000000\n"
            "📍 قدسيا – الاحداث – موبيلاتي - 096000000\n\n"
            "✅ اضغط (متابعة) إذا كنت تملك كودًا سريًا من وكيل لإضافة رصيد لمحفظتك."
        )
        bot.send_message(msg.chat.id, text, reply_markup=keyboard)

    @bot.message_handler(func=lambda msg: msg.text == "✅ متابعة")
    def ask_for_secret_code(msg):
        history.setdefault(msg.from_user.id, []).append("enter_secret_code")
        bot.send_message(msg.chat.id, "🔐 أدخل الكود السري (لن يظهر في المحادثة):")
        bot.register_next_step_handler(msg, verify_code)

    def verify_code(msg):
        code = msg.text.strip()
        if code not in VALID_SECRET_CODES:
            bot.send_message(msg.chat.id, "❌ كود غير صحيح أو غير معتمد.")
            return
        bot.send_message(msg.chat.id, "💰 أدخل المبلغ الذي تريد تحويله للمحفظة:")
        bot.register_next_step_handler(msg, lambda m: confirm_amount(m, code))

    def confirm_amount(msg, code):
        try:
            amount = int(msg.text.strip())
        except:
            bot.send_message(msg.chat.id, "❌ الرجاء إدخال مبلغ صحيح.")
            return

        user = f"{msg.from_user.first_name} (@{msg.from_user.username or 'بدون_معرف'})"
        user_id = msg.from_user.id
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        data = load_code_operations()

        if code not in data:
            data[code] = []
        data[code].append({
            "user": user,
            "user_id": user_id,
            "amount": amount,
            "date": now
        })

        save_code_operations(data)

        register_user_if_not_exist(user_id)
        update_balance(user_id, amount)

        bot.send_message(msg.chat.id, f"✅ تم تحويل {amount:,} ل.س إلى محفظتك عبر وكيل.")
        bot.send_message(ADMIN_MAIN_ID, f"✅ تم شحن {amount:,} ل.س للمستخدم `{user_id}` عبر كود `{code}`", parse_mode="Markdown")
