import json
import os

from video_processor import analyze_video
from decision_engine import make_signal_decision


# ==========================================
# BASE DIRECTORY
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ==========================================
# DIRECTORIES
# ==========================================

VIDEOS_DIR = os.path.join(
    BASE_DIR,
    "videos"
)

OUTPUTS_DIR = os.path.join(
    BASE_DIR,
    "outputs"
)

os.makedirs(
    OUTPUTS_DIR,
    exist_ok=True
)


# ==========================================
# ROADS
# ==========================================

ROADS = {

    "roadA": {
        "name": "Road A",
        "input": os.path.join(
            VIDEOS_DIR,
            "roadA.mp4"
        ),
        "output": os.path.join(
            OUTPUTS_DIR,
            "roadA_analyzed.mp4"
        ),
        "json": os.path.join(
            OUTPUTS_DIR,
            "roadA_analysis.json"
        )
    },

    "roadB": {
        "name": "Road B",
        "input": os.path.join(
            VIDEOS_DIR,
            "roadB.mp4"
        ),
        "output": os.path.join(
            OUTPUTS_DIR,
            "roadB_analyzed.mp4"
        ),
        "json": os.path.join(
            OUTPUTS_DIR,
            "roadB_analysis.json"
        )
    },

    "roadC": {
        "name": "Road C",
        "input": os.path.join(
            VIDEOS_DIR,
            "roadC.mp4"
        ),
        "output": os.path.join(
            OUTPUTS_DIR,
            "roadC_analyzed.mp4"
        ),
        "json": os.path.join(
            OUTPUTS_DIR,
            "roadC_analysis.json"
        )
    },

    "roadD": {
        "name": "Road D",
        "input": os.path.join(
            VIDEOS_DIR,
            "roadD.mp4"
        ),
        "output": os.path.join(
            OUTPUTS_DIR,
            "roadD_analyzed.mp4"
        ),
        "json": os.path.join(
            OUTPUTS_DIR,
            "roadD_analysis.json"
        )
    }
}


# ==========================================
# MAIN ANALYSIS
# ==========================================

def main():

    print()
    print("======================================")
    print("      SENTINEL AI")
    print("   MULTI-ROAD ANALYSIS")
    print("======================================")


    all_results = {}


    # ======================================
    # ANALYZE EACH ROAD
    # ======================================

    for road_id, road in ROADS.items():

        print()
        print("--------------------------------------")
        print(
            f"Starting analysis: "
            f"{road['name']}"
        )
        print("--------------------------------------")


        # Check video exists

        if not os.path.exists(
            road["input"]
        ):

            print(
                f"WARNING: Video not found:"
            )

            print(
                road["input"]
            )

            continue


        # Analyze video

        result = analyze_video(

            road["name"],

            road["input"],

            road["output"],

            road["json"]
        )


        all_results[
            road_id
        ] = result


    # ======================================
    # CHECK RESULTS
    # ======================================

    if not all_results:

        raise Exception(
            "No road videos were successfully analyzed."
        )


    # ======================================
    # SAVE ALL ROAD ANALYSIS
    # ======================================

    all_roads_file = os.path.join(
        BASE_DIR,
        "all_roads_analysis.json"
    )


    with open(
        all_roads_file,
        "w"
    ) as json_file:

        json.dump(
            {
                "roads": all_results
            },
            json_file,
            indent=4
        )


    print()
    print("======================================")
    print("ALL ROAD ANALYSIS COMPLETED")
    print("======================================")

    print(
        f"Saved to: {all_roads_file}"
    )


    # ======================================
    # SIGNAL DECISION
    # ======================================

    print()
    print("--------------------------------------")
    print("Generating traffic signal decision...")
    print("--------------------------------------")


    make_signal_decision()


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":

    main()