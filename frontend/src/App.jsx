import { useEffect, useState } from "react";
import "./App.css";

const API = "http://localhost:5001";

function App() {
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedVideo, setExpandedVideo] = useState(null);

  useEffect(() => {
    const urls = files.map((file) => URL.createObjectURL(file));
    setPreviews(urls);
    return () => urls.forEach((url) => URL.revokeObjectURL(url));
  }, [files]);

  function handleFiles(event) {
    const selected = Array.from(event.target.files || []);
    setFiles((current) => [...current, ...selected]);
    setResult(null);
    event.target.value = "";
  }

  function removeFile(index) {
    setFiles((current) => current.filter((_, i) => i !== index));
    setResult(null);
  }

  async function startAnalysis() {
    if (!files.length || loading) return;
    setLoading(true);
    setResult(null);

    const formData = new FormData();
    files.forEach((file) => formData.append("videos", file));

    try {
      const response = await fetch(`${API}/api/analyze`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Analysis failed");
      }

      setResult(data);
    } catch (error) {
      alert(error.message);
    } finally {
      setLoading(false);
    }
  }

  const getRoadResult = (index) => {
    if (!result?.all_roads) return null;
    const roads = Object.values(result.all_roads);
    return roads[index] || null;
  };

  const navigateTo = (id) => {
    const target = document.getElementById(id);
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  };

  const totalVehicles = result?.all_roads
    ? Object.values(result.all_roads).reduce(
        (sum, road) => sum + (Number(road.total_vehicles) || 0),
        0
      )
    : "--";

  const trafficLevels = result?.all_roads
    ? Object.values(result.all_roads).map((road) => road.traffic_level)
    : [];

  const highestTraffic =
    trafficLevels.includes("HIGH")
      ? "HIGH"
      : trafficLevels.includes("MEDIUM")
        ? "MEDIUM"
        : trafficLevels.includes("LOW")
          ? "LOW"
          : "--";

  return (
    <div className="app">

      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <span className="signal-mini red"></span>
            <span className="signal-mini yellow"></span>
            <span className="signal-mini green"></span>
          </div>
          <div>
            <h1>Sentinel <span>AI</span></h1>
            <p>Intelligent Traffic Monitoring System</p>
          </div>
        </div>

        <nav className="main-nav">
          <button className="active" onClick={() => navigateTo("dashboard")}>
            Dashboard
          </button>
          <button onClick={() => navigateTo("analysis")}>
            Analysis
          </button>
          <button onClick={() => navigateTo("history")}>
            History
          </button>
        </nav>

        <div className="topbar-right">
          <div className="session-chip">
            <span className="session-dot"></span>
            System Online
          </div>
          <div className="system-clock">CONTROL CENTER</div>
        </div>
      </header>

      <main id="dashboard">

        <section className="hero">
          <div>
            <span className="eyebrow">TRAFFIC OPERATIONS CENTER</span>
            <h2>Intelligent Road Monitoring</h2>
            <p>
              Analyze multiple road camera feeds and generate an AI-assisted
              traffic signal priority decision.
            </p>
          </div>

          <div className="hero-state">
            <span className="hero-state-label">SYSTEM STATE</span>
            <strong>{loading ? "ANALYZING" : result ? "DECISION READY" : "STANDBY"}</strong>
          </div>
        </section>

        <section className="metrics-strip">
          <div className="metric-card">
            <span>ROAD FEEDS</span>
            <strong>{files.length}</strong>
            <small>ACTIVE INPUTS</small>
          </div>

          <div className="metric-card">
            <span>TOTAL VEHICLES DETECTED</span>
            <strong>{totalVehicles}</strong>
            <small>{result ? "AI DETECTED" : "AWAITING ANALYSIS"}</small>
          </div>

          <div className="metric-card">
            <span>TRAFFIC LEVEL</span>
            <strong className={highestTraffic === "HIGH" ? "danger-number" : ""}>
              {highestTraffic}
            </strong>
            <small>ACROSS MONITORED ROADS</small>
          </div>

          <div className="metric-card accent">
            <span>RECOMMENDED ROAD</span>
            <strong>{result?.recommended_road || "--"}</strong>
            <small>{result ? "AI PRIORITY" : "NO DECISION YET"}</small>
          </div>
        </section>

        <section className="workspace setup-section">

          <div className="workspace-heading">
            <div>
              <span className="eyebrow">01 / INPUT</span>
              <h3>Camera Feed Setup</h3>
            </div>
            <span className="step-status">READY</span>
          </div>

          <div className="upload-layout">

            <label className="upload-zone">
              <input
                type="file"
                accept="video/*"
                multiple
                onChange={handleFiles}
              />

              <div className="upload-symbol">
                <span>+</span>
              </div>

              <strong>Add road camera feeds</strong>
              <span>Drop video files here or browse from your computer</span>
              <small>Multiple CCTV feeds supported</small>
            </label>

            <div className="feed-panel">
              <div className="feed-panel-header">
                <div>
                  <span>INPUT QUEUE</span>
                  <strong>{files.length} feeds selected</strong>
                </div>

                {files.length > 0 && (
                  <label className="mini-add">
                    + Add
                    <input
                      type="file"
                      accept="video/*"
                      multiple
                      onChange={handleFiles}
                    />
                  </label>
                )}
              </div>

              {files.length === 0 ? (
                <div className="empty-queue">
                  <span>—</span>
                  <p>No road feeds selected</p>
                  <small>Add videos to begin monitoring.</small>
                </div>
              ) : (
                <div className="queue-list">
                  {files.map((file, index) => (
                    <div className="queue-item" key={`${file.name}-${index}`}>
                      <div className="queue-index">
                        {String(index + 1).padStart(2, "0")}
                      </div>

                      <div className="queue-info">
                        <strong>ROAD {String.fromCharCode(65 + index)}</strong>
                        <span>{file.name}</span>
                      </div>

                      <button
                        className="queue-remove"
                        onClick={() => removeFile(index)}
                        disabled={loading}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <button
                className="primary-action"
                onClick={startAnalysis}
                disabled={!files.length || loading}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    PROCESSING ROAD FEEDS
                  </>
                ) : (
                  <>
                    START AI ANALYSIS <span>→</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </section>

        <section id="history" className="workspace monitoring-section">

            <div className="workspace-heading">
              <div>
                <span className="eyebrow">02 / MONITOR</span>
                <h3>Live Road Feeds</h3>
              </div>

              <div className="live-badge">
                <span></span> LIVE MONITORING
              </div>
            </div>

            {previews.length > 0 ? (
              <div className="camera-grid">
                {previews.map((url, index) => {
                const road = getRoadResult(index);
                const isRecommended =
                  result?.recommended_road === road?.road;

                return (
                  <article
                    className={`camera-card ${
                      isRecommended ? "recommended-camera" : ""
                    }`}
                    key={url}
                  >
                    <div className="camera-top">
                      <div className="camera-road">
                        <span className="camera-number">
                          {String(index + 1).padStart(2, "0")}
                        </span>
                        <div>
                          <strong>ROAD {String.fromCharCode(65 + index)}</strong>
                          <small>{files[index]?.name}</small>
                        </div>
                      </div>

                      <div className="camera-state">
                        <span></span> LIVE
                      </div>
                    </div>

                    <div
                      className="camera-video"
                      onClick={() =>
                        setExpandedVideo({
                          url: result?.videos?.[index]?.video
                            ? `${API}${result.videos[index].video}`
                            : url,
                          road: `ROAD ${String.fromCharCode(65 + index)}`,
                        })
                      }
                      title="Click to enlarge video"
                    >
                      <video
                        src={
                          result?.videos?.[index]?.video
                            ? `${API}${result.videos[index].video}`
                            : url
                        }
                        autoPlay
                        muted
                        loop
                        playsInline
                      />

                      <div className="video-labels">
                        <span>REC</span>
                        <span>{road?.traffic_level || "MONITORING"}</span>
                      </div>
                      <span className="video-expand-hint">CLICK TO EXPAND</span>
                    </div>

                    <div className="camera-data">
                      <div>
                        <span>TRAFFIC</span>
                        <strong>{road?.traffic_level || "--"}</strong>
                      </div>
                      <div>
                        <span>VEHICLES</span>
                        <strong>{road?.total_vehicles ?? "--"}</strong>
                      </div>
                      <div>
                        <span>PRIORITY</span>
                        <strong>{road?.priority_score ?? "--"}</strong>
                      </div>
                    </div>

                    {road && (
                      <div className="vehicle-row">
                        <span>Cars <b>{road.cars ?? 0}</b></span>
                        <span>Motorcycles <b>{road.motorcycles ?? 0}</b></span>
                        <span>Buses <b>{road.buses ?? 0}</b></span>
                        <span>Trucks <b>{road.trucks ?? 0}</b></span>
                      </div>
                    )}

                    {road?.confirmed_emergencies?.length > 0 && (
                      <div className="emergency-alert">
                        <span className="alert-icon">!</span>
                        <div>
                          <strong>EMERGENCY DETECTED</strong>
                          <small>{road.confirmed_emergencies.join(", ")}</small>
                        </div>
                      </div>
                    )}

                    {isRecommended && (
                      <div className="recommended-bar">
                        <span>●</span> GREEN SIGNAL PRIORITY
                      </div>
                    )}
                  </article>
                );
                })}
              </div>
            ) : (
              <div className="empty-monitoring">
              <div className="empty-monitoring-icon">▣</div>
              <strong>No road feeds selected</strong>
              <span>Add video feeds in Camera Feed Setup to display live road monitoring.</span>
            </div>
          )}
          </section>

        {loading && (
          <section className="analysis-banner">
            <div className="analysis-loader"></div>
            <div>
              <strong>AI ANALYSIS IN PROGRESS</strong>
              <span>Processing all road feeds simultaneously.</span>
            </div>
          </section>
        )}

        <section id="analysis" className="workspace decision-workspace">
          {result && !loading ? (
            <>
            <div className="workspace-heading">
              <div>
                <span className="eyebrow">03 / DECISION</span>
                <h3>AI Signal Recommendation</h3>
              </div>

              <span className="decision-ready">DECISION READY</span>
            </div>

            <div className="decision-grid">

              <div className="decision-main">
                <div className="traffic-signal">
                  <span className="signal-red"></span>
                  <span className="signal-yellow"></span>
                  <span className="signal-green active"></span>
                </div>

                <div className="decision-copy">
                  <span>GREEN SIGNAL PRIORITY</span>
                  <h4>{result.recommended_road}</h4>

                  <div className="green-duration">
                    <strong>{result.recommended_green_time}</strong>
                    <span>SECONDS<br />GREEN</span>
                  </div>

                  <p>{result.reason}</p>
                </div>
              </div>

              <div className="decision-stats">
                <div>
                  <span>TRAFFIC SCORE</span>
                  <strong>{result.traffic_score}</strong>
                </div>
                <div>
                  <span>EMERGENCY SCORE</span>
                  <strong>{result.emergency_score}</strong>
                </div>
                <div>
                  <span>PRIORITY SCORE</span>
                  <strong>{result.priority_score}</strong>
                </div>
              </div>
            </div>

            <div className="road-analysis">
              <div className="subheading">
                <span className="eyebrow">ROAD COMPARISON</span>
                <h4>Priority Analysis</h4>
              </div>

              <div className="road-table">
                <div className="road-table-head">
                  <span>ROAD</span>
                  <span>PRIORITY</span>
                  <span>TRAFFIC</span>
                  <span>EMERGENCY</span>
                  <span>SIGNAL</span>
                </div>

                {Object.entries(result.all_roads || {}).map(([id, road]) => {
                  const recommended =
                    road.road === result.recommended_road;

                  return (
                    <div
                      className={`road-table-row ${
                        recommended ? "selected-road" : ""
                      }`}
                      key={id}
                    >
                      <div className="table-road">
                        <span>{road.road.replace("Road ", "")}</span>
                        <strong>{road.road}</strong>
                        {recommended && <small>RECOMMENDED</small>}
                      </div>

                      <strong>{road.priority_score}</strong>
                      <strong>{road.traffic_level}</strong>

                      <strong
                        className={
                          road.confirmed_emergencies?.length
                            ? "danger-text"
                            : ""
                        }
                      >
                        {road.confirmed_emergencies?.length
                          ? road.confirmed_emergencies.join(", ")
                          : "NONE"}
                      </strong>

                      <span className="signal-result">
                        {recommended ? "● GREEN" : "WAIT"}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
            </>
          ) : (
            <div className="analysis-empty">
              <div className="analysis-empty-mark">AI</div>
              <div>
                <strong>{loading ? "AI analysis in progress" : "Analysis not available yet"}</strong>
                <span>
                  {loading
                    ? "Processing all road feeds simultaneously."
                    : "Run AI analysis after selecting road camera feeds to view the signal recommendation and priority analysis."}
                </span>
              </div>
            </div>
          )}
        </section>
      </main>

      {expandedVideo && (
        <div
          className="video-modal"
          onClick={() => setExpandedVideo(null)}
          role="dialog"
          aria-modal="true"
          aria-label={`${expandedVideo.road} enlarged video`}
        >
          <div className="video-modal-panel" onClick={(e) => e.stopPropagation()}>
            <div className="video-modal-header">
              <div>
                <span>LIVE ROAD FEED</span>
                <strong>{expandedVideo.road}</strong>
              </div>
              <button
                className="video-modal-close"
                onClick={() => setExpandedVideo(null)}
                aria-label="Close enlarged video"
              >
                ×
              </button>
            </div>
            <video
              src={expandedVideo.url}
              autoPlay
              muted
              loop
              playsInline
              controls
            />
          </div>
        </div>
      )}

      <footer>
        <span>SENTINEL AI</span>
        <span>INTELLIGENT TRAFFIC MANAGEMENT SYSTEM</span>
        <span>AI ENGINE • ONLINE</span>
      </footer>
    </div>
  );
}

export default App;