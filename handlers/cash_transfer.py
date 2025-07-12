from telebot import types
from config import ADMIN_MAIN_ID
from handlers.wallet import users_wallet, register_user_if_not_exist, update_balance
from handlers import keyboards

user_states = {}
user_requests = {}
pending_cash_requests = set()

COMMISSION_PER_50000 = 3500

def calculate_commission(amount):
    blocks = amount // 50000
    remainder = amount % 50000
    commission = blocks * COMMISSION_PER_50000
    if remainder > 0:
        commission += int(COMMISSION_PER_50000 * (remainder / 50000))
    return commission

def start_cash_transfer(bot, message, history=None):
    user_id = message.from_user.id
    register_user_if_not_exist(user_id)
    if history is not None:
        history.setdefault(user_id, []).append("cash_menu")

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("سيرياتيل كاش", "أم تي إن كاش", "شام كاش")
    kb.add("⬅️ رجوع", "🔄 ابدأ من جديد")

    bot.send_message(message.chat.id, "📤 اختر نوع التحويل من محفظتك:", reply_markup=kb)

def make_inline_buttons(*buttons):
    kb = types.InlineKeyboardMarkup()
    for text, data in buttons:
        kb.add(types.InlineKeyboardButton(text, callback_data=data))
    return kb

def register(bot, history):

    @bot.message_handler(func=lambda msg: msg.text == "🧧 تحويل كاش من محفظتك")
    def open_cash_menu(msg):
        start_cash_transfer(bot, msg, history)

    @bot.message_handler(func=lambda msg: msg.text in ["سيرياتيل كاش", "أم تي إن كاش", "شام كاش"])
    def handle_cash_type(msg):
        user_id = msg.from_user.id
        cash_type = msg.text
        user_states[user_id] = {"step": "show_commission", "cash_type": cash_type}
        history.setdefault(user_id, []).append("cash_menu")

        text = (
            "⚠️ تنويه:\n"
            "العمولة لكل 50000 ل.س هي 3500 ل.س.\n"
            "هل تريد المتابعة وكتابة الرقم أو الكود المراد التحويل له؟"
        )
        kb = make_inline_buttons(
            ("✅ موافق", "commission_confirm"),
            ("❌ إلغاء", "commission_cancel")
        )
        bot.send_message(msg.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "commission_cancel")
    def commission_cancel(call):
        user_id = call.from_user.id
        bot.edit_message_text("❌ تم إلغاء العملية.", call.message.chat.id, call.message.message_id)
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data == "commission_confirm")
    def commission_confirmed(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_number"
        bot.edit_message_text(
            "📲 أكتب الرقم أو الكود المراد التحويل له:",
            call.message.chat.id,
            call.message.message_id
            # لا أزرار هنا، يسمح للعميل بالكتابة بحرية
        )

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_number")
    def get_target_number(msg):
        user_id = msg.from_user.id
        number = msg.text.strip()
        if not number:
            bot.send_message(msg.chat.id, "❌ الرجاء إدخال رقم صحيح.")
            return

        user_states[user_id]["target_number"] = number
        user_states[user_id]["step"] = "awaiting_amount"  # ننتقل مباشرة لطلب المبلغ
        bot.send_message(
            msg.chat.id,
            "💰 الآن، أكتب المبلغ الذي تريد صرفه من المحفظة:"
            # بدون أزرار لكتابة المبلغ بحرية
        )

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_amount")
    def get_amount(msg):
        user_id = msg.from_user.id
        try:
            amount = int(msg.text.strip().replace(",", ""))
        except:
            bot.send_message(
                msg.chat.id,
                "❌ الرجاء إدخال مبلغ صحيح.",
                reply_markup=make_inline_buttons(
                    ("⬅️ رجوع", "cash_back"),
                    ("❌ إلغاء", "cash_cancel")
                )
            )
            return

        commission = calculate_commission(amount)
        total_deduction = amount + commission

        balance = users_wallet.get(user_id, {}).get("balance", 0)
        if balance < total_deduction:
            diff = total_deduction - balance
            bot.send_message(
                msg.chat.id,
                f"❌ رصيد محفظتك غير كافٍ، تحتاج إلى {diff:,} ل.س إضافية.",
                reply_markup=keyboards.wallet_menu()
            )
            user_states.pop(user_id, None)
            return

        user_states[user_id]["amount"] = amount
        user_states[user_id]["commission"] = commission
        user_states[user_id]["total_deduction"] = total_deduction
        user_states[user_id]["step"] = "awaiting_confirm"

        number = user_states[user_id]["target_number"]
        cash_type = user_states[user_id]["cash_type"]

        confirm_text = (
            f"⚠️ تأكيد التحويل:\n"
            f"هل أنت متأكد من تحويل {amount:,} ل.س إلى الرقم: {number}؟\n"
            f"سيتم خصم {total_deduction:,} ل.س (المبلغ + العمولة) من محفظتك.\n"
            f"نوع العملية: {cash_type}"
        )

        kb = make_inline_buttons(
            ("✅ موافق", "cash_confirm"),
            ("✏️ تعديل", "cash_edit"),
            ("❌ إلغاء", "cash_cancel")
        )
        bot.send_message(msg.chat.id, confirm_text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data in ["cash_confirm", "cash_cancel", "cash_edit"])
    def process_cash_confirmation(call):
        user_id = call.from_user.id
        if user_id not in user_states:
            bot.answer_callback_query(call.id, "❌ لم يتم العثور على طلب لتحويل الكاش.")
            return

        state = user_states[user_id]

        if call.data == "cash_cancel":
            bot.edit_message_text("❌ تم إلغاء عملية التحويل.", call.message.chat.id, call.message.message_id)
            user_states.pop(user_id, None)
            return

        if call.data == "cash_edit":
            user_states[user_id]["step"] = "awaiting_number"
            bot.edit_message_text(
                "📲 أعد كتابة الرقم أو الكود المراد التحويل له:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=make_inline_buttons(
                    ("❌ إلغاء", "cash_cancel"),
                    ("✅ موافق", "number_confirm")
                )
            )
            return

        amount = state["amount"]
        commission = state["commission"]
        total_deduction = state["total_deduction"]
        target_number = state["target_number"]
        cash_type = state["cash_type"]

        user_name = call.from_user.first_name
        user_telegram_id = user_id

        if users_wallet.get(user_id, {}).get("balance", 0) < total_deduction:
            bot.send_message(
                call.message.chat.id,
                "❌ رصيد محفظتك غير كافٍ لإتمام العملية، تم إلغاء الطلب."
            )
            user_states.pop(user_id, None)
            return

        if user_id in pending_cash_requests:
            bot.send_message(call.message.chat.id, "⚠️ لديك طلب تحويل كاش قيد الانتظار.")
            return

        pending_cash_requests.add(user_id)
        user_requests[user_id] = state.copy()

        msg_to_admin = (
            f"📢 طلب تحويل كاش جديد:\n"
            f"👤 المستخدم: {user_name}\n"
            f"🆔 المعرف: `{user_telegram_id}`\n"
            f"💸 نوع العملية: {cash_type}\n"
            f"🔢 الرقم/الكود: {target_number}\n"
            f"💰 المبلغ المطلوب: {amount:,} ل.س\n"
            f"💵 إجمالي الخصم (مع العمولة): {total_deduction:,} ل.س"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ تأكيد التنفيذ", callback_data=f"admin_confirm_{user_id}"),
            types.InlineKeyboardButton("❌ رفض العملية", callback_data=f"admin_reject_{user_id}")
        )

        bot.send_message(ADMIN_MAIN_ID, msg_to_admin, reply_markup=markup)
        bot.edit_message_text("⏳ تم إرسال طلبك إلى الإدارة، الرجاء الانتظار.", call.message.chat.id, call.message.message_id)
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_confirm_") or call.data.startswith("admin_reject_"))
    def admin_handle_decision(call):
        admin_id = call.from_user.id
        if admin_id != ADMIN_MAIN_ID:
            bot.answer_callback_query(call.id, "❌ هذا الأمر مخصص للأدمن فقط.")
            return

        user_id = int(call.data.split("_")[-1])
        if user_id not in pending_cash_requests:
            bot.send_message(call.message.chat.id, "❌ هذا الطلب غير موجود أو تم التعامل معه سابقًا.")
            return

        if call.data.startswith("admin_reject_"):
            bot.send_message(user_id, "❌ تم رفض طلب تحويل الكاش من قبل الإدارة.")
            bot.answer_callback_query(call.id, "❌ تم رفض العملية")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            pending_cash_requests.discard(user_id)
            user_requests.pop(user_id, None)
            return

        order = user_requests.get(user_id)
        if not order:
            bot.send_message(call.message.chat.id, "❌ لم يتم العثور على تفاصيل الطلب.")
            return

        total_deduction = order["total_deduction"]

        if users_wallet.get(user_id, {}).get("balance", 0) < total_deduction:
            bot.send_message(user_id, "❌ رصيدك غير كافٍ لتنفيذ الطلب.")
            bot.answer_callback_query(call.id, "❌ الرصيد غير كافٍ")
            pending_cash_requests.discard(user_id)
            user_requests.pop(user_id, None)
            return

        update_balance(user_id, -total_deduction)
        bot.send_message(user_id, f"✅ تم خصم {total_deduction:,} ل.س من محفظتك بنجاح.")
        bot.answer_callback_query(call.id, "✅ تم تنفيذ الطلب")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        pending_cash_requests.discard(user_id)
        user_requests.pop(user_id, None)
