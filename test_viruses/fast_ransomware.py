"""
⚠️ Fast Ransomware Simulator - CRITICAL THREAT LEVEL
فيروس سريع جداً - مستوى تهديد حرج

يقوم بـ:
- تعديل أكثر من 50 ملف في أقل من دقيقة
- تشفير الملفات
- تغيير الامتدادات بشكل جماعي
- محاكاة سلوك حقيقي للرانسوم وير

⚠️ هذا سيؤدي إلى تنبيه CRITICAL وإيقاف تلقائي للعملية!
"""

import os
import time
import random
import string

TARGET_DIR = r"C:\Users\Public\Documents\TestArea"
NUM_FILES = 100  # عدد كبير من الملفات
ENCRYPTION_SPEED = 0.01  # سريع جداً!


def generate_random_content(size=1024):
    """توليد محتوى عشوائي (يبدو مشفراً)"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size))


def fast_attack():
    """هجوم سريع جداً"""
    print("[!] FAST RANSOMWARE ATTACK STARTED!")
    print(f"[!] Targeting: {TARGET_DIR}")
    print(f"[!] Files to create/encrypt: {NUM_FILES}")
    print(f"[!] Speed: MAXIMUM\n")
    
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    start_time = time.time()
    
    # المرحلة 1: إنشاء ملفات بسرعة
    print("[*] Phase 1: Creating files rapidly...")
    for i in range(NUM_FILES):
        filename = os.path.join(TARGET_DIR, f"victim_file_{i}.txt")
        with open(filename, 'w') as f:
            f.write(f"Important data {i}\n")
        
        if i % 10 == 0:
            print(f"    Progress: {i}/{NUM_FILES}")
        
        time.sleep(ENCRYPTION_SPEED)
    
    # المرحلة 2: تشفير بسرعة
    print("\n[*] Phase 2: Encrypting files...")
    files = [f for f in os.listdir(TARGET_DIR) if f.endswith('.txt')]
    
    for i, filename in enumerate(files):
        filepath = os.path.join(TARGET_DIR, filename)
        
        # استبدال المحتوى بمحتوى "مشفر"
        with open(filepath, 'w') as f:
            f.write(generate_random_content(2048))
        
        # تغيير الامتداد
        new_filepath = filepath.replace('.txt', '.locked')
        os.rename(filepath, new_filepath)
        
        if i % 10 == 0:
            print(f"    Encrypted: {i}/{len(files)}")
        
        time.sleep(ENCRYPTION_SPEED)
    
    elapsed = time.time() - start_time
    
    print(f"\n[!] ATTACK COMPLETE!")
    print(f"[!] Files processed: {NUM_FILES}")
    print(f"[!] Time elapsed: {elapsed:.2f} seconds")
    print(f"[!] Speed: {NUM_FILES/elapsed:.2f} files/second")
    print(f"\n[!] YOUR DETECTION SYSTEM SHOULD HAVE STOPPED THIS!")
    print(f"[!] Check for CRITICAL alerts and automatic containment.")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("⚠️⚠️⚠️ CRITICAL RANSOMWARE SIMULATOR ⚠️⚠️⚠️")
    print("="*70)
    
    input("\nPress ENTER to start the attack (or Ctrl+C to cancel)...")
    
    try:
        fast_attack()
    except KeyboardInterrupt:
        print("\n\n[!] Attack interrupted!")
