import base64
import urllib.parse
import string

# --- MORSE CODE DICTIONARIES ---
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--', '?': '..--..',
    "'": '.----.', '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
    '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.',
    '-': '-....-', '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.',
    ' ': '/'
}
REVERSE_MORSE_DICT = {v: k for k, v in MORSE_CODE_DICT.items()}

# --- EMOJI DICTIONARIES ---
EMOJI_DICT = {
    'A': '🍎', 'B': '🍌', 'C': '🐈', 'D': '🐶', 'E': '🐘', 'F': '🐸', 'G': '🦒',
    'H': '🐹', 'I': '🍦', 'J': '👖', 'K': '🦘', 'L': '🦁', 'M': '🐒', 'N': '🥜',
    'O': '🐙', 'P': '🐧', 'Q': '👑', 'R': '🐇', 'S': '🐍', 'T': '🐢', 'U': '🦄',
    'V': '🌋', 'W': '🍉', 'X': '✖️', 'Y': '🪀', 'Z': '🦓', ' ': ' '
}
REVERSE_EMOJI_DICT = {v: k for k, v in EMOJI_DICT.items()}

# --- LEETSPEAK DICTIONARIES ---
LEET_DICT = {
    'a': '4', 'b': '8', 'e': '3', 'g': '9', 'i': '1', 'o': '0', 's': '5', 't': '7'
}
REVERSE_LEET_DICT = {v: k for k, v in LEET_DICT.items()}

# ==========================================
# BASE64
# ==========================================
def encode_base64(text: str) -> str:
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')

def decode_base64(text: str) -> str:
    try:
        return base64.b64decode(text.encode('utf-8')).decode('utf-8')
    except Exception:
        return "Error: Invalid Base64 string."

# ==========================================
# BINARY
# ==========================================
def encode_binary(text: str) -> str:
    return ' '.join(format(ord(char), '08b') for char in text)

def decode_binary(text: str) -> str:
    try:
        # Filter out extra spaces and handle bits
        binary_values = text.strip().split()
        return ''.join(chr(int(bv, 2)) for bv in binary_values)
    except Exception:
        return "Error: Invalid Binary sequence."

# ==========================================
# MORSE CODE
# ==========================================
def encode_morse(text: str) -> str:
    return ' '.join(MORSE_CODE_DICT.get(char, '') for char in text.upper())

def decode_morse(text: str) -> str:
    try:
        return ''.join(REVERSE_MORSE_DICT.get(code, '') for code in text.split(' '))
    except Exception:
        return "Error: Invalid Morse code."

# ==========================================
# HEXADECIMAL
# ==========================================
def encode_hex(text: str) -> str:
    return text.encode('utf-8').hex()

def decode_hex(text: str) -> str:
    try:
        # Strip spaces if user formatted with spaces
        clean_text = text.replace(' ', '').replace('0x', '')
        return bytes.fromhex(clean_text).decode('utf-8')
    except Exception:
        return "Error: Invalid Hexadecimal string."

# ==========================================
# CAESAR CIPHER
# ==========================================
def encode_caesar(text: str, shift: int = 3) -> str:
    result = []
    for char in text:
        if char.isalpha():
            start = ord('A') if char.isupper() else ord('a')
            result.append(chr((ord(char) - start + shift) % 26 + start))
        else:
            result.append(char)
    return ''.join(result)

def decode_caesar(text: str, shift: int = 3) -> str:
    return encode_caesar(text, -shift)

# ==========================================
# ROT13
# ==========================================
def encode_rot13(text: str) -> str:
    return encode_caesar(text, 13)

def decode_rot13(text: str) -> str:
    return encode_caesar(text, 13)

# ==========================================
# VIGENÈRE
# ==========================================
def encode_vigenere(text: str, keyword: str = "KEY") -> str:
    if not keyword:
        return text
    keyword = keyword.upper()
    result = []
    kw_index = 0
    for char in text:
        if char.isalpha():
            start = ord('A') if char.isupper() else ord('a')
            shift = ord(keyword[kw_index % len(keyword)]) - ord('A')
            result.append(chr((ord(char) - start + shift) % 26 + start))
            kw_index += 1
        else:
            result.append(char)
    return ''.join(result)

def decode_vigenere(text: str, keyword: str = "KEY") -> str:
    if not keyword:
        return text
    keyword = keyword.upper()
    result = []
    kw_index = 0
    for char in text:
        if char.isalpha():
            start = ord('A') if char.isupper() else ord('a')
            shift = ord(keyword[kw_index % len(keyword)]) - ord('A')
            result.append(chr((ord(char) - start - shift + 26) % 26 + start))
            kw_index += 1
        else:
            result.append(char)
    return ''.join(result)

# ==========================================
# ATBASH
# ==========================================
def encode_atbash(text: str) -> str:
    result = []
    for char in text:
        if char.isalpha():
            if char.isupper():
                result.append(chr(ord('Z') - (ord(char) - ord('A'))))
            else:
                result.append(chr(ord('z') - (ord(char) - ord('a'))))
        else:
            result.append(char)
    return ''.join(result)

def decode_atbash(text: str) -> str:
    return encode_atbash(text)

# ==========================================
# URL ENCODING
# ==========================================
def encode_url(text: str) -> str:
    return urllib.parse.quote(text)

def decode_url(text: str) -> str:
    return urllib.parse.unquote(text)


# ==========================================
# NOVELTY MODES
# ==========================================

# 1. Reverse Text
def encode_reverse(text: str) -> str:
    return text[::-1]

def decode_reverse(text: str) -> str:
    return text[::-1]

# 2. Leetspeak
def encode_leetspeak(text: str) -> str:
    return ''.join(LEET_DICT.get(c.lower(), c) for c in text)

def decode_leetspeak(text: str) -> str:
    # Decoding leetspeak is inherently lossy since '4' could have been 'a' or just '4'.
    # We will do our best attempt via direct dictionary replace.
    return ''.join(REVERSE_LEET_DICT.get(c, c) for c in text)

# 3. Emoji Substitution
def encode_emoji(text: str) -> str:
    return ''.join(EMOJI_DICT.get(c.upper(), c) for c in text)

def decode_emoji(text: str) -> str:
    # A character-by-character replace won't work well for multi-byte emojis.
    # Instead, we should check each character/symbol. 
    # For a simple substitution, since our dict maps 1 character to 1 emoji character (usually), this approach works.
    result = text
    for emoji, char in REVERSE_EMOJI_DICT.items():
        if emoji != ' ':
            result = result.replace(emoji, char)
    return result

# ==========================================
# CIPHER REGISTRY
# ==========================================
CIPHERS = {
    "base64": {"encode": encode_base64, "decode": decode_base64},
    "binary": {"encode": encode_binary, "decode": decode_binary},
    "morse": {"encode": encode_morse, "decode": decode_morse},
    "hex": {"encode": encode_hex, "decode": decode_hex},
    "caesar": {"encode": encode_caesar, "decode": decode_caesar, "needs_key": True, "key_type": "int", "default_key": 3},
    "rot13": {"encode": encode_rot13, "decode": decode_rot13},
    "vigenere": {"encode": encode_vigenere, "decode": decode_vigenere, "needs_key": True, "key_type": "str", "default_key": "KEY"},
    "atbash": {"encode": encode_atbash, "decode": decode_atbash},
    "url": {"encode": encode_url, "decode": decode_url},
    "reverse": {"encode": encode_reverse, "decode": decode_reverse},
    "leetspeak": {"encode": encode_leetspeak, "decode": decode_leetspeak},
    "emoji": {"encode": encode_emoji, "decode": decode_emoji}
}
