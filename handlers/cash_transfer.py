# handlers/cash_transfer.py

from telebot import types
from config import ADMIN_MAIN_ID
from services.wallet_service import has_sufficient_balance, deduct_balance, get_balance
from handlers.wallet import register_user_if_not_exist
from handlers import keyboards
import logging

user_states = {}

# أنواع الكاش والعمولة الخاصة بها
CASH_TYPES = [
    ("تحويل إلى سيرياتيل كاش", 3500),
    ("تحويل إلى شام كاش", 3500),
    ("تحويل إلى أم تي إن كاش", 3500),
]

COMPANY_BUTTONS = [
    ("شركة الهرم", "alharam"),
    ("شركة الفؤاد", "alfouad"),
    ("شركة شخاشير", "shakhashir"),
]
COMPANY_COMMISSION = 1500  # لكل 50000

def calculate_commission(amount, commission_per_50000):
    blocks = amount // 50000
    remainder = amount % 50000
    commission = blocks * commission_per_50000
    if remainder > 0:
        commission += int(commission_per_50000 * (remainder / 50000))
    return commission

def make_inline_buttons(*buttons):
    kb = types.InlineKeyboardMarkup()
    for text, data in buttons:
        kb.add(types.InlineKeyboardButton(text, callback_data=data))
    return kb

def cash_transfer_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for cash_type, _ in CASH_TYPES:
        markup.add(types.KeyboardButton(cash_type))
    markup.add(types.KeyboardButton("حوالة مالية عبر شركات"))
    markup.add(types.KeyboardButton("⬅️ رجوع"))
    markup.add(types.KeyboardButton("🔄 ابدأ من جديد"))
    return markup

def companies_main_menu():
    kb = types.InlineKeyboardMarkup()
    for name, data in COMPANY_BUTTONS:
        kb.add(types.InlineKeyboardButton(name, callback_data=f"company_{data}"))
    kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="cancel_company"))
    return kb

def start_cash_transfer(bot, message, history=None):
    user_id = message.from_user.id
    register_user_if_not_exist(user_id)
    if history is not None:
        history.setdefault(user_id, []).append("cash_menu")
    bot.send_message(message.chat.id, "📤 اختر نوع التحويل من محفظتك:", reply_markup=cash_transfer_menu())

def register(bot, history):
    # ========== الكاش العادي ==========
    @bot.message_handler(func=lambda msg: msg.text == "🧧 تحويل كاش من محفظتك")
    def open_cash_menu(msg):
        start_cash_transfer(bot, msg, history)

    @bot.message_handler(func=lambda msg: msg.text in [t[0] for t in CASH_TYPES])
    def handle_cash_type(msg):
        user_id = msg.from_user.id
        cash_type = msg.text
        commission_per_50000 = next(comm for name, comm in CASH_TYPES if name == cash_type)
        user_states[user_id] = {
            "step": "awaiting_number",
            "cash_type": cash_type,
            "commission_per_50000": commission_per_50000
        }
        bot.send_message(msg.chat.id, "📲 أكتب الرقم أو الكود المراد التحويل له:")

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_number")
    def get_target_number(msg):
        user_id = msg.from_user.id
        user_states[user_id]["number"] = msg.text
        user_states[user_id]["step"] = "awaiting_amount"
        bot.send_message(msg.chat.id, "💰 اكتب المبلغ الذي تريد تحويله:")

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_amount")
    def get_amount_and_confirm(msg):
        user_id = msg.from_user.id
        try:
            amount = int(msg.text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(msg.chat.id, "⚠️ الرجاء إدخال مبلغ صحيح بالأرقام.")
            return

        state = user_states[user_id]
        commission = calculate_commission(amount, state["commission_per_50000"])
        total = amount + commission

        summary = (
            f"📤 تأكيد العملية:\n"
            f"📲 الرقم: {state['number']}\n"
            f"💸 المبلغ: {amount:,} ل.س\n"
            f"🧾 العمولة: {commission:,} ل.س\n"
            f"✅ الإجمالي: {total:,} ل.س\n"
            f"💼 الطريقة: {state['cash_type']}"
        )

        kb = make_inline_buttons(
            ("✔️ تأكيد", "cash_confirm"),
            ("✏️ تعديل", "cash_edit"),
            ("❌ إلغاء", "cash_cancel")
        )
        bot.send_message(msg.chat.id, summary, reply_markup=kb)
        state["amount"] = amount
        state["commission"] = commission
        state["total"] = total
        state["step"] = "confirming"

    @bot.callback_query_handler(func=lambda call: call.data == "cash_edit")
    def edit_transfer(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_number"
        bot.edit_message_text("✏️ أعد إدخال الرقم أو الكود المراد التحويل له:",
                              call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "cash_cancel")
    def cancel_transfer(call):
        user_id = call.from_user.id
        bot.edit_message_text("🚫 تم إلغاء الطلب.", call.message.chat.id, call.message.message_id)
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data == "cash_confirm")
    def confirm_transfer(call):
        user_id = call.from_user.id
        state = user_states.get(user_id, {})
        total = state.get("total")
        # تأكد من الرصيد قبل إرسال الطلب للإدارة
        if not has_sufficient_balance(user_id, total):
            kb = make_inline_buttons(
                ("💳 شحن المحفظة", "recharge_wallet"),
                ("⬅️ رجوع", "cash_cancel")
            )
            bot.send_message(
                call.message.chat.id,
                f"❌ لا يوجد رصيد كافٍ في محفظتك.\n💡 الرجاء شحن المحفظة بمبلغ {total:,} ل.س أو أكثر لإتمام العملية.",
                reply_markup=kb
            )
            return

        bot.edit_message_text("✅ تم إرسال طلبك بانتظار موافقة الإدارة.", call.message.chat.id, call.message.message_id)
        kb_admin = make_inline_buttons(
            ("✅ قبول", f"admin_cash_accept_{user_id}_{total}"),
            ("❌ رفض", f"admin_cash_reject_{user_id}")
        )
        balance = get_balance(user_id)
        message = (
            f"📤 طلب تحويل كاش جديد:\n"
            f"👤 المستخدم: {user_id}\n"
            f"💳 رصيده الحالي: {balance:,} ل.س\n"
            f"📲 الرقم: {state.get('number')}\n"
            f"💰 المبلغ: {state.get('amount'):,} ل.س\n"
            f"💼 الطريقة: {state.get('cash_type')}\n"
            f"🧾 العمولة: {state.get('commission'):,} ل.س\n"
            f"✅ الإجمالي: {state.get('total'):,} ل.س"
        )
        bot.send_message(ADMIN_MAIN_ID, message, reply_markup=kb_admin)
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data == "recharge_wallet")
    def show_recharge_methods(call):
        bot.send_message(call.message.chat.id, "💳 اختر طريقة شحن المحفظة:", reply_markup=keyboards.recharge_menu())

    # ========== منطق قبول/رفض الأدمن (كاش) ==========
    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_cash_accept_"))
    def admin_accept_cash_transfer(call):
        try:
            parts = call.data.split("_")
            user_id = int(parts[-2])
            total = int(parts[-1])

            if not has_sufficient_balance(user_id, total):
                bot.send_message(user_id, f"❌ فشل تحويل الكاش: لا يوجد رصيد كافٍ في محفظتك.")
                bot.answer_callback_query(call.id, "❌ لا يوجد رصيد كافٍ لدى العميل.")
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                bot.send_message(call.message.chat.id, f"❌ لا يوجد رصيد كافٍ لدى العميل `{user_id}`.", parse_mode="Markdown")
                return

            deduct_balance(user_id, total)
            bot.send_message(user_id, "✅ تم خصم المبلغ وتحويل الكاش بنجاح (موافقة الإدارة).")
            bot.answer_callback_query(call.id, "✅ تم قبول الطلب")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(call.message.chat.id, f"✅ تم قبول طلب الكاش وتم خصم المبلغ من المستخدم `{user_id}`", parse_mode="Markdown")
        except Exception as e:
            logging.exception("❌ خطأ عند قبول طلب كاش من الأدمن:")
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_cash_reject_"))
    def admin_reject_cash_transfer(call):
        try:
            user_id = int(call.data.split("_")[-1])
            bot.send_message(call.message.chat.id, "📝 اكتب سبب الرفض أو أرسل صورة:")
            bot.register_next_step_handler_by_chat_id(
                call.message.chat.id,
                lambda m: process_cash_rejection(m, user_id, call),
            )
        except Exception as e:
            logging.exception("❌ خطأ عند رفض طلب كاش من الأدمن:")
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ: {e}")

    def process_cash_rejection(msg, user_id, call):
        if msg.content_type == "photo":
            file_id = msg.photo[-1].file_id
            bot.send_photo(user_id, file_id, caption="❌ تم رفض طلبك من الإدارة. الصورة مرسلة من الدعم.")
        else:
            reason = msg.text.strip()
            bot.send_message(user_id, f"❌ تم رفض طلب تحويل الكاش من الإدارة.\n📝 السبب: {reason}")
        bot.answer_callback_query(call.id, "❌ تم رفض الطلب")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, f"❌ تم رفض طلب الكاش للمستخدم `{user_id}`", parse_mode="Markdown")

    # ========== حوالة مالية عبر شركات ==========
    @bot.message_handler(func=lambda msg: msg.text == "حوالة مالية عبر شركات")
    def open_companies_menu(msg):
        user_id = msg.from_user.id
        user_states[user_id] = {"step": "main_company"}
        bot.send_message(
            msg.chat.id,
            "🟢 اختر شركة الحوالة المالية:",
            reply_markup=companies_main_menu()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("company_"))
    def choose_company(call):
        user_id = call.from_user.id
        company_code = call.data.split("_")[1]
        company_name = next(n for n, d in COMPANY_BUTTONS if d == company_code)
        user_states[user_id] = {
            "step": "info_company",
            "company": company_name,
            "company_code": company_code
        }
        kb = make_inline_buttons(
            ("❌ إلغاء", "cancel_company"),
            ("✔️ تأكيد", "confirm_company")
        )
        bot.edit_message_text(
            f"🔸 هذه الخدمة تخولك إلى استلام حوالتك المالية عبر **{company_name}**.\n"
            f"💡 سيتم إضافة عمولة {COMPANY_COMMISSION} ل.س لكل 50000 ل.س.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_company")
    def cancel_company(call):
        user_id = call.from_user.id
        user_states.pop(user_id, None)
        bot.edit_message_text("تم الإلغاء، عدت إلى القائمة.", call.message.chat.id, call.message.message_id)
        # يمكنك إعادة المستخدم لقائمة المنتجات هنا إن أحببت

    @bot.callback_query_handler(func=lambda call: call.data == "confirm_company")
    def company_confirmed(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "fullname_company"
        bot.edit_message_text(
            "👤 أدخل اسم المستفيد كاملًا (الاسم - الكنية - أبن الأب):",
            call.message.chat.id, call.message.message_id
        )

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "fullname_company")
    def get_fullname(msg):
        user_id = msg.from_user.id
        user_states[user_id]["fullname"] = msg.text.strip()
        user_states[user_id]["step"] = "fullname_confirm_company"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cancel_company"),
            ("✏️ تعديل", "edit_fullname_company"),
            ("✔️ تأكيد", "confirm_fullname_company")
        )
        bot.send_message(
            msg.chat.id,
            f"الاسم المدخل: {msg.text.strip()}\n\nهل تريد المتابعة؟",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "edit_fullname_company")
    def edit_fullname(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "fullname_company"
        bot.send_message(call.message.chat.id, "👤 أعد إدخال اسم المستفيد (الاسم - الكنية - أبن الأب):")

    @bot.callback_query_handler(func=lambda call: call.data == "confirm_fullname_company")
    def confirm_fullname(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "phone_company"
        bot.send_message(
            call.message.chat.id,
            "📱 أدخل رقم موبايل المستفيد:"
        )

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "phone_company")
    def get_phone(msg):
        user_id = msg.from_user.id
        user_states[user_id]["phone"] = msg.text.strip()
        user_states[user_id]["step"] = "phone_confirm_company"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cancel_company"),
            ("✏️ تعديل", "edit_phone_company"),
            ("✔️ تأكيد", "confirm_phone_company")
        )
        bot.send_message(
            msg.chat.id,
            f"رقم الموبايل المدخل: {msg.text.strip()}\n\nهل تريد المتابعة؟",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "edit_phone_company")
    def edit_phone(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "phone_company"
        bot.send_message(call.message.chat.id, "📱 أعد إدخال رقم موبايل المستفيد:")

    @bot.callback_query_handler(func=lambda call: call.data == "confirm_phone_company")
    def confirm_phone(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "amount_company"
        bot.send_message(
            call.message.chat.id,
            "💸 أدخل المبلغ المراد إرساله (بالليرة السورية):"
        )

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "amount_company")
    def get_amount(msg):
        user_id = msg.from_user.id
        try:
            amount = int(msg.text.strip())
            if amount <= 0:
                raise ValueError
        except Exception:
            bot.send_message(msg.chat.id, "❌ الرجاء إدخال مبلغ صحيح.")
            return
        user_states[user_id]["amount"] = amount
        user_states[user_id]["step"] = "amount_confirm_company"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cancel_company"),
            ("✏️ تعديل", "edit_amount_company"),
            ("✔️ تأكيد", "confirm_amount_company")
        )
        bot.send_message(
            msg.chat.id,
            f"المبلغ المدخل: {amount:,} ل.س\n\nهل تريد المتابعة؟",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "edit_amount_company")
    def edit_amount(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "amount_company"
        bot.send_message(call.message.chat.id, "💸 أعد إدخال المبلغ:")

    @bot.callback_query_handler(func=lambda call: call.data == "confirm_amount_company")
    def confirm_amount(call):   # بدون أي مسافة زائدة هنا
    user_id = call.from_user.id
    state = user_states.get(user_id, {})
    company = state.get("company", "")
    fullname = state.get("fullname", "")
    phone = state.get("phone", "")
    amount = state.get("amount", 0)
    commission = calculate_commission(amount, COMPANY_COMMISSION)
    total = amount + commission
    user_states[user_id]["commission"] = commission
    user_states[user_id]["total"] = total

    kb = make_inline_buttons(
        ("❌ إلغاء", "cancel_company"),
        ("✏️ تعديل", "edit_final_company"),
        ("✔️ تأكيد", "send_request_company")
    )
    bot.send_message(
        call.message.chat.id,
        f"🟢 هل أنت متأكد من إرسال حوالة مالية قدرها {amount:,} ل.س\n"
        f"للمستلم {fullname} (رقم: {phone})؟\n"
        f"🧾 العمولة: {commission:,} ل.س\n"
        f"✅ الإجمالي: {total:,} ل.س",
        reply_markup=kb
    )


