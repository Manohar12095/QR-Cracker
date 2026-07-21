Visit at : https://qr-cracker.vercel.app/
# QR Code Cracker — Core Engine

## Setup
```
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000

## What this core does
- Generates STATIC QR codes (content baked into the code forever) for text, URL, email, phone, SMS, WiFi, and vCard.
- Generates DYNAMIC QR codes (code points to /r/<short_id> on your server, which looks up and redirects to the real destination). This lets you:
  - Edit the destination anytime WITHOUT reprinting the QR code
  - Log every scan (timestamp + device type) for analytics
- SQLite database (qr_cracker.db, auto-created on first run) stores dynamic codes and scan logs.

## Important: BASE_URL in app.py
Dynamic QR codes only work for OTHER people's phones if BASE_URL points to a
publicly reachable address (e.g. after deploying to Render/Railway/PythonAnywhere).
On localhost, dynamic codes will only resolve on the same machine.

## Next layers to build on top of this core
- Scanner (upload/webcam) using opencv + pyzbar
- Batch generation from CSV
- URL-safety analyzer (phishing/shortener flags)
- Dashboard charts (matplotlib or Chart.js)
- Frame/template styles
