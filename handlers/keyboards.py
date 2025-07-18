from telebot import types

# -------------------------------------------------
# القائمة الرئيسية
# -------------------------------------------------
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 المنتجات"),
        types.KeyboardButton("💳 شحن محفظتي"),
        types.KeyboardButton("💰 محفظتي"),
        types.KeyboardButton("🛠️ الدعم الفني"),
        types.KeyboardButton("🔄 ابدأ من جديد"),
        types.KeyboardButton("🌐 صفحتنا"),
    )
    return markup


# -------------------------------------------------
# قائمة المنتجات (زر «تحويل كاش» الموحَّد)
# -------------------------------------------------
def products_menu():
    # row_width=2 ⇒ تيليجرام سيضع زرين في كل صف
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    buttons = [
        types.KeyboardButton("🎮 شحن ألعاب و تطبيقات"),
        types.KeyboardButton("💳 تحويل وحدات فاتورة سوري"),
        types.KeyboardButton("🌐 دفع مزودات الإنترنت ADSL"),
        types.KeyboardButton("🎓 دفع رسوم جامعية"),
        types.KeyboardButton("💵 تحويل كاش"),  # ← دمج الزرين هنا
        types.KeyboardButton("🖼️ خدمات إعلانية وتصميم"),
    ]
    markup.add(*buttons)

    # زر «رجوع» في صف مستقل
    markup.add(types.KeyboardButton("⬅️ رجوع"))
    return markup


# -------------------------------------------------
# فئات الألعاب
# -------------------------------------------------
def game_categories():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("🎯 شحن شدات ببجي العالمية"),
        types.KeyboardButton("🔥 شحن جواهر فري فاير"),
        types.KeyboardButton("🏏 تطبيق جواكر"),
        types.KeyboardButton("⬅️ رجوع"),
    )
    return markup


# -------------------------------------------------
# قائمة شحن المحفظة
# -------------------------------------------------
def recharge_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("📲 سيرياتيل كاش"),
        types.KeyboardButton("📲 أم تي إن كاش"),
        types.KeyboardButton("📲 شام كاش"),
        types.KeyboardButton("💳 Payeer"),
        types.KeyboardButton("⬅️ رجوع"),
        types.KeyboardButton("🔄 ابدأ من جديد"),
    )
    return markup


# -------------------------------------------------
# تحويل كاش (سيرياتيل / إم تي إن / شام)
# -------------------------------------------------
def cash_transfer_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("تحويل إلى سيرياتيل كاش"),
        types.KeyboardButton("تحويل إلى أم تي إن كاش"),
        types.KeyboardButton("تحويل إلى شام كاش"),
        types.KeyboardButton("⬅️ رجوع"),
        types.KeyboardButton("🔄 ابدأ من جديد"),
    )
    return markup


# -------------------------------------------------
# تحويل عبر شركات
# -------------------------------------------------
def companies_transfer_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("شركة الهرم"),
        types.KeyboardButton("شركة الفؤاد"),
        types.KeyboardButton("شركة شخاشير"),
        types.KeyboardButton("⬅️ رجوع"),
        types.KeyboardButton("🔄 ابدأ من جديد"),
    )
    return markup


# -------------------------------------------------
# وحدات رصيد سوري تل
# -------------------------------------------------
def syrian_balance_menu():
    from handlers.syr_units import SYRIATEL_PRODUCTS
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    buttons = [
        types.KeyboardButton(f"{p.name} - {p.price:,} ل.س") for p in SYRIATEL_PRODUCTS
    ]
    buttons.append(types.KeyboardButton("⬅️ رجوع"))
    markup.add(*buttons)
    return markup


# -------------------------------------------------
# قائمة المحفظة
# -------------------------------------------------
def wallet_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("💰 محفظتي"),
        types.KeyboardButton("🛍️ مشترياتي"),
        types.KeyboardButton("📑 سجل التحويلات"),
        types.KeyboardButton("🔁 تحويل من محفظتك إلى محفظة عميل آخر"),
        types.KeyboardButton("⬅️ رجوع"),
        types.KeyboardButton("🔄 ابدأ من جديد"),
    )
    return markup


# -------------------------------------------------
# الدعم الفني
# -------------------------------------------------
def support_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("🛠️ الدعم الفني"),
        types.KeyboardButton("⬅️ رجوع"),
    )
    return markup


# -------------------------------------------------
# الروابط
# -------------------------------------------------
def links_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("🌐 موقعنا"),
        types.KeyboardButton("📘 فيس بوك"),
        types.KeyboardButton("📸 إنستغرام"),
        types.KeyboardButton("⬅️ رجوع"),
    )
    return markup


# -------------------------------------------------
# خدمات وسائط الإعلام
# -------------------------------------------------
def media_services_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("🖼️ تصميم لوغو احترافي"),
        types.KeyboardButton("📱 إدارة ونشر يومي"),
        types.KeyboardButton("📢 إطلاق حملة إعلانية"),
        types.KeyboardButton("🧾 باقة متكاملة شهرية"),
        types.KeyboardButton("✏️ طلب مخصص"),
        types.KeyboardButton("⬅️ رجوع"),
    )
    return markup


# -------------------------------------------------
# إخفاء لوحة المفاتيح
# -------------------------------------------------
def hide_keyboard():
    return types.ReplyKeyboardRemove()
