# handlers/keyboards.py
from telebot import types

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 المنتجات"),
        types.KeyboardButton("💳 شحن محفظتي"),
        types.KeyboardButton("💰 محفظتي"),
        types.KeyboardButton("🛠️ الدعم الفني"),
        types.KeyboardButton("🖼️ خدمات إعلانية وتصميم"),
        types.KeyboardButton("🌐 صفحتنا"),
        types.KeyboardButton("🔄 ابدأ من جديد")
    )
    return markup

def products_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("🎮 شحن ألعاب و تطبيقات"),
        types.KeyboardButton("💵 شراء رصيد كاش"),
        types.KeyboardButton("💳 تحويل رصيد سوري"),
        types.KeyboardButton("🌐 دفع مزودات الإنترنت ADSL"),
        types.KeyboardButton("🎓 دفع رسوم جامعية"),
        types.KeyboardButton("🖼️ خدمات إعلانية وتصميم"),
        types.KeyboardButton("⬅️ رجوع")
    )
    return markup

def game_categories():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("🎯 شحن شدات ببجي العالمية"),
        types.KeyboardButton("🔥 شحن جواهر فري فاير"),
        types.KeyboardButton("🏏 تطبيق جواكر"),
        types.KeyboardButton("⬅️ رجوع")
    )
    return markup

def recharge_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("📲 سيرياتيل كاش"),
        types.KeyboardButton("📲 أم تي إن كاش"),
        types.KeyboardButton("📲 شام كاش"),
        types.KeyboardButton("💳 Payeer"),
        types.KeyboardButton("⬅️ رجوع"),
        types.KeyboardButton("🔄 ابدأ من جديد")
    )
    return markup

def cash_transfer_menu():
    return recharge_menu()

def syrian_balance_menu():
    from handlers.syr_units import SYRIATEL_PRODUCTS
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    buttons = [types.KeyboardButton(f"{p.name} - {p.price:,} ل.س") for p in SYRIATEL_PRODUCTS]
    buttons.append(types.KeyboardButton("⬅️ رجوع"))
    markup.add(*buttons)
    return markup

def wallet_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("💰 محفظتي"),
        types.KeyboardButton("🛍️ مشترياتي"),
        types.KeyboardButton("📑 سجل التحويلات"),
        types.KeyboardButton("🔁 تحويل من محفظتك إلى محفظة عميل آخر"),
        types.KeyboardButton("⬅️ رجوع"),
        types.KeyboardButton("🔄 ابدأ من جديد")
    )
    return markup

def support_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("🛠️ الدعم الفني"),
        types.KeyboardButton("⬅️ رجوع")
    )
    return markup

def media_services_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("🖼️ تصميم لوغو احترافي"),
        types.KeyboardButton("📱 إدارة ونشر يومي"),
        types.KeyboardButton("📢 إطلاق حملة إعلانية"),
        types.KeyboardButton("🧾 باقة متكاملة شهرية"),
        types.KeyboardButton("✏️ طلب مخصّص"),
        types.KeyboardButton("⬅️ رجوع")
    )
    return markup

def links_menu():
    # قائمة الروابط (تظهر بأزرار قابلة للضغط تفتح المتصفح)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🌐 موقعنا الرسمي", url="https://example.com"),
        types.InlineKeyboardButton("📢 قناتنا على تيليجرام", url="https://t.me/YourChannel")
    )
    return markup

def hide_keyboard():
    return types.ReplyKeyboardRemove()
