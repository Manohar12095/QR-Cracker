import json

def encode_custom(text: str, mapping_json: str) -> str:
    try:
        mapping = json.loads(mapping_json)
        result = []
        for char in text:
            # Handle case preservation if mapping is lower/upper
            upper_char = char.upper()
            if upper_char in mapping:
                mapped_char = mapping[upper_char]
                if char.islower():
                    result.append(mapped_char.lower())
                else:
                    result.append(mapped_char.upper())
            else:
                result.append(char)
        return ''.join(result)
    except Exception:
        return "Error: Invalid custom cipher mapping."

def decode_custom(text: str, mapping_json: str) -> str:
    try:
        mapping = json.loads(mapping_json)
        reverse_mapping = {v.upper(): k for k, v in mapping.items()}
        result = []
        for char in text:
            upper_char = char.upper()
            if upper_char in reverse_mapping:
                mapped_char = reverse_mapping[upper_char]
                if char.islower():
                    result.append(mapped_char.lower())
                else:
                    result.append(mapped_char.upper())
            else:
                result.append(char)
        return ''.join(result)
    except Exception:
        return "Error: Invalid custom cipher mapping."
