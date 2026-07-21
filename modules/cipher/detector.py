import re
import string

def detect_pattern(text: str) -> dict:
    """
    Analyzes the text and tries to guess the encoding/cipher based on structural patterns.
    """
    text = text.strip()
    if not text:
        return {"detected": "Unknown", "confidence": "0%"}
    
    # 1. Binary Check (only 0s, 1s, and spaces)
    if re.match(r'^[01\s]+$', text):
        # Additional heuristic: chunk size often 8
        parts = text.split()
        if all(len(p) == 8 for p in parts) or len(text) >= 8:
            return {"detected": "Binary", "confidence": "High (only 0/1 bits found)"}

    # 2. Morse Code Check (only ., -, and spaces)
    if re.match(r'^[\.\-\s\/]+$', text):
        return {"detected": "Morse Code", "confidence": "High (only dots and dashes found)"}

    # 3. Hexadecimal Check (only 0-9, a-f, A-F, and spaces)
    # A bit tricky since normal text might just be "bad face" which is valid hex. 
    # Usually hex pairs are 2 chars long if space separated.
    clean_hex = text.replace(' ', '').replace('0x', '')
    if re.match(r'^[0-9a-fA-F]+$', clean_hex):
        # Heuristic: Even length and mostly numbers or standard hex letters
        if len(clean_hex) % 2 == 0 and len(clean_hex) > 4:
            return {"detected": "Hexadecimal", "confidence": "Medium-High (valid hex string)"}
            
    # 4. Base64 Check
    # Ends with = or ==, or matches [a-zA-Z0-9+/]+
    # Needs to be a multiple of 4 in length
    clean_b64 = text.replace('\n', '').replace('\r', '').replace(' ', '')
    if len(clean_b64) % 4 == 0 and len(clean_b64) > 4:
        if re.match(r'^[A-Za-z0-9+/]+={0,2}$', clean_b64):
            return {"detected": "Base64", "confidence": "Medium-High (Base64 charset and padding)"}

    # 5. URL Encoding Check
    if '%' in text and re.search(r'%[0-9a-fA-F]{2}', text):
        return {"detected": "URL Encoded", "confidence": "High (contains percent-encoding)"}

    # 6. Letter Frequency / Substitution (Caesar, Vigenere, ROT13, Atbash)
    # Check if text is mostly alphabetic but gibberish
    alpha_chars = [c for c in text if c.isalpha()]
    if len(alpha_chars) > 5:
        return {"detected": "Substitution Cipher", "confidence": "Low (Likely Caesar, ROT13, Vigenère, or Atbash)"}

    return {"detected": "Unknown", "confidence": "Low (No distinct patterns)"}
