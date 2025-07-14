from datetime import datetime

from database.db import get_table

# ---------------------------------------------------------------------------
# جداول Supabase (يجب أن تطابق الأسـماء فى لوحة Supabase)
# ---------------------------------------------------------------------------
TABLE_NAME = "houssin363"           # جدول حسابات المستخدمين
TRANSACTION_TABLE = "transactions"  # جدول سجلّ العمليات المالية

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _select_single(table_name: str, column: str, user_id: int):
    """جلب قيمة عمود واحد من أول صف يطابق user_id."""
    response = (
        get_table(table_name)
        .select(column)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return response.data[0][column] if response.data else None


# ---------------------------------------------------------------------------
# عمليات على حساب المستخدم
# ---------------------------------------------------------------------------

def register_user_if_not_exist(user_id: int, name: str = "مستخدم") -> None:
    """
    إدراج المستخدم إذا لم يكن موجوداً، أو تجاهل الإدراج إن كان موجوداً.
    يعتمد على عمود user_id الفريد فى الجدول houssin363.
    """
    (
        get_table(TABLE_NAME)
        .upsert(
            {
                "user_id": user_id,
                "name": name,
                "balance": 0,
                "purchases": [],  # الأعمدة الأخرى لها قيَم افتراضية فى قاعدة البيانات
            },
            on_conflict="user_id",
        )
        .execute()
    )


def get_balance(user_id: int) -> int:
    """إرجاع رصيد المستخدم، أو 0 إن لم يُوجد صف."""
    balance = _select_single(TABLE_NAME, "balance", user_id)
    return balance if balance is not None else 0


def get_purchases(user_id: int):
    """إرجاع قائمة المشتريات، أو قائمة فارغة."""
    purchases = _select_single(TABLE_NAME, "purchases", user_id)
    return purchases if purchases is not None else []


# ---------------------------------------------------------------------------
# سجلّ العمليات المالية
# ---------------------------------------------------------------------------

def record_transaction(user_id: int, amount: int, description: str) -> None:
    """تسجيل حركة مالية فى جدول transactions."""
    data = {
        "user_id": user_id,
        "amount": amount,
        "description": description,
        "timestamp": datetime.utcnow().isoformat(),
    }
    get_table(TRANSACTION_TABLE).insert(data).execute()


def get_transfers(user_id: int, limit: int = 10):
    """جلب آخر الحركات المالية للمستخدم بصيغة نصية جاهزة للعرض."""
    response = (
        get_table(TRANSACTION_TABLE)
        .select("description", "amount", "timestamp")
        .eq("user_id", user_id)
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )
    transfers = []
    for row in response.data or []:
        ts = row["timestamp"][:19].replace("T", " ")
        transfers.append(f"{row['description']} ({row['amount']} ل.س) في {ts}")
    return transfers


# ---------------------------------------------------------------------------
# عمليات الرصيد
# ---------------------------------------------------------------------------

def _update_balance(user_id: int, delta: int):
    new_balance = get_balance(user_id) + delta
    get_table(TABLE_NAME).update({"balance": new_balance}).eq("user_id", user_id).execute()


def has_sufficient_balance(user_id: int, amount: int) -> bool:
    return get_balance(user_id) >= amount


def add_balance(user_id: int, amount: int, description: str = "إيداع يدوي") -> None:
    _update_balance(user_id, amount)
    record_transaction(user_id, amount, description)


def deduct_balance(user_id: int, amount: int, description: str = "خصم تلقائي") -> None:
    _update_balance(user_id, -amount)
    record_transaction(user_id, -amount, description)


def transfer_balance(from_user_id: int, to_user_id: int, amount: int, fee: int = 8000) -> bool:
    """تحويل رصيد بين مستخدمين مع رسوم ثابتة."""
    total = amount + fee
    if not has_sufficient_balance(from_user_id, total):
        return False

    deduct_balance(from_user_id, total, f"تحويل إلى {to_user_id} (شامل الرسوم)")
    add_balance(to_user_id, amount, f"تحويل من {from_user_id}")
    return True
