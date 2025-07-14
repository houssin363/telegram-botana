import os
import telebot
from config import API_TOKEN, ADMIN_MAIN_ID

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
# 6) تشغيل البوت مع معالجة الأخطاء العامة
# ---------------------------------------------------------
print("🤖 البوت يعمل الآن…")

def run_bot():
    try:
        bot.infinity_polling(
            none_stop=True,
            skip_pending=True,
            long_polling_timeout=40,
        )
    except Exception as e:
        # أرسل الخطأ إلى الأدمن ليعرف بما حدث
        bot.send_message(ADMIN_MAIN_ID, f"❌ حدث خطأ في polling: {e}")
        # يمكنك إعادة المحاولة بعد تأخير بسيط:
        run_bot()

if __name__ == "__main__":
    run_bot()
