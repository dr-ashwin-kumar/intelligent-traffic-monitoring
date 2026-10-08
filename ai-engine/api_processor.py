import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from video_processor import analyze_video


# ==========================================
# BASE DIRECTORY
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ==========================================
# PROCESS ONE ROAD
# ==========================================

def process_road(road):

    print()
    print("--------------------------------------")
    print(f"Processing: {road['name']}")
    print("--------------------------------------")

    return analyze_video(
        road_name=road["name"],
        video_path=road["input"],
        output_video_path=road["outputVideo"],
        output_json_path=road["outputJson"]
    )


# ==========================================
# MAIN PROCESSOR
# ==========================================

def main():

    if len(sys.argv) < 2:

        raise ValueError(
            "No road data received."
        )


    # ======================================
    # READ REQUEST
    # ======================================

    request_data = json.loads(
        sys.argv[1]
    )

    roads = request_data.get(
        "roads",
        []
    )


    if not roads:

        raise ValueError(
            "No videos received."
        )


    print()
    print("======================================")
    print("       SENTINEL AI AI ENGINE")
    print("======================================")

    print(
        f"Total roads: {len(roads)}"
    )

    print(
        "Starting parallel video analysis..."
    )


    # ======================================
    # PROCESS VIDEOS IN PARALLEL
    # ======================================

    all_results = {}


    max_workers = min(
        len(roads),
        os.cpu_count() or 1
    )


    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        futures = {

            executor.submit(
                process_road,
                road
            ): road

            for road in roads
        }


        for future in as_completed(
            futures
        ):

            road = futures[future]

            try:

                result = future.result()

                road_id = (
                    os.path.splitext(
                        os.path.basename(
                            road["input"]
                        )
                    )[0]
                )

                all_results[road_id] = result


            except Exception as error:

                print(
                    f"ERROR processing "
                    f"{road['name']}: {error}"
                )

                raise


    # ======================================
    # SORT RESULTS
    # ======================================

    ordered_results = {}

    for road in roads:

        road_id = (
            os.path.splitext(
                os.path.basename(
                    road["input"]
                )
            )[0]
        )

        if road_id in all_results:

            ordered_results[
                road_id
            ] = all_results[
                road_id
            ]


    # ======================================
    # SAVE ALL ROAD ANALYSIS
    # ======================================

    analysis_file = os.path.join(
        BASE_DIR,
        "all_roads_analysis.json"
    )


    with open(
        analysis_file,
        "w"
    ) as json_file:

        json.dump(
            {
                "roads":
                    ordered_results
            },
            json_file,
            indent=4
        )


    print()
    print("======================================")
    print("ALL ROAD ANALYSIS COMPLETED")
    print("======================================")

    print(
        f"Saved to: {analysis_file}"
    )


    # ======================================
    # RUN DECISION ENGINE
    # ======================================

    print()
    print("--------------------------------------")
    print("Generating traffic signal decision...")
    print("--------------------------------------")


    from decision_engine import (
        make_signal_decision
    )


    decision = make_signal_decision()


    # ======================================
    # MOVE DECISION INTO JOB DIRECTORY
    # ======================================

    job_output_dir = os.path.dirname(
        roads[0]["outputJson"]
    )


    decision_source = os.path.join(
        BASE_DIR,
        "signal_decision.json"
    )


    decision_destination = os.path.join(
        job_output_dir,
        "signal_decision.json"
    )


    if os.path.exists(
        decision_source
    ):

        with open(
            decision_source,
            "r"
        ) as source:

            decision_data = json.load(
                source
            )


        with open(
            decision_destination,
            "w"
        ) as destination:

            json.dump(
                decision_data,
                destination,
                indent=4
            )


    # ======================================
    # FINAL OUTPUT
    # ======================================

    print()
    print("======================================")
    print("       SENTINEL AI COMPLETE")
    print("======================================")

    print(
        f"Recommended Road: "
        f"{decision['recommended_road']}"
    )

    print(
        f"Green Time: "
        f"{decision['recommended_green_time']} seconds"
    )

    print(
        f"Reason: "
        f"{decision['reason']}"
    )


if __name__ == "__main__":

    main()