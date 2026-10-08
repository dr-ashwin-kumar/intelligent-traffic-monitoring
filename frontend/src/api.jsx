const API_URL = "http://localhost:5001";

export const uploadVideos = async (formData) => {
    const response = await fetch(
        `${API_URL}/api/videos/upload`,
        {
            method: "POST",
            body: formData
        }
    );

    if (!response.ok) {
        throw new Error("Video upload failed");
    }

    return response.json();
};