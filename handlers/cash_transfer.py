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
            "step": "awaiting_number",
            "cash_type": cash_type,
            "commission_per_50000": commission_per_50000
        }
        bot.send_message(
            msg.chat.id,
            f"💡 تنويه: العمولة لكل 50000 ل.س هي 3500 ل.س.\n\n📲 أكتب الرقم المراد التحويل له:"
        )

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_number")
    def get_target_number(msg):
        user_id = msg.from_user.id
        user_states[user_id]["number"] = msg.text
        user_states[user_id]["step"] = "awaiting_amount"
        bot.send_message(msg.chat.id, "💰 اكتب المبلغ الذي تريد صرفه من المحفظة:")

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
        state["amount"] = amount
        state["commission"] = commission
        state["total"] = total
        state["step"] = "confirming"

        if not has_sufficient_balance(user_id, total):
            kb = make_inline_buttons(
                ("💳 شحن المحفظة", "recharge_wallet"),
                ("⬅️ رجوع", "cash_cancel")
            )
            bot.send_message(
                msg.chat.id,
                f"❌ لا يوجد رصيد كافٍ في محفظتك.\n💡 يجب شحن محفظتك بمبلغ {total:,} ل.س أو أكثر.\n",
                reply_markup=kb
            )
            return

        summary = (
            f"📤 تأكيد العملية:\n"
            f"📲 الرقم: {state['number']}\n"
            f"💸 المبلغ: {amount:,} ل.س\n"
            f"🧾 العمولة: {commission:,} ل.س\n"
            f"✅ سيتم خصم {total:,} ل.س من محفظتك.\n"
            f"💼 الطريقة: {state['cash_type']}"
        )
        kb = make_inline_buttons(
            ("✔️ تأكيد", "cash_confirm"),
            ("❌ إلغاء", "cash_cancel")
        )
        bot.send_message(msg.chat.id, summary, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "cash_cancel")
    def cancel_transfer(call):
        user_id = call.from_user.id
        user_states.pop(user_id, None)
        bot.edit_message_text("🚫 تم إلغاء الطلب.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "cash_confirm")
    def confirm_transfer(call):
        user_id = call.from_user.id
        state = user_states.get(user_id, {})
        total = state.get("total")
        if not has_sufficient_balance(user_id, total):
            kb = make_inline_buttons(
                ("💳 شحن المحفظة", "recharge_wallet"),
                ("⬅️ رجوع", "cash_cancel")
            )
            bot.send_message(
                call.message.chat.id,
                f"❌ لا يوجد رصيد كافٍ في محفظتك.\n💡 يجب شحن محفظتك بمبلغ {total:,} ل.س أو أكثر.\n",
                reply_markup=kb
            )
            return

        # رسالة للعميل
        bot.edit_message_text("✅ طلبك قيد التنفيذ (الموقت المتوقع من 1 إلى 3 دقائق).", call.message.chat.id, call.message.message_id)
        # رسالة للأدمن
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

    # قبول/رفض الأدمن لطلبات الكاش
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

    # ========== الحوالات عبر شركات ==========
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
        bot.send_message(msg.chat.id, f"💡 تنويه: العمولة لكل 50000 ل.س هي 1500 ل.س.\n\n👤 أدخل اسم المستفيد كاملًا (الاسم - الكنية - أبن الأب):")

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "fullname_company")
    def get_fullname(msg):
        user_id = msg.from_user.id
        user_states[user_id]["fullname"] = msg.text.strip()
        user_states[user_id]["step"] = "phone_company"
        bot.send_message(msg.chat.id, "📱 أدخل رقم موبايل المستفيد:")

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "phone_company")
    def get_phone(msg):
        user_id = msg.from_user.id
        user_states[user_id]["phone"] = msg.text.strip()
        user_states[user_id]["step"] = "amount_company"
        bot.send_message(msg.chat.id, "💸 أدخل المبلغ المراد إرساله (بالليرة السورية):")

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "amount_company")
    def get_amount_company(msg):
        user_id = msg.from_user.id
        try:
            amount = int(msg.text.strip())
            if amount <= 0:
                raise ValueError
        except Exception:
            bot.send_message(msg.chat.id, "❌ الرجاء إدخال مبلغ صحيح.")
            return
        state = user_states[user_id]
        commission = calculate_commission(amount, state["commission_per_50000"])
        total = amount + commission
        state["amount"] = amount
        state["commission"] = commission
        state["total"] = total

        if not has_sufficient_balance(user_id, total):
            kb = make_inline_buttons(
                ("💳 شحن المحفظة", "recharge_wallet"),
                ("⬅️ رجوع", "cash_cancel")
            )
            bot.send_message(
                msg.chat.id,
                f"❌ لا يوجد رصيد كافٍ في محفظتك.\n💡 يجب شحن محفظتك بمبلغ {total:,} ل.س أو أكثر.",
                reply_markup=kb
            )
            return

        kb = make_inline_buttons(
            ("✔️ تأكيد", "company_confirm"),
            ("❌ إلغاء", "cash_cancel")
        )
        bot.send_message(
            msg.chat.id,
            f"🟢 تأكيد العملية:\n"
            f"👤 المستفيد: {state['fullname']}\n"
            f"📱 رقم الموبايل: {state['phone']}\n"
            f"💸 المبلغ: {amount:,} ل.س\n"
            f"🧾 العمولة: {commission:,} ل.س\n"
            f"✅ سيتم خصم {total:,} ل.س من محفظتك.\n"
            f"🏦 الشركة: {state['company']}",
            reply_markup=kb
        )
        state["step"] = "company_wait_confirm"

    @bot.callback_query_handler(func=lambda call: call.data == "company_confirm")
    def company_confirm(call):
        user_id = call.from_user.id
        state = user_states.get(user_id, {})
        total = state.get("total")
        if not has_sufficient_balance(user_id, total):
            kb = make_inline_buttons(
                ("💳 شحن المحفظة", "recharge_wallet"),
                ("⬅️ رجوع", "cash_cancel")
            )
            bot.send_message(
                call.message.chat.id,
                f"❌ لا يوجد رصيد كافٍ في محفظتك.\n💡 يجب شحن محفظتك بمبلغ {total:,} ل.س أو أكثر.",
                reply_markup=kb
            )
            return

        # رسالة للعميل
        bot.edit_message_text("✅ طلبك قيد التنفيذ (الموقت المتوقع من 1 إلى 3 دقائق).", call.message.chat.id, call.message.message_id)
        # رسالة للأدمن
        kb_admin = make_inline_buttons(
            ("✅ تأكيد العملية", f"admin_company_accept_{user_id}_{total}"),
            ("❌ رفض العملية", f"admin_company_reject_{user_id}")
        )
        balance = get_balance(user_id)
        message = (
            f"📤 طلب حوالة عبر شركة\n"
            f"👤 العميل: {call.from_user.first_name or ''} ({user_id})\n"
            f"🏦 الشركة: {state.get('company')}\n"
            f"👤 المستفيد: {state.get('fullname')}\n"
            f"📱 رقم الموبايل: {state.get('phone')}\n"
            f"💸 المبلغ المطلوب: {state.get('amount'):,} ل.س\n"
            f"🧾 العمولة: {state.get('commission'):,} ل.س\n"
            f"✅ الإجمالي المطلوب خصمه: {state.get('total'):,} ل.س\n"
            f"💳 رصيد العميل الحالي: {balance:,} ل.س"
        )
        bot.send_message(ADMIN_MAIN_ID, message, reply_markup=kb_admin)
        state["step"] = "waiting_admin_company"

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_company_accept_"))
    def admin_accept_company(call):
        try:
            parts = call.data.split("_")
            user_id = int(parts[-2])
            total = int(parts[-1])
            if not has_sufficient_balance(user_id, total):
                bot.send_message(user_id, f"❌ فشل الحوالة: لا يوجد رصيد كافٍ في محفظتك.")
                bot.answer_callback_query(call.id, "❌ لا يوجد رصيد كافٍ لدى العميل.")
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                return
            deduct_balance(user_id, total)
            bot.send_message(user_id, "✅ تم خصم المبلغ من محفظتك بنجاح.")
            bot.answer_callback_query(call.id, "✅ تم قبول الطلب")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except Exception as e:
            logging.exception("❌ خطأ عند قبول حوالة من الأدمن:")
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_company_reject_"))
    def admin_reject_company(call):
        try:
            user_id = int(call.data.split("_")[-1])
            bot.send_message(call.message.chat.id, "📝 اكتب سبب الرفض أو أرسل صورة:")
            bot.register_next_step_handler_by_chat_id(
                call.message.chat.id,
                lambda m: process_cash_rejection(m, user_id, call),
            )
        except Exception as e:
            logging.exception("❌ خطأ عند رفض حوالة من الأدمن:")
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ: {e}")
