"""
app.py
-------
Flask entry point. Routes are intentionally thin — they call into
generator.py and database.py rather than containing logic themselves,
so the "core" stays testable and reusable outside of Flask if needed.
"""

import os
import io

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, send_from_directory

import database
import generator
from modules.cipher import ciphers, detector

# ── Optional scanner libraries (graceful fallback) ──────────────────────────
try:
    import cv2
    import numpy as np
    from pyzbar import pyzbar
    SCANNER_AVAILABLE = True
except Exception:
    SCANNER_AVAILABLE = False

app = Flask(__name__)
app.secret_key = "dev-secret-change-this-in-production"
# Optimize performance by caching static files
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

# Route to serve generated images from /tmp on Vercel serverless
@app.route("/static/generated/<path:filename>")
def serve_generated(filename):
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
        return send_from_directory("/tmp/generated", filename)
    return send_from_directory(os.path.join(app.root_path, "static", "generated"), filename)

# Change this to your real deployed URL when you host it (e.g. Render/Railway).
# Dynamic QR codes encode THIS + /r/<short_id>, so it must be publicly reachable
# for scans from other people's phones to work.
BASE_URL = "http://127.0.0.1:5000"


@app.before_request
def _ensure_db():
    database.init_db()


# ── Dashboard ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    codes = database.get_all_codes()
    scan_counts = {c["short_id"]: database.get_scan_count(c["short_id"]) for c in codes}
    stats = {
        "total_codes": len(codes),
        "total_scans": sum(scan_counts.values()),
    }
    return render_template("index.html", codes=codes, stats=stats, scan_counts=scan_counts)


# ── Generator ────────────────────────────────────────────────────────────────

@app.route("/generate", methods=["GET", "POST"])
def generate():
    if request.method == "GET":
        return render_template("generate.html")

    qr_type = request.form.get("qr_type", "text")
    mode = request.form.get("mode", "static")  # 'static' or 'dynamic'
    fg_color = request.form.get("fg_color", "#000000")
    bg_color = request.form.get("bg_color", "#ffffff")

    fields = {k: v for k, v in request.form.items() if k not in ("qr_type", "mode", "fg_color", "bg_color")}

    if mode == "dynamic":
        # Dynamic codes need the actual destination content stored up front,
        # even though the QR image itself only encodes the redirect link.
        target_content = generator.build_data_string(qr_type, fields)
        short_id, filename = generator.generate_dynamic_qr(BASE_URL, fg_color, bg_color)
        database.create_dynamic_code(short_id, qr_type, target_content, filename)
        flash("Dynamic QR code created. You can edit its destination anytime.")
        return redirect(url_for("view_code", short_id=short_id))

    # Static mode
    data, filename = generator.generate_static_qr(qr_type, fields, fg_color, bg_color)
    return render_template("result.html", filename=filename, data=data, mode="static")


# ── Dynamic redirect ─────────────────────────────────────────────────────────

@app.route("/r/<short_id>")
def resolve(short_id):
    """
    The heart of the dynamic QR feature: every scan hits this route first.
    We log the scan, then redirect to whatever the code currently points to.
    """
    code = database.get_dynamic_code(short_id)
    if code is None:
        return "This QR code doesn't exist or was deleted.", 404

    user_agent = request.headers.get("User-Agent", "").lower()
    if "mobile" in user_agent or "android" in user_agent or "iphone" in user_agent:
        device_type = "mobile"
    else:
        device_type = "desktop"

    database.log_scan(short_id, device_type)

    target = code["target_content"]
    # Only redirect for URL-type content; other types (wifi/vcard/text) get
    # shown on a landing page instead, since a browser can't "open" WiFi settings.
    if code["qr_type"] == "url":
        return redirect(target)
    return render_template("landing.html", code=code)


# ── Code detail / edit / delete ───────────────────────────────────────────────

@app.route("/code/<short_id>")
def view_code(short_id):
    code = database.get_dynamic_code(short_id)
    if code is None:
        return "Not found", 404
    scan_count = database.get_scan_count(short_id)
    scans = database.get_scans_for_code(short_id)
    return render_template("code_detail.html", code=code, scan_count=scan_count, scans=scans, base_url=BASE_URL)


@app.route("/code/<short_id>/edit", methods=["POST"])
def edit_code(short_id):
    new_target = request.form.get("new_target", "")
    database.update_target(short_id, new_target)
    flash("Destination updated. The printed QR code still works — no need to reprint it.")
    return redirect(url_for("view_code", short_id=short_id))


@app.route("/code/<short_id>/delete", methods=["POST"])
def delete_code(short_id):
    database.delete_code(short_id)
    flash("QR code deleted.")
    return redirect(url_for("index"))


# ── Download ──────────────────────────────────────────────────────────────────

@app.route("/download/<filename>")
def download_qr(filename):
    """Serve a generated QR image as a direct download."""
    # Security: strip any path separators to prevent directory traversal
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(generator.OUTPUT_DIR, safe_filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_file(file_path, as_attachment=True, download_name=safe_filename)


# ── Scanner ───────────────────────────────────────────────────────────────────

@app.route("/scan", methods=["GET", "POST"])
def scan_page():
    """Upload a QR image and decode it using OpenCV + pyzbar."""
    if request.method == "GET":
        return render_template("scan.html", scanner_available=SCANNER_AVAILABLE)

    if not SCANNER_AVAILABLE:
        return render_template(
            "scan.html",
            scanner_available=False,
            error="Scanner libraries (opencv-python, pyzbar) are not installed. "
                  "Run: pip install opencv-python pyzbar"
        )

    image_file = request.files.get("image")
    if not image_file or image_file.filename == "":
        return render_template("scan.html", scanner_available=True,
                               error="No image file provided.")

    # Read image bytes → numpy array → decode QR
    try:
        file_bytes = np.frombuffer(image_file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image — unsupported format.")

        decoded_objects = pyzbar.decode(img)
        if not decoded_objects:
            return render_template("scan.html", scanner_available=True,
                                   error="No QR code found in the image. Try a clearer photo.")

        obj = decoded_objects[0]
        data = obj.data.decode("utf-8", errors="replace")
        qr_type = obj.type  # e.g. "QRCODE", "EAN13", etc.
        result = {"data": data, "type": qr_type}
        return render_template("scan.html", scanner_available=True, result=result)

    except Exception as exc:
        return render_template("scan.html", scanner_available=True,
                               error=f"Scan failed: {exc}")


# ── Cipher Playground ──────────────────────────────────────────────────────────

@app.route("/playground")
def playground():
    custom_ciphers_data = database.get_custom_ciphers()
    return render_template("playground.html", ciphers=ciphers.CIPHERS, custom_ciphers=custom_ciphers_data)

@app.route("/api/cipher/encode", methods=["POST"])
def api_cipher_encode():
    data = request.json
    text = data.get("text", "")
    cipher_type = data.get("cipher", "")
    key = data.get("key")
    
    if cipher_type.startswith("custom_"):
        cipher_id = int(cipher_type.split("_")[1])
        c_data = database.get_custom_cipher(cipher_id)
        if not c_data:
            return jsonify({"error": "Custom cipher not found"}), 404
        from modules.cipher import custom_cipher
        result = custom_cipher.encode_custom(text, c_data["mapping_json"])
        return jsonify({"result": result})

    if cipher_type not in ciphers.CIPHERS:
        return jsonify({"error": "Unknown cipher type"}), 400
        
    cipher_info = ciphers.CIPHERS[cipher_type]
    try:
        if cipher_info.get("needs_key"):
            # Handle key typing based on key_type
            if cipher_info.get("key_type") == "int":
                key = int(key) if key else cipher_info.get("default_key")
            elif cipher_info.get("key_type") == "str":
                key = str(key) if key else cipher_info.get("default_key")
            result = cipher_info["encode"](text, key)
        else:
            result = cipher_info["encode"](text)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/cipher/decode", methods=["POST"])
def api_cipher_decode():
    data = request.json
    text = data.get("text", "")
    cipher_type = data.get("cipher", "")
    key = data.get("key")
    
    if cipher_type.startswith("custom_"):
        cipher_id = int(cipher_type.split("_")[1])
        c_data = database.get_custom_cipher(cipher_id)
        if not c_data:
            return jsonify({"error": "Custom cipher not found"}), 404
        from modules.cipher import custom_cipher
        result = custom_cipher.decode_custom(text, c_data["mapping_json"])
        return jsonify({"result": result})

    if cipher_type not in ciphers.CIPHERS:
        return jsonify({"error": "Unknown cipher type"}), 400
        
    cipher_info = ciphers.CIPHERS[cipher_type]
    try:
        if cipher_info.get("needs_key"):
            if cipher_info.get("key_type") == "int":
                key = int(key) if key else cipher_info.get("default_key")
            elif cipher_info.get("key_type") == "str":
                key = str(key) if key else cipher_info.get("default_key")
            result = cipher_info["decode"](text, key)
        else:
            result = cipher_info["decode"](text)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/cipher/detect", methods=["POST"])
def api_cipher_detect():
    data = request.json
    text = data.get("text", "")
    result = detector.detect_pattern(text)
    return jsonify(result)

@app.route("/api/cipher/custom", methods=["GET", "POST"])
def api_cipher_custom():
    if request.method == "GET":
        ciphers_data = database.get_custom_ciphers()
        result = [{"id": c["id"], "name": c["name"], "mapping": c["mapping_json"]} for c in ciphers_data]
        return jsonify(result)
        
    elif request.method == "POST":
        data = request.json
        name = data.get("name")
        mapping = data.get("mapping")
        if not name or not mapping:
            return jsonify({"error": "Name and mapping required"}), 400
        import json
        database.create_custom_cipher(name, json.dumps(mapping))
        return jsonify({"success": True})

@app.route("/api/cipher/custom/<int:cipher_id>", methods=["DELETE"])
def api_cipher_custom_delete(cipher_id):
    database.delete_custom_cipher(cipher_id)
    return jsonify({"success": True})

# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    database.init_db()
    app.run(debug=True)
