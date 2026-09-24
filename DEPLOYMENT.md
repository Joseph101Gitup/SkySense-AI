# SKYsense AI: Production Deployment Guide

**Document Version**: 2.1  
**Last Updated**: September 2026  
**Target**: Live, publicly accessible Django web application  

---

## Overview

This guide covers all steps to deploy SKYsense AI as a production web application.

The production stack is:

```
Internet → Nginx (TLS termination + reverse proxy) → Gunicorn (WSGI) → Django 5.2
                                                    ↘ Serves /media/  (uploaded images)
                                WhiteNoise (embedded into Django) → Serves /static/
```

> [!IMPORTANT]
> Run `python manage.py test tests` and verify **87/87 tests pass** before proceeding with any deployment step.

---

## 1. Pre-Deployment Checklist

Run the automated audit script to validate all prerequisites:

```bash
python scripts/production_check.py
```

Expected output: `[SUCCESS] Production readiness audit PASSED with 0 critical failures.`

Manual checklist:

- [ ] `python manage.py test tests` → `Ran 87 tests ... OK`
- [ ] `python manage.py check --deploy` → `System check identified no issues.`
- [ ] `.env` file present on server (never committed to git)
- [ ] `DJANGO_DEBUG=False` in production `.env`
- [ ] `DJANGO_SECRET_KEY` set to a unique cryptographic key (50+ chars)
- [ ] `DJANGO_ALLOWED_HOSTS` includes your domain
- [ ] `DJANGO_CSRF_TRUSTED_ORIGINS` includes your HTTPS domain
- [ ] PostgreSQL provisioned (for multi-node; SQLite is fine for single-node)
- [ ] TLS/SSL certificate obtained (e.g. Let's Encrypt via Certbot)
- [ ] Nginx installed and configured
- [ ] `python manage.py collectstatic --noinput` completed

---

## 2. Settings Architecture

Three settings files manage environment-specific configuration:

| File | Purpose |
|---|---|
| [`settings_base.py`](file:///d:/personal/SkySense_AI/05_Backend/skysense/settings_base.py) | Shared settings (apps, middleware, static/media paths, upload constraints, security headers) |
| [`settings.py`](file:///d:/personal/SkySense_AI/05_Backend/skysense/settings.py) | Default entry point — auto-detects testing, deploy check, and production env context |
| [`settings_prod.py`](file:///d:/personal/SkySense_AI/05_Backend/skysense/settings_prod.py) | Explicit production settings — hardened SSL, HSTS, WhiteNoise, PostgreSQL routing |

To use production settings explicitly:

```bash
export DJANGO_SETTINGS_MODULE=skysense.settings_prod
# or
python manage.py runserver --settings=skysense.settings_prod
```

---

## 3. Environment Configuration

### Step 1: Copy the Template

```bash
cp .env.example .env
```

### Step 2: Generate a Production Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(60))"
```

### Step 3: Edit `.env` for Production

```ini
# ==========================================================
# Production .env — DO NOT commit this file
# ==========================================================

DJANGO_SECRET_KEY=<paste-your-60-char-cryptographic-key>
DJANGO_DEBUG=False
DJANGO_ENV=production
DJANGO_ALLOWED_HOSTS=skysense.ai,www.skysense.ai
DJANGO_CSRF_TRUSTED_ORIGINS=https://skysense.ai,https://www.skysense.ai

DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000

# PostgreSQL (recommended for production)
DATABASE_URL=postgres://skysense_user:STRONGPASSWORD@localhost:5432/skysense_db
DB_CONN_MAX_AGE=600

MAX_UPLOAD_SIZE_MB=15
ALLOWED_IMAGE_MIME_TYPES=image/jpeg,image/png
ALLOWED_IMAGE_EXTENSIONS=.jpg,.jpeg,.png

AI_MODEL_WEIGHTS_PATH=/srv/skysense/03_AI_Model/models/best_xception_rainfall.keras

DJANGO_LOG_LEVEL=WARNING
```

> [!CAUTION]
> Never commit `.env` to git. The `.gitignore` already excludes it. Verify with `git check-ignore -v .env`.

---

## 4. Installing Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate    # Linux/macOS
# venv\Scripts\Activate.ps1  # Windows PowerShell

# Install all verified dependencies
pip install -r requirements.txt

# Linux production: also install gunicorn
pip install gunicorn>=21.2.0
```

### `requirements.txt` contents summary:

| Package | Version | Role |
|---|---|---|
| `Django` | 5.2.17 | Web framework |
| `whitenoise` | 6.12.0 | Static file serving (compressed + cached) |
| `Pillow` | 12.3.0 | Image validation & preprocessing |
| `tensorflow` | 2.21.0 | Deep learning inference engine |
| `keras` | 3.15.1 | Xception model loading & prediction |
| `numpy` | 2.4.6 | Tensor operations |
| `scikit-learn` | 1.9.1 | Evaluation metrics |
| `gunicorn` | 21.2+ | Production WSGI server (Linux) |

---

## 5. Database Setup

### SQLite (Single-Node / Edge Deployment — Default)

SQLite requires no additional setup. Django manages the file automatically:

```bash
python manage.py migrate
python manage.py createsuperuser
```

### PostgreSQL (Recommended for Multi-Node Production)

```sql
-- Run as the postgres superuser
CREATE USER skysense_user WITH PASSWORD 'STRONGPASSWORD';
CREATE DATABASE skysense_db OWNER skysense_user;
GRANT ALL PRIVILEGES ON DATABASE skysense_db TO skysense_user;
```

```bash
pip install psycopg2-binary
python manage.py migrate
python manage.py createsuperuser
```

---

## 6. Collect Static Files (WhiteNoise)

WhiteNoise serves compressed, hashed static assets directly from Django with zero separate CDN required:

```bash
python manage.py collectstatic --noinput
```

This writes all static assets to `05_Backend/staticfiles/`. WhiteNoise then serves them with `Cache-Control: max-age=31536000, immutable` for optimal browser caching.

---

## 7. Gunicorn WSGI Server (Linux)

### Test Gunicorn starts correctly:

```bash
cd 05_Backend
gunicorn skysense.wsgi:application \
  --workers 2 \
  --bind 127.0.0.1:8000 \
  --timeout 120 \
  --log-level info
```

### Gunicorn systemd Unit File

Create `/etc/systemd/system/skysense.service`:

```ini
[Unit]
Description=SKYsense AI Django (Gunicorn)
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/srv/skysense/05_Backend
EnvironmentFile=/srv/skysense/.env
ExecStart=/srv/skysense/venv/bin/gunicorn skysense.wsgi:application \
    --workers 2 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/skysense/access.log \
    --error-logfile /var/log/skysense/error.log \
    --log-level warning
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable skysense
sudo systemctl start skysense
sudo systemctl status skysense
```

---

## 8. Nginx Reverse Proxy Configuration

Create `/etc/nginx/sites-available/skysense`:

```nginx
# HTTP → HTTPS redirect
server {
    listen 80;
    server_name skysense.ai www.skysense.ai;
    return 301 https://$host$request_uri;
}

# HTTPS Production Server
server {
    listen 443 ssl http2;
    server_name skysense.ai www.skysense.ai;

    # TLS Certificates (Let's Encrypt via Certbot)
    ssl_certificate     /etc/letsencrypt/live/skysense.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/skysense.ai/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Upload size limit (match Django MAX_UPLOAD_SIZE_MB)
    client_max_body_size 16M;

    # Static files → served by WhiteNoise via Django (no direct Nginx rule needed)
    # Uncomment below for maximum performance (bypasses Gunicorn for static):
    # location /static/ {
    #     alias /srv/skysense/05_Backend/staticfiles/;
    #     expires 1y;
    #     add_header Cache-Control "public, immutable";
    # }

    # Media files → served directly by Nginx
    location /media/ {
        alias /srv/skysense/05_Backend/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Application → forwarded to Gunicorn
    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/skysense /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### TLS Certificate (Let's Encrypt)

```bash
sudo certbot --nginx -d skysense.ai -d www.skysense.ai
```

---

## 9. Deployment Workflow

Complete, ordered deployment sequence:

```bash
# 1. Pull latest code
git pull origin main

# 2. Install / update dependencies
source venv/bin/activate
pip install -r requirements.txt

# 3. Apply database migrations
cd 05_Backend
python manage.py migrate

# 4. Collect static assets
python manage.py collectstatic --noinput

# 5. Run deployment checks
python manage.py check --deploy

# 6. Run test suite (must pass before going live)
python manage.py test tests

# 7. Restart Gunicorn
sudo systemctl restart skysense

# 8. Reload Nginx (if config changed)
sudo nginx -t && sudo systemctl reload nginx

# 9. Run production audit
python ../scripts/production_check.py
```

---

## 10. Windows-Only Deployment (Waitress)

For Windows Server environments where Gunicorn is unavailable:

```bash
pip install waitress
```

```python
# serve_windows.py
from waitress import serve
import os
import sys

sys.path.insert(0, r'D:\skysense\05_Backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skysense.settings')
os.environ.setdefault('DJANGO_ENV', 'production')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

if __name__ == '__main__':
    print("Starting SKYsense AI on http://0.0.0.0:8000")
    serve(application, host='0.0.0.0', port=8000, threads=4)
```

```bash
python serve_windows.py
```

Place Nginx for Windows or IIS as the TLS-terminating reverse proxy in front.

---

## 11. TensorFlow Lite Edge Deployment

For deploying the model on Raspberry Pi / edge nodes with the TFLite model (20.5 MB):

```bash
# On edge device
pip install tflite-runtime numpy pillow requests
```

```python
# tflite_edge_predict.py — standalone edge inference script
import numpy as np
import requests
from PIL import Image

# Option A: Local TFLite inference
try:
    import tflite_runtime.interpreter as tflite
    interpreter = tflite.Interpreter(model_path="xception_rainfall.tflite")
except ImportError:
    import tensorflow as tf
    interpreter = tf.lite.Interpreter(model_path="xception_rainfall.tflite")

interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

img = Image.open("sky.jpg").convert("RGB").resize((256, 256))
input_data = np.expand_dims(np.array(img, dtype=np.float32) / 255.0, axis=0)

interpreter.set_tensor(input_details[0]['index'], input_data)
interpreter.invoke()
probs = interpreter.get_tensor(output_details[0]['index'])[0]
classes = ["Low_to_Medium_Rain", "Medium_to_Heavy_Rain", "No_to_Low_Rain"]
print(f"Prediction: {classes[probs.argmax()]} ({probs.max()*100:.1f}%)")

# Option B: Forward to central REST API
# response = requests.post("https://skysense.ai/api/predict/",
#     files={"image": open("sky.jpg","rb")},
#     data={"device_id": "RPI-NODE-01", "temperature": 28.4})
# print(response.json())
```

---

## 12. Security Hardening Summary

The following production security controls are verified by `manage.py check --deploy`:

| Control | Implementation |
|---|---|
| **HTTPS Enforcement** | `SECURE_SSL_REDIRECT=True` + Nginx 301 redirect |
| **HSTS (1 Year)** | `SECURE_HSTS_SECONDS=31536000`, Nginx `Strict-Transport-Security` |
| **Secure Session Cookie** | `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True` |
| **Secure CSRF Cookie** | `CSRF_COOKIE_SECURE=True`, `CSRF_COOKIE_HTTPONLY=True` |
| **Content Sniffing** | `SECURE_CONTENT_TYPE_NOSNIFF=True` |
| **Clickjacking** | `X_FRAME_OPTIONS=DENY` |
| **Reverse Proxy Trust** | `SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')` |
| **Upload Limits** | 15 MB max via `DATA_UPLOAD_MAX_MEMORY_SIZE` + Nginx `client_max_body_size 16M` |
| **MIME Validation** | Whitelist: `image/jpeg`, `image/png` only |
| **Binary Image Verification** | Pillow `Image.open().verify()` — rejects corrupt/non-image payloads |
| **UUID File Storage** | Uploaded filenames replaced with UUID hex to prevent path injection |
| **Debug Mode** | `DEBUG=False` — custom `400.html`, `403.html`, `404.html`, `500.html` error views |
| **Secret Management** | `DJANGO_SECRET_KEY` loaded from `.env` (never hardcoded; `.env` in `.gitignore`) |
| **WhiteNoise** | Serves static files with `CompressedManifestStaticFilesStorage` (gzip + hashing) |
| **Path Traversal** | Sample image paths validated using `.resolve().relative_to()` |

---

## 13. Deployment Verification

After deployment, verify the live application:

```bash
# 1. Health check — landing page returns HTTP 200
curl -I https://skysense.ai/

# 2. HTTPS redirect works from HTTP
curl -I http://skysense.ai/

# 3. HSTS header present
curl -I https://skysense.ai/ | grep -i strict-transport

# 4. API endpoint accepts an image
curl -X POST https://skysense.ai/api/predict/ \
  -F "image=@demo_images/no_low/Ci_Ci-N010.jpg" \
  -F "device_id=DEPLOY-TEST-01"

# 5. Static assets served correctly
curl -I https://skysense.ai/static/css/main.css

# 6. Security headers present
curl -I https://skysense.ai/ | grep -E "(X-Frame|X-Content|Strict|Referrer)"
```

Expected API response:

```json
{
  "success": true,
  "prediction": "No_to_Low_Rain",
  "confidence": 0.817,
  "probabilities": {
    "Low_to_Medium_Rain": 0.112,
    "Medium_to_Heavy_Rain": 0.071,
    "No_to_Low_Rain": 0.817
  },
  "timestamp": "2026-09-24T06:00:00.000000+00:00",
  "model_version": "Xception-v1.0",
  "processing_time_ms": 41.2
}
```

---

## 14. Monitoring & Logs

```bash
# Gunicorn application logs
sudo journalctl -u skysense -f

# Access logs
tail -f /var/log/skysense/access.log

# Error logs
tail -f /var/log/skysense/error.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```
