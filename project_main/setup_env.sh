#!/bin/bash

# ชื่อ Virtual Environment
VENV_NAME="penv"

echo "==== 🚀 Starting Setup for Raspberry Pi Project ===="

# 1. สร้าง Virtual Environment (ถ้ายังไม่มี)
if [ ! -d "$VENV_NAME" ]; then
    echo "[1/4] Creating virtual environment: $VENV_NAME..."
    python3 -m venv $VENV_NAME
else
    echo "[1/4] Virtual environment '$VENV_NAME' already exists."
fi

# 2. Activate Virtual Environment
echo "[2/4] Activating virtual environment..."
source $VENV_NAME/bin/activate

# 3. อัปเกรด pip
echo "[3/4] Upgrading pip..."
pip install --upgrade pip

# 4. ติดตั้ง Libraries จาก requirements.txt
echo "[4/4] Installing dependencies..."
# ลองติดตั้ง mediapipe แบบระบุ version หรือหาตัวที่เข้ากันได้
# หมายเหตุ: บน Pi บางรุ่น mediapipe อาจหาไม่เจอ ต้องใช้ mediapipe-rpi4 หรือ opencv ตัวอื่น
pip install -r requirements.txt

echo ""
echo "==== ✅ Setup Complete! ===="
echo "To run the program, use:"
echo "  source $VENV_NAME/bin/activate"
echo "  python3 main.py"
echo "============================="
