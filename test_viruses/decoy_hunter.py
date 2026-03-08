"""
⚠️ Decoy Hunter Simulator - HIGH THREAT
محاكي البحث عن ملفات الفخاخ

يقوم بـ:
- البحث عن ملفات Decoy (الفخاخ)
- محاولة الوصول إليها
- تعديلها

⚠️ هذا سيؤدي إلى تنبيه فوري عند لمس أول ملف Decoy!
"""

import os
import sys
import time
from pathlib import Path

# المجلدات التي قد تحتوي على Decoy Files
SEARCH_PATHS = [
    r"C:\Users\Public\Documents",
    r"C:\Users\Public\Desktop",
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Pictures")
]

# أسماء مشبوهة للملفات (عادة تكون Decoy)
SUSPICIOUS_NAMES = [
    "password", "confidential", "financial", "backup",
    "secret", "private", "wallet", "bank", "credit"
]


def find_decoy_files():
    """البحث عن ملفات Decoy المحتملة"""
    print("[*] Hunting for decoy files...")
    print("[*] Searching in common directories...\n")
    
    potential_decoys = []
    
    for search_path in SEARCH_PATHS:
        if not os.path.exists(search_path):
            continue
        
        print(f"[*] Scanning: {search_path}")
        
        try:
            for root, dirs, files in os.walk(search_path):
                # لا تذهب بعيداً جداً
                if root.count(os.sep) - search_path.count(os.sep) > 2:
                    continue
                
                for filename in files:
                    # تحقق من الأسماء المشبوهة
                    filename_lower = filename.lower()
                    if any(suspicious in filename_lower for suspicious in SUSPICIOUS_NAMES):
                        filepath = os.path.join(root, filename)
                        potential_decoys.append(filepath)
                        print(f"    [+] Found suspicious: {filename}")
        
        except Exception as e:
            print(f"    [!] Error scanning {search_path}: {e}")
    
    return potential_decoys


def attack_decoy_files(decoy_files):
    """مهاجمة ملفات Decoy"""
    print(f"\n[!] Found {len(decoy_files)} potential decoy files")
    print("[!] Starting attack on decoy files...\n")
    
    if not decoy_files:
        print("[!] No decoy files found. Creating some in TestArea instead...")
        test_dir = r"C:\Users\Public\Documents\TestArea"
        os.makedirs(test_dir, exist_ok=True)
        
        # إنشاء ملفات اختبار بأسماء مشبوهة
        for name in ["passwords.txt", "financial_report.docx", "backup_keys.xlsx"]:
            filepath = os.path.join(test_dir, name)
            with open(filepath, 'w') as f:
                f.write("Sensitive data here\n")
            decoy_files.append(filepath)
            print(f"[+] Created test file: {name}")
    
    print("\n[!] Attacking files in 3 seconds...")
    time.sleep(3)
    
    attacked = 0
    for filepath in decoy_files[:10]:  # أول 10 ملفات فقط
        try:
            print(f"[!] Attacking: {filepath}")
            
            # محاولة قراءة الملف (هذا سيؤدي إلى تنبيه!)
            with open(filepath, 'r') as f:
                content = f.read()
            
            # محاولة تعديل الملف (ALERT!)
            with open(filepath, 'a') as f:
                f.write("\n[ENCRYPTED BY RANSOMWARE]")
            
            attacked += 1
            print(f"    [✓] Successfully attacked!")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"    [✗] Failed: {e}")
    
    print(f"\n[!] Attack complete: {attacked} files compromised")
    print("[!] ⚠️ THE SYSTEM SHOULD HAVE DETECTED THIS! ⚠️")
    print("[!] Check for 'decoy_file_compromised' alerts!")


def main():
    print("\n" + "="*70)
    print("🎯 DECOY HUNTER RANSOMWARE SIMULATOR")
    print("="*70)
    print("\nThis simulator will:")
    print("1. Search for decoy/honeypot files")
    print("2. Attempt to access and modify them")
    print("3. Trigger immediate HIGH alerts\n")
    print("⚠️ Any access to decoy files = INSTANT DETECTION!")
    print("="*70 + "\n")
    
    input("Press ENTER to start hunting (or Ctrl+C to cancel)...")
    
    # البحث عن Decoy files
    decoy_files = find_decoy_files()
    
    # مهاجمتها
    attack_decoy_files(decoy_files)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Hunt cancelled!")
        sys.exit(1)
