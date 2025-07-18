# -*- coding: utf-8 -*-
"""
start.py  (مع زر ستارت + متابعة القناة عبر InlineKeyboard)
-----------------------------------------------------------
تم تلبية الطلب: إضافة زر *ستارت* في رسالة الترحيب، وكذلك في رسالة
متابعة/الاشتراك بالقناة (Force Subscribe).

التدفق:
  /start  -> فحص الاشتراك (إن طُلب) ->
      - غير مشترك: رسالة اشتراك + زرين: [اشترك الآن - URL] [✅ تم الاشتراك | ستارت]
      - مشترك: رسالة ترحيب + زر [🚀 ستارت]
  الضغط على ستارت (callback) يسجل المستخدم (إن لم يكن مسجل) ويدخل القائمة الرئيسية.

تم الحفاظ على بقية الكود (رسائل نصية قديمة) للتوافق العكسي.
"""

from telebot import types
from handlers import keyboards
from config import BOT_NAME, FORCE_SUB_CHANNEL_USERNAME
from services.wallet_service import register_user_if_not_exist  # هذا مهم

# --------------------------
# مفاتيح Callback جديدة
# --------------------------
CB_START = "cb_start_main"
CB_CHECK_SUB = "cb_check_sub"

def _sub_inline_kb():
    """لوحة اشتراك بالقناة + زر ستارت لإعادة الفحص."""
    kb = types.InlineKeyboardMarkup()
    # رابط الاشتراك
    if FORCE_SUB_CHANNEL_USERNAME:
        kb.add(
            types.InlineKeyboardButton(
                "🔔 اشترك الآن في القناة",
                url=f"https://t.me/{FORCE_SUB_CHANNEL_USERNAME[1:]}"  # إزالة @
            )
        )
    # زر ستارت (إعادة التحقق / متابعة)
    kb.add(types.InlineKeyboardButton("✅ تم الاشتراك | ستارت", callback_data=CB_CHECK_SUB))
    return kb

def _welcome_inline_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🚀 ستارت", callback_data=CB_START))
    return kb


def register(bot, user_history):

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id
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
    # Callback: إعادة فحص الاشتراك / ستارت
    # ---------------------------------------
    @bot.callback_query_handler(func=lambda c: c.data == CB_CHECK_SUB)
    def cb_check_subscription(call):
        user_id = call.from_user.id
        # فحص مرة أخرى
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
    # Callback: ستارت (إدخال القائمة الرئيسية)
    # ---------------------------------------
    @bot.callback_query_handler(func=lambda c: c.data == CB_START)
    def cb_start_main(call):
        user_id = call.from_user.id
        name = getattr(call.from_user, "full_name", None) or call.from_user.first_name
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
        name = msg.from_user.full_name if hasattr(msg.from_user, "full_name") else msg.from_user.first_name
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
