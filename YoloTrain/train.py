"""
train.py - Download dataset จาก Roboflow + Train YOLO11n สำหรับ Finger Detection
รันไฟล์นี้ทีเดียว จะได้ best.pt สำหรับ Project011

วิธีใช้:
    cd Desktop/Project/YoloTrain
    python train.py
"""

import multiprocessing


def main():
    from roboflow import Roboflow

    # ========================================
    # ขั้น 1: Download Dataset จาก Roboflow
    # ========================================
    print("=" * 50)
    print("  ขั้น 1: กำลัง Download Dataset...")
    print("=" * 50)

    rf = Roboflow(api_key="ekTKDcHd22SkTXRleX5r")
    project = rf.workspace("dolphin-aedmg").project("finger-izdit-0cyzz")
    version = project.version(1)
    dataset = version.download("yolov11")

    print(f"✅ Download เสร็จ! Dataset อยู่ที่: {dataset.location}")

    # ========================================
    # ขั้น 2: Train YOLO11 Nano
    # ========================================
    print("=" * 50)
    print("  ขั้น 2: กำลัง Train YOLO11n...")
    print("  GPU: NVIDIA RTX 4050")
    print("  ใช้เวลาประมาณ 10-15 นาที")
    print("=" * 50)

    from ultralytics import YOLO

    # โหลด pretrained YOLO11 nano (เล็กสุด เร็วสุด เหมาะกับ Pi 5)
    model = YOLO("yolo11n.pt")

    # เริ่ม Train
    results = model.train(
        data=f"{dataset.location}/data.yaml",   # path ไปยัง dataset
        epochs=50,                               # จำนวนรอบ train
        imgsz=512,                               # ขนาดภาพ (ตรงกับ dataset)
        batch=16,                                # RTX 4050 รับได้ 16
        device=0,                                # ใช้ GPU (RTX 4050)
        patience=10,                             # หยุดก่อนถ้าไม่ดีขึ้น 10 รอบ
        workers=0,                               # ป้องกัน multiprocessing error บน Windows
        project="runs",                          # โฟลเดอร์เก็บผลลัพธ์
        name="finger_detect",                    # ชื่อการ train
    )

    # ========================================
    # ขั้น 3: สรุปผล
    # ========================================
    print("=" * 50)
    print("  ✅ Train เสร็จแล้ว!")
    print("=" * 50)
    print(f"  📁 ไฟล์ best.pt อยู่ที่: runs/finger_detect/weights/best.pt")
    print(f"  📁 ไฟล์ last.pt อยู่ที่: runs/finger_detect/weights/last.pt")
    print()
    print("  ขั้นถัดไป:")
    print("  1. copy best.pt → Project011/models/best.pt")
    print("  2. รัน Project011 บน Raspberry Pi 5")
    print("=" * 50)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
