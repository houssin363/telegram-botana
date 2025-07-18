from telebot import types
from services.wallet_service import has_sufficient_balance, deduct_balance, get_balance
from config import ADMIN_MAIN_ID
from handlers.wallet import register_user_if_not_exist
from handlers import keyboards
import math  # لإدارة صفحات الكيبورد

user_states = {}

# قائمة أنواع التحويل الكاش لاستخدامها في الكيبورد الجديد
CASH_TYPES = [
    "تحويل إلى سيرياتيل كاش",
    "تحويل إلى أم تي إن كاش",
    "تحويل إلى شام كاش",
]

CASH_PAGE_SIZE = 3  # عدد العناصر لكل صفحة

def build_cash_menu(page: int = 0):
    """يبني كيبورد مُقسّم إلى صفحات لاختيار نوع التحويل."""
    total = len(CASH_TYPES)
    pages = max(1, math.ceil(total / CASH_PAGE_SIZE))
    page = max(0, min(page, pages - 1))

    kb = types.InlineKeyboardMarkup()
    start = page * CASH_PAGE_SIZE
    end = start + CASH_PAGE_SIZE

    for idx, label in enumerate(CASH_TYPES[start:end], start=start):
        kb.add(types.InlineKeyboardButton(label, callback_data=f"cash_sel_{idx}"))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("◀️", callback_data=f"cash_page_{page-1}"))
    nav.append(types.InlineKeyboardButton(f"{page+1}/{pages}", callback_data="cash_noop"))
    if page < pages - 1:
        nav.append(types.InlineKeyboardButton("▶️", callback_data=f"cash_page_{page+1}"))
    kb.row(*nav)
    kb.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="commission_cancel"))
    return kb


COMMISSION_PER_50000 = 3500

def calculate_commission(amount):
    blocks = amount // 50000
    remainder = amount % 50000
    commission = blocks * COMMISSION_PER_50000
    if remainder > 0:
        commission += int(COMMISSION_PER_50000 * (remainder / 50000))
    return commission

def start_cash_transfer(bot, message, history=None):
    """إظهار قائمة اختيار نوع الكاش باستخدام InlineKeyboard مع Pagination."""
    user_id = message.from_user.id
    register_user_if_not_exist(user_id)
    if history is not None:
        history.setdefault(user_id, []).append("cash_menu")
    bot.send_message(
        message.chat.id,
        "📤 اختر نوع التحويل من محفظتك:",
        reply_markup=build_cash_menu(0)
    )

def make_inline_buttons(*buttons):
    kb = types.InlineKeyboardMarkup()
    for text, data in buttons:
        kb.add(types.InlineKeyboardButton(text, callback_data=data))
    return kb

def register(bot, history):

    # ======== دعم الكيبورد الجديد Inline + Pagination ========
    @bot.callback_query_handler(func=lambda c: c.data.startswith("cash_page_"))
    def _paginate_cash_menu(call):
        page = int(call.data.split("_")[-1])
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=build_cash_menu(page)
        )
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cash_sel_"))
    def _cash_type_selected(call):
        idx = int(call.data.split("_")[-1])
        if idx < 0 or idx >= len(CASH_TYPES):
            bot.answer_callback_query(call.id, "❌ خيار غير صالح.")
            return
        cash_type = CASH_TYPES[idx]
        user_id = call.from_user.id
        user_states[user_id] = {"step": "show_commission", "cash_type": cash_type}
        history.setdefault(user_id, []).append("cash_menu")
        text = (
            "⚠️ تنويه:\n"
            f"العمولة لكل 50000 ل.س هي {COMMISSION_PER_50000} ل.س.\n"
            "هل تريد المتابعة وكتابة الرقم المراد التحويل له؟"
        )
        kb = make_inline_buttons(
            ("✅ موافق", "commission_confirm"),
            ("❌ إلغاء", "commission_cancel")
        )
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=lambda msg: msg.text == "🧧 تحويل كاش من محفظتك")
    def open_cash_menu(msg):
        start_cash_transfer(bot, msg, history)

    @bot.message_handler(func=lambda msg: msg.text in [
        "تحويل إلى سيرياتيل كاش",
        "تحويل إلى أم تي إن كاش",
        "تحويل إلى شام كاش"
    ])
    def handle_cash_type(msg):
        user_id = msg.from_user.id
        cash_type = msg.text
        user_states[user_id] = {"step": "show_commission", "cash_type": cash_type}
        history.setdefault(user_id, []).append("cash_menu")
        text = (
            "⚠️ تنويه:\n"
            f"العمولة لكل 50000 ل.س هي {COMMISSION_PER_50000} ل.س.\n"
            "هل تريد المتابعة وكتابة الرقم المراد التحويل له؟"
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
        kb = make_inline_buttons(
            ("❌ إلغاء", "commission_cancel")
        )
        bot.edit_message_text("📲 أكتب الرقم المراد التحويل له:", call.message.chat.id, call.message.message_id, reply_markup=kb)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "awaiting_number")
    def get_target_number(msg):
        user_id = msg.from_user.id
        user_states[user_id]["number"] = msg.text
        user_states[user_id]["step"] = "confirm_number"
        kb = make_inline_buttons(
            ("❌ إلغاء", "commission_cancel"),
            ("✏️ تعديل", "edit_number"),
            ("✔️ تأكيد", "number_confirm")
        )
        bot.send_message(
            msg.chat.id,
            f"الرقم المدخل: {msg.text}\n\nهل تريد المتابعة؟",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "edit_number")
    def edit_number(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_number"
        bot.send_message(call.message.chat.id, "📲 أعد كتابة الرقم المراد التحويل له:")

    @bot.callback_query_handler(func=lambda call: call.data == "number_confirm")
    def number_confirm(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_amount"
        kb = make_inline_buttons(
            ("❌ إلغاء", "commission_cancel")
        )
        bot.edit_message_text("💰 اكتب المبلغ الذي تريد تحويله:", call.message.chat.id, call.message.message_id, reply_markup=kb)

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
        commission = calculate_commission(amount)
        total = amount + commission
        state["amount"] = amount
        state["commission"] = commission
        state["total"] = total
        state["step"] = "confirming"

        kb = make_inline_buttons(
            ("❌ إلغاء", "commission_cancel"),
            ("✏️ تعديل", "edit_amount"),
            ("✔️ تأكيد", "cash_confirm")
        )
        summary = (
            f"📤 تأكيد العملية:\n"
            f"📲 الرقم: {state['number']}\n"
            f"💸 المبلغ: {amount:,} ل.س\n"
            f"🧾 العمولة: {commission:,} ل.س\n"
            f"✅ الإجمالي: {total:,} ل.س\n"
            f"💼 الطريقة: {state['cash_type']}"
        )
        bot.send_message(msg.chat.id, summary, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "edit_amount")
    def edit_amount(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "awaiting_amount"
        bot.send_message(call.message.chat.id, "💰 أعد كتابة المبلغ:")

    @bot.callback_query_handler(func=lambda call: call.data == "cash_confirm")
    def confirm_transfer(call):
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
                ("⬅️ رجوع", "commission_cancel")
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

        # عند التأكيد: ترسل رسالة للأدمن مع أزرار تأكيد ورفض فقط، ويُبقي بيانات العميل حتى قرار الأدمن
        user_states[user_id]["step"] = "waiting_admin"
        kb_admin = make_inline_buttons(
            ("✅ تأكيد التحويل", f"admin_cash_accept_{user_id}_{total}"),
            ("❌ رفض التحويل", f"admin_cash_reject_{user_id}")
        )
        message = (
            f"📤 طلب تحويل كاش جديد:\n"
            f"👤 المستخدم: {user_id}\n"
            f"📲 الرقم: {data.get('number')}\n"
            f"💰 المبلغ: {amount:,} ل.س\n"
            f"💼 الطريقة: {data.get('cash_type')}\n"
            f"🧾 العمولة: {commission:,} ل.س\n"
            f"✅ الإجمالي: {total:,} ل.س\n\n"
            f"يمكنك الرد برسالة أو صورة ليصل للعميل."
        )
        bot.edit_message_text("✅ تم إرسال الطلب، بانتظار موافقة الإدارة.", call.message.chat.id, call.message.message_id)
        msg_admin = bot.send_message(ADMIN_MAIN_ID, message, reply_markup=kb_admin)
        # حفظ معرف رسالة الأدمن للرد
        user_states[user_id]["admin_message_id"] = msg_admin.message_id
        user_states[user_id]["admin_chat_id"] = ADMIN_MAIN_ID

    @bot.callback_query_handler(func=lambda call: call.data == "recharge_wallet")
    def show_recharge_methods(call):
        bot.send_message(call.message.chat.id, "💳 اختر طريقة شحن المحفظة:", reply_markup=keyboards.recharge_menu())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_cash_accept_"))
    def admin_accept_cash_transfer(call):
        try:
            parts = call.data.split("_")
            user_id = int(parts[-2])
            total = int(parts[-1])
            data = user_states.get(user_id, {})
            if not has_sufficient_balance(user_id, total):
                bot.send_message(user_id, f"❌ فشل تحويل الكاش: لا يوجد رصيد كافٍ في محفظتك.")
                bot.answer_callback_query(call.id, "❌ لا يوجد رصيد كافٍ لدى العميل.")
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                return
            deduct_balance(user_id, total)
            # الرسالة المطلوبة للعميل
            bot.send_message(
                user_id,
                f"✅ تم شراء {data.get('cash_type')} للرقم {data.get('number')} بمبلغ {data.get('amount'):,} ل.س بنجاح."
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
            bot.send_message(call.message.chat.id, "📝 أرسل رسالة أو صورة للعميل مع صورة التحويل أو تأكيد العملية.")
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, forward_admin_message)
            user_states.pop(user_id, None)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ: {e}")
         
    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_cash_accept_"))
    def admin_accept_cash_transfer(call):
        try:
            parts = call.data.split("_")
            user_id = int(parts[-2])
            total = int(parts[-1])
            data = user_states.get(user_id, {})
            if not has_sufficient_balance(user_id, total):
                bot.send_message(user_id, f"❌ فشل تحويل الكاش: لا يوجد رصيد كافٍ في محفظتك.")
                bot.answer_callback_query(call.id, "❌ لا يوجد رصيد كافٍ لدى العميل.")
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                return
            deduct_balance(user_id, total)
            # الرسالة المطلوبة للعميل
            bot.send_message(
                user_id,
                f"✅ تم شراء {data.get('cash_type')} للرقم {data.get('number')} بمبلغ {data.get('amount'):,} ل.س بنجاح."
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
            bot.send_message(
                call.message.chat.id,
                "📝 أرسل رسالة أو صورة للعميل مع صورة التحويل أو تأكيد العملية."
            )
            bot.register_next_step_handler_by_chat_id(
                call.message.chat.id,
                forward_admin_message
            )
            user_states.pop(user_id, None)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_cash_reject_"))
    def admin_reject_cash_transfer(call):
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
