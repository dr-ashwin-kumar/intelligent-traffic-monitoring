const express = require("express");
const cors = require("cors");
const multer = require("multer");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const db = require("./db");

const app = express();

const PORT = 5001;

const BASE_DIR = path.join(__dirname, "../..");

const UPLOAD_DIR = path.join(
  BASE_DIR,
  "backend",
  "uploads"
);

const OUTPUT_DIR = path.join(
  BASE_DIR,
  "backend",
  "outputs"
);

const AI_ENGINE_DIR = path.join(
  BASE_DIR,
  "ai-engine"
);

const PYTHON = path.join(
  AI_ENGINE_DIR,
  "venv",
  "bin",
  "python"
);

// ==========================================
// DIRECTORIES
// ==========================================

fs.mkdirSync(UPLOAD_DIR, { recursive: true });
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

// ==========================================
// MIDDLEWARE
// ==========================================

app.use(cors());
app.use(express.json());

// ==========================================
// MULTER
// ==========================================

const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, UPLOAD_DIR);
  },

  filename: function (req, file, cb) {
    const extension = path.extname(file.originalname);

    const name = path
      .basename(file.originalname, extension)
      .replace(/[^a-zA-Z0-9_-]/g, "_");

    const filename = `${Date.now()}_${name}${extension}`;

    cb(null, filename);
  }
});

const upload = multer({
  storage,

  limits: {
    // 2 GB per request
    fileSize: 2 * 1024 * 1024 * 1024
  },

  fileFilter: function (req, file, cb) {
    if (
      file.mimetype &&
      file.mimetype.startsWith("video/")
    ) {
      cb(null, true);
    } else {
      cb(
        new Error(
          "Only video files are allowed."
        )
      );
    }
  }
});

// ==========================================
// HEALTH CHECK
// ==========================================

app.get("/api/health", (req, res) => {
  res.json({
    status: "online",
    service: "Sentinel AI Backend",
    ai_engine: fs.existsSync(PYTHON)
      ? "available"
      : "python environment not found"
  });
});

// ==========================================
// ANALYZE VIDEOS
// ==========================================

app.post(
  "/api/analyze",
  upload.array("videos"),
  async (req, res) => {
    try {
      const files = req.files || [];

      // --------------------------------------
      // VALIDATION
      // --------------------------------------

      if (files.length === 0) {
        return res.status(400).json({
          error:
            "Please upload at least one video."
        });
      }

      console.log();

      console.log(
        "======================================"
      );

      console.log(
        "SENTINEL AI ANALYSIS REQUEST"
      );

      console.log(
        "======================================"
      );

      console.log(
        `Videos received: ${files.length}`
      );

      // --------------------------------------
      // CREATE JOB DIRECTORY
      // --------------------------------------

      const jobId = `job_${Date.now()}`;

      const jobDir = path.join(
        OUTPUT_DIR,
        jobId
      );

      fs.mkdirSync(jobDir, {
        recursive: true
      });

      // --------------------------------------
      // PREPARE ROAD INFORMATION
      // --------------------------------------

      const roads = files.map(
        (file, index) => {
          const roadName =
            `Road ${String.fromCharCode(
              65 + index
            )}`;

          const outputVideo =
            path.join(
              jobDir,
              `${roadName.replace(
                " ",
                ""
              )}_analyzed.mp4`
            );

          const outputJson =
            path.join(
              jobDir,
              `${roadName.replace(
                " ",
                ""
              )}_analysis.json`
            );

          return {
            name: roadName,
            input: file.path,
            outputVideo,
            outputJson
          };
        }
      );

      console.log();

      console.log("Roads:");

      roads.forEach((road) => {
        console.log(
          `  ${road.name}: ${path.basename(
            road.input
          )}`
        );
      });

      // --------------------------------------
      // RUN PYTHON AI ENGINE
      // --------------------------------------

      const pythonScript =
        path.join(
          AI_ENGINE_DIR,
          "api_processor.py"
        );

      const inputData =
        JSON.stringify({
          roads
        });

      const pythonProcess =
        spawn(
          PYTHON,
          [
            pythonScript,
            inputData
          ],
          {
            cwd: AI_ENGINE_DIR
          }
        );

      let stdout = "";
      let stderr = "";

      pythonProcess.stdout.on(
        "data",
        (data) => {
          const text =
            data.toString();

          stdout += text;

          console.log(
            text.trim()
          );
        }
      );

      pythonProcess.stderr.on(
        "data",
        (data) => {
          const text =
            data.toString();

          stderr += text;

          console.error(
            text.trim()
          );
        }
      );

      pythonProcess.on(
        "error",
        (error) => {
          console.error(
            "Python process error:",
            error
          );
        }
      );

      pythonProcess.on(
        "close",
        async (code) => {
          try {
            // --------------------------------
            // AI ENGINE ERROR
            // --------------------------------

            if (code !== 0) {
              console.error(
                "AI engine failed."
              );

              console.error(
                stderr
              );

              return res.status(500).json({
                error:
                  "AI engine failed.",
                details:
                  stderr || stdout
              });
            }

            // --------------------------------
            // FIND DECISION
            // --------------------------------

            const decisionFile =
              path.join(
                jobDir,
                "signal_decision.json"
              );

            if (
              !fs.existsSync(
                decisionFile
              )
            ) {
              return res.status(500).json({
                error:
                  "AI analysis completed but no signal decision was generated."
              });
            }

            const decision =
              JSON.parse(
                fs.readFileSync(
                  decisionFile,
                  "utf8"
                )
              );

            console.log();

            console.log(
              "======================================"
            );

            console.log(
              "AI ANALYSIS COMPLETED"
            );

            console.log(
              "======================================"
            );

            console.log(
              `Recommended Road: ${
                decision.recommended_road
              }`
            );

            console.log(
              `Green Time: ${
                decision.recommended_green_time
              } seconds`
            );

            console.log(
              `Reason: ${
                decision.reason
              }`
            );

            // =================================
            // SAVE RESULTS TO MYSQL
            // =================================

            let connection;

            try {
              connection =
                await db.getConnection();

              await connection.beginTransaction();

              console.log();
              console.log(
                "Saving analysis to MySQL..."
              );

              // --------------------------------
              // 1. ANALYSIS SESSION
              // --------------------------------

              const [
                sessionResult
              ] =
                await connection.execute(
                  `
                  INSERT INTO analysis_sessions
                  (
                    job_id,
                    total_videos,
                    recommended_road,
                    recommended_green_time,
                    reason
                  )
                  VALUES (?, ?, ?, ?, ?)
                  `,
                  [
                    jobId,
                    roads.length,
                    decision.recommended_road ||
                      null,
                    decision.recommended_green_time ||
                      null,
                    decision.reason ||
                      null
                  ]
                );

              const sessionId =
                sessionResult.insertId;

              console.log(
                `Analysis session saved: ${sessionId}`
              );

              // --------------------------------
              // 2. SAVE EACH ROAD
              // --------------------------------

              const allRoads =
                decision.all_roads || {};

              for (
                const [roadId, roadData]
                of Object.entries(allRoads)
              ) {
                const roadName =
                  roadData.road ||
                  roadId;

                const trafficScore =
                  Number(
                    roadData.traffic_score ||
                      0
                  );

                const trafficLevel =
                  roadData.traffic_level ||
                  "UNKNOWN";

                const maximumVehicleCount =
                  Number(
                    roadData.maximum_vehicle_count ||
                      roadData.max_vehicle_count ||
                      roadData.maximum_vehicles ||
                      0
                  );

                const priorityScore =
                  Number(
                    roadData.priority_score ||
                      0
                  );

                const greenTime =
                  Number(
                    roadData.recommended_green_time ||
                      0
                  );

                // Find matching uploaded road
                const matchingRoad =
                  roads.find(
                    (road) =>
                      road.name ===
                      roadName
                  );

                const videoFilename =
                  matchingRoad
                    ? path.basename(
                        matchingRoad.input
                      )
                    : null;

                const [
                  roadResult
                ] =
                  await connection.execute(
                    `
                    INSERT INTO road_analysis
                    (
                      session_id,
                      road_name,
                      video_filename,
                      traffic_score,
                      traffic_level,
                      maximum_vehicle_count,
                      priority_score,
                      recommended_green_time
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    `,
                    [
                      sessionId,
                      roadName,
                      videoFilename,
                      trafficScore,
                      trafficLevel,
                      maximumVehicleCount,
                      priorityScore,
                      greenTime
                    ]
                  );

                const roadAnalysisId =
                  roadResult.insertId;

                // --------------------------------
                // 3. EMERGENCY DETECTIONS
                // --------------------------------

                const emergencyVehicles =
                  roadData.emergency_vehicles ||
                  {};

                const confirmedEmergencies =
                  roadData.confirmed_emergencies ||
                  [];

                const policeCount =
                  Number(
                    emergencyVehicles.Police ||
                      emergencyVehicles.police ||
                      0
                  );

                const ambulanceCount =
                  Number(
                    emergencyVehicles.ambulance ||
                      0
                  );

                const firetruckCount =
                  Number(
                    emergencyVehicles.firetruck ||
                      0
                  );

                const confirmedEmergency =
                  confirmedEmergencies.length > 0
                    ? confirmedEmergencies.join(
                        ", "
                      )
                    : null;

                await connection.execute(
                  `
                  INSERT INTO emergency_detections
                  (
                    road_analysis_id,
                    police_count,
                    ambulance_count,
                    firetruck_count,
                    confirmed_emergency
                  )
                  VALUES (?, ?, ?, ?, ?)
                  `,
                  [
                    roadAnalysisId,
                    policeCount,
                    ambulanceCount,
                    firetruckCount,
                    confirmedEmergency
                  ]
                );

                console.log(
                  `Saved ${roadName}`
                );
              }

              // --------------------------------
              // 4. SIGNAL DECISION
              // --------------------------------

              await connection.execute(
                `
                INSERT INTO signal_decisions
                (
                  session_id,
                  recommended_road,
                  priority_score,
                  green_time,
                  reason
                )
                VALUES (?, ?, ?, ?, ?)
                `,
                [
                  sessionId,
                  decision.recommended_road ||
                    "Unknown",
                  Number(
                    decision.priority_score ||
                      0
                  ),
                  Number(
                    decision.recommended_green_time ||
                      0
                  ),
                  decision.reason ||
                    null
                ]
              );

              // --------------------------------
              // COMMIT
              // --------------------------------

              await connection.commit();

              console.log();
              console.log(
                "MySQL database updated successfully."
              );

              console.log(
                `Session ID: ${sessionId}`
              );

            } catch (dbError) {

              if (connection) {
                try {
                  await connection.rollback();
                } catch (rollbackError) {
                  console.error(
                    "Rollback failed:",
                    rollbackError.message
                  );
                }
              }

              console.error();
              console.error(
                "MySQL save failed:"
              );

              console.error(
                dbError
              );

              return res.status(500).json({
                error:
                  "AI analysis completed but database save failed.",
                details:
                  dbError.message
              });

            } finally {

              if (connection) {
                connection.release();
              }
            }

            // =================================
            // RETURN RESULT TO FRONTEND
            // =================================

            return res.json({
              success: true,

              job_id: jobId,

              videos: roads.map(
                (road) => ({
                  road: road.name,

                  video:
                    `/api/videos/${jobId}/${path.basename(
                      road.outputVideo
                    )}`
                })
              ),

              ...decision
            });

          } catch (error) {

            console.error(
              "Error after AI processing:",
              error
            );

            return res.status(500).json({
              error:
                error.message
            });
          }
        }
      );

    } catch (error) {

      console.error(
        error
      );

      return res.status(500).json({
        error:
          error.message
      });
    }
  }
);

// ==========================================
// SERVE ANALYZED VIDEOS
// ==========================================

app.get(
  "/api/videos/:jobId/:filename",
  (req, res) => {

    const filePath =
      path.join(
        OUTPUT_DIR,
        req.params.jobId,
        req.params.filename
      );

    if (
      !fs.existsSync(filePath)
    ) {
      return res.status(404).json({
        error:
          "Video not found."
      });
    }

    res.sendFile(
      filePath
    );
  }
);

// ==========================================
// ERROR HANDLER
// ==========================================

app.use(
  (error, req, res, next) => {

    console.error(
      error
    );

    res.status(400).json({
      error:
        error.message
    });
  }
);

// ==========================================
// MYSQL CONNECTION TEST
// ==========================================

db.getConnection()
  .then((connection) => {

    console.log(
      "MySQL connected successfully"
    );

    connection.release();

  })
  .catch((error) => {

    console.error(
      "MySQL connection failed:",
      error.message
    );
  });

// ==========================================
// START SERVER
// ==========================================

app.listen(
  PORT,
  () => {

    console.log();

    console.log(
      "======================================"
    );

    console.log(
      "       SENTINEL AI BACKEND"
    );

    console.log(
      "======================================"
    );

    console.log(
      `Server running on port ${PORT}`
    );

    console.log(
      `AI Engine: ${AI_ENGINE_DIR}`
    );

    console.log(
      `Python: ${PYTHON}`
    );

    console.log();
  }
);