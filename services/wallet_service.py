# ✅ الخدمات المتعلقة بالمحفظة باستخدام Supabase

from database.db import get_table
from datetime import datetime

TABLE_NAME = "houssin363"
TRANSACTION_TABLE = "transactions"

# ✅ جلب رصيد المستخدم

def get_balance(user_id):
    response = get_table(TABLE_NAME).select("balance").eq("user_id", user_id).single().execute()
    if response.data and "balance" in response.data:
        return response.data["balance"]
    return 0

# ✅ جلب المشتريات

def get_purchases(user_id):
    response = get_table(TABLE_NAME).select("purchases").eq("user_id", user_id).single().execute()
    if response.data and "purchases" in response.data:
        return response.data["purchases"]
    return []

# ✅ جلب سجل التحويلات

def get_transfers(user_id):
    response = get_table(TRANSACTION_TABLE).select("description", "amount", "timestamp").eq("user_id", user_id).order("timestamp", desc=True).limit(10).execute()
    if response.data:
        return [f"{row['description']} ({row['amount']} ل.س) في {row['timestamp'][:19].replace('T', ' ')}" for row in response.data]
    return []

# ✅ التحقق من الرصيد الكافي

def has_sufficient_balance(user_id, amount):
    return get_balance(user_id) >= amount

# ✅ خصم الرصيد

def deduct_balance(user_id, amount):
    current = get_balance(user_id)
    new_balance = current - amount
    get_table(TABLE_NAME).update({"balance": new_balance}).eq("user_id", user_id).execute()
    record_transaction(user_id, -amount, "خصم تلقائي")

# ✅ إضافة رصيد

def add_balance(user_id, amount):
    current = get_balance(user_id)
    new_balance = current + amount
    get_table(TABLE_NAME).update({"balance": new_balance}).eq("user_id", user_id).execute()
    record_transaction(user_id, amount, "إيداع يدوي")

# ✅ تسجيل العملية

def record_transaction(user_id, amount, description):
    data = {
        "user_id": user_id,
        "amount": amount,
        "description": description,
        "timestamp": datetime.utcnow().isoformat()
    }
    get_table(TRANSACTION_TABLE).insert(data).execute()

# ✅ تنفيذ تحويل بين مستخدمين

def transfer_balance(from_id, to_id, amount):
    if not has_sufficient_balance(from_id, amount + 8000):
        return False
    deduct_balance(from_id, amount)
    add_balance(to_id, amount)
    record_transaction(from_id, -amount, f"تحويل إلى {to_id}")
    record_transaction(to_id, amount, f"استلام من {from_id}")
    return True
