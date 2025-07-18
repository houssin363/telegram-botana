# -*- coding: utf-8 -*-
"""
start.py  (ستارت ينظّف العمليات المعلّقة + زر جديد)
================================================
- زر ستارت جديد (يمكن تعديل النص عبر START_BTN_TEXT).
- لوحة الاشتراك تفصل بين زر الاشتراك وزر ستارت.
- عند ضغط ستارت: يتم تنظيف أي عمليات معلّقة للمستخدم (مثال: طلبات مزودي الإنترنت).
  * يحذف user_net_state و pending_orders (إن وُجِدت) من handlers.internet_providers.
  * لا يُرسل إشعار للأدمن؛ يُعامَل الأمر كأن المستخدم لم يُكمل العملية.
- باقي التدفق كما في الملف السابق.  (مصدر: الملف الأصلي).

"""

from telebot import types
from handlers import keyboards
from config import BOT_NAME, FORCE_SUB_CHANNEL_USERNAME
from services.wallet_service import register_user_if_not_exist  # هذا مهم

# --------------------------
# إعدادات واجهة قابلة للتعديل
# --------------------------
START_BTN_TEXT = "🚀 ستارت جديد"  # غيّر الشكل/النص كما تريد
START_BTN_TEXT_SUB = "✅ تم الاشتراك"  # زر فحص الاشتراك
SUB_BTN_TEXT = "🔔 اشترك الآن في القناة"


# --------------------------
# مفاتيح Callback جديدة
# --------------------------
CB_START = "cb_start_main"
CB_CHECK_SUB = "cb_check_sub"


# --------------------------
# تنظيف العمليات المعلّقة (Best Effort)
# --------------------------
def _reset_user_flows(user_id: int):
    """حذف أي حالات/طلبات غير مكتملة تخص المستخدم.

    حاليًا يدعم:
    - handlers.internet_providers.user_net_state
    - handlers.internet_providers.pending_orders (إن وُجد؛ يعتمد على نسخة الملف)
    لا تُرسل رسائل للأدمن؛ يُعامل كإلغاء صامت.
    """
    try:
        from handlers import internet_providers
    except Exception:
        return

    # حذف حالة تفاعلية
    try:
        internet_providers.user_net_state.pop(user_id, None)
    except Exception:
        pass

    # حذف أي طلبات معلّقة تخص المستخدم
    try:
        po = getattr(internet_providers, "pending_orders", None)
        if isinstance(po, dict):
            for oid in list(po.keys()):
                try:
                    if po[oid].get("user_id") == user_id:
                        po.pop(oid, None)
                except Exception:
                    continue
    except Exception:
        pass


# --------------------------
# لوحات Inline
# --------------------------
def _sub_inline_kb():
    """لوحة اشتراك بالقناة + زر فحص اشتراك + ستارت."""
    kb = types.InlineKeyboardMarkup(row_width=1)
    # رابط الاشتراك
    if FORCE_SUB_CHANNEL_USERNAME:
        kb.add(
            types.InlineKeyboardButton(
                SUB_BTN_TEXT,
                url=f"https://t.me/{FORCE_SUB_CHANNEL_USERNAME[1:]}"  # إزالة @
            )
        )
    # زر فحص الاشتراك
    kb.add(types.InlineKeyboardButton(START_BTN_TEXT_SUB, callback_data=CB_CHECK_SUB))
    # زر ستارت مباشر (قد يستخدمه البعض بعد الاشتراك أو لتجاهل الرسالة)
    kb.add(types.InlineKeyboardButton(START_BTN_TEXT, callback_data=CB_START))
    return kb


def _welcome_inline_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(START_BTN_TEXT, callback_data=CB_START))
    return kb


def register(bot, user_history):

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id

        # التنظيف قبل أي شيء
        _reset_user_flows(user_id)

        # التحقق من الاشتراك إذا كان مفعّلاً
        if FORCE_SUB_CHANNEL_USERNAME:
            try:
                status = bot.get_chat_member(FORCE_SUB_CHANNEL_USERNAME, user_id).status
                if status not in ["member", "creator", "administrator"]:
                    bot.send_message(
                        message.chat.id,
                        f"⚠️ للاستخدام الكامل لبوت {BOT_NAME}\nيرجى الاشتراك بالقناة أولاً.",
                        reply_markup=_sub_inline_kb()
                    )
                    return
            except Exception:  # في حال فشل get_chat_member
                bot.send_message(
                    message.chat.id,
                    f"⚠️ للاستخدام الكامل لبوت {BOT_NAME}\nيرجى الاشتراك بالقناة أولاً.",
                    reply_markup=_sub_inline_kb()
                )
                return

        # بعد الاشتراك أو إذا لم يكن هناك شرط اشتراك
        bot.send_message(
            message.chat.id,
            WELCOME_MESSAGE,
            parse_mode="Markdown",
            reply_markup=_welcome_inline_kb()
        )
        user_history[user_id] = []


    # ---------------------------------------
    # Callback: إعادة فحص الاشتراك
    # ---------------------------------------
    @bot.callback_query_handler(func=lambda c: c.data == CB_CHECK_SUB)
    def cb_check_subscription(call):
        user_id = call.from_user.id

        # التنظيف (فور الضغط)
        _reset_user_flows(user_id)

        if FORCE_SUB_CHANNEL_USERNAME:
            try:
                status = bot.get_chat_member(FORCE_SUB_CHANNEL_USERNAME, user_id).status
                if status not in ["member", "creator", "administrator"]:
                    bot.answer_callback_query(call.id, "لم يتم العثور على اشتراك. اشترك ثم أعد المحاولة.", show_alert=True)
                    return
            except Exception:
                bot.answer_callback_query(call.id, "تعذر التحقق الآن. حاول لاحقاً.", show_alert=True)
                return

        # لو وصلنا هنا، اعتبره مشترك وأرسل الترحيب مع زر ستارت
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=WELCOME_MESSAGE,
            parse_mode="Markdown",
            reply_markup=_welcome_inline_kb()
        )
        user_history[user_id] = []


    # ---------------------------------------
    # Callback: ستارت (إدخال القائمة الرئيسية + تنظيف)
    # ---------------------------------------
    @bot.callback_query_handler(func=lambda c: c.data == CB_START)
    def cb_start_main(call):
        user_id = call.from_user.id
        name = getattr(call.from_user, "full_name", None) or call.from_user.first_name

        # تنظيف العمليات المعلّقة قبل الدخول
        _reset_user_flows(user_id)

        register_user_if_not_exist(user_id, name)
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "✨ تم تسجيلك بنجاح! هذه القائمة الرئيسية.",
            reply_markup=keyboards.main_menu()
        )


    # ---------------------------------------
    # دعم الرسائل النصية القديمة (توافقية)
    # ---------------------------------------
    @bot.message_handler(func=lambda msg: msg.text == "🚀 ابدأ بالتسوق العالمي")
    def enter_main_menu(msg):
        user_id = msg.from_user.id
        name = getattr(msg.from_user, "full_name", None) or msg.from_user.first_name

        # تنظيف
        _reset_user_flows(user_id)

        register_user_if_not_exist(user_id, name)
        bot.send_message(
            msg.chat.id,
            "✨ تم تسجيلك بنجاح! هذه القائمة الرئيسية.",
            reply_markup=keyboards.main_menu()
        )


    @bot.message_handler(func=lambda msg: msg.text == "🔄 ابدأ من جديد")
    def restart_user(msg):
        send_welcome(msg)


    @bot.message_handler(func=lambda msg: msg.text == "🌐 صفحتنا")
    def send_links(msg):
        user_id = msg.from_user.id
        user_history.setdefault(user_id, []).append("send_links")
        text = (
            "🌐 روابط صفحتنا:\n\n"
            "🔗 موقعنا الإلكتروني: https://example.com\n"
            "📘 فيسبوك: https://facebook.com/yourpage\n"
            "▶️ يوتيوب: https://youtube.com/yourchannel\n"
            "🎮 كيك: https://kick.com/yourchannel"
        )
        bot.send_message(msg.chat.id, text, reply_markup=keyboards.links_menu())


    @bot.message_handler(func=lambda msg: msg.text == "⬅️ رجوع")
    def go_back(msg):
        _reset_user_flows(msg.from_user.id)
        bot.send_message(msg.chat.id, "⬅️ تم الرجوع للقائمة الرئيسية", reply_markup=keyboards.main_menu())


# ---------------------------------------
# رسالة الترحيب الأصلية (دون تغيير جوهري)
# ---------------------------------------
WELCOME_MESSAGE = (
    f"مرحبًا بك في {BOT_NAME}, وجهتك الأولى للتسوق الإلكتروني!\n\n"
    "🚀 نحن هنا نقدم لك تجربة تسوق لا مثيل لها:\n"
    "💼 منتجات عالية الجودة.\n"
    "⚡ سرعة في التنفيذ.\n"
    "📞 دعم فني خبير تحت تصرفك.\n\n"
    "🌟 لماذا نحن الأفضل؟\n"
    "1️⃣ توفير منتجات رائعة بأسعار تنافسية.\n"
    "2️⃣ تجربة تسوق آمنة وسهلة.\n"
    "3️⃣ فريق محترف جاهز لخدمتك على مدار الساعة.\n\n"
    "🚨 *تحذيرات هامة لا يمكن تجاهلها!*\n"
    "1️⃣ أي معلومات خاطئة ترسلها... عليك تحمل مسؤوليتها.\n"
    "2️⃣ *سيتم حذف محفظتك* إذا لم تقم بأي عملية شراء خلال 40 يومًا.\n"
    "3️⃣ *لا تراسل الإدارة* إلا في حالة الطوارئ!\n\n"
    "🔔 *هل أنت جاهز؟* لأننا على استعداد تام لتلبية احتياجاتك!\n"
    "👇 اضغط على زر 🚀 للمتابعة."
)
