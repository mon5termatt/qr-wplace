QR Generator (Minimal 21x21+)

A tiny Flask web app for generating the smallest possible standard QR codes (min version 1 = 21x21 modules), with live preview and download.

Features
- Live QR generation as you type (no submit)
- Auto-picks minimal QR version >= 1 (21x21)
- Customization: foreground/background color, transparent background, border, and scale
- Exact counts: black, white, total pixels
- Click preview to download; filename includes a slug + short hash
- Simple, single-file app: `web_app.py`

Requirements
- Python 3.10+
- Install deps: `pip install -r requirements.txt`

Libraries used
- Flask (web)
- segno (preferred) and/or qrcode[pil] (fallback)

Run locally
```bash
# create venv (optional)
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
python web_app.py
```
App starts on http://127.0.0.1:5000 (binds to 0.0.0.0 for LAN access).

Docker (python:3.10-slim)
```bash
docker compose build
docker compose up -d
```
Visit http://localhost:5000.

Usage notes
- Minimum size is standard QR version 1 (21x21). App steps up versions only when data requires.
- Border adds quiet-zone modules around the code; scale sets pixels per module.
- Transparent background sets the light modules to transparent (RGBA PNG).

License
MIT
