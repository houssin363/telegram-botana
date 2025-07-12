# الخدمات المتعلقة بالمحفظة (العمليات على الرصيد وغيره)

def get_balance(user_id):
    # في المستقبل: جلب الرصيد من قاعدة البيانات بناءً على user_id
    return 150  # رصيد افتراضي للتجربة

def record_transaction(user_id, amount, description):
    # في المستقبل: سجل العملية في قاعدة البيانات
    print(f"🔁 عملية مالية: المستخدم={user_id} | المبلغ={amount} | {description}")
