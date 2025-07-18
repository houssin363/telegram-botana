# -*- coding: utf-8 -*-
# handlers/internet_providers.py  (نسخة مُحدَّثة بأزرار InlineKeyboardMarkup)
#
# تمت تلبية طلب: التحويل من ReplyKeyboardMarkup إلى InlineKeyboardMarkup فقط،
# مع الحفاظ على التدفق العام (اختيار مزود > سرعة > إدخال رقم > تأكيد/إلغاء).
# لم يتم إجراء تغييرات أخرى غير لازمة (منطق الرصيد/الحفظ كما هو متوقَّع).
#
# ملاحظة: إذا كان لديك نظام تسجيل منفصل، تأكد من استدعاء register(bot) في مكانه المعتاد.

from telebot import types
from database.models.product import Product
from services.wallet_service import has_sufficient_balance, deduct_balance
from config import ADMIN_MAIN_ID

# ============================
#        الثوابت الأصلية
# ============================
INTERNET_PROVIDERS = [
    "تراسل", "أم تي أن", "سيرياتيل", "آية", "سوا", "رن نت", "سما نت", "أمنية",
    "ناس", "هايبر نت", "MTS", "يارا", "دنيا", "آينت"
]

INTERNET_SPEEDS = [
    {"label": "1 ميغا", "price": 19500},
    {"label": "2 ميغا", "price": 25000},
    {"label": "4 ميغا", "price": 39000},
    {"label": "8 ميغا", "price": 65000},
    {"label": "16 ميغا", "price": 84000},
]

COMMISSION_PER_5000 = 600
user_net_state = {}  # {user_id: {step, provider?, speed?, price?, phone?}}


# ============================
#   حساب العمولة المجمّعة
# ============================
def calculate_commission(amount: int) -> int:
    """احسب العمولة بتجميع 600 لكل 5000 (تقريب لأعلى)."""
    if amount <= 0:
        return 0
    # تقسيم مع تقريب للأعلى
    blocks = (amount + 5000 - 1) // 5000
    return blocks * COMMISSION_PER_5000


# ============================
#   مفاتيح callback ثابتة
# ============================
CB_PROV_PREFIX = "iprov"       # اختيار مزوّد
CB_SPEED_PREFIX = "ispeed"     # اختيار سرعة (index)
CB_BACK_PROV = "iback_prov"    # رجوع لقائمة المزودين
CB_BACK_SPEED = "iback_speed"  # رجوع لقائمة السرعات
CB_CONFIRM = "iconfirm"        # تأكيد الطلب
CB_CANCEL = "icancel"          # إلغاء


# ============================
#   توليد لوحات Inline
# ============================
def _provider_inline_kb() -> types.InlineKeyboardMarkup:
    """لوحة اختيار مزوّد (telebot لا يوفّر insert؛ نستخدم add(*buttons))."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for name in INTERNET_PROVIDERS:
        buttons.append(
            types.InlineKeyboardButton(
                text=f"🌐 {name}",
                callback_data=f"{CB_PROV_PREFIX}:{name}"
            )
        )
    if buttons:
        kb.add(*buttons)  # telebot يقوم بتوزيعها حسب row_width
    kb.add(types.InlineKeyboardButton("❌ إلغاء", callback_data=CB_CANCEL))
    return kb


def _speeds_inline_kb() -> types.InlineKeyboardMarkup:
    """لوحة اختيار السرعة."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for idx, speed in enumerate(INTERNET_SPEEDS):
        buttons.append(
            types.InlineKeyboardButton(
                text=f"{speed['label']} - {speed['price']:,} ل.س",
                callback_data=f"{CB_SPEED_PREFIX}:{idx}"
            )
        )
    if buttons:
        kb.add(*buttons)
    kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data=CB_BACK_PROV))
    return kb


def _confirm_inline_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("✅ تأكيد", callback_data=CB_CONFIRM))
    kb.add(types.InlineKeyboardButton("⬅️ تعديل", callback_data=CB_BACK_SPEED))
    kb.add(types.InlineKeyboardButton("❌ إلغاء", callback_data=CB_CANCEL))
    return kb


# ============================
#   بدء قائمة مزودي الإنترنت
# ============================
def start_internet_provider_menu(bot, message):
    """إرسال قائمة مزودي الإنترنت بأزرار Inline."""
    bot.send_message(
        message.chat.id,
        "⚠️ اختر أحد مزودات الإنترنت:\n💸 العمولة لكل 5000 ل.س = 600 ل.س",
        reply_markup=_provider_inline_kb()
    )
    user_net_state[message.from_user.id] = {"step": "choose_provider"}


# ============================
#   أدوات داخلية مساعدة
# ============================
import re
_PHONE_RE = re.compile(r"[+\d]+")

def _normalize_phone(txt: str) -> str:
    """إزالة أي محارف غير أرقام أو + وجمعها في سلسلة واحدة."""
    if not txt:
        return ""
    clean = txt.replace(" ", "").replace("-", "").replace("_", "")
    m = _PHONE_RE.findall(clean)
    return ''.join(m)


# ============================
#   التسجيل في البوت
# ============================
def register(bot):
    """تسجيل معالجات الرسائل و callback لمزوّدات الإنترنت."""

    # --- فتح القائمة من زر رئيسي (نفس النص القديم لعدم كسر بقية الملفات) ---
    @bot.message_handler(func=lambda msg: msg.text == "🌐 دفع مزودات الإنترنت ADSL")
    def open_net_menu(msg):
        start_internet_provider_menu(bot, msg)


    # =========================
    #      CALLBACK HANDLERS
    # =========================

    # اختيار مزوّد
    @bot.callback_query_handler(func=lambda c: c.data.startswith(f"{CB_PROV_PREFIX}:"))
    def cb_choose_provider(call):
        user_id = call.from_user.id
        provider = call.data.split(":", 1)[1]
        if provider not in INTERNET_PROVIDERS:
            bot.answer_callback_query(call.id, "خيار غير صالح.")
            return
        user_net_state[user_id] = {"step": "choose_speed", "provider": provider}
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="⚡ اختر السرعة المطلوبة:\n💸 العمولة لكل 5000 ل.س = 600 ل.س",
            reply_markup=_speeds_inline_kb()
        )


    # رجوع من السرعات إلى قائمة المزودين
    @bot.callback_query_handler(func=lambda c: c.data == CB_BACK_PROV)
    def cb_back_to_prov(call):
        user_id = call.from_user.id
        user_net_state[user_id] = {"step": "choose_provider"}
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="⚠️ اختر أحد مزودات الإنترنت:\n💸 العمولة لكل 5000 ل.س = 600 ل.س",
            reply_markup=_provider_inline_kb()
        )


    # اختيار سرعة
    @bot.callback_query_handler(func=lambda c: c.data.startswith(f"{CB_SPEED_PREFIX}:"))
    def cb_choose_speed(call):
        user_id = call.from_user.id
        try:
            idx = int(call.data.split(":", 1)[1])
            speed = INTERNET_SPEEDS[idx]
        except (ValueError, IndexError):
            bot.answer_callback_query(call.id, "خيار غير صالح.")
            return

        st = user_net_state.setdefault(user_id, {})
        st.update({"step": "enter_phone", "speed": speed["label"], "price": speed["price"]})

        bot.answer_callback_query(call.id)  # اغلاق نافذة التحميل
        # أرسل رسالة جديدة لطلب الرقم (لا نحرر الرسالة السابقة لعدم فقد سجل)
        bot.send_message(
            call.message.chat.id,
            "📱 أرسل رقم الهاتف / الحساب المطلوب شحنه (أرقام فقط، يمكنك تضمين + أو 0).\nأرسل /cancel للإلغاء."
        )


    # رجوع من شاشة التأكيد إلى السرعات
    @bot.callback_query_handler(func=lambda c: c.data == CB_BACK_SPEED)
    def cb_back_to_speed(call):
        user_id = call.from_user.id
        st = user_net_state.get(user_id, {})
        if "provider" not in st:  # احتياط
            return cb_back_to_prov(call)
        st["step"] = "choose_speed"
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="⚡ اختر السرعة المطلوبة:\n💸 العمولة لكل 5000 ل.س = 600 ل.س",
            reply_markup=_speeds_inline_kb()
        )


    # إلغاء كامل
    @bot.callback_query_handler(func=lambda c: c.data == CB_CANCEL)
    def cb_cancel(call):
        user_net_state.pop(call.from_user.id, None)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="تم الإلغاء. أرسل /start للعودة إلى القائمة الرئيسية."
        )


    # =========================
    #   مرحلة إدخال الهاتف
    # =========================
    @bot.message_handler(func=lambda m: user_net_state.get(m.from_user.id, {}).get("step") == "enter_phone")
    def handle_phone_entry(msg):
        user_id = msg.from_user.id
        phone = _normalize_phone(msg.text)
        if not phone or len(phone) < 5:
            return bot.reply_to(msg, "⚠️ رقم غير صالح، أعد الإرسال.")

        st = user_net_state[user_id]
        st["phone"] = phone
        st["step"] = "confirm"

        price = st["price"]
        comm = calculate_commission(price)
        total = price + comm

        summary = (
            "📦 *تفاصيل الطلب*\n"
            f"مزود: {st['provider']}\n"
            f"سرعة: {st['speed']}\n"
            f"السعر: {price:,} ل.س\n"
            f"العمولة: {comm:,} ل.س\n"
            f"الإجمالي: {total:,} ل.س\n\n"
            f"رقم: `{phone}`\n\nهل ترغب بالمتابعة؟"
        )

        bot.send_message(
            msg.chat.id,
            summary,
            parse_mode="Markdown",
            reply_markup=_confirm_inline_kb()
        )


    # =========================
    #   تأكيد الدفع
    # =========================
    @bot.callback_query_handler(func=lambda c: c.data == CB_CONFIRM)
    def cb_confirm(call):
        user_id = call.from_user.id
        st = user_net_state.get(user_id)
        if not st or st.get("step") != "confirm":
            bot.answer_callback_query(call.id, "انتهت صلاحية هذا الطلب.", show_alert=True)
            return

        price = st["price"]
        comm = calculate_commission(price)
        total = price + comm

        # التحقق من الرصيد
        if not has_sufficient_balance(user_id, total):
            bot.answer_callback_query(call.id, "رصيد غير كافٍ.", show_alert=True)
            bot.send_message(call.message.chat.id, "⚠️ رصيدك غير كافٍ لإتمام العملية.")
            return

        # خصم الرصيد
        deduct_balance(user_id, total)

        # إنشاء سجل المنتج (حقول تقريبية، عدّل حسب نموذجك)
        try:
            Product.create(
                user_id=user_id,
                provider=st['provider'],
                speed=st['speed'],
                phone=st['phone'],
                amount=price,
                commission=comm,
                total=total,
            )
        except Exception as e:  # pylint: disable=broad-except
            bot.send_message(ADMIN_MAIN_ID, f"[internet_providers] خطأ حفظ المنتج: {e}")

        # إشعار الإدمن بالطلب
        admin_msg = (
            "طلب دفع مزوّد إنترنت جديد:\n"
            f"المستخدم: {user_id}\n"
            f"مزود: {st['provider']}\n"
            f"سرعة: {st['speed']}\n"
            f"رقم: {st['phone']}\n"
            f"المبلغ: {price:,} + عمولة {comm:,} = {total:,} ل.س"
        )
        bot.send_message(ADMIN_MAIN_ID, admin_msg)

        # تأكيد للمستخدم
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="✅ تم استلام طلبك وسيجري التنفيذ قريبًا. شكراً لك!"
        )

        # مسح الحالة
        user_net_state.pop(user_id, None)


    # =========================
    #   /cancel أثناء إدخال الرقم
    # =========================
    @bot.message_handler(commands=['cancel'])
    def cancel_cmd(msg):
        user_net_state.pop(msg.from_user.id, None)
        bot.send_message(msg.chat.id, "تم الإلغاء. أرسل /start للعودة للقائمة.")


    # =========================
    #   احتياط: رجوع يدوي بالنص
    # =========================
    @bot.message_handler(func=lambda m: m.text == "⬅️ رجوع")
    def txt_back(msg):
        # اجعلها تعيد فتح القائمة الرئيسية (متوافق مع القديم)
        start_internet_provider_menu(bot, msg)

