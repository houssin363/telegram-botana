from telebot import types

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛍️ المنتجات"),
        types.KeyboardButton("💳 إعادة الشحن"),
        types.KeyboardButton("💼 المحفظة"),
        types.KeyboardButton("📤 تحويل رصيد"),
        types.KeyboardButton("🛠️ الدعم الفني"),
        types.KeyboardButton("🔄 ابدأ من جديد"),
        types.KeyboardButton("🌐 صفحتنا")
    )
    return markup

def links_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("⬅️ رجوع"))
    return markup

def products_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("🎮 شحن ألعاب و تطبيقات"),
        # يمكنك إضافة أنواع منتجات أخرى مثل بطاقات أو كاش هنا لاحقاً
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
