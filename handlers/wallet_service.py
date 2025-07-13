"""
هذا الملف يوفر دوال التحقق من الرصيد وخصمه
يُستدعى من handlers/syr_units.py
"""

# مثال بسيط: استخدم قاعدة بيانات حقيقية أو ملف لاحقًا
_user_balances = {}

def has_sufficient_balance(user_id: int, amount: float) -> bool:
    """
    تتحقق مما إذا كان لدى المستخدم رصيد كافٍ.
    """
    balance = _user_balances.get(user_id, 0)
    return balance >= amount

def deduct_balance(user_id: int, amount: float) -> None:
    """
    تخصم المبلغ من رصيد المستخدم.
    """
    balance = _user_balances.get(user_id, 0)
    _user_balances[user_id] = max(balance - amount, 0)
