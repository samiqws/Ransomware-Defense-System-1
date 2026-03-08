import os
import logging

logger = logging.getLogger(__name__)

# Dictionary mapping file extensions to their valid Magic Bytes (hex signatures)
MAGIC_BYTES = {
    '.pdf': [b'%PDF-'],
    '.zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
    '.docx': [b'PK\x03\x04'],  # Office Open XML files are ZIP archives
    '.xlsx': [b'PK\x03\x04'],
    '.pptx': [b'PK\x03\x04'],
    '.doc': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],  # Legacy MS Office
    '.xls': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
    '.ppt': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
    '.jpg': [b'\xff\xd8\xff'],
    '.jpeg': [b'\xff\xd8\xff'],
    '.png': [b'\x89PNG\r\n\x1a\n'],
    '.gif': [b'GIF87a', b'GIF89a'],
    '.rar': [b'Rar!\x1a\x07\x00', b'Rar!\x1a\x07\x01\x00'],
    '.7z': [b'7z\xbc\xaf\x27\x1c'],
    '.exe': [b'MZ'],
    '.dll': [b'MZ'],
    '.sys': [b'MZ'],
    '.rtf': [b'{\\rtf1'],
    '.bmp': [b'BM'],
    '.mp3': [b'ID3', b'\xff\xfb'],
    '.wav': [b'RIFF'],
}

def verify_file_header(file_path: str) -> bool:
    """
    Extremely fast O(1) check if a file's content matches its extension's magic bytes.
    Reads only the first 8 bytes.
    
    Returns:
    - True: Header matches, or extension is untracked, or empty file (safe).
    - False: Extension is known but header is completely wrong (highly suspicious/encrypted).
    """
    try:
        if not os.path.exists(file_path):
            return True
            
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in MAGIC_BYTES:
            return True  # Cannot verify, assume valid to prevent false positives
            
        with open(file_path, 'rb') as f:
            header = f.read(8)
            
        if not header:
            return True # Empty file
            
        valid_signatures = MAGIC_BYTES[ext]
        
        # Special check for RIFF/WAV files where 'WAVE' is at byte 8
        if ext == '.wav' and header.startswith(b'RIFF'):
            return True
            
        for sig in valid_signatures:
            if header.startswith(sig):
                return True
                    
        # Known extension, but completely unrecognized bytes - probably encrypted!
        logger.warning(f"🚨 MAGIC BYTES MISMATCH: '{file_path}' claims to be '{ext}' but header is {header.hex()}!")
        return False
        
    except Exception as e:
        logger.debug(f"Could not verify magic bytes for {file_path}: {e}")
        return True # Default to True on locked/system files
