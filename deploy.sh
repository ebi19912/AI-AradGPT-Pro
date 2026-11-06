#!/usr/bin/env bash
# ==============================================================================
# اسکریپت استقرار و راه‌اندازی خودکار AradGPT Pro 2.0 (FastAPI Core) روی سرور لینوکس
# ==============================================================================

set -e

echo "🚀 شروع فرایند نصب و راه‌اندازی AradGPT Pro 2.0 (بدون Streamlit)..."

sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv git curl nginx ufw

if [ ! -d "venv" ]; then
    echo "🐍 ایجاد محیط مجازی پایتون (venv)..."
    python3 -m venv venv
fi

echo "📥 نصب پکیج‌های پایتون از requirements.txt..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "🛠️ راه‌اندازی و بررسی ساختار پایگاه‌داده و کاتالوگ مدل‌ها..."
./venv/bin/python repair.py
./venv/bin/python modules/parse_openrouter.py

SERVICE_PATH="/etc/systemd/system/aradgpt.service"
CURRENT_DIR=$(pwd)

echo "⚙️ ساخت سرویس سیستمی systemd در $SERVICE_PATH..."
sudo bash -c "cat > $SERVICE_PATH" <<EOF
[Unit]
Description=AradGPT Pro FastAPI Service
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8501
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
Environment=LC_ALL=C.UTF-8
Environment=LANG=C.UTF-8

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 فعال‌سازی و شروع بکار سرویس AradGPT..."
sudo systemctl daemon-reload
sudo systemctl enable aradgpt
sudo systemctl restart aradgpt

echo "🛡️ تنظیم فایروال UFW..."
sudo ufw allow 80/tcp || true
sudo ufw allow 443/tcp || true
sudo ufw allow 8501/tcp || true

echo "=============================================================================="
echo "🎉 استقرار AradGPT Pro 2.0 با موفقیت پایان یافت!"
echo "🌐 آدرس سرور: http://$(curl -s ifconfig.me):8501"
echo "👤 نام کاربری ادمین پیش‌فرض: admin"
echo "🔑 رمز عبور ادمین پیش‌فرض: admin123"
echo "=============================================================================="
