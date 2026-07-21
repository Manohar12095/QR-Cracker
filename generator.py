"""
generator.py
-------------
Turns user input into (a) a properly-formatted QR data string for the chosen
type, and (b) a saved PNG image. This is the "engine" of the whole app —
everything else (routes, database, dashboard) exists to feed data into or
read results out of this module.
"""

import os
import random
import string

import qrcode

_HERE = os.path.dirname(os.path.abspath(__file__))

if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
    OUTPUT_DIR = "/tmp/generated"
else:
    OUTPUT_DIR = os.path.join(_HERE, "static", "generated")


def _random_short_id(length: int = 6) -> str:
    """Generate a short, URL-safe random ID for dynamic QR codes, e.g. 'a1B2c3'."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def build_data_string(qr_type: str, fields: dict) -> str:
    """
    Convert form fields into the correctly-formatted string a QR reader
    expects for each type. This is the part that makes a QR code actually
    *do* something (open WiFi settings, add a contact, etc.) rather than
    just show plain text.
    """
    qr_type = qr_type.lower()

    if qr_type == "text":
        return fields.get("text", "")

    if qr_type == "url":
        url = fields.get("url", "").strip()
        if url and not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url

    if qr_type == "email":
        return f"mailto:{fields.get('email', '')}?subject={fields.get('subject', '')}&body={fields.get('body', '')}"

    if qr_type == "phone":
        return f"tel:{fields.get('phone', '')}"

    if qr_type == "sms":
        return f"smsto:{fields.get('phone', '')}:{fields.get('message', '')}"

    if qr_type == "wifi":
        ssid = fields.get("ssid", "")
        password = fields.get("password", "")
        encryption = fields.get("encryption", "WPA")  # WPA, WEP, or nopass
        return f"WIFI:T:{encryption};S:{ssid};P:{password};;"

    if qr_type == "vcard":
        return (
            "BEGIN:VCARD\n"
            "VERSION:3.0\n"
            f"N:{fields.get('name', '')}\n"
            f"ORG:{fields.get('org', '')}\n"
            f"TEL:{fields.get('phone', '')}\n"
            f"EMAIL:{fields.get('email', '')}\n"
            "END:VCARD"
        )

    # Fallback: treat unknown types as plain text
    return fields.get("text", "")


def generate_qr_image(data: str, filename: str, fg_color: str = "black", bg_color: str = "white") -> str:
    """
    Render `data` as a QR PNG saved under static/generated/<filename>.
    Returns the file path (relative to the Flask static folder) for use in
    templates.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fg_color, back_color=bg_color)
    full_path = os.path.join(OUTPUT_DIR, filename)
    img.save(full_path)

    return full_path


def generate_static_qr(qr_type: str, fields: dict, fg_color: str = "black", bg_color: str = "white") -> tuple[str, str]:
    """
    Static QR: the final content is baked directly into the code.
    Returns (data_string, filename).
    """
    data = build_data_string(qr_type, fields)
    filename = f"static_{_random_short_id()}.png"
    generate_qr_image(data, filename, fg_color, bg_color)
    return data, filename


def generate_dynamic_qr(base_redirect_url: str, fg_color: str = "black", bg_color: str = "white") -> tuple[str, str]:
    """
    Dynamic QR: the code encodes a redirect URL (e.g. http://yourserver/r/a1B2c3),
    NOT the final content. The server looks up short_id at scan time and can
    change the destination without ever reprinting the code.
    Returns (short_id, filename).
    """
    short_id = _random_short_id()
    redirect_url = f"{base_redirect_url.rstrip('/')}/r/{short_id}"
    filename = f"dynamic_{short_id}.png"
    generate_qr_image(redirect_url, filename, fg_color, bg_color)
    return short_id, filename
