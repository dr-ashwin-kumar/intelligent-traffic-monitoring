import json
import os


# ==========================================
# CONFIGURATION
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

ANALYSIS_FILE = os.path.join(
    BASE_DIR,
    "all_roads_analysis.json"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "signal_decision.json"
)


# ==========================================
# EMERGENCY VEHICLE PRIORITY
# ==========================================

EMERGENCY_PRIORITY = {
    "Police": 2,
    "ambulance": 5,
    "firetruck": 5
}


# ==========================================
# EMERGENCY GREEN TIME
# ==========================================

EMERGENCY_GREEN_TIME = {
    "Police": 40,
    "ambulance": 60,
    "firetruck": 60
}


# ==========================================
# TRAFFIC GREEN TIME
# ==========================================

def get_traffic_green_time(traffic_score):

    if traffic_score <= 10:
        return 20

    elif traffic_score <= 25:
        return 40

    else:
        return 60


# ==========================================
# CALCULATE EMERGENCY SCORE
# ==========================================

def calculate_emergency_score(
    confirmed_emergencies,
    maximum_counts
):

    emergency_score = 0

    for emergency_name in confirmed_emergencies:

        base_priority = EMERGENCY_PRIORITY.get(
            emergency_name,
            0
        )

        vehicle_count = maximum_counts.get(
            emergency_name,
            1
        )

        vehicle_count = max(
            1,
            int(vehicle_count)
        )

        emergency_score += (
            base_priority *
            vehicle_count
        )

    return emergency_score


# ==========================================
# CALCULATE ROAD PRIORITY
# ==========================================

def calculate_road_priority(road_data):

    traffic_data = road_data.get(
        "traffic",
        {}
    )

    emergency_data = road_data.get(
        "emergency_vehicles",
        {}
    )

    # ======================================
    # TRAFFIC SCORE
    # ======================================

    traffic_score = float(
        traffic_data.get(
            "average_traffic_score",
            0
        )
    )

    # ======================================
    # EMERGENCY DATA
    # ======================================

    confirmed_emergencies = (
        emergency_data.get(
            "confirmed_emergencies",
            []
        )
    )

    maximum_counts = (
        emergency_data.get(
            "maximum_counts",
            {
                "Police": 0,
                "ambulance": 0,
                "firetruck": 0
            }
        )
    )

    # ======================================
    # EMERGENCY SCORE
    # ======================================

    emergency_score = calculate_emergency_score(
        confirmed_emergencies,
        maximum_counts
    )

    # ======================================
    # TOTAL SCORE
    # ======================================

    priority_score = (
        traffic_score +
        emergency_score
    )

    return (
        round(traffic_score, 2),
        emergency_score,
        round(priority_score, 2)
    )


# ==========================================
# DETERMINE GREEN TIME
# ==========================================

def determine_green_time(
    traffic_score,
    confirmed_emergencies
):

    # ======================================
    # NORMAL TRAFFIC TIMING
    # ======================================

    green_time = get_traffic_green_time(
        traffic_score
    )

    reason = (
        "Traffic-based signal timing"
    )

    # ======================================
    # EMERGENCY OVERRIDE
    # ======================================

    if confirmed_emergencies:

        highest_emergency = max(
            confirmed_emergencies,
            key=lambda name:
                EMERGENCY_PRIORITY.get(
                    name,
                    0
                )
        )

        green_time = (
            EMERGENCY_GREEN_TIME.get(
                highest_emergency,
                60
            )
        )

        reason = (
            "Confirmed emergency vehicle: "
            +
            ", ".join(
                confirmed_emergencies
            )
        )

    return (
        green_time,
        reason
    )


# ==========================================
# SIGNAL DECISION
# ==========================================

def make_signal_decision():

    # ======================================
    # CHECK ANALYSIS FILE
    # ======================================

    if not os.path.exists(
        ANALYSIS_FILE
    ):

        raise FileNotFoundError(

            f"Analysis file not found:\n"
            f"{ANALYSIS_FILE}\n\n"
            f"Run main.py first."
        )

    # ======================================
    # LOAD ALL ROAD DATA
    # ======================================

    with open(
        ANALYSIS_FILE,
        "r"
    ) as json_file:

        data = json.load(
            json_file
        )

    roads = data.get(
        "roads",
        {}
    )

    if not roads:

        raise ValueError(
            "No road analysis data found."
        )

    # ======================================
    # ANALYZE EVERY ROAD
    # ======================================

    road_results = {}

    for road_id, road_data in roads.items():

        (
            traffic_score,
            emergency_score,
            priority_score
        ) = calculate_road_priority(
            road_data
        )

        traffic_data = road_data.get(
            "traffic",
            {}
        )

        emergency_data = road_data.get(
            "emergency_vehicles",
            {}
        )

        traffic_level = traffic_data.get(
            "traffic_level",
            "LOW"
        )

        confirmed_emergencies = (
            emergency_data.get(
                "confirmed_emergencies",
                []
            )
        )

        maximum_counts = (
            emergency_data.get(
                "maximum_counts",
                {
                    "Police": 0,
                    "ambulance": 0,
                    "firetruck": 0
                }
            )
        )

        # ==================================
        # GREEN TIME
        # ==================================

        (
            green_time,
            reason
        ) = determine_green_time(
            traffic_score,
            confirmed_emergencies
        )

        # ==================================
        # STORE ROAD RESULT
        # ==================================

        road_results[road_id] = {

            "road": road_data.get(
                "road",
                road_id
            ),

            "traffic_score":
                traffic_score,

            "traffic_level":
                traffic_level,

            # ==================================
            # NORMAL VEHICLE INFORMATION
            # ==================================

            "total_vehicles":
                traffic_data.get(
                    "total_vehicles",
                    0
                ),

            "cars":
                traffic_data.get(
                    "cars",
                    0
                ),

            "motorcycles":
                traffic_data.get(
                    "motorcycles",
                    0
                ),

            "buses":
                traffic_data.get(
                    "buses",
                    0
                ),

            "trucks":
                traffic_data.get(
                    "trucks",
                    0
                ),

            # ==================================
            # EMERGENCY INFORMATION
            # ==================================

            "emergency_score":
                emergency_score,

            "priority_score":
                priority_score,

            "emergency_vehicles":
                maximum_counts,

            "confirmed_emergencies":
                confirmed_emergencies,

            "recommended_green_time":
                green_time,

            "reason":
                reason
        }

    # ==========================================
    # FIND ROADS WITH CONFIRMED EMERGENCIES
    # ==========================================

    emergency_roads = {

        road_id: road_data

        for road_id, road_data
        in road_results.items()

        if road_data[
            "confirmed_emergencies"
        ]
    }

    # ==========================================
    # SELECT ROAD
    #
    # EMERGENCY OVERRIDES TRAFFIC
    # ==========================================

    if emergency_roads:

        print()

        print(
            "CONFIRMED EMERGENCY DETECTED"
        )

        print(
            "Emergency roads will receive priority."
        )

        recommended_road_id = max(

            emergency_roads,

            key=lambda road_id: (

                emergency_roads[
                    road_id
                ][
                    "emergency_score"
                ],

                emergency_roads[
                    road_id
                ][
                    "priority_score"
                ]
            )
        )

        selection_mode = (
            "Emergency priority"
        )

    else:

        recommended_road_id = max(

            road_results,

            key=lambda road_id:

                road_results[
                    road_id
                ][
                    "priority_score"
                ]
        )

        selection_mode = (
            "Traffic priority"
        )

    recommended = road_results[
        recommended_road_id
    ]

    # ==========================================
    # BUILD FINAL DECISION
    # ==========================================

    decision = {

        "recommended_road":
            recommended["road"],

        "traffic_score":
            recommended["traffic_score"],

        "traffic_level":
            recommended["traffic_level"],

        "total_vehicles":
            recommended["total_vehicles"],

        "cars":
            recommended["cars"],

        "motorcycles":
            recommended["motorcycles"],

        "buses":
            recommended["buses"],

        "trucks":
            recommended["trucks"],

        "emergency_score":
            recommended["emergency_score"],

        "priority_score":
            recommended["priority_score"],

        "emergency_vehicles":
            recommended[
                "emergency_vehicles"
            ],

        "confirmed_emergencies":
            recommended[
                "confirmed_emergencies"
            ],

        "recommended_green_time":
            recommended[
                "recommended_green_time"
            ],

        "reason":
            recommended["reason"],

        "selection_mode":
            selection_mode,

        "road_priorities": {

            road_data["road"]:
                road_data["priority_score"]

            for road_data
            in road_results.values()
        },

        "all_roads":
            road_results
    }

    # ==========================================
    # SAVE DECISION
    # ==========================================

    with open(
        OUTPUT_FILE,
        "w"
    ) as json_file:

        json.dump(
            decision,
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
        "TRAFFIC SIGNAL DECISION"
    )

    print(
        "======================================"
    )

    print()

    # ==========================================
    # ROAD PRIORITIES
    # ==========================================

    print(
        "ROAD PRIORITIES:"
    )

    for road_id, road_data in (
        road_results.items()
    ):

        print(

            f"  {road_data['road']}: "
            f"{road_data['priority_score']}"

        )

    print()

    # ==========================================
    # SELECTION MODE
    # ==========================================

    print(
        f"Selection Mode: "
        f"{selection_mode}"
    )

    print()

    # ==========================================
    # RECOMMENDED ROAD
    # ==========================================

    print(
        f"Recommended Road: "
        f"{recommended['road']}"
    )

    print(
        f"Traffic Score: "
        f"{recommended['traffic_score']}"
    )

    print(
        f"Traffic Level: "
        f"{recommended['traffic_level']}"
    )

    print(
        f"Total Vehicles: "
        f"{recommended['total_vehicles']}"
    )

    print(
        f"Cars: "
        f"{recommended['cars']}"
    )

    print(
        f"Motorcycles: "
        f"{recommended['motorcycles']}"
    )

    print(
        f"Buses: "
        f"{recommended['buses']}"
    )

    print(
        f"Trucks: "
        f"{recommended['trucks']}"
    )

    print(
        f"Emergency Score: "
        f"{recommended['emergency_score']}"
    )

    print(
        f"Priority Score: "
        f"{recommended['priority_score']}"
    )

    print()

    # ==========================================
    # EMERGENCY VEHICLES
    # ==========================================

    print(
        "Emergency Vehicles:"
    )

    for emergency_name, count in (
        recommended[
            "emergency_vehicles"
        ].items()
    ):

        print(
            f"  {emergency_name}: "
            f"{count}"
        )

    print()

    # ==========================================
    # CONFIRMED EMERGENCIES
    # ==========================================

    print(
        "Confirmed Emergencies:"
    )

    if recommended[
        "confirmed_emergencies"
    ]:

        for emergency_name in (
            recommended[
                "confirmed_emergencies"
            ]
        ):

            print(
                f"  {emergency_name}"
            )

    else:

        print(
            "  None"
        )

    print()

    # ==========================================
    # GREEN TIME
    # ==========================================

    print(

        f"Recommended Green Time: "
        f"{recommended['recommended_green_time']} "
        f"seconds"

    )

    print(

        f"Reason: "
        f"{recommended['reason']}"

    )

    print()

    print(
        "Decision saved to:"
    )

    print(
        OUTPUT_FILE
    )

    print()

    return decision


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    make_signal_decision()