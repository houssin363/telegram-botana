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
    markup.add(
        types.KeyboardButton("⬅️ رجوع")
    )
    return markup
