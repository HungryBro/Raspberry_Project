"""
train.py - Download dataset extrdb v2 จาก Roboflow + Train YOLO11n
สำหรับ Sign Language Detection (27 classes: a-z + 0)

รันไฟล์นี้ทีเดียว จะได้ best.pt สำหรับ Project011

วิธีใช้:
    cd Desktop/Project/YoloTrain
    pip install roboflow ultralytics
    python train.py
"""

import multiprocessing

def main():
    from roboflow import Roboflow

    # ========================================
    # ขั้น 1: Download Dataset จาก Roboflow
    # ========================================
    print("=" * 50)
    print("  ขั้น 1: กำลัง Download Dataset extrdb v2...")
    print("  (8100 ภาพ, 27 classes: a-z + 0)")
    print("=" * 50)

    rf = Roboflow(api_key="ekTKDcHd22SkTXRleX5r")
    project = rf.workspace("school-yzxdc").project("extrdb")
    version = project.version(2)
    dataset = version.download("yolov11")

    print(f"✅ Download เสร็จ! Dataset อยู่ที่: {dataset.location}")

    # ========================================
    # ขั้น 2: Train YOLO11 Nano
    # ========================================
    print("=" * 50)
    print("  ขั้น 2: กำลัง Train YOLO11n...")
    print("  GPU: NVIDIA RTX 4050")
    print("  Dataset: extrdb v2 (Sign Language, 8100 ภาพ)")
    print("  Epochs: 100 (patience=15)")
    print("  ใช้เวลาประมาณ 30-60 นาที")
    print("=" * 50)

    from ultralytics import YOLO

    # โหลด pretrained YOLO11 nano
    model = YOLO("yolo11n.pt")

    # เริ่ม Train
    results = model.train(
        data=f"{dataset.location}/data.yaml",
        epochs=100,                              # 100 รอบ (patience จะหยุดก่อนถ้าพอแล้ว)
        imgsz=640,                               # ตรงกับ dataset
        batch=16,                                # RTX 4050 รับได้
        device=0,                                # GPU
        patience=15,                             # หยุดถ้าไม่ดีขึ้น 15 รอบ
        workers=0,                               # ป้องกัน multiprocessing error บน Windows
        augment=True,                            # เปิด augmentation เพิ่มความแม่น
        project="runs",
        name="sign_v1",
    )

    # ========================================
    # ขั้น 3: สรุปผล
    # ========================================
    print("=" * 50)
    print("  ✅ Train เสร็จแล้ว!")
    print("=" * 50)
    print(f"  📁 ไฟล์ best.pt อยู่ที่: runs/sign_v1/weights/best.pt")
    print()
    print("  ขั้นถัดไป:")
    print("  1. copy best.pt → Project011/models/best.pt")
    print("  2. แก้ config.py ให้ใช้ local model แทน cloud API")
    print("  3. รัน Project011 บน Raspberry Pi 5 (ไม่ต้องต่อ internet!)")
    print("=" * 50)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
