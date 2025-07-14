import os
import sys
import logging
import telebot
from config import API_TOKEN

# ---------------------------------------------------------
# تسجيل الأخطاء لظهورها في سجلّ Render
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

def _unhandled_exception_hook(exc_type, exc_value, exc_tb):
    """طباعة أي استثناء غير مُعالج بالكامل في اللوجز."""
    logging.critical("❌ Unhandled exception:", exc_info=(exc_type, exc_value, exc_tb))

sys.excepthook = _unhandled_exception_hook

# ---------------------------------------------------------
# 1) إنشاء كائن البوت ثم حذف أي Webhook سابق لتجنّب خطأ 409
# ---------------------------------------------------------
bot = telebot.TeleBot(API_TOKEN)
bot.delete_webhook(drop_pending_updates=True)

# ---------------------------------------------------------
# 2) استيراد جميع الهاندلرز بعد تهيئة البوت
# ---------------------------------------------------------
from handlers import (
    start,
    wallet,
    support,
    admin,
    recharge,
    cash_transfer,
    products,
    media_services,
    wholesale,
    syr_units,  # تسجيل وحدات سورية
)
from handlers.keyboards import (
    main_menu,
    products_menu,
    game_categories,
    recharge_menu,
    cash_transfer_menu,
    syrian_balance_menu,
    wallet_menu,
    support_menu,
    links_menu,
    media_services_menu,
)

# ---------------------------------------------------------
# 3) حالة المستخدم
# ---------------------------------------------------------
user_state: dict[int, str] = {}

# ---------------------------------------------------------
# 4) تسجيل الهاندلرز مع تمرير user_state للتتبع
# ---------------------------------------------------------
start.register(bot, user_state)
wallet.register(bot, user_state)
support.register(bot, user_state)
admin.register(bot, user_state)
recharge.register(bot, user_state)
cash_transfer.register(bot, user_state)
products.register(bot, user_state)
media_services.register(bot, user_state)
wholesale.register(bot, user_state)
syr_units.register(bot, user_state)

# ---------------------------------------------------------
# 4.1) ربط النظام الجديد لأوامر المنتجات (لا تحذف هذا السطر)
# ---------------------------------------------------------
ADMIN_IDS = [123456789]  # ضع هنا آيدي الأدمنات الذين يستلمون الطلبات (يمكنك إضافة أكثر من آيدي)
products.setup_inline_handlers(bot, ADMIN_IDS)
# ---------------------------------------------------------
# 5) زر الرجوع الذكي
# ---------------------------------------------------------
@bot.message_handler(func=lambda msg: msg.text == "⬅️ رجوع")
def handle_back(msg):
    user_id = msg.from_user.id
    state = user_state.get(user_id, "main_menu")

    if state == "products_menu":
        bot.send_message(msg.chat.id, "⬅️ عدت إلى المنتجات.", reply_markup=products_menu())
        user_state[user_id] = "main_menu"
    elif state == "main_menu":
        bot.send_message(msg.chat.id, "⬅️ عدت إلى القائمة الرئيسية.", reply_markup=main_menu())
    elif state == "game_menu":
        bot.send_message(msg.chat.id, "⬅️ عدت إلى الألعاب.", reply_markup=game_categories())
        user_state[user_id] = "products_menu"
    elif state == "cash_menu":
        bot.send_message(msg.chat.id, "⬅️ عدت إلى قائمة الكاش.", reply_markup=cash_transfer_menu())
        user_state[user_id] = "main_menu"
    elif state == "syrian_transfer":
        bot.send_message(msg.chat.id, "⬅️ عدت إلى تحويل الرصيد السوري.", reply_markup=syrian_balance_menu())
        user_state[user_id] = "products_menu"
    else:
        bot.send_message(msg.chat.id, "⬅️ عدت إلى البداية.", reply_markup=main_menu())
        user_state[user_id] = "main_menu"

# ---------------------------------------------------------
# 6) تشغيل البوت
# ---------------------------------------------------------
print("🤖 البوت يعمل الآن…")

try:
    bot.infinity_polling(
        none_stop=True,
        skip_pending=True,
        long_polling_timeout=40,
    )
except telebot.apihelper.ApiTelegramException as e:
    # خطأ 409 = نسخة أخرى من البوت متصلة بالفعل
    if getattr(e, "error_code", None) == 409:
        logging.critical("❌ تم إيقاف هذه النسخة لأن نسخة أخرى من البوت متصلة بالفعل.")
    else:
        # أعد رفع الخطأ لتعرف المشكلات الأخرى
        raise
import scheduled_tasks  # لإطلاق المهام الدورية تلقائيًا عند تشغيل البوت
