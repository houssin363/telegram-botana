from datetime import datetime

from database.db import get_table

# ---------------------------------------------------------------------------
# جداول Supabase (تأكّد أن أسمائها مطابقة لما هو في لوحة Supabase)
# ---------------------------------------------------------------------------
TABLE_NAME = "houssin363"          # جدول حسابات المستخدمين
TRANSACTION_TABLE = "transactions"  # جدول سجلّ العمليات المالية

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _select_single(table_name: str, column: str, user_id: int):
    """إرجاع أول صف مطابق أو قائمة فارغة من Supabase بدون استخدام maybe_single()."""
    response = (
        get_table(table_name)
        .select(column)
        .eq("user_id", user_id)
        .limit(1)       # SAFE: لا يطلق استثناء 204
        .execute()
    )
    return response.data[0][column] if response.data else None


# ---------------------------------------------------------------------------
# عمليات على حساب المستخدم
# ---------------------------------------------------------------------------

def register_user_if_not_exist(user_id: int, name: str = "مستخدم") -> None:
    """إدراج أو تحديث صفّ المستخدم تلقائيًا باستخدام upsert.

    - إذا كان الصف موجودًا (مفتاح "user_id") → يتجاهل الإدراج.
    - إذا غير موجود → يُنشئ صفًا بقيم افتراضية.
    """
    (
        get_table(TABLE_NAME)
        .upsert(
            {
                "user_id": user_id,
                "name": name,
                "balance": 0,
                "purchases": [],  # نوع العمود jsonb
            },
            on_conflict="user_id",
        )
        .execute()
    )


def get_balance(user_id: int) -> int:
    """إرجاع رصيد المستخدم أو 0 إن لم يُوجد صف."""
    balance = _select_single(TABLE_NAME, "balance", user_id)
    return balance if balance is not None else 0


def get_purchases(user_id: int):
    """إرجاع قائمة المشتريات أو قائمة فارغة."""
    purchases = _select_single(TABLE_NAME, "purchases", user_id)
    return purchases if purchases is not None else []


# ---------------------------------------------------------------------------
# سجلّ العمليات المالية
# ---------------------------------------------------------------------------

def record_transaction(user_id: int, amount: int, description: str) -> None:
    data = {
        "user_id": user_id,
        "amount": amount,
        "description": description,
        "timestamp": datetime.utcnow().isoformat(),
    }
    get_table(TRANSACTION_TABLE).insert(data).execute()


def get_transfers(user_id: int, limit: int = 10):
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
    """تحويل رصيد بين مستخدمين (مع رسوم ثابتة)."""
    total = amount + fee
    if not has_sufficient_balance(from_user_id, total):
        return False

    # خصم من المرسِل (المبلغ + الرسوم)
    deduct_balance(from_user_id, total, description=f"تحويل إلى {to_user_id} (شامل الرسوم)")

    # إضافة للمستقبِل (فقط المبلغ)
    add_balance(to_user_id, amount, description=f"تحويل من {from_user_id}")

    return True
