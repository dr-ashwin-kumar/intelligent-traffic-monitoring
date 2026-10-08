import { useState } from "react";
import { uploadVideos } from "../api";

function VideoUpload() {

    const [videos, setVideos] = useState({
        roadA: null,
        roadB: null,
        roadC: null,
        roadD: null
    });

    const [message, setMessage] = useState("");

    const handleFileChange = (road, file) => {

        setVideos({
            ...videos,
            [road]: file
        });

    };

    const handleUpload = async () => {

        if (
            !videos.roadA ||
            !videos.roadB ||
            !videos.roadC ||
            !videos.roadD
        ) {
            setMessage("Please select all four road videos.");
            return;
        }

        const formData = new FormData();

        formData.append("roadA", videos.roadA);
        formData.append("roadB", videos.roadB);
        formData.append("roadC", videos.roadC);
        formData.append("roadD", videos.roadD);

        try {

            setMessage("Uploading videos...");

            const result = await uploadVideos(formData);

            console.log(result);

            setMessage("All four videos uploaded successfully.");

        } catch (error) {

            console.error(error);

            setMessage("Video upload failed.");

        }
    };

    return (
        <div>

            <h2>Upload Traffic Videos</h2>

            <div>
                <label>Road A</label>

                <input
                    type="file"
                    accept="video/*"
                    onChange={(e) =>
                        handleFileChange("roadA", e.target.files[0])
                    }
                />
            </div>

            <div>
                <label>Road B</label>

                <input
                    type="file"
                    accept="video/*"
                    onChange={(e) =>
                        handleFileChange("roadB", e.target.files[0])
                    }
                />
            </div>

            <div>
                <label>Road C</label>

                <input
                    type="file"
                    accept="video/*"
                    onChange={(e) =>
                        handleFileChange("roadC", e.target.files[0])
                    }
                />
            </div>

            <div>
                <label>Road D</label>

                <input
                    type="file"
                    accept="video/*"
                    onChange={(e) =>
                        handleFileChange("roadD", e.target.files[0])
                    }
                />
            </div>

            <button onClick={handleUpload}>
                Upload Videos
            </button>

            <p>{message}</p>

        </div>
    );
}

export default VideoUpload;