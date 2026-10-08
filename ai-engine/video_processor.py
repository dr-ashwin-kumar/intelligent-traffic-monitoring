import cv2
import os
import json
from ultralytics import YOLO
from collections import deque


# ==========================================
# BASE DIRECTORY
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ==========================================
# MODELS
# ==========================================

GENERAL_MODEL_PATH = os.path.join(
    BASE_DIR,
    "yolo11n.pt"
)

EMERGENCY_MODEL_PATH = os.path.join(
    BASE_DIR,
    "emergency_model",
    "runs",
    "detect",
    "emergency_yolo11n",
    "weights",
    "best.pt"
)


# ==========================================
# VEHICLE CLASSES
# COCO classes used by yolo11n.pt
# ==========================================

VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}


# ==========================================
# EMERGENCY VEHICLE CLASSES
# ==========================================

EMERGENCY_CLASSES = {
    0: "Police",
    1: "ambulance",
    2: "firetruck"
}


# ==========================================
# EMERGENCY WEIGHTS
# ==========================================

EMERGENCY_WEIGHTS = {
    "Police": 2,
    "ambulance": 5,
    "firetruck": 5
}


# ==========================================
# CONFIRMATION SETTINGS
# ==========================================

EMERGENCY_CONFIRMATION_FRAMES = 3


# ==========================================
# TRAFFIC LEVEL
# ==========================================

def get_traffic_level(score):

    if score <= 10:
        return "LOW"

    elif score <= 25:
        return "MEDIUM"

    else:
        return "HIGH"


# ==========================================
# VIDEO ANALYSIS
# ==========================================

def analyze_video(
    road_name,
    video_path,
    output_video_path,
    output_json_path
):

    print()
    print("======================================")
    print(f"Analyzing: {road_name}")
    print("======================================")

    print(
        f"Loading general model: "
        f"{GENERAL_MODEL_PATH}"
    )

    print(
        f"Loading emergency model: "
        f"{EMERGENCY_MODEL_PATH}"
    )

    # ======================================
    # LOAD MODELS
    # ======================================

    general_model = YOLO(
        GENERAL_MODEL_PATH
    )

    emergency_model = YOLO(
        EMERGENCY_MODEL_PATH
    )

    print(
        f"General model classes: "
        f"{general_model.names}"
    )

    print(
        f"Emergency model classes: "
        f"{emergency_model.names}"
    )


    # ======================================
    # OPEN VIDEO
    # ======================================

    video = cv2.VideoCapture(
        video_path
    )

    if not video.isOpened():

        raise Exception(
            f"Could not open video: "
            f"{video_path}"
        )


    fps = video.get(
        cv2.CAP_PROP_FPS
    )

    width = int(
        video.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )

    height = int(
        video.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    total_frames = int(
        video.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )


    print(
        f"Video resolution: "
        f"{width} x {height}"
    )

    print(
        f"FPS: {fps}"
    )

    print(
        f"Total frames: {total_frames}"
    )


    # ======================================
    # OUTPUT VIDEO
    # ======================================

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    output = cv2.VideoWriter(
        output_video_path,
        fourcc,
        fps,
        (width, height)
    )


    # ======================================
    # ROI
    # ======================================

    roi_top = int(
        height * 0.40
    )

    roi_bottom = height

    roi_left = 0
    roi_right = width


    # ======================================
    # TRAFFIC HISTORY
    # ======================================

    score_history = deque(
        maxlen=10
    )


    # ======================================
    # EMERGENCY TRACK HISTORY
    # ======================================

    emergency_streaks = {

        "Police": 0,
        "ambulance": 0,
        "firetruck": 0

    }


    # ======================================
    # MAXIMUM VEHICLE COUNTS
    # ======================================

    maximum_vehicle_counts = {

        "Car": 0,
        "Motorcycle": 0,
        "Bus": 0,
        "Truck": 0

    }


    # ======================================
    # TOTAL VEHICLE DETECTIONS
    # ======================================

    total_vehicle_detections = {

        "Car": 0,
        "Motorcycle": 0,
        "Bus": 0,
        "Truck": 0

    }


    # ======================================
    # MAXIMUM EMERGENCY COUNTS
    # ======================================

    maximum_emergency_counts = {

        "Police": 0,
        "ambulance": 0,
        "firetruck": 0

    }


    # ======================================
    # TOTAL EMERGENCY DETECTIONS
    # ======================================

    total_emergency_detections = {

        "Police": 0,
        "ambulance": 0,
        "firetruck": 0

    }


    # ======================================
    # MAXIMUM TRAFFIC
    # ======================================

    maximum_current_count = 0

    maximum_score = 0


    # ======================================
    # FRAME DATA
    # ======================================

    frame_number = 0

    final_average_score = 0

    final_traffic_level = "LOW"

    final_confirmed_emergencies = []


    # ======================================
    # PROCESS VIDEO
    # ======================================

    while True:

        success, frame = video.read()

        if not success:
            break


        frame_number += 1


        # ==================================
        # GENERAL VEHICLE DETECTION
        # ==================================

        general_results = general_model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )


        # ==================================
        # EMERGENCY VEHICLE DETECTION
        # ==================================

        emergency_results = emergency_model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )


        # ==================================
        # CURRENT VEHICLES
        # ==================================

        current_vehicle_counts = {

            "Car": 0,
            "Motorcycle": 0,
            "Bus": 0,
            "Truck": 0

        }


        # ==================================
        # CURRENT EMERGENCIES
        # ==================================

        current_emergency_classes = set()


        # ==================================
        # PROCESS GENERAL VEHICLES
        # ==================================

        for result in general_results:

            if result.boxes is None:
                continue


            for box in result.boxes:

                class_id = int(
                    box.cls[0]
                )

                confidence = float(
                    box.conf[0]
                )


                if class_id not in VEHICLE_CLASSES:
                    continue


                vehicle_name = (
                    VEHICLE_CLASSES[
                        class_id
                    ]
                )


                # ------------------------------
                # COUNT VEHICLE
                # ------------------------------

                current_vehicle_counts[
                    vehicle_name
                ] += 1

                total_vehicle_detections[
                    vehicle_name
                ] += 1


                # ------------------------------
                # DRAW VEHICLE
                # ------------------------------

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )


                label = (
                    f"{vehicle_name} "
                    f"{confidence:.2f}"
                )


                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )


                cv2.putText(
                    frame,
                    label,
                    (
                        x1,
                        max(y1 - 10, 20)
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )


        # ==================================
        # UPDATE MAX VEHICLE COUNTS
        # ==================================

        for vehicle_name in (
            maximum_vehicle_counts
        ):

            maximum_vehicle_counts[
                vehicle_name
            ] = max(

                maximum_vehicle_counts[
                    vehicle_name
                ],

                current_vehicle_counts[
                    vehicle_name
                ]

            )


        # ==================================
        # PROCESS EMERGENCY VEHICLES
        # ==================================

        for result in emergency_results:

            if result.boxes is None:
                continue


            for box in result.boxes:

                class_id = int(
                    box.cls[0]
                )

                confidence = float(
                    box.conf[0]
                )


                if (
                    class_id
                    not in EMERGENCY_CLASSES
                ):
                    continue


                emergency_name = (
                    EMERGENCY_CLASSES[
                        class_id
                    ]
                )


                current_emergency_classes.add(
                    emergency_name
                )


                total_emergency_detections[
                    emergency_name
                ] += 1


                # ------------------------------
                # DRAW EMERGENCY DETECTION
                # ------------------------------

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )


                label = (
                    f"{emergency_name} "
                    f"{confidence:.2f}"
                )


                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 255),
                    3
                )


                cv2.putText(
                    frame,
                    label,
                    (
                        x1,
                        max(y1 - 10, 20)
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )


        # ==========================================
        # UPDATE EMERGENCY STREAKS
        # ==========================================

        for emergency_name in (
            emergency_streaks
        ):

            if (
                emergency_name
                in current_emergency_classes
            ):

                emergency_streaks[
                    emergency_name
                ] += 1

            else:

                emergency_streaks[
                    emergency_name
                ] = 0


        # ==========================================
        # CONFIRMED EMERGENCIES
        # ==========================================

        confirmed_emergencies = []

        for (
            emergency_name,
            streak
        ) in emergency_streaks.items():

            if (
                streak
                >= EMERGENCY_CONFIRMATION_FRAMES
            ):

                confirmed_emergencies.append(
                    emergency_name
                )


        final_confirmed_emergencies = (
            confirmed_emergencies.copy()
        )


        # ==========================================
        # CURRENT EMERGENCY COUNTS
        # ==========================================

        current_emergency_counts = {

            "Police": 0,
            "ambulance": 0,
            "firetruck": 0

        }


        for emergency_name in (
            current_emergency_classes
        ):

            current_emergency_counts[
                emergency_name
            ] += 1


        # ==========================================
        # UPDATE MAXIMUM EMERGENCY COUNTS
        # ==========================================

        for emergency_name in (
            maximum_emergency_counts
        ):

            maximum_emergency_counts[
                emergency_name
            ] = max(

                maximum_emergency_counts[
                    emergency_name
                ],

                current_emergency_counts[
                    emergency_name
                ]

            )


        # ==========================================
        # EMERGENCY SCORE
        # ==========================================

        emergency_score = 0

        for emergency_name in (
            confirmed_emergencies
        ):

            emergency_score += (
                EMERGENCY_WEIGHTS[
                    emergency_name
                ]
            )


        # ==========================================
        # TOTAL CURRENT VEHICLES
        # ==========================================

        normal_vehicle_count = sum(
            current_vehicle_counts.values()
        )


        # Emergency vehicles are kept
        # separately and are not added again
        # to normal vehicle count.

        current_vehicle_count = (
            normal_vehicle_count
        )


        # ==========================================
        # TRAFFIC SCORE
        # ==========================================

        traffic_score = (
            current_vehicle_count
        )


        maximum_current_count = max(
            maximum_current_count,
            current_vehicle_count
        )


        maximum_score = max(
            maximum_score,
            traffic_score
        )


        # ==========================================
        # ROLLING SCORE
        # ==========================================

        score_history.append(
            traffic_score
        )


        if len(score_history) > 0:

            average_score = (
                sum(score_history)
                /
                len(score_history)
            )

        else:

            average_score = 0


        final_average_score = (
            average_score
        )


        final_traffic_level = (
            get_traffic_level(
                average_score
            )
        )


        # ==========================================
        # DISPLAY INFORMATION
        # ==========================================

        cv2.putText(
            frame,
            f"Traffic: {final_traffic_level}",
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            (
                f"Vehicles: "
                f"{current_vehicle_count}"
            ),
            (30, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            (
                f"Cars: "
                f"{current_vehicle_counts['Car']} "
                f"Bikes: "
                f"{current_vehicle_counts['Motorcycle']}"
            ),
            (30, 115),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            (
                f"Buses: "
                f"{current_vehicle_counts['Bus']} "
                f"Trucks: "
                f"{current_vehicle_counts['Truck']}"
            ),
            (30, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            (
                f"Traffic Score: "
                f"{average_score:.2f}"
            ),
            (30, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )


        # ==========================================
        # EMERGENCY STATUS
        # ==========================================

        if confirmed_emergencies:

            emergency_text = (
                "CONFIRMED: "
                +
                ", ".join(
                    confirmed_emergencies
                )
            )


            cv2.putText(
                frame,
                emergency_text,
                (30, 220),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        else:

            cv2.putText(
                frame,
                "Emergency: None confirmed",
                (30, 220),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )


        # ==========================================
        # ROI LINE
        # ==========================================

        cv2.line(
            frame,
            (roi_left, roi_top),
            (roi_right, roi_top),
            (255, 255, 255),
            2
        )


        # ==========================================
        # WRITE FRAME
        # ==========================================

        output.write(frame)


    # ==========================================
    # RELEASE VIDEO
    # ==========================================

    video.release()

    output.release()


    # ==========================================
    # FINAL RESULTS
    # ==========================================

    final_average_score = round(
        final_average_score,
        2
    )


    # ==========================================
    # FINAL VEHICLE TOTAL
    # ==========================================

    total_vehicle_count = sum(
        maximum_vehicle_counts.values()
    )


    # ==========================================
    # FINAL JSON
    # ==========================================

    analysis = {

        "road": road_name,

        "video": video_path,

        "traffic": {

            "total_vehicles":
                total_vehicle_count,

            "cars":
                maximum_vehicle_counts[
                    "Car"
                ],

            "motorcycles":
                maximum_vehicle_counts[
                    "Motorcycle"
                ],

            "buses":
                maximum_vehicle_counts[
                    "Bus"
                ],

            "trucks":
                maximum_vehicle_counts[
                    "Truck"
                ],

            "average_traffic_score":
                final_average_score,

            "maximum_traffic_score":
                maximum_score,

            "traffic_level":
                final_traffic_level,

            "maximum_vehicle_count":
                maximum_current_count
        },

        "vehicle_detections": {

            "maximum_counts":
                maximum_vehicle_counts,

            "total_detections":
                total_vehicle_detections
        },

        "emergency_vehicles": {

            "maximum_counts":
                maximum_emergency_counts,

            "total_detections":
                total_emergency_detections,

            "confirmed_emergencies":
                final_confirmed_emergencies,

            "confirmation_frames":
                EMERGENCY_CONFIRMATION_FRAMES
        }
    }


    # ==========================================
    # SAVE JSON
    # ==========================================

    with open(
        output_json_path,
        "w"
    ) as json_file:

        json.dump(
            analysis,
            json_file,
            indent=4
        )


    # ==========================================
    # PRINT RESULT
    # ==========================================

    print()

    print(
        "======================================"
    )

    print(
        "Analysis complete."
    )

    print(
        "======================================"
    )

    print(
        f"Total vehicles: "
        f"{total_vehicle_count}"
    )

    print(
        f"Cars: "
        f"{maximum_vehicle_counts['Car']}"
    )

    print(
        f"Motorcycles: "
        f"{maximum_vehicle_counts['Motorcycle']}"
    )

    print(
        f"Buses: "
        f"{maximum_vehicle_counts['Bus']}"
    )

    print(
        f"Trucks: "
        f"{maximum_vehicle_counts['Truck']}"
    )

    print()

    print(
        f"Average traffic score: "
        f"{final_average_score:.2f}"
    )

    print(
        f"Traffic level: "
        f"{final_traffic_level}"
    )

    print()

    print(
        "Emergency vehicles:"
    )

    for (
        emergency_name,
        count
    ) in maximum_emergency_counts.items():

        print(
            f"  {emergency_name}: "
            f"{count}"
        )


    print()

    print(
        "Confirmed emergencies:"
    )

    if final_confirmed_emergencies:

        for emergency_name in (
            final_confirmed_emergencies
        ):

            print(
                f"  {emergency_name}"
            )

    else:

        print(
            "  None"
        )


    print()

    print(
        f"Video saved: "
        f"{output_video_path}"
    )

    print(
        f"JSON saved: "
        f"{output_json_path}"
    )


    return analysis


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    analyze_video(

        road_name="Road A",

        video_path="../videos/roadA.mp4",

        output_video_path=(
            "roadA_vehicle_detection.mp4"
        ),

        output_json_path=(
            "roadA_analysis.json"
        )
    )