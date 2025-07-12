# منطق شحن الرصيد

def validate_recharge_code(code):
    # تحقق من كود الشحن — لاحقًا اربطه بملف JSON أو قاعدة بيانات
    valid_codes = ["ABC123", "XYZ789"]
    return code in valid_codes

def apply_recharge(user_id, amount):
    # في المستقبل: سجل الشحن في قاعدة البيانات
    print(f"💰 تم شحن {amount} للمستخدم {user_id}")
