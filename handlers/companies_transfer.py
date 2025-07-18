from telebot import types
from services.wallet_service import add_purchase, has_sufficient_balance
from config import ADMIN_MAIN_ID
from handlers.wallet import register_user_if_not_exist
from handlers import keyboards

user_states = {}

COMMISSION_PER_50000 = 1500

def calculate_commission(amount):
    blocks = amount // 50000
    remainder = amount % 50000
    commission = blocks * COMMISSION_PER_50000
    if remainder > 0:
        commission += int(COMMISSION_PER_50000 * (remainder / 50000))
    return commission

def make_inline_buttons(*buttons):
    kb = types.InlineKeyboardMarkup()
    for text, data in buttons:
        kb.add(types.InlineKeyboardButton(text, callback_data=data))
    return kb

# هنا التعديل: قائمة الشركات الآن InlineKeyboardButton
def companies_transfer_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("شركة الهرم", callback_data="company_alharam"),
        types.InlineKeyboardButton("شركة الفؤاد", callback_data="company_alfouad"),
        types.InlineKeyboardButton("شركة شخاشير", callback_data="company_shakhashir"),
        types.InlineKeyboardButton("⬅️ رجوع", callback_data="back"),
        types.InlineKeyboardButton("🔄 ابدأ من جديد", callback_data="restart")
    )
    return kb

def register_companies_transfer(bot, history):

    @bot.message_handler(func=lambda msg: msg.text == "حوالة مالية عبر شركات")
    def open_companies_menu(msg):
        user_id = msg.from_user.id
        register_user_if_not_exist(user_id)
        user_states[user_id] = {"step": None}
        history.setdefault(user_id, []).append("companies_menu")
        bot.send_message(msg.chat.id, "💸 اختر الشركة التي تريد التحويل عبرها:", reply_markup=companies_transfer_menu())

    # هذه الهاندلرات تم تعديلها لتتعامل مع inline buttons
    @bot.callback_query_handler(func=lambda call: call.data in [
        "company_alharam", "company_alfouad", "company_shakhashir"
    ])
    def select_company(call):
        user_id = call.from_user.id
        company_map = {
            "company_alharam": "شركة الهرم",
            "company_alfouad": "شركة الفؤاد",
            "company_shakhashir": "شركة شخاشير"
        }
        company = company_map[call.data]
        user_states[user_id] = {"step": "show_commission", "company": company}
        history.setdefault(user_id, []).append("companies_menu")
        text = (
            "⚠️ تنويه:\n"
            f"العمولة عن كل 50000 ل.س هي {COMMISSION_PER_50000} ل.س.\n"
            "هل ترغب بمتابعة تنفيذ حوالة عبر الشركة المختارة؟"
        )
        kb = make_inline_buttons(
            ("✅ موافق", "company_commission_confirm"),
            ("❌ إلغاء", "company_commission_cancel")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "company_commission_cancel")
    def company_commission_cancel(call):
        user_id = call.from_user.id
        bot.edit_message_text("❌ تم إلغاء العملية.", call.message.chat.id, call.message.message_id)
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data == "company_commission_confirm")
    def company_commission_confirm(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_beneficiary_name"
        kb = make_inline_buttons(
            ("❌ إلغاء", "company_commission_cancel")
        )
        bot.edit_message_text(
            "👤 أرسل اسم المستفيد (الكنية الاسم ابن الأب):",
            call.message.chat.id, call.message.message_id,
            reply_markup=kb
        )

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_beneficiary_name")
    def get_beneficiary_name(msg):
        user_id = msg.from_user.id
        user_states[user_id]["beneficiary_name"] = msg.text.strip()
        user_states[user_id]["step"] = "confirm_beneficiary_name"
        kb = make_inline_buttons(
            ("❌ إلغاء", "company_commission_cancel"),
            ("✏️ تعديل", "edit_beneficiary_name"),
            ("✔️ تأكيد", "beneficiary_name_confirm")
        )
        bot.send_message(
            msg.chat.id,
            f"👤 الاسم المدخل: {msg.text}\n\nهل تريد المتابعة؟",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "edit_beneficiary_name")
    def edit_beneficiary_name(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_beneficiary_name"
        bot.send_message(call.message.chat.id, "👤 أعد إرسال اسم المستفيد (الكنية الاسم ابن الأب):")

    @bot.callback_query_handler(func=lambda call: call.data == "beneficiary_name_confirm")
    def beneficiary_name_confirm(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_beneficiary_number"
        kb = make_inline_buttons(
            ("❌ إلغاء", "company_commission_cancel")
        )
        bot.edit_message_text("📱 أرسل رقم المستفيد (يجب أن يبدأ بـ 09):", call.message.chat.id, call.message.message_id, reply_markup=kb)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_beneficiary_number")
    def get_beneficiary_number(msg):
        user_id = msg.from_user.id
        number = msg.text.strip()
        if not (number.startswith("09") and number.isdigit() and len(number) == 10):
            bot.send_message(msg.chat.id, "⚠️ يجب أن يبدأ الرقم بـ 09 ويتكون من 10 أرقام.")
            return
        user_states[user_id]["beneficiary_number"] = number
        user_states[user_id]["step"] = "confirm_beneficiary_number"
        kb = make_inline_buttons(
            ("❌ إلغاء", "company_commission_cancel"),
            ("✏️ تعديل", "edit_beneficiary_number"),
            ("✔️ تأكيد", "beneficiary_number_confirm")
        )
        bot.send_message(
            msg.chat.id,
            f"📱 الرقم المدخل: {number}\n\nهل تريد المتابعة؟",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "edit_beneficiary_number")
    def edit_beneficiary_number(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_beneficiary_number"
        bot.send_message(call.message.chat.id, "📱 أعد إرسال رقم المستفيد (يجب أن يبدأ بـ 09):")

    @bot.callback_query_handler(func=lambda call: call.data == "beneficiary_number_confirm")
    def beneficiary_number_confirm(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_transfer_amount"
        kb = make_inline_buttons(
            ("❌ إلغاء", "company_commission_cancel")
        )
        bot.edit_message_text("💵 أرسل المبلغ المراد تحويله (مثال: 12345):", call.message.chat.id, call.message.message_id, reply_markup=kb)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_transfer_amount")
    def get_transfer_amount(msg):
        user_id = msg.from_user.id
        try:
            amount = int(msg.text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(msg.chat.id, "⚠️ الرجاء إدخال مبلغ صحيح بالأرقام فقط.")
            return

        commission = calculate_commission(amount)
        total = amount + commission
        user_states[user_id]["amount"] = amount
        user_states[user_id]["commission"] = commission
        user_states[user_id]["total"] = total
        user_states[user_id]["step"] = "confirming_transfer"
        kb = make_inline_buttons(
            ("❌ إلغاء", "company_commission_cancel"),
            ("✏️ تعديل", "edit_transfer_amount"),
            ("✔️ تأكيد", "company_transfer_confirm")
        )
        summary = (
            f"📤 تأكيد العملية:\n"
            f"👤 المستفيد: {user_states[user_id]['beneficiary_name']}\n"
            f"📱 رقم المستفيد: {user_states[user_id]['beneficiary_number']}\n"
            f"💸 المبلغ: {amount:,} ل.س\n"
            f"🧾 العمولة: {commission:,} ل.س\n"
            f"✅ الإجمالي: {total:,} ل.س\n"
            f"🏢 الشركة: {user_states[user_id]['company']}\n"
        )
        bot.send_message(msg.chat.id, summary, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "edit_transfer_amount")
    def edit_transfer_amount(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_transfer_amount"
        bot.send_message(call.message.chat.id, "💵 أعد إرسال المبلغ (مثال: 12345):")

    @bot.callback_query_handler(func=lambda call: call.data == "company_transfer_confirm")
    def company_transfer_confirm(call):
        user_id = call.from_user.id
        data = user_states.get(user_id, {})
        amount = data.get('amount')
        commission = data.get('commission')
        total = data.get('total')
        balance = get_balance(user_id)

        if balance < total:
            shortage = total - balance
            kb = make_inline_buttons(
                ("💳 شحن المحفظة", "recharge_wallet"),
                ("⬅️ رجوع", "company_commission_cancel")
            )
            bot.edit_message_text(
                f"❌ لا يوجد رصيد كافٍ في محفظتك.\n"
                f"الإجمالي المطلوب: {total:,} ل.س\n"
                f"رصيدك الحالي: {balance:,} ل.س\n"
                f"المبلغ الناقص: {shortage:,} ل.س\n"
                "يرجى شحن المحفظة أو العودة.",
                call.message.chat.id, call.message.message_id,
                reply_markup=kb
            )
            return

        # إرسال الطلب إلى الأدمن
        user_states[user_id]["step"] = "waiting_admin"
        kb_admin = make_inline_buttons(
            ("✅ تأكيد الحوالة", f"admin_company_accept_{user_id}_{total}"),
            ("❌ رفض الحوالة", f"admin_company_reject_{user_id}")
        )
        msg = (
            f"📤 طلب حوالة مالية عبر شركات:\n"
            f"👤 المستخدم: {user_id}\n"
            f"👤 المستفيد: {data.get('beneficiary_name')}\n"
            f"📱 رقم المستفيد: {data.get('beneficiary_number')}\n"
            f"💰 المبلغ: {amount:,} ل.س\n"
            f"🏢 الشركة: {data.get('company')}\n"
            f"🧾 العمولة: {commission:,} ل.س\n"
            f"✅ الإجمالي: {total:,} ل.س\n\n"
            f"يمكنك الرد برسالة أو صورة ليصل للعميل."
        )
        bot.edit_message_text("✅ تم إرسال الطلب، بانتظار موافقة الإدارة.", call.message.chat.id, call.message.message_id)
        msg_admin = bot.send_message(ADMIN_MAIN_ID, msg, reply_markup=kb_admin)
        user_states[user_id]["admin_message_id"] = msg_admin.message_id
        user_states[user_id]["admin_chat_id"] = ADMIN_MAIN_ID

    @bot.callback_query_handler(func=lambda call: call.data == "recharge_wallet")
    def show_recharge_methods(call):
        bot.send_message(call.message.chat.id, "💳 اختر طريقة شحن المحفظة:", reply_markup=keyboards.recharge_menu())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_company_accept_"))
    def admin_accept_company_transfer(call):
        try:
            parts = call.data.split("_")
            user_id = int(parts[-2])
            total = int(parts[-1])
            data = user_states.get(user_id, {})
            if not has_sufficient_balance(user_id, total):
                bot.send_message(user_id, "❌ فشل الحوالة: لا يوجد رصيد كافٍ في محفظتك.")
                bot.answer_callback_query(call.id, "❌ لا يوجد رصيد كافٍ لدى العميل.")
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                return
            deduct_balance(user_id, total)
            bot.send_message(
                user_id,
                f"✅ تم تنفيذ الحوالة عبر {data.get('company')} للمستفيد {data.get('beneficiary_name')} بمبلغ {data.get('amount'):,} ل.س بنجاح."
            )
            bot.answer_callback_query(call.id, "✅ تم قبول الطلب")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            # يبقى للأدمن إرسال صورة أو رسالة إضافية
            def forward_admin_message(m):
                if m.content_type == "photo":
                    file_id = m.photo[-1].file_id
                    bot.send_photo(user_id, file_id, caption=m.caption or "تمت العملية بنجاح.")
                else:
                    bot.send_message(user_id, m.text or "تمت العملية بنجاح.")
            bot.send_message(call.message.chat.id, "📝 أرسل رسالة أو صورة للعميل مع صورة الحوالة أو تأكيد العملية.")
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, forward_admin_message)
            user_states.pop(user_id, None)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_company_reject_"))
    def admin_reject_company_transfer(call):
        try:
            user_id = int(call.data.split("_")[-1])
            def handle_reject(m):
                txt = m.text if m.content_type == "text" else "❌ تم رفض الطلب."
                if m.content_type == "photo":
                    bot.send_photo(user_id, m.photo[-1].file_id, caption=(m.caption or txt))
                else:
                    bot.send_message(user_id, f"❌ تم رفض الطلب من الإدارة.\n📝 السبب: {txt}")
                bot.answer_callback_query(call.id, "❌ تم رفض الطلب")
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                user_states.pop(user_id, None)
            bot.send_message(call.message.chat.id, "📝 اكتب سبب الرفض أو أرسل صورة:")
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, handle_reject)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ: {e}")

