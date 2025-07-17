from telebot import types

# Aliases for convenience
InlineKeyboardButton = types.InlineKeyboardButton
InlineKeyboardMarkup = types.InlineKeyboardMarkup
InlineKeyboardRemove = types.InlineKeyboardRemove  # corrected to remove inline keyboard

def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("🛒 المنتجات", callback_data="🛒 المنتجات"),
        InlineKeyboardButton("💳 شحن محفظتي", callback_data="💳 شحن محفظتي"),
        InlineKeyboardButton("💰 محفظتي", callback_data="💰 محفظتي"),
        InlineKeyboardButton("🛠️ الدعم الفني", callback_data="🛠️ الدعم الفني"),
        InlineKeyboardButton("🔄 ابدأ من جديد", callback_data="🔄 ابدأ من جديد"),
        InlineKeyboardButton("🌐 صفحتنا", callback_data="🌐 صفحتنا"),
    ]
    markup.add(*buttons)
    return markup

def products_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("🎮 شحن ألعاب و تطبيقات", callback_data="🎮 شحن ألعاب و تطبيقات"),
        InlineKeyboardButton("💳 تحويل وحدات فاتورة سوري", callback_data="💳 تحويل وحدات فاتورة سوري"),
        InlineKeyboardButton("🌐 دفع مزودات الإنترنت ADSL", callback_data="🌐 دفع مزودات الإنترنت ADSL"),
        InlineKeyboardButton("🎓 دفع رسوم جامعية", callback_data="🎓 دفع رسوم جامعية"),
        InlineKeyboardButton("حوالة مالية عبر شركات", callback_data="حوالة مالية عبر شركات"),
        InlineKeyboardButton("💵 تحويل الى رصيد كاش", callback_data="💵 تحويل الى رصيد كاش"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="⬅️ رجوع"),
    ]
    markup.add(*buttons)
    return markup

def game_categories():
    markup = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("🎯 شحن شدات ببجي العالمية", callback_data="🎯 شحن شدات ببجي العالمية"),
        InlineKeyboardButton("🔥 شحن جواهر فري فاير", callback_data="🔥 شحن جواهر فري فاير"),
        InlineKeyboardButton("🏏 تطبيق جواكر", callback_data="🏏 تطبيق جواكر"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="⬅️ رجوع"),
    ]
    markup.add(*buttons)
    return markup

def recharge_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("📲 سيرياتيل كاش", callback_data="📲 سيرياتيل كاش"),
        InlineKeyboardButton("📲 أم تي إن كاش", callback_data="📲 أم تي إن كاش"),
        InlineKeyboardButton("📲 شام كاش", callback_data="📲 شام كاش"),
        InlineKeyboardButton("💳 Payeer", callback_data="💳 Payeer"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="⬅️ رجوع"),
        InlineKeyboardButton("🔄 ابدأ من جديد", callback_data="🔄 ابدأ من جديد"),
    ]
    markup.add(*buttons)
    return markup

def cash_transfer_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("تحويل إلى سيرياتيل كاش", callback_data="تحويل إلى سيرياتيل كاش"),
        InlineKeyboardButton("تحويل إلى أم تي إن كاش", callback_data="تحويل إلى أم تي إن كاش"),
        InlineKeyboardButton("تحويل إلى شام كاش", callback_data="تحويل إلى شام كاش"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="⬅️ رجوع"),
        InlineKeyboardButton("🔄 ابدأ من جديد", callback_data="🔄 ابدأ من جديد"),
    ]
    markup.add(*buttons)
    return markup

def companies_transfer_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("شركة الهرم", callback_data="شركة الهرم"),
        InlineKeyboardButton("شركة الفؤاد", callback_data="شركة الفؤاد"),
        InlineKeyboardButton("شركة شخاشير", callback_data="شركة شخاشير"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="⬅️ رجوع"),
        InlineKeyboardButton("🔄 ابدأ من جديد", callback_data="🔄 ابدأ من جديد"),
    ]
    markup.add(*buttons)
    return markup

def syrian_balance_menu(page=1, page_size=5):
    from handlers.syr_units import SYRIATEL_PRODUCTS
    items = [(f"{p.name} - {p.price:,} ل.س", f"{p.name}") for p in SYRIATEL_PRODUCTS]
    total = len(items)
    pages = (total + page_size - 1) // page_size
    page = max(1, min(page, pages))
    start = (page - 1) * page_size
    end = start + page_size

    markup = InlineKeyboardMarkup(row_width=1)
    for text, data in items[start:end]:
        markup.add(InlineKeyboardButton(text, callback_data=data))

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"syriatel_page_{page-1}"))
    if page < pages:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"syriatel_page_{page+1}"))
    if nav_buttons:
        markup.row(*nav_buttons)

    markup.add(InlineKeyboardButton("⬅️ رجوع", callback_data="⬅️ رجوع"))
    return markup

def wallet_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("💰 محفظتي", callback_data="💰 محفظتي"),
        InlineKeyboardButton("🛍️ مشترياتي", callback_data="🛍️ مشترياتي"),
        InlineKeyboardButton("📑 سجل التحويلات", callback_data="📑 سجل التحويلات"),
        InlineKeyboardButton("🔁 تحويل من محفظتك إلى محفظة عميل آخر", callback_data="🔁 تحويل من محفظتك إلى محفظة عميل آخر"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="⬅️ رجوع"),
        InlineKeyboardButton("🔄 ابدأ من جديد", callback_data="🔄 ابدأ من جديد"),
    ]
    markup.add(*buttons)
    return markup

def support_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("🛠️ الدعم الفني", callback_data="🛠️ الدعم الفني"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="⬅️ رجوع"),
    ]
    markup.add(*buttons)
    return markup

def links_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("🌐 موقعنا", callback_data="🌐 موقعنا"),
        InlineKeyboardButton("📘 فيس بوك", callback_data="📘 فيس بوك"),
        InlineKeyboardButton("📸 إنستغرام", callback_data="📸 إنستغرام"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="⬅️ رجوع"),
    ]
    markup.add(*buttons)
    return markup

def media_services_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("🖼️ تصميم لوغو احترافي", callback_data="🖼️ تصميم لوغو احترافي"),
        InlineKeyboardButton("📱 إدارة ونشر يومي", callback_data="📱 إدارة ونشر يومي"),
        InlineKeyboardButton("📢 إطلاق حملة إعلانية", callback_data="📢 إطلاق حملة إعلانية"),
        InlineKeyboardButton("🧾 باقة متكاملة شهرية", callback_data="🧾 باقة متكاملة شهرية"),
        InlineKeyboardButton("✏️ طلب مخصص", callback_data="✏️ طلب مخصص"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="⬅️ رجوع"),
    ]
    markup.add(*buttons)
    return markup

def hide_keyboard():
    # Returns an empty inline keyboard to remove it
    return InlineKeyboardRemove()

def register_callback_handlers(bot):
    @bot.callback_query_handler(func=lambda call: True)
    def handle_inline_query(call):
        data = call.data
        # Pagination for Syrian balance menu
        if data.startswith("syriatel_page_"):
            page = int(data.split("_")[-1])
            markup = syrian_balance_menu(page=page)
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup
            )
        # Process other callback_data as needed...
        bot.answer_callback_query(call.id)
