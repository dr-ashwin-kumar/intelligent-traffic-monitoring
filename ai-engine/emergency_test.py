import cv2
from ultralytics import YOLO


MODEL_PATH = "emergency.pt"
VIDEO_PATH = "videos/roadA.mp4"


model = YOLO(MODEL_PATH)

video = cv2.VideoCapture(VIDEO_PATH)

if not video.isOpened():
    raise Exception("Could not open Road A video")


success, frame = video.read()

video.release()


if not success:
    raise Exception("Could not read a frame from Road A")


results = model.predict(
    frame,
    conf=0.40,
    verbose=False
)


print()
print("======================================")
print("EMERGENCY VEHICLE TEST")
print("======================================")


for result in results:

    if result.boxes is None:
        continue

    for box in result.boxes:

        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        class_name = model.names[class_id]

        print(
            f"Detected: {class_name} "
            f"| Confidence: {confidence:.2f}"
        )


print()
print("Test completed.")