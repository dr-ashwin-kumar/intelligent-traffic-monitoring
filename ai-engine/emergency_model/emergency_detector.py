from ultralytics import YOLO

MODEL_PATH = "runs/detect/emergency_yolo11n/weights/best.pt"

model = YOLO(MODEL_PATH)

results = model.predict(
    source="dataset/emergency_data/test/images",
    imgsz=640,
    conf=0.50,
    save=True
)

print("\nEmergency detection completed.")
print("Results saved in runs/detect/predict/")
