import re

def safe_sql_check(query: str) -> bool:
    """
    ตรวจสอบว่าคำสั่ง SQL ปลอดภัยหรือไม่
    return True = ปลอดภัย, False = อันตราย
    """
    forbidden = ["drop", "delete", "alter", "insert", "update", "truncate"]
    pattern = r"|".join(fr"\b{word}\b" for word in forbidden)
    return not bool(re.search(pattern, query.lower()))

def safe_execute(sql_func, query: str):
    if not safe_sql_check(query):
        return "Unsafe SQL detected. Execution blocked."
    return sql_func(query)
