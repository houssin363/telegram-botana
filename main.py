import os
import telebot
from config import API_TOKEN
from handlers import start, wallet, support, admin, recharge, cash_transfer, products

bot = telebot.TeleBot(API_TOKEN)
user_history = {}

# تسجيل الهاندلرز
start.register(bot, user_history)
wallet.register(bot, user_history)
support.register(bot, user_history)
admin.register(bot, user_history)
recharge.register(bot, user_history)
cash_transfer.register(bot, user_history)
products.register(bot, user_history)

print("🤖 البوت يعمل الآن...")

bot.infinity_polling()
