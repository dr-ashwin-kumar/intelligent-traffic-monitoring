import cv2
import json
from ultralytics import YOLO
from collections import Counter, deque


# ==============================
# CONFIGURATION
# ==============================

MODEL_PATH = "yolo11n.pt"

VIDEO_PATH = "../backend/src/uploads/215258.mp4"

OUTPUT_VIDEO_PATH = "traffic_density_result.mp4"

OUTPUT_JSON_PATH = "traffic_analysis.json"


# ==============================
# VEHICLE CLASSES
# ==============================

VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}


# ==============================
# VEHICLE WEIGHTS
# ==============================

VEHICLE_WEIGHTS = {
    "car": 1,
    "motorcycle": 1,
    "bus": 3,
    "truck": 3
}


# ==============================
# LOAD MODEL
# ==============================

model = YOLO(MODEL_PATH)


# ==============================
# OPEN VIDEO
# ==============================

video = cv2.VideoCapture(VIDEO_PATH)

if not video.isOpened():
    print("Could not open video")
    exit()


fps = video.get(cv2.CAP_PROP_FPS)

width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))

height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))


print(f"Video resolution: {width} x {height}")
print(f"FPS: {fps}")


# ==============================
# OUTPUT VIDEO
# ==============================

fourcc = cv2.VideoWriter_fourcc(*"mp4v")

output = cv2.VideoWriter(
    OUTPUT_VIDEO_PATH,
    fourcc,
    fps,
    (width, height)
)


# ==============================
# REGION OF INTEREST
# ==============================

roi_top = int(height * 0.40)
roi_bottom = height

roi_left = 0
roi_right = width


# ==============================
# ROLLING SCORE
# ==============================

score_history = deque(maxlen=10)


# ==============================
# TRACKING DATA
# ==============================

frame_number = 0

maximum_current_count = 0

maximum_score = 0

maximum_vehicle_counts = {
    "car": 0,
    "motorcycle": 0,
    "bus": 0,
    "truck": 0
}


# ==============================
# FINAL STATE
# ==============================

final_average_score = 0

final_traffic_level = "LOW"


# ==============================
# PROCESS VIDEO
# ==============================

while True:

    success, frame = video.read()

    if not success:
        break

    frame_number += 1


    # ==============================
    # YOLO TRACKING
    # ==============================

    results = model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        verbose=False
    )


    # Current vehicles inside ROI

    current_vehicles = {}


    # ==============================
    # PROCESS DETECTIONS
    # ==============================

    for result in results:

        if result.boxes is None:
            continue


        for box in result.boxes:

            if box.id is None:
                continue


            track_id = int(box.id[0])

            class_id = int(box.cls[0])

            confidence = float(box.conf[0])


            # Ignore non-vehicle objects

            if class_id not in VEHICLE_CLASSES:
                continue


            vehicle_type = VEHICLE_CLASSES[class_id]


            # Bounding box

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )


            # Center point

            center_x = int((x1 + x2) / 2)

            center_y = int((y1 + y2) / 2)


            # Check whether vehicle is inside ROI

            inside_roi = (
                roi_left <= center_x <= roi_right
                and
                roi_top <= center_y <= roi_bottom
            )


            if not inside_roi:
                continue


            # Store current vehicle

            current_vehicles[track_id] = vehicle_type


            # ==============================
            # DRAW VEHICLE
            # ==============================

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )


            label = (
                f"{vehicle_type} "
                f"#{track_id} "
                f"{confidence:.2f}"
            )


            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )


    # ==============================
    # CURRENT VEHICLE COUNT
    # ==============================

    current_count = len(current_vehicles)


    # ==============================
    # CURRENT VEHICLE BREAKDOWN
    # ==============================

    current_vehicle_counts = Counter(
        current_vehicles.values()
    )


    # ==============================
    # CURRENT TRAFFIC SCORE
    # ==============================

    current_score = 0


    for vehicle_type in current_vehicles.values():

        current_score += VEHICLE_WEIGHTS[vehicle_type]


    # Add to rolling history

    score_history.append(current_score)


    # ==============================
    # ROLLING AVERAGE
    # ==============================

    average_score = (
        sum(score_history) /
        len(score_history)
    )


    final_average_score = average_score


    # ==============================
    # TRAFFIC LEVEL
    # ==============================

    if average_score <= 10:

        traffic_level = "LOW"

    elif average_score <= 25:

        traffic_level = "MEDIUM"

    else:

        traffic_level = "HIGH"


    final_traffic_level = traffic_level


    # ==============================
    # MAXIMUM VALUES
    # ==============================

    if current_count > maximum_current_count:

        maximum_current_count = current_count


    if current_score > maximum_score:

        maximum_score = current_score


    # Store maximum vehicle counts

    for vehicle_type in VEHICLE_CLASSES.values():

        count = current_vehicle_counts[vehicle_type]

        if count > maximum_vehicle_counts[vehicle_type]:

            maximum_vehicle_counts[vehicle_type] = count


    # ==============================
    # DRAW ROI
    # ==============================

    cv2.rectangle(
        frame,
        (roi_left, roi_top),
        (roi_right, roi_bottom),
        (255, 255, 0),
        2
    )


    cv2.putText(
        frame,
        "TRAFFIC ROI",
        (20, roi_top - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2
    )


    # ==============================
    # DISPLAY INFORMATION
    # ==============================

    cv2.putText(
        frame,
        f"Current Vehicles: {current_count}",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )


    cv2.putText(
        frame,
        f"Current Score: {current_score}",
        (20, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )


    cv2.putText(
        frame,
        f"Average Score: {average_score:.1f}",
        (20, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )


    cv2.putText(
        frame,
        f"Traffic Level: {traffic_level}",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )


    cv2.putText(
        frame,
        f"Frame: {frame_number}",
        (20, 150),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2
    )


    # ==============================
    # WRITE OUTPUT FRAME
    # ==============================

    output.write(frame)


# ==============================
# RELEASE VIDEO
# ==============================

video.release()

output.release()


# ==============================
# CREATE JSON RESULT
# ==============================

analysis_result = {
    "road": "Road A",

    "video": {
        "frames_processed": frame_number,
        "fps": fps,
        "width": width,
        "height": height
    },

    "traffic": {
        "maximum_vehicles_in_roi": maximum_current_count,
        "maximum_traffic_score": maximum_score,
        "average_traffic_score": round(
            final_average_score,
            2
        ),
        "traffic_level": final_traffic_level
    },

    "vehicle_counts": {
        "car": maximum_vehicle_counts["car"],
        "motorcycle": maximum_vehicle_counts["motorcycle"],
        "bus": maximum_vehicle_counts["bus"],
        "truck": maximum_vehicle_counts["truck"]
    }
}


# ==============================
# SAVE JSON
# ==============================

with open(
    OUTPUT_JSON_PATH,
    "w"
) as json_file:

    json.dump(
        analysis_result,
        json_file,
        indent=4
    )


# ==============================
# FINAL OUTPUT
# ==============================

print()

print("==============================")
print("TRAFFIC DENSITY ANALYSIS")
print("==============================")

print(
    f"Total frames processed: "
    f"{frame_number}"
)

print(
    f"Maximum vehicles in ROI: "
    f"{maximum_current_count}"
)

print(
    f"Maximum traffic score: "
    f"{maximum_score}"
)

print(
    f"Final rolling average score: "
    f"{final_average_score:.2f}"
)

print(
    f"Final traffic level: "
    f"{final_traffic_level}"
)

print()

print(
    f"JSON result: "
    f"{OUTPUT_JSON_PATH}"
)

print(
    f"Output video: "
    f"{OUTPUT_VIDEO_PATH}"
)