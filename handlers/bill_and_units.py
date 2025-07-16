from telebot import types
from services.wallet_service import has_sufficient_balance, deduct_balance, get_balance
from config import ADMIN_MAIN_ID

# --- قوائم المنتجات (وحدات) وأسعارها
SYRIATEL_UNITS = [
    {"name": "1000 وحدة", "price": 1200},
    {"name": "1500 وحدة", "price": 1800},
    {"name": "2013 وحدة", "price": 2400},
    {"name": "3068 وحدة", "price": 3682},
    {"name": "4506 وحدة", "price": 5400},
    {"name": "5273 وحدة", "price": 6285},
    {"name": "7190 وحدة", "price": 8628},
    {"name": "9587 وحدة", "price": 11500},
    {"name": "13039 وحدة", "price": 15500},
]

MTN_UNITS = [
    {"name": "1000 وحدة", "price": 1200},
    {"name": "5000 وحدة", "price": 6000},
    {"name": "7000 وحدة", "price": 8400},
    {"name": "10000 وحدة", "price": 12000},
    {"name": "15000 وحدة", "price": 18000},
    {"name": "20000 وحدة", "price": 24000},
    {"name": "23000 وحدة", "price": 27600},
    {"name": "30000 وحدة", "price": 36000},
    {"name": "36000 وحدة", "price": 43200},
]

user_states = {}

def make_inline_buttons(*buttons):
    kb = types.InlineKeyboardMarkup()
    for text, data in buttons:
        kb.add(types.InlineKeyboardButton(text, callback_data=data))
    return kb

def units_bills_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton("🔴 وحدات سيرياتيل"),
        types.KeyboardButton("🔴 فاتورة سيرياتيل"),
        types.KeyboardButton("🟡 وحدات MTN"),
        types.KeyboardButton("🟡 فاتورة MTN"),
    )
    kb.add(types.KeyboardButton("⬅️ رجوع"))
    return kb

def register_bill_and_units(bot, history):
    # ===== قائمة الخدمات الرئيسية =====
    @bot.message_handler(func=lambda msg: msg.text == "💳 تحويل وحدات فاتورة سوري")
    def open_main_menu(msg):
        user_id = msg.from_user.id
        history.setdefault(user_id, []).append("units_bills_menu")
        user_states[user_id] = {"step": None}
        bot.send_message(msg.chat.id, "اختر الخدمة:", reply_markup=units_bills_menu())

    ########## وحدات سيرياتيل ##########
    @bot.message_handler(func=lambda msg: msg.text == "🔴 وحدات سيرياتيل")
    def syr_units_menu(msg):
        user_id = msg.from_user.id
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for u in SYRIATEL_UNITS:
            kb.add(types.KeyboardButton(f"{u['name']} - {u['price']:,} ل.س"))
        kb.add(types.KeyboardButton("⬅️ رجوع"))
        user_states[user_id] = {"step": "select_syr_unit"}
        bot.send_message(msg.chat.id, "اختر كمية الوحدات:", reply_markup=kb)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "select_syr_unit")
    def syr_unit_select(msg):
        user_id = msg.from_user.id
        unit = next((u for u in SYRIATEL_UNITS if f"{u['name']} - {u['price']:,} ل.س" == msg.text), None)
        if not unit:
            bot.send_message(msg.chat.id, "⚠️ اختر كمية من القائمة.")
            return
        user_states[user_id] = {"step": "syr_unit_number", "unit": unit}
        kb = make_inline_buttons(("❌ إلغاء", "cancel_all"))
        bot.send_message(msg.chat.id, "📱 أدخل الرقم أو الكود الذي يبدأ بـ 093 أو 098 أو 099:", reply_markup=kb)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "syr_unit_number")
    def syr_unit_number(msg):
        user_id = msg.from_user.id
        number = msg.text.strip()
        state = user_states[user_id]
        state["number"] = number
        state["step"] = "syr_unit_confirm"
        unit = state["unit"]
        kb = make_inline_buttons(
            ("❌ إلغاء", "cancel_all"),
            ("✔️ تأكيد الشراء", "syr_unit_final_confirm")
        )
        bot.send_message(
            msg.chat.id,
            f"هل أنت متأكد من شراء {unit['name']} بسعر {unit['price']:,} ل.س للرقم:\n{number}؟",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "syr_unit_final_confirm")
    def syr_unit_final_confirm(call):
        user_id = call.from_user.id
        state = user_states[user_id]
        state["step"] = "wait_admin_syr_unit"
        kb_admin = make_inline_buttons(
            ("✅ تأكيد العملية", f"admin_accept_syr_unit_{user_id}"),
            ("❌ رفض", f"admin_reject_syr_unit_{user_id}")
        )
        summary = (
            f"🔴 طلب وحدات سيرياتيل:\n"
            f"👤 المستخدم: {user_id}\n"
            f"📱 الرقم/الكود: {state['number']}\n"
            f"💵 الكمية: {state['unit']['name']}\n"
            f"💰 السعر: {state['unit']['price']:,} ل.س\n"
            f"✅ بانتظار موافقة الإدارة"
        )
        bot.send_message(call.message.chat.id, "✅ تم إرسال الطلب للإدارة، بانتظار الموافقة.")
        bot.send_message(ADMIN_MAIN_ID, summary, reply_markup=kb_admin)

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_all")
    def cancel_all(call):
        user_states.pop(call.from_user.id, None)
        bot.edit_message_text("❌ تم إلغاء العملية.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_accept_syr_unit_"))
    def admin_accept_syr_unit(call):
        user_id = int(call.data.split("_")[-1])
        state = user_states.get(user_id, {})
        price = state.get("unit", {}).get("price", 0)
        balance = get_balance(user_id)
        if balance < price:
            kb = make_inline_buttons(
                ("❌ إلغاء", "cancel_all"),
                ("💼 الذهاب للمحفظة", "go_wallet")
            )
            bot.send_message(user_id,
                f"❌ لا يوجد رصيد كافٍ في محفظتك.\nرصيدك: {balance:,} ل.س\nالمطلوب: {price:,} ل.س\n"
                f"الناقص: {price - balance:,} ل.س", reply_markup=kb)
            bot.answer_callback_query(call.id, "❌ رصيد غير كافٍ")
            user_states.pop(user_id, None)
            return
        deduct_balance(user_id, price)
        bot.send_message(user_id, f"✅ تم شراء {state['unit']['name']} لوحدات سيرياتيل بنجاح.")
        bot.answer_callback_query(call.id, "✅ تم تنفيذ العملية")
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_reject_syr_unit_"))
    def admin_reject_syr_unit(call):
        user_id = int(call.data.split("_")[-1])
        bot.send_message(user_id, "❌ تم رفض طلب وحدات سيرياتيل من الإدارة.")
        bot.answer_callback_query(call.id, "❌ تم رفض الطلب")
        user_states.pop(user_id, None)

    ########## وحدات MTN ##########
    @bot.message_handler(func=lambda msg: msg.text == "🟡 وحدات MTN")
    def mtn_units_menu(msg):
        user_id = msg.from_user.id
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for u in MTN_UNITS:
            kb.add(types.KeyboardButton(f"{u['name']} - {u['price']:,} ل.س"))
        kb.add(types.KeyboardButton("⬅️ رجوع"))
        user_states[user_id] = {"step": "select_mtn_unit"}
        bot.send_message(msg.chat.id, "اختر كمية الوحدات:", reply_markup=kb)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "select_mtn_unit")
    def mtn_unit_select(msg):
        user_id = msg.from_user.id
        unit = next((u for u in MTN_UNITS if f"{u['name']} - {u['price']:,} ل.س" == msg.text), None)
        if not unit:
            bot.send_message(msg.chat.id, "⚠️ اختر كمية من القائمة.")
            return
        user_states[user_id] = {"step": "mtn_unit_number", "unit": unit}
        kb = make_inline_buttons(("❌ إلغاء", "cancel_all"))
        bot.send_message(msg.chat.id, "📱 أدخل الرقم أو الكود الذي يبدأ بـ 094 أو 095 أو 096:", reply_markup=kb)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "mtn_unit_number")
    def mtn_unit_number(msg):
        user_id = msg.from_user.id
        number = msg.text.strip()
        state = user_states[user_id]
        state["number"] = number
        state["step"] = "mtn_unit_confirm"
        unit = state["unit"]
        kb = make_inline_buttons(
            ("❌ إلغاء", "cancel_all"),
            ("✔️ تأكيد الشراء", "mtn_unit_final_confirm")
        )
        bot.send_message(
            msg.chat.id,
            f"هل أنت متأكد من شراء {unit['name']} بسعر {unit['price']:,} ل.س للرقم:\n{number}؟",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "mtn_unit_final_confirm")
    def mtn_unit_final_confirm(call):
        user_id = call.from_user.id
        state = user_states[user_id]
        state["step"] = "wait_admin_mtn_unit"
        kb_admin = make_inline_buttons(
            ("✅ تأكيد العملية", f"admin_accept_mtn_unit_{user_id}"),
            ("❌ رفض", f"admin_reject_mtn_unit_{user_id}")
        )
        summary = (
            f"🟡 طلب وحدات MTN:\n"
            f"👤 المستخدم: {user_id}\n"
            f"📱 الرقم/الكود: {state['number']}\n"
            f"💵 الكمية: {state['unit']['name']}\n"
            f"💰 السعر: {state['unit']['price']:,} ل.س\n"
            f"✅ بانتظار موافقة الإدارة"
        )
        bot.send_message(call.message.chat.id, "✅ تم إرسال الطلب للإدارة، بانتظار الموافقة.")
        bot.send_message(ADMIN_MAIN_ID, summary, reply_markup=kb_admin)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_accept_mtn_unit_"))
    def admin_accept_mtn_unit(call):
        user_id = int(call.data.split("_")[-1])
        state = user_states.get(user_id, {})
        price = state.get("unit", {}).get("price", 0)
        balance = get_balance(user_id)
        if balance < price:
            kb = make_inline_buttons(
                ("❌ إلغاء", "cancel_all"),
                ("💼 الذهاب للمحفظة", "go_wallet")
            )
            bot.send_message(user_id,
                f"❌ لا يوجد رصيد كافٍ في محفظتك.\nرصيدك: {balance:,} ل.س\nالمطلوب: {price:,} ل.س\n"
                f"الناقص: {price - balance:,} ل.س", reply_markup=kb)
            bot.answer_callback_query(call.id, "❌ رصيد غير كافٍ")
            user_states.pop(user_id, None)
            return
        deduct_balance(user_id, price)
        bot.send_message(user_id, f"✅ تم شراء {state['unit']['name']} لوحدات MTN بنجاح.")
        bot.answer_callback_query(call.id, "✅ تم تنفيذ العملية")
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_reject_mtn_unit_"))
    def admin_reject_mtn_unit(call):
        user_id = int(call.data.split("_")[-1])
        bot.send_message(user_id, "❌ تم رفض طلب وحدات MTN من الإدارة.")
        bot.answer_callback_query(call.id, "❌ تم رفض الطلب")
        user_states.pop(user_id, None)

    ########## فاتورة سيرياتيل ##########
    @bot.message_handler(func=lambda msg: msg.text == "🔴 فاتورة سيرياتيل")
    def syr_bill_entry(msg):
        user_id = msg.from_user.id
        user_states[user_id] = {"step": "syr_bill_number"}
        kb = make_inline_buttons(("❌ إلغاء", "cancel_all"))
        bot.send_message(msg.chat.id, "📱 أدخل رقم سيرياتيل المراد دفع فاتورته:", reply_markup=kb)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "syr_bill_number")
    def syr_bill_number(msg):
        user_id = msg.from_user.id
        number = msg.text.strip()
        user_states[user_id]["number"] = number
        user_states[user_id]["step"] = "syr_bill_number_confirm"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cancel_all"),
            ("✏️ تعديل", "edit_syr_bill_number"),
            ("✔️ تأكيد", "confirm_syr_bill_number")
        )
        bot.send_message(msg.chat.id, f"هل الرقم التالي صحيح؟\n{number}", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "edit_syr_bill_number")
    def edit_syr_bill_number(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "syr_bill_number"
        bot.send_message(call.message.chat.id, "📱 أعد إدخال رقم الموبايل:")

    @bot.callback_query_handler(func=lambda call: call.data == "confirm_syr_bill_number")
    def confirm_syr_bill_number(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "syr_bill_amount"
        kb = make_inline_buttons(("❌ إلغاء", "cancel_all"))
        bot.send_message(call.message.chat.id, "💵 أدخل مبلغ الفاتورة بالليرة:", reply_markup=kb)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "syr_bill_amount")
    def syr_bill_amount(msg):
        user_id = msg.from_user.id
        try:
            amount = int(msg.text)
            if amount <= 0:
                raise ValueError
        except:
            bot.send_message(msg.chat.id, "⚠️ أدخل مبلغ صحيح.")
            return
        user_states[user_id]["amount"] = amount
        user_states[user_id]["step"] = "syr_bill_amount_confirm"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cancel_all"),
            ("✏️ تعديل", "edit_syr_bill_amount"),
            ("✔️ تأكيد", "confirm_syr_bill_amount")
        )
        bot.send_message(
            msg.chat.id,
            f"هل المبلغ التالي صحيح؟\n{amount:,} ل.س", reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "edit_syr_bill_amount")
    def edit_syr_bill_amount(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "syr_bill_amount"
        bot.send_message(call.message.chat.id, "💵 أعد إرسال مبلغ الفاتورة:")

    @bot.callback_query_handler(func=lambda call: call.data == "confirm_syr_bill_amount")
    def confirm_syr_bill_amount(call):
        user_id = call.from_user.id
        amount = user_states[user_id]["amount"]
        amount_with_fee = int(amount * 1.17)
        user_states[user_id]["amount_with_fee"] = amount_with_fee
        user_states[user_id]["step"] = "syr_bill_final_confirm"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cancel_all"),
            ("✔️ تأكيد", "final_confirm_syr_bill")
        )
        bot.send_message(
            call.message.chat.id,
            f"سيتم دفع فاتورة سيرياتيل للرقم: {user_states[user_id]['number']}\n"
            f"المبلغ: {amount:,} ل.س\n"
            f"أجور التحويل : {amount_with_fee-amount:,} ل.س\n"
            f"الإجمالي: {amount_with_fee:,} ل.س\n"
            "هل تريد المتابعة؟",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "final_confirm_syr_bill")
    def final_confirm_syr_bill(call):
        user_id = call.from_user.id
        total = user_states[user_id]["amount_with_fee"]
        balance = get_balance(user_id)
        if balance < total:
            kb = make_inline_buttons(
                ("❌ إلغاء", "cancel_all"),
                ("💼 الذهاب للمحفظة", "go_wallet")
            )
            bot.send_message(call.message.chat.id,
                f"❌ لا يوجد رصيد كافٍ.\nرصيدك: {balance:,} ل.س\nالمطلوب: {total:,} ل.س\n"
                f"الناقص: {total-balance:,} ل.س", reply_markup=kb)
            user_states.pop(user_id, None)
            return
        user_states[user_id]["step"] = "wait_admin_syr_bill"
        kb_admin = make_inline_buttons(
            ("✅ تأكيد دفع الفاتورة", f"admin_accept_syr_bill_{user_id}_{total}"),
            ("❌ رفض", f"admin_reject_syr_bill_{user_id}")
        )
        summary = (
            f"🔴 طلب دفع فاتورة سيرياتيل:\n"
            f"👤 المستخدم: {user_id}\n"
            f"📱 الرقم: {user_states[user_id]['number']}\n"
            f"💵 المبلغ: {user_states[user_id]['amount']:,} ل.س\n"
            f"🧾 مع العمولة : {total:,} ل.س"
        )
        bot.send_message(ADMIN_MAIN_ID, summary, reply_markup=kb_admin)
        bot.send_message(call.message.chat.id, "✅ تم إرسال الطلب إلى الإدارة، بانتظار الموافقة.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_accept_syr_bill_"))
    def admin_accept_syr_bill(call):
        user_id = int(call.data.split("_")[-2])
        total = int(call.data.split("_")[-1])
        if not has_sufficient_balance(user_id, total):
            bot.send_message(user_id, "❌ لا يوجد رصيد كافٍ في محفظتك.")
            bot.answer_callback_query(call.id, "❌ رصيد غير كافٍ")
            return
        deduct_balance(user_id, total)
        bot.send_message(user_id, f"✅ تم دفع فاتورة سيرياتيل بنجاح.\nالمبلغ المقتطع: {total:,} ل.س")
        bot.answer_callback_query(call.id, "✅ تم تنفيذ الدفع")
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_reject_syr_bill_"))
    def admin_reject_syr_bill(call):
        user_id = int(call.data.split("_")[-1])
        bot.send_message(user_id, "❌ تم رفض طلب دفع الفاتورة من الإدارة.")
        bot.answer_callback_query(call.id, "❌ تم رفض الطلب")
        user_states.pop(user_id, None)

    ########## فاتورة MTN ##########
    @bot.message_handler(func=lambda msg: msg.text == "🟡 فاتورة MTN")
    def mtn_bill_entry(msg):
        user_id = msg.from_user.id
        user_states[user_id] = {"step": "mtn_bill_number"}
        kb = make_inline_buttons(("❌ إلغاء", "cancel_all"))
        bot.send_message(msg.chat.id, "📱 أدخل رقم MTN المراد دفع فاتورته:", reply_markup=kb)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "mtn_bill_number")
    def mtn_bill_number(msg):
        user_id = msg.from_user.id
        number = msg.text.strip()
        user_states[user_id]["number"] = number
        user_states[user_id]["step"] = "mtn_bill_number_confirm"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cancel_all"),
            ("✏️ تعديل", "edit_mtn_bill_number"),
            ("✔️ تأكيد", "confirm_mtn_bill_number")
        )
        bot.send_message(msg.chat.id, f"هل الرقم التالي صحيح؟\n{number}", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == "edit_mtn_bill_number")
    def edit_mtn_bill_number(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "mtn_bill_number"
        bot.send_message(call.message.chat.id, "📱 أعد إدخال رقم الموبايل:")

    @bot.callback_query_handler(func=lambda call: call.data == "confirm_mtn_bill_number")
    def confirm_mtn_bill_number(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "mtn_bill_amount"
        kb = make_inline_buttons(("❌ إلغاء", "cancel_all"))
        bot.send_message(call.message.chat.id, "💵 أدخل مبلغ الفاتورة بالليرة:", reply_markup=kb)

    @bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "mtn_bill_amount")
    def mtn_bill_amount(msg):
        user_id = msg.from_user.id
        try:
            amount = int(msg.text)
            if amount <= 0:
                raise ValueError
        except:
            bot.send_message(msg.chat.id, "⚠️ أدخل مبلغ صحيح.")
            return
        user_states[user_id]["amount"] = amount
        user_states[user_id]["step"] = "mtn_bill_amount_confirm"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cancel_all"),
            ("✏️ تعديل", "edit_mtn_bill_amount"),
            ("✔️ تأكيد", "confirm_mtn_bill_amount")
        )
        bot.send_message(
            msg.chat.id,
            f"هل المبلغ التالي صحيح؟\n{amount:,} ل.س", reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "edit_mtn_bill_amount")
    def edit_mtn_bill_amount(call):
        user_id = call.from_user.id
        user_states[user_id]["step"] = "mtn_bill_amount"
        bot.send_message(call.message.chat.id, "💵 أعد إرسال مبلغ الفاتورة:")

    @bot.callback_query_handler(func=lambda call: call.data == "confirm_mtn_bill_amount")
    def confirm_mtn_bill_amount(call):
        user_id = call.from_user.id
        amount = user_states[user_id]["amount"]
        amount_with_fee = int(amount * 1.17)
        user_states[user_id]["amount_with_fee"] = amount_with_fee
        user_states[user_id]["step"] = "mtn_bill_final_confirm"
        kb = make_inline_buttons(
            ("❌ إلغاء", "cancel_all"),
            ("✔️ تأكيد", "final_confirm_mtn_bill")
        )
        bot.send_message(
            call.message.chat.id,
            f"سيتم دفع فاتورة MTN للرقم: {user_states[user_id]['number']}\n"
            f"المبلغ: {amount:,} ل.س\n"
            f"أجور التحويل : {amount_with_fee-amount:,} ل.س\n"
            f"الإجمالي: {amount_with_fee:,} ل.س\n"
            "هل تريد المتابعة؟",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "final_confirm_mtn_bill")
    def final_confirm_mtn_bill(call):
        user_id = call.from_user.id
        total = user_states[user_id]["amount_with_fee"]
        balance = get_balance(user_id)
        if balance < total:
            kb = make_inline_buttons(
                ("❌ إلغاء", "cancel_all"),
                ("💼 الذهاب للمحفظة", "go_wallet")
            )
            bot.send_message(call.message.chat.id,
                f"❌ لا يوجد رصيد كافٍ.\nرصيدك: {balance:,} ل.س\nالمطلوب: {total:,} ل.س\n"
                f"الناقص: {total-balance:,} ل.س", reply_markup=kb)
            user_states.pop(user_id, None)
            return
        user_states[user_id]["step"] = "wait_admin_mtn_bill"
        kb_admin = make_inline_buttons(
            ("✅ تأكيد دفع الفاتورة", f"admin_accept_mtn_bill_{user_id}_{total}"),
            ("❌ رفض", f"admin_reject_mtn_bill_{user_id}")
        )
        summary = (
            f"🟡 طلب دفع فاتورة MTN:\n"
            f"👤 المستخدم: {user_id}\n"
            f"📱 الرقم: {user_states[user_id]['number']}\n"
            f"💵 المبلغ: {user_states[user_id]['amount']:,} ل.س\n"
            f"🧾 مع العمولة : {total:,} ل.س"
        )
        bot.send_message(ADMIN_MAIN_ID, summary, reply_markup=kb_admin)
        bot.send_message(call.message.chat.id, "✅ تم إرسال الطلب إلى الإدارة، بانتظار الموافقة.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_accept_mtn_bill_"))
    def admin_accept_mtn_bill(call):
        user_id = int(call.data.split("_")[-2])
        total = int(call.data.split("_")[-1])
        if not has_sufficient_balance(user_id, total):
            bot.send_message(user_id, "❌ لا يوجد رصيد كافٍ في محفظتك.")
            bot.answer_callback_query(call.id, "❌ رصيد غير كافٍ")
            return
        deduct_balance(user_id, total)
        bot.send_message(user_id, f"✅ تم دفع فاتورة MTN بنجاح.\nالمبلغ المقتطع: {total:,} ل.س")
        bot.answer_callback_query(call.id, "✅ تم تنفيذ الدفع")
        user_states.pop(user_id, None)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_reject_mtn_bill_"))
    def admin_reject_mtn_bill(call):
        user_id = int(call.data.split("_")[-1])
        bot.send_message(user_id, "❌ تم رفض طلب دفع الفاتورة من الإدارة.")
        bot.answer_callback_query(call.id, "❌ تم رفض الطلب")
        user_states.pop(user_id, None)

    # زر الذهاب للمحفظة في حال الرصيد غير كافٍ
    @bot.callback_query_handler(func=lambda call: call.data == "go_wallet")
    def go_wallet(call):
        user_states.pop(call.from_user.id, None)
        bot.send_message(call.message.chat.id, "💼 للذهاب للمحفظة، اضغط على زر المحفظة في القائمة الرئيسية.")

