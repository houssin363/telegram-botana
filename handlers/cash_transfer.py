# handlers/cash_transfer.py

from telebot import types
from config import ADMIN_MAIN_ID
from services.wallet_service import has_sufficient_balance, deduct_balance, get_balance
from handlers.wallet import register_user_if_not_exist
from handlers import keyboards
import logging

user_states = {}

def cash_transfer_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("تحويل إلى سيرياتيل كاش"),
        types.KeyboardButton("تحويل إلى أم تي إن كاش"),
        types.KeyboardButton("تحويل إلى شام كاش"),
        types.KeyboardButton("حوالة مالية عبر شركات"),
        types.KeyboardButton("⬅️ رجوع"),
        types.KeyboardButton("🔄 ابدأ من جديد")
    )
    return markup

def companies_transfer_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("شركة الهرم"),
        types.KeyboardButton("شركة الفؤاد"),
        types.KeyboardButton("شركة شخاشير"),
        types.KeyboardButton("⬅️ رجوع"),
        types.KeyboardButton("🔄 ابدأ من جديد")
    )
    return markup

def make_inline_buttons(*buttons):
    kb = types.InlineKeyboardMarkup()
    for text, data in buttons:
        kb.add(types.InlineKeyboardButton(text, callback_data=data))
    return kb

def calculate_commission(amount, commission_per_50000):
    blocks = amount // 50000
    remainder = amount % 50000
    commission = blocks * commission_per_50000
    if remainder > 0:
        commission += int(commission_per_50000 * (remainder / 50000))
    return commission

def start_cash_transfer(bot, message, history=None):
    user_id = message.from_user.id
    register_user_if_not_exist(user_id)
    if history is not None:
        history.setdefault(user_id, []).append("cash_menu")
    bot.send_message(message.chat.id, "📤 اختر نوع التحويل من محفظتك:", reply_markup=cash_transfer_menu())

def register(bot, history):
    # ========== الكاش العادي ==========
    @bot.message_handler(func=lambda msg: msg.text in [
        "تحويل إلى سيرياتيل كاش",
        "تحويل إلى أم تي إن كاش",
        "تحويل إلى شام كاش"
    ])
    def handle_cash_type(msg):
        user_id = msg.from_user.id
        cash_type = msg.text
        commission_per_50000 = 3500
        user_states[user_id] = {
            "step": "cash_notice",
            "cash_type": cash_type,
            "commission_per_50000": commission_per_50000
        }
        kb = make_inline_buttons(
            ("❌ إلغاء", "cash_cancel_main"),
            ("✔️ تأكيد", "cash_notice_confirm")
        )
        bot.send_message(
            msg.chat.id,
            f"💡 العمولة لكل 50000 ل.س = 3500 ل.س.\n\nهل تريد المتابعة؟",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "cash_cancel_main")
    def cash_cancel_main(call):
        user_id = call.from_user.id
        user_states.pop(user_id, None)
        bot.edit_message_text("✅ عدت للقائمة الرئيسية.", call.message.chat.id, call.message.message_id,
                              reply_markup=cash_transfer_menu())

    @bot.callback_query_handler(func=lambda call: call.data == "cash_notice_confirm")
    def cash_notice_confirm(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_number"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cash_cancel_main")
        )
        bot.edit_message_text("📲 أكتب الرقم المراد التحويل له:", call.message.chat.id, call.message.message_id, reply_markup=kb)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_number")
    def get_target_number(msg):
        user_id = msg.from_user.id
        user_states[user_id]["number"] = msg.text
        user_states[user_id]["step"] = "confirm_number"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cash_cancel_main"),
            ("✏️ تعديل", "cash_edit_number"),
            ("✔️ تأكيد", "cash_number_confirm")
        )
        bot.send_message(
            msg.chat.id,
            f"الرقم المدخل: {msg.text}\n\nهل تريد المتابعة؟",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "cash_edit_number")
    def cash_edit_number(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_number"
        bot.send_message(call.message.chat.id, "📲 أعد كتابة الرقم المراد التحويل له:")

    @bot.callback_query_handler(func=lambda call: call.data == "cash_number_confirm")
    def cash_number_confirm(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_amount"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cash_cancel_main")
        )
        bot.edit_message_text("💰 اكتب المبلغ الذي تريد صرفه من المحفظة:", call.message.chat.id, call.message.message_id, reply_markup=kb)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_amount")
    def get_amount(msg):
        user_id = msg.from_user.id
        try:
            amount = int(msg.text)
            if amount <= 0:
                raise ValueError
        except Exception:
            bot.send_message(msg.chat.id, "⚠️ الرجاء إدخال مبلغ صحيح بالأرقام.")
            return

        state = user_states[user_id]
        commission = calculate_commission(amount, state["commission_per_50000"])
        total = amount + commission
        state["amount"] = amount
        state["commission"] = commission
        state["total"] = total
        state["step"] = "confirm_amount"

        kb = make_inline_buttons(
            ("❌ إلغاء", "cash_cancel_main"),
            ("✏️ تعديل", "cash_edit_amount"),
            ("✔️ تأكيد", "cash_amount_confirm")
        )
        bot.send_message(
            msg.chat.id,
            f"المبلغ: {amount:,} ل.س\n"
            f"العمولة: {commission:,} ل.س\n"
            f"الإجمالي المطلوب خصمه: {total:,} ل.س\n\nهل أنت متأكد؟",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "cash_edit_amount")
    def cash_edit_amount(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_amount"
        bot.send_message(call.message.chat.id, "💰 أعد إدخال المبلغ:")

    @bot.callback_query_handler(func=lambda call: call.data == "cash_amount_confirm")
    def cash_amount_confirm(call):
        user_id = call.from_user.id
        state = user_states.get(user_id, {})
        total = state.get("total", 0)
        balance = get_balance(user_id)
        if balance < total:
            shortage = total - balance
            kb = make_inline_buttons(
                ("💳 شحن المحفظة", "recharge_wallet"),
                ("⬅️ رجوع", "cash_cancel_main")
            )
            bot.edit_message_text(
                f"❌ لا يوجد رصيد كافٍ في محفظتك.\n"
                f"المبلغ المطلوب: {total:,} ل.س\n"
                f"رصيدك الحالي: {balance:,} ل.س\n"
                f"المبلغ الناقص: {shortage:,} ل.س\n"
                "يرجى شحن المحفظة أو العودة للقائمة.",
                call.message.chat.id, call.message.message_id,
                reply_markup=kb
            )
            return

        # إرسال رسالة التأكيد النهائية
        kb = make_inline_buttons(
            ("✔️ تأكيد التحويل", "cash_confirm_final"),
            ("❌ إلغاء", "cash_cancel_main")
        )
        bot.edit_message_text(
            f"هل أنت متأكد من تحويل {state['amount']:,} ل.س إلى الرقم {state['number']}؟\n"
            f"سيتم خصم {state['total']:,} ل.س من محفظتك.",
            call.message.chat.id, call.message.message_id,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "cash_confirm_final")
    def cash_confirm_final(call):
        user_id = call.from_user.id
        state = user_states.get(user_id, {})
        total = state.get("total", 0)
        if not has_sufficient_balance(user_id, total):
            kb = make_inline_buttons(
                ("💳 شحن المحفظة", "recharge_wallet"),
                ("⬅️ رجوع", "cash_cancel_main")
            )
            bot.edit_message_text(
                f"❌ لا يوجد رصيد كافٍ في محفظتك.\nيرجى شحن المحفظة أو العودة للقائمة.",
                call.message.chat.id, call.message.message_id,
                reply_markup=kb
            )
            return

        # رسالة للعميل
        bot.edit_message_text("✅ طلبك قيد التنفيذ (من 1 إلى 3 دقائق).", call.message.chat.id, call.message.message_id)
        # رسالة للإدارة
        kb_admin = make_inline_buttons(
            ("✅ تأكيد العملية", f"admin_cash_accept_{user_id}_{total}"),
            ("❌ رفض العملية", f"admin_cash_reject_{user_id}")
        )
        balance = get_balance(user_id)
        message = (
            f"📤 طلب كاش جديد\n"
            f"👤 العميل: {call.from_user.first_name or ''} ({user_id})\n"
            f"💼 العملية: {state.get('cash_type')}\n"
            f"📲 الرقم: {state.get('number')}\n"
            f"💰 المبلغ المطلوب: {state.get('amount'):,} ل.س\n"
            f"🧾 العمولة: {state.get('commission'):,} ل.س\n"
            f"✅ الإجمالي المطلوب خصمه: {state.get('total'):,} ل.س\n"
            f"💳 رصيد العميل الحالي: {balance:,} ل.س"
        )
        bot.send_message(ADMIN_MAIN_ID, message, reply_markup=kb_admin)
        state["step"] = "waiting_admin"

    @bot.callback_query_handler(func=lambda call: call.data == "recharge_wallet")
    def show_recharge_methods(call):
        bot.send_message(call.message.chat.id, "💳 اختر طريقة شحن المحفظة:", reply_markup=keyboards.recharge_menu())

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
                return
            deduct_balance(user_id, total)
            bot.send_message(user_id, "✅ تم خصم المبلغ من محفظتك بنجاح.")
            bot.answer_callback_query(call.id, "✅ تم قبول الطلب")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
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
    try:
        if msg.content_type == "photo":
            file_id = msg.photo[-1].file_id
            caption = "❌ تم رفض طلبك من الإدارة."
            if msg.caption:
                caption += f"\n📝 السبب: {msg.caption}"
            bot.send_photo(user_id, file_id, caption=caption)
        else:
            reason = msg.text.strip() if msg.text else "بدون سبب"
            bot.send_message(user_id, f"❌ تم رفض طلب تحويل الكاش من الإدارة.\n📝 السبب: {reason}")
        bot.answer_callback_query(call.id, "❌ تم رفض الطلب")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception as ex:
        logging.exception("❌ خطأ في process_cash_rejection:")
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ أثناء إرسال سبب الرفض: {ex}")

    # ========== حوالة مالية عبر شركات ==========
    @bot.message_handler(func=lambda msg: msg.text == "حوالة مالية عبر شركات")
    def open_companies_menu(msg):
        user_id = msg.from_user.id
        user_states[user_id] = {"step": "choose_company"}
        bot.send_message(
            msg.chat.id,
            "🟢 اختر شركة الحوالة المالية:",
            reply_markup=companies_transfer_menu()
        )

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "choose_company" and msg.text in [
        "شركة الهرم", "شركة الفؤاد", "شركة شخاشير"
    ])
    def handle_company_choice(msg):
        user_id = msg.from_user.id
        company = msg.text
        commission_per_50000 = 1500
        user_states[user_id] = {
            "step": "fullname_company",
            "company": company,
            "commission_per_50000": commission_per_50000
        }
        kb = make_inline_buttons(
            ("❌ إلغاء", "cash_cancel_main"),
            ("✔️ تأكيد", "company_fullname_confirm")
        )
        bot.send_message(msg.chat.id, f"💡 العمولة لكل 50000 ل.س = 1500 ل.س.\n\n👤 أدخل اسم المستفيد كاملًا (الاسم - الكنية - أبن الأب):", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "company_fullname_confirm")
    def company_fullname_confirm(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "fullname_company"
        bot.send_message(call.message.chat.id, "👤 أعد إدخال اسم المستفيد:")

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "fullname_company")
    def get_fullname(msg):
        user_id = msg.from_user.id
        user_states[user_id]["fullname"] = msg.text.strip()
        user_states[user_id]["step"] = "phone_company"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cash_cancel_main"),
            ("✏️ تعديل", "company_edit_fullname"),
            ("✔️ تأكيد", "company_phone_confirm")
        )
        bot.send_message(msg.chat.id, f"الاسم المدخل: {msg.text.strip()}\n\nهل تريد المتابعة؟", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "company_edit_fullname")
    def company_edit_fullname(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "fullname_company"
        bot.send_message(call.message.chat.id, "👤 أعد إدخال اسم المستفيد:")

    @bot.callback_query_handler(func=lambda call: call.data == "company_phone_confirm")
    def company_phone_confirm(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "phone_company"
        bot.send_message(call.message.chat.id, "📱 أدخل رقم موبايل المستفيد:")

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "phone_company")
    def get_phone(msg):
        user_id = msg.from_user.id
        user_states[user_id]["phone"] = msg.text.strip()
        user_states[user_id]["step"] = "amount_company"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cash_cancel_main"),
            ("✏️ تعديل", "company_edit_phone"),
            ("✔️ تأكيد", "company_amount_confirm")
        )
        bot.send_message(msg.chat.id, f"رقم الموبايل المدخل: {msg.text.strip()}\n\nهل تريد المتابعة؟", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "company_edit_phone")
    def company_edit_phone(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "phone_company"
        bot.send_message(call.message.chat.id, "📱 أعد إدخال رقم موبايل المستفيد:")

    @bot
