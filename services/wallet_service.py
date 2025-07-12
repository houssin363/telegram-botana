# 🏦 الخدمات المتعلقة بالمحفظة باستخدام Supabase

from database.db import get_table
from datetime import datetime

# اسم الجدول الفعلي للمستخدمين
TABLE_NAME = "houssin363"

# ✅ جلب رصيد المستخدم من قاعدة البيانات
def get_balance(user_id):
    response = get_table(TABLE_NAME).select("balance").eq("user_id", user_id).single().execute()
    if response.data and "balance" in response.data:
        return response.data["balance"]
    return 0

# ✅ جلب سجل المشتريات
def get_purchases(user_id):
    response = get_table(TABLE_NAME).select("purchases").eq("user_id", user_id).single().execute()
    if response.data and "purchases" in response.data:
        return response.data["purchases"]
    return []

# ✅ التحقق من وجود رصيد كافٍ
def has_sufficient_balance(user_id, amount):
    balance = get_balance(user_id)
    return balance >= amount

# ✅ خصم مبلغ من رصيد المستخدم
def deduct_balance(user_id, amount):
    current_balance = get_balance(user_id)
    new_balance = current_balance - amount
    get_table(TABLE_NAME).update({"balance": new_balance}).eq("user_id", user_id).execute()
    record_transaction(user_id, -amount, "خصم تلقائي")

# ✅ إضافة مبلغ إلى الرصيد
def add_balance(user_id, amount):
    current_balance = get_balance(user_id)
    new_balance = current_balance + amount
    get_table(TABLE_NAME).update({"balance": new_balance}).eq("user_id", user_id).execute()
    record_transaction(user_id, amount, "إيداع يدوي")

# ✅ تسجيل عملية مالية
def record_transaction(user_id, amount, description):
    transaction = {
        "user_id": user_id,
        "amount": amount,
        "description": description,
        "timestamp": datetime.utcnow().isoformat()
    }
    get_table("transactions").insert(transaction).execute()
