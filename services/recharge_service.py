from database.db import get_table

def validate_recharge_code(code):
    # تحقق من الكود في الجدول الفعلي
    table = get_table("recharge_codes")
    response = table.select("*").eq("code", code).eq("used", False).execute()
    return response.data[0] if response.data else None

def apply_recharge(user_id, code):
    # تسجيل الشحن وتحديث الكود كمستخدم
    table = get_table("recharge_codes")
    recharge = validate_recharge_code(code)
    if recharge:
        # تحديث حالة الكود
        table.update({
            "used": True,
            "used_by": user_id,
            "used_at": datetime.utcnow().isoformat()
        }).eq("id", recharge['id']).execute()
        # شحن الرصيد
        from services.wallet_service import add_balance
        add_balance(user_id, recharge["amount"], "شحن رصيد عبر كود")
        return True
    return False
