"""
⚠️ Stealth Ransomware Simulator - LOW/MEDIUM THREAT
فيروس خفي - مستوى تهديد منخفض/متوسط

يقوم بـ:
- التعديل ببطء (5-9 ملفات/دقيقة)
- محاولة التهرب من الكشف
- التشفير التدريجي

⚠️ هذا اختبار لقدرة النظام على كشف الهجمات البطيئة
"""

import os
import time
import random

TARGET_DIR = r"C:\Users\Public\Documents\TestArea"
NUM_FILES = 15
DELAY_MIN = 3  # 3-8 ثواني بين كل ملف
DELAY_MAX = 8


def stealth_attack():
    """هجوم خفي بطيء"""
    print("[*] Stealth Ransomware Starting...")
    print("[*] Mode: SLOW AND STEADY")
    print(f"[*] Target: {TARGET_DIR}")
    print(f"[*] Delay: {DELAY_MIN}-{DELAY_MAX} seconds between files\n")
    
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    # إنشاء ملفات ببطء
    print("[*] Creating files slowly to avoid detection...")
    for i in range(NUM_FILES):
        filename = os.path.join(TARGET_DIR, f"stealth_{i}.docx")
        
        with open(filename, 'w') as f:
            f.write(f"Confidential Document {i}\n")
            f.write("Financial Report 2024\n")
            f.write("Internal Use Only\n")
        
        print(f"[+] Created: {filename}")
        
        # تأخير عشوائي
        delay = random.uniform(DELAY_MIN, DELAY_MAX)
        print(f"    Waiting {delay:.1f} seconds...")
        time.sleep(delay)
    
    print("\n[*] Now encrypting files slowly...")
    time.sleep(5)
    
    # تشفير ببطء
    files = [f for f in os.listdir(TARGET_DIR) if f.startswith('stealth_')]
    for filename in files:
        filepath = os.path.join(TARGET_DIR, filename)
        
        # "تشفير"
        with open(filepath, 'w') as f:
            f.write("ENCRYPTED_DATA_" + "X"*500)
        
        # تغيير الامتداد
        new_path = filepath.replace('.docx', '.crypto')
        os.rename(filepath, new_path)
        
        print(f"[+] Encrypted: {filename}")
        
        delay = random.uniform(DELAY_MIN, DELAY_MAX)
        print(f"    Waiting {delay:.1f} seconds...")
        time.sleep(delay)
    
    print("\n[✓] Stealth attack complete!")
    print("[?] Did the system detect this slow attack?")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🕵️ STEALTH RANSOMWARE SIMULATOR - SLOW ATTACK")
    print("="*70)
    print("\nThis will take several minutes to complete.")
    print("It tests if the system can detect slow, stealthy attacks.\n")
    
    input("Press ENTER to start (or Ctrl+C to cancel)...")
    
    try:
        stealth_attack()
    except KeyboardInterrupt:
        print("\n\n[!] Attack stopped!")
