## อธิบาย Project_AI ทำการตรวจจับมือเพื่อสั่งการพัดลม

## 010 mediapipe
ใช้ mediapipe เพื่อตรวจจับมือโดยใช้คำแหน่งของมือทั้ง 20 จุด

## 011 yolo model no train (ไม่สามารถรันได้เนื่องจากไม่สามารถลง library inference ที่จำเป็นต่อการรันได้เพราะจะส่งผลกระทบต่อ Project AI หลัก)
ใช้ yolo model จาก cloud ของ roboflow โดยที่ยังไม่ต้อง train model เอง แต่ต้องใช้ API

## 012 yolo model train
ใช้ yolo model ที่ train เองจาก dataset ที่เอามาจาก roboflow
Dataset : https://universe.roboflow.com/school-yzxdc/extrdb/dataset/2

## 013 yolo and mediapipe
เอา yolo model ที่ train เองมาใช้กับ mediapipe เพื่อตรวจจับมือ