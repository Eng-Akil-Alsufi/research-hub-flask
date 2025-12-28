"""
سكربت إنشاء أول حساب مدير نظام
يتم تشغيل هذا السكربت مرة واحدة فقط عند تثبيت النظام لأول مرة
"""

import mysql.connector
from datetime import datetime

# إعدادات قاعدة البيانات
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  
    'database': 'research_hub_db',
    'charset': 'utf8mb4'
}

def create_first_admin():
    """إنشاء أول حساب مدير نظام"""
    try:
        # الاتصال بقاعدة البيانات
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # التحقق من وجود مدير نظام بالفعل
        cursor.execute("""
            SELECT COUNT(*) as admin_count 
            FROM Users 
            WHERE RoleID = 1
        """)
        
        result = cursor.fetchone()
        
        if result['admin_count'] > 0:
            print("⚠️  يوجد بالفعل حساب مدير نظام في قاعدة البيانات!")
            print("   لا حاجة لإنشاء حساب جديد.")
            cursor.close()
            conn.close()
            return
        
        # بيانات المدير الافتراضي
        admin_username = 'admin'
        admin_password = 'admin123'
        
        # إنشاء حساب المدير
        cursor.execute("""
            INSERT INTO Users (Username, Password, RoleID, IsActive)
            VALUES (%s, %s, 1, TRUE)
        """, (admin_username, admin_password))
        
        conn.commit()
        
        print("✅ تم إنشاء حساب مدير النظام بنجاح!")
        print("=" * 50)
        print("📋 بيانات تسجيل الدخول:")
        print(f"   اسم المستخدم: {admin_username}")
        print(f"   كلمة المرور: {admin_password}")
        print("=" * 50)
        print("⚠️  تحذير أمني:")
        print("   يرجى تغيير كلمة المرور بعد تسجيل الدخول لأول مرة!")
        print("=" * 50)
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {err}")
        print("   تأكد من:")
        print("   1. تشغيل خادم MySQL (XAMPP)")
        print("   2. إنشاء قاعدة البيانات 'research_hub_db'")
        print("   3. تشغيل سكربت إعداد قاعدة البيانات أولاً")
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 سكربت إنشاء أول حساب مدير نظام")
    print("=" * 50)
    create_first_admin()
