"""
Decryption Tool for Basic Ransomware Simulator
أداة فك التشفير للفيروس الاختباري
"""

import os
import sys
from pathlib import Path

TEST_DIRECTORY = r"C:\Users\Public\Documents\TestArea"
FILE_EXTENSION = ".encrypted"


def simple_decrypt(data):
    """فك التشفير (نفس عملية التشفير لـ XOR)"""
    key = 0xAA
    return bytes([byte ^ key for byte in data])


def decrypt_files(directory):
    """فك تشفير جميع الملفات المشفرة"""
    print(f"[*] Decrypting files in {directory}\n")
    
    # الحصول على الملفات المشفرة
    encrypted_files = [f for f in os.listdir(directory) 
                      if f.endswith(FILE_EXTENSION)]
    
    if not encrypted_files:
        print("[!] No encrypted files found!")
        return
    
    decrypted_count = 0
    for filename in encrypted_files:
        filepath = os.path.join(directory, filename)
        
        try:
            # قراءة البيانات المشفرة
            with open(filepath, 'rb') as f:
                encrypted_data = f.read()
            
            # فك التشفير
            decrypted_data = simple_decrypt(encrypted_data)
            
            # اسم الملف الأصلي
            original_filepath = filepath.replace(FILE_EXTENSION, '')
            
            # كتابة البيانات المفككة
            with open(original_filepath, 'wb') as f:
                f.write(decrypted_data)
            
            # حذف الملف المشفر
            os.remove(filepath)
            
            decrypted_count += 1
            print(f"[✓] Decrypted: {filename} -> {os.path.basename(original_filepath)}")
            
        except Exception as e:
            print(f"[✗] Failed to decrypt {filename}: {e}")
    
    # حذف ملف الفدية
    ransom_note = os.path.join(directory, "RANSOM_NOTE.txt")
    if os.path.exists(ransom_note):
        os.remove(ransom_note)
        print(f"[✓] Removed ransom note")
    
    print(f"\n[✓] Decryption complete: {decrypted_count} files restored")


def cleanup_test_files(directory):
    """حذف جميع ملفات الاختبار"""
    print(f"\n[*] Cleaning up test files in {directory}\n")
    
    # حذف ملفات rapid_test
    for filename in os.listdir(directory):
        if filename.startswith('rapid_test_') or filename.startswith('document_'):
            filepath = os.path.join(directory, filename)
            try:
                os.remove(filepath)
                print(f"[✓] Removed: {filename}")
            except Exception as e:
                print(f"[✗] Failed to remove {filename}: {e}")
    
    print("[✓] Cleanup complete")


def main():
    print("\n" + "="*70)
    print("        🔓 RANSOMWARE DECRYPTION TOOL")
    print("="*70)
    print(f"\nTarget Directory: {TEST_DIRECTORY}\n")
    
    print("Options:")
    print("1. Decrypt files only")
    print("2. Decrypt and cleanup all test files")
    print("3. Cancel")
    
    choice = input("\nSelect option (1/2/3): ").strip()
    
    if choice == '1':
        decrypt_files(TEST_DIRECTORY)
    elif choice == '2':
        decrypt_files(TEST_DIRECTORY)
        cleanup_test_files(TEST_DIRECTORY)
    else:
        print("[!] Operation cancelled.")
        sys.exit(0)
    
    print("\n" + "="*70)
    print("        ✅ OPERATION COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[✗] Error: {e}")
        sys.exit(1)
