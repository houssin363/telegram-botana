from telebot import types
import math

# ---------------------------------------------------------------
# أداة مساعدة موحدة لبناء لوحات Inline مع Pagination
# ---------------------------------------------------------------
def _build_paged_inline_keyboard(
    labels,
    prefix: str,
    page: int = 0,
    page_size: int = 6,
    include_back: bool = True,
    back_cb: str | None = None,
):
    """يرجع كائن InlineKeyboardMarkup مع أزرار العناصر والتنقّل."""
    total = len(labels)
    pages = max(1, math.ceil(total / page_size))
    page = max(0, min(page, pages - 1))
    start, end = page * page_size, (page + 1) * page_size
    page_labels = labels[start:end]

    kb = types.InlineKeyboardMarkup()

    # أزرار العناصر
    for idx, text in enumerate(page_labels, start=start):
        cb = f"{prefix}:sel:{idx}"
        kb.add(types.InlineKeyboardButton(text=text, callback_data=cb))

    # صف التنقّل
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("◀️", callback_data=f"{prefix}:page:{page-1}"))
    nav.append(types.InlineKeyboardButton(f"{page+1}/{pages}", callback_data=f"{prefix}:noop"))
    if page < pages - 1:
        nav.append(types.InlineKeyboardButton("▶️", callback_data=f"{prefix}:page:{page+1}"))
    if nav:
        kb.row(*nav)

    # زر الرجوع
    if include_back:
        if back_cb is None:
            back_cb = f"{prefix}:back"
        kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data=back_cb))

    return kb


# ---------------------------------------------------------------
# القائمة الرئيسية – أصبحت Inline
# ---------------------------------------------------------------
def main_menu(page: int = 0):
    labels = [
        "🛒 المنتجات",
        "💳 شحن محفظتي",
        "💰 محفظتي",
        "🛠️ الدعم الفني",
        "🔄 ابدأ من جديد",
        "🌐 صفحتنا"
    ]
    return _build_paged_inline_keyboard(labels, prefix="main", page=page, page_size=6, include_back=False)


# ---------------------------------------------------------------
# قوائم المنتجات وما بعدها
# ---------------------------------------------------------------
def products_menu(page: int = 0):
    labels = [
        "🎮 شحن ألعاب و تطبيقات",
        "💳 تحويل وحدات فاتورة سوري",
        "🌐 دفع مزودات الإنترنت ADSL",
        "🎓 دفع رسوم جامعية",
        "حوالة مالية عبر شركات",
        "💵 تحويل الى رصيد كاش",
    ]
    return _build_paged_inline_keyboard(labels, prefix="prod", page=page, page_size=4)

def game_categories(page: int = 0):
    labels = [
        "🎯 شحن شدات ببجي العالمية",
        "🔥 شحن جواهر فري فاير",
        "🏏 تطبيق جواكر",
    ]
    return _build_paged_inline_keyboard(labels, prefix="gamecat", page=page, page_size=4)

def recharge_menu(page: int = 0):
    labels = [
        "📲 سيرياتيل كاش",
        "📲 أم تي إن كاش",
        "📲 شام كاش",
        "💳 Payeer",
        "🔄 ابدأ من جديد",
    ]
    return _build_paged_inline_keyboard(labels, prefix="rech", page=page, page_size=4)

def cash_transfer_menu(page: int = 0):
    labels = [
        "تحويل إلى سيرياتيل كاش",
        "تحويل إلى أم تي إن كاش",
        "تحويل إلى شام كاش",
        "🔄 ابدأ من جديد",
    ]
    return _build_paged_inline_keyboard(labels, prefix="cashtr", page=page, page_size=4)

def companies_transfer_menu(page: int = 0):
    labels = [
        "شركة الهرم",
        "شركة الفؤاد",
        "شركة شخاشير",
        "🔄 ابدأ من جديد",
    ]
    return _build_paged_inline_keyboard(labels, prefix="comptr", page=page, page_size=4)


# ---------------------------------------------------------------
# قائمة وحدات سيرياتيل (ديناميكية) – Inline مع Pagination
# ---------------------------------------------------------------
def syrian_balance_menu(page: int = 0):
    from handlers.syr_units import SYRIATEL_PRODUCTS
    labels = [f"{p.name} - {p.price:,} ل.س" for p in SYRIATEL_PRODUCTS]
    return _build_paged_inline_keyboard(labels, prefix="syrbal", page=page, page_size=5)


# ---------------------------------------------------------------
# قوائم المحفظة والدعم والروابط
# ---------------------------------------------------------------
def wallet_menu(page: int = 0):
    labels = [
        "💰 محفظتي",
        "🛍️ مشترياتي",
        "📑 سجل التحويلات",
        "🔁 تحويل من محفظتك إلى محفظة عميل آخر",
        "🔄 ابدأ من جديد",
    ]
    return _build_paged_inline_keyboard(labels, prefix="wallet", page=page, page_size=4)

def support_menu(page: int = 0):
    labels = ["🛠️ الدعم الفني"]
    return _build_paged_inline_keyboard(labels, prefix="support", page=page, page_size=4)

def links_menu(page: int = 0):
    labels = [
        "🌐 موقعنا",
        "📘 فيس بوك",
        "📸 إنستغرام",
    ]
    return _build_paged_inline_keyboard(labels, prefix="links", page=page, page_size=4)

def media_services_menu(page: int = 0):
    labels = [
        "🖼️ تصميم لوغو احترافي",
        "📱 إدارة ونشر يومي",
        "📢 إطلاق حملة إعلانية",
        "🧾 باقة متكاملة شهرية",
        "✏️ طلب مخصص",
    ]
    return _build_paged_inline_keyboard(labels, prefix="media", page=page, page_size=5)

# ---------------------------------------------------------------
# إخفاء الكيبورد (لم يتغيّر)
# ---------------------------------------------------------------
def hide_keyboard():
    return types.ReplyKeyboardRemove()
