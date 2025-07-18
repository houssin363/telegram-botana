from telebot import types

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


def products_menu(page: int = 1) -> types.ReplyKeyboardMarkup:
    """
    page = 1 ➜ الصفحة الأولى
    page = 2 ➜ الصفحة الثانية
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # محتوى كل صفحة
    page1 = [
        "🎮 شحن ألعاب و تطبيقات",
        "💳 تحويل وحدات فاتورة سوري",
        "🌐 دفع مزودات الإنترنت ADSL",
        "🎓 دفع رسوم جامعية",
        "➡️ التالي",                 # زر الانتقال للصفحة 2
    ]

    page2 = [
        "حوالة مالية عبر شركات",
        "💵 تحويل الى رصيد كاش",
        "🖼️ خدمات إعلانية وتصميم",
        "⬅️ السابق",                 # رجوع للصفحة 1
    ]

    buttons = page1 if page == 1 else page2
    markup.add(*(types.KeyboardButton(b) for b in buttons))
    return markup

# -------------------------------------------------
# معالجات البوت
# -------------------------------------------------
@bot.message_handler(commands=["products"])
def send_products(message):
    """إرسال الصفحة الأولى عند أمر /products"""
    bot.send_message(
        message.chat.id,
        "اختر خدمة:",
        reply_markup=products_menu(page=1)
    )

# زر «التالي» ⇠ انتقل للصفحة 2
@bot.message_handler(func=lambda m: m.text == "➡️ التالي")
def next_page(message):
    bot.send_message(
        message.chat.id,
        "صفحة ٢/٢:",
        reply_markup=products_menu(page=2)
    )

# زر «السابق» ⇠ ارجع للصفحة 1
@bot.message_handler(func=lambda m: m.text == "⬅️ السابق")
def prev_page(message):
    bot.send_message(
        message.chat.id,
        "صفحة ١/٢:",
        reply_markup=products_menu(page=1)
    )
    
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
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("تحويل إلى سيرياتيل كاش"),
        types.KeyboardButton("تحويل إلى أم تي إن كاش"),
        types.KeyboardButton("تحويل إلى شام كاش"),
        types.KeyboardButton("⬅️ رجوع"),
        types.KeyboardButton("🔄 ابدأ من جديد")
    )
    return markup

def companies_transfer_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("شركة الهرم"),
        types.KeyboardButton("شركة الفؤاد"),
        types.KeyboardButton("شركة شخاشير"),
        types.KeyboardButton("⬅️ رجوع"),
        types.KeyboardButton("🔄 ابدأ من جديد")
    )
    return markup

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

def hide_keyboard():
    return types.ReplyKeyboardRemove()
