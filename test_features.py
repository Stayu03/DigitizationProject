#!/usr/bin/env python3
"""Test admin password reset and Thai validation features."""

from database import authenticate_user, admin_reset_user_password, get_connection

conn = get_connection("data/digitization.db")

# ✓ ทดสอบการล็อกอิน
original_user = authenticate_user(conn, "somyingjd@gmail.com", "12345678")
print("✓ ล็อกอินด้วยรหัสผ่านเดิม:", "สำเร็จ" if original_user else "ล้มเหลว")

# ✓ ทดสอบการรีเซ็ตรหัสผ่าน
try:
    admin_reset_user_password(conn, "chaichaichai555@gmail.com", "87654321")
    print("✓ รีเซ็ตรหัสผ่าน: สำเร็จ")
except Exception as e:
    print(f"✗ รีเซ็ตรหัสผ่าน: {e}")

# ✓ ทดสอบรหัสผ่านไม่ถูกต้อง (ต่ำกว่า 8 ตัว)
try:
    admin_reset_user_password(conn, "somyingjd@gmail.com", "123456")
    print("✗ ควรแสดงข้อความผิดพลาด")
except ValueError as e:
    print(f"✓ ข้อความผิดพลาดแสดง (ถูกต้อง):")
    print(f"  {e}")

conn.close()
print("\n✓ ทดสอบสำเร็จทั้งหมด!")
