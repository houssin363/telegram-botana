from telebot import types
from handlers import keyboards
from config import BOT_NAME, FORCE_SUB_CHANNEL_USERNAME
from services.wallet_service import register_user_if_not_exist  # هذا مهم

def register(bot, user_history):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id
        # التحقق من الاشتراك إذا كنت تريد ذلك، يمكنك تعطيله إن لم يكن ضروريًا
        if FORCE_SUB_CHANNEL_USERNAME:
            try:
                status = bot.get_chat_member(FORCE_SUB_CHANNEL_USERNAME, user_id).status
                if status not in ["member", "creator", "administrator"]:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(
                        types.InlineKeyboardButton("🔔 اشترك الآن في القناة", url=f"https://t.me/{FORCE_SUB_CHANNEL_USERNAME[1:]}")
                    )
                    bot.send_message(
                        message.chat.id,
                        f"⚠️ للاستخدام الكامل لبوت {BOT_NAME}\nيرجى الاشتراك بالقناة أولاً.",
                        reply_markup=markup
                    )
                    return
            except:
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton("🔔 اشترك الآن في القناة", url=f"https://t.me/{FORCE_SUB_CHANNEL_USERNAME[1:]}")
                )
                bot.send_message(
                    message.chat.id,
                    f"⚠️ للاستخدام الكامل لبوت {BOT_NAME}\nيرجى الاشتراك بالقناة أولاً.",
                    reply_markup=markup
                )
                return

        # بعد الاشتراك أو إذا لم يكن هناك شرط اشتراك
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🚀 ابدأ بالتسوق العالمي")
        bot.send_message(
            message.chat.id,
            WELCOME_MESSAGE,
            parse_mode="Markdown",
            reply_markup=markup
        )
        user_history[user_id] = []

    @bot.message_handler(func=lambda msg: msg.text == "🚀 ابدأ بالتسوق العالمي")
    def enter_main_menu(msg):
        user_id = msg.from_user.id
        name = msg.from_user.full_name if hasattr(msg.from_user, "full_name") else msg.from_user.first_name
        # تسجيل المستخدم تلقائيًا إذا لم يكن مسجلاً
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
