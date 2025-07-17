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

def products_menu():
    # تم التحويل إلى لوحة أزرار مضمّنة (InlineKeyboardMarkup)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎮 شحن ألعاب و تطبيقات", callback_data="product_game_recharge"),
        types.InlineKeyboardButton("💳 تحويل وحدات فاتورة سوري", callback_data="product_syrian_units_transfer"),
        types.InlineKeyboardButton("🌐 دفع مزودات الإنترنت ADSL", callback_data="product_adsl_payment"),
        types.InlineKeyboardButton("🎓 دفع رسوم جامعية", callback_data="product_university_fees"),
        types.InlineKeyboardButton("حوالة مالية عبر شركات", callback_data="product_companies_transfer"),
        types.InlineKeyboardButton("💵 تحويل الى رصيد كاش", callback_data="product_cash_credit"),
        types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main")
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
