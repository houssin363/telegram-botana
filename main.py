import os
import telebot
from config import API_TOKEN
from handlers import start, wallet, support, admin, recharge, cash_transfer, products, media_services, wholesale
from handlers.keyboards import main_menu, products_menu, game_categories, cash_transfer_menu, syrian_balance_menu

bot = telebot.TeleBot(API_TOKEN)

# 🧠 تتبع حالة المستخدم
user_state = {}

# تسجيل الهاندلرز مع تمرير user_state للتتبع
start.register(bot, user_state)
wallet.register(bot, user_state)
support.register(bot, user_state)
admin.register(bot, user_state)
recharge.register(bot, user_state)
cash_transfer.register(bot, user_state)
products.register(bot, user_state)
media_services.register(bot, user_state)
wholesale.register(bot, user_state)

# ⬅️ زر الرجوع الذكي
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

print("🤖 البوت يعمل الآن...")

bot.infinity_polling()
