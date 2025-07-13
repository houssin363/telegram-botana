from database.db import get_table
from datetime import datetime

# اسم جدول المستخدمين في supabase (تأكد أنه مطابق تمامًا)
TABLE_NAME = "houssin363"

# اسم جدول سجل العمليات (تحويلات أو إيداعات)
TRANSACTION_TABLE = "transactions"

# ✅ تسجيل المستخدم تلقائيًا عند أول دخول
def register_user_if_not_exist(user_id, name="مستخدم"):
    table = get_table(TABLE_NAME)
    # تحقق: إذا يوجد مستخدم بنفس user_id في الجدول
    result = table.select("user_id").eq("user_id", user_id).maybe_single().execute()
    if not result.data:
        # إذا غير موجود: أضفه ببيانات افتراضية
        table.insert({
            "user_id": user_id,
            "name": name,
            "balance": 0,
            "purchases": [],   # تأكد أن نوع العمود json أو jsonb
        }).execute()

# ✅ جلب رصيد المستخدم الحالي
def get_balance(user_id):
    response = (
        get_table(TABLE_NAME)
        .select("balance")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if response.data and "balance" in response.data:
        return response.data["balance"]
    return 0

# ✅ جلب قائمة المشتريات
def get_purchases(user_id):
    response = (
        get_table(TABLE_NAME)
        .select("purchases")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if response.data and "purchases" in response.data:
        return response.data["purchases"]
    return []

# ✅ جلب سجل آخر 10 عمليات مالية
def get_transfers(user_id):
    response = (
        get_table(TRANSACTION_TABLE)
        .select("description", "amount", "timestamp")
        .eq("user_id", user_id)
        .order("timestamp", desc=True)
        .limit(10)
        .execute()
    )
    if response.data:
        return [
            f"{row['description']} ({row['amount']} ل.س) في {row['timestamp'][:19].replace('T', ' ')}"
            for row in response.data
        ]
    return []

# ✅ تحقق من وجود رصيد كافٍ
def has_sufficient_balance(user_id, amount):
    return get_balance(user_id) >= amount

# ✅ خصم مبلغ من الرصيد مع تسجيل العملية في جدول التحويلات
def deduct_balance(user_id, amount):
    current = get_balance(user_id)
    new_balance = current - amount
    get_table(TABLE_NAME).update({"balance": new_balance}).eq("user_id", user_id).execute()
    record_transaction(user_id, -amount, "خصم تلقائي")

# ✅ إضافة مبلغ للرصيد مع تسجيل العملية في جدول التحويلات
def add_balance(user_id, amount):
    current = get_balance(user_id)
    new_balance = current + amount
    get_table(TABLE_NAME).update({"balance": new_balance}).eq("user_id", user_id).execute()
    record_transaction(user_id, amount, "إيداع يدوي")

# ✅ تسجيل أي عملية في جدول التحويلات
def record_transaction(user_id, amount, description):
    data = {
        "user_id": user_id,
        "amount": amount,
        "description": description,
        "timestamp": datetime.utcnow().isoformat()
    }
    get_table(TRANSACTION_TABLE).insert(data).execute()

# ✅ تحويل رصيد بين مستخدمين (مع رسوم تحويل إن وجدت)
def transfer_balance(from_user_id, to_user_id, amount):
    # رسوم التحويل ثابتة (مثلاً 8000)، غيّر الرقم حسب النظام عندك
    fee = 8000
    if not has_sufficient_balance(from_user_id, amount + fee):
        return False

    deduct_balance(from_user_id, amount)
    add_balance(to_user_id, amount)
    record_transaction(from_user_id, -amount, f"تحويل إلى {to_user_id}")
    record_transaction(to_user_id, amount, f"تحويل من {from_user_id}")
    return True
