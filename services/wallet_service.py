from database.db import get_table
from datetime import datetime

TABLE_NAME = "houssin363"

def get_balance(user_id):
    response = get_table(TABLE_NAME).select("balance").eq("user_id", user_id).single().execute()
    if response.data and "balance" in response.data:
        return response.data["balance"]
    return 0

def get_purchases(user_id):
    response = get_table(TABLE_NAME).select("purchases").eq("user_id", user_id).single().execute()
    if response.data and "purchases" in response.data:
        return response.data["purchases"]
    return []

def get_transfers(user_id):
    response = get_table("transactions").select("*").eq("user_id", user_id).order("timestamp", desc=True).limit(10).execute()
    if response.data:
        return [
            f"{tx['timestamp'][:16].replace('T', ' ')} - {tx['description']}: {tx['amount']:,} ل.س"
            for tx in response.data
        ]
    return []

def has_sufficient_balance(user_id, amount):
    balance = get_balance(user_id)
    return balance >= amount

def deduct_balance(user_id, amount):
    current_balance = get_balance(user_id)
    new_balance = current_balance - amount
    get_table(TABLE_NAME).update({"balance": new_balance}).eq("user_id", user_id).execute()
    record_transaction(user_id, -amount, "خصم تلقائي")

def add_balance(user_id, amount):
    current_balance = get_balance(user_id)
    new_balance = current_balance + amount
    get_table(TABLE_NAME).update({"balance": new_balance}).eq("user_id", user_id).execute()
    record_transaction(user_id, amount, "إيداع يدوي")

def record_transaction(user_id, amount, description):
    transaction = {
        "user_id": user_id,
        "amount": amount,
        "description": description,
        "timestamp": datetime.utcnow().isoformat()
    }
    get_table("transactions").insert(transaction).execute()

def transfer_balance(sender_id, receiver_id, amount):
    if not has_sufficient_balance(sender_id, amount + 8000):
        return False

    sender_balance = get_balance(sender_id)
    receiver_balance = get_balance(receiver_id)

    get_table(TABLE_NAME).update({"balance": sender_balance - amount}).eq("user_id", sender_id).execute()
    get_table(TABLE_NAME).update({"balance": receiver_balance + amount}).eq("user_id", receiver_id).execute()

    record_transaction(sender_id, -amount, f"تحويل إلى {receiver_id}")
    record_transaction(receiver_id, amount, f"استلام من {sender_id}")

    return True
