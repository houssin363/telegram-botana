from telebot import types
from handlers.syr_units import SYRIATEL_PRODUCTS

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 المنتجات"),
        types.KeyboardButton("💳 شحن محفظتي"),
        types.KeyboardButton("💰 محفظتي"),
        types.KeyboardButton("🛠️ الدعم الفني"),
        types.KeyboardButton("🔄 ابدأ من جديد"),
        types.KeyboardButton("🌐 صفحتنا")
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

# Same layout as recharge_menu (for going back into the cash-transfer flow)
def cash_transfer_menu():
    return recharge_menu()

def syrian_balance_menu():
    """
    يُعيد لوحة الأزرار لجميع منتجات سيرياتيل (الوحدات)،
    مع زر للعودة إلى القائمة السابقة.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    # أزرار لكل منتج سيرياتيل بحسب اسمه
    buttons = [types.KeyboardButton(p.name) for p in SYRIATEL_PRODUCTS]
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
        types.KeyboardButton("🧑‍💼 تواصل مع الادمن"),
        types.KeyboardButton("⬅️ رجوع")
    )
    return markup

def hide_keyboard():
    return types.ReplyKeyboardRemove()

def links_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("🌐 موقعنا"),
        types.KeyboardButton("📘 فيس بوك"),
        types.KeyboardButton("📸 إنستغرام"),
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
        types.KeyboardButton("✏️ طلب مخصص"),
        types.KeyboardButton("⬅️ رجوع")
    )
    return markup
