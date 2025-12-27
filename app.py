from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd

# ─── 1) Define the input schema ─────────────────────────────────
class TrafficRecord(BaseModel):
    sensor: str             # e.g., "roadA"
    speed: float            # the current speed reading
    timestamp: int          # UNIX seconds

# ─── 2) Load the trained model ───────────────────────────────────
model = joblib.load("model.joblib")
def congestion_level(speed_now, speed_pred):
    if speed_now <= 5:
        return "HIGH"

    if speed_now <= 15:
        return "HIGH"

    if speed_now <= 30:
        if speed_pred < speed_now * 0.8:
            return "HIGH"
        else:
            return "MEDIUM"

    if speed_pred < speed_now * 0.7:
        return "MEDIUM"

    return "LOW"


# We need to recreate the same features you trained on
SENSOR_COLUMNS = [col for col in model.feature_names_in_ if col.startswith("sensor_")]

app = FastAPI(title="Congestion Predictor")

# ─── 3) Health check endpoint ───────────────────────────────────
@app.get("/ping")
def ping():
    return {"ping": "pong"}

# ─── 4) Prediction endpoint ─────────────────────────────────────
@app.post("/predict")
def predict(record: TrafficRecord):
    try:
        df = pd.DataFrame([record.dict()])
        df["speed_mean_3"] = df["speed"]
        df["speed_lag1"]   = df["speed"]

        # one-hot encode each sensor
        df["sensor_roadA"] = 1 if record.sensor == "roadA" else 0
        df["sensor_roadB"] = 1 if record.sensor == "roadB" else 0
        df["sensor_roadC"] = 1 if record.sensor == "roadC" else 0

        FEATURE_NAMES = [
            "speed_mean_3",
            "speed_lag1",
            "sensor_roadA",
            "sensor_roadB",
            "sensor_roadC",
        ]
        X = df[FEATURE_NAMES]

        pred = model.predict(X)[0]
        pred = min(pred, record.speed * 1.5)
        congestion = congestion_level(record.speed, pred)
        return {
            "sensor": record.sensor,
            "current_speed": record.speed,
            "predicted_speed_next": pred,
            "congestion": congestion,
            "timestamp": record.timestamp,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# ─── 5) Run with: uvicorn app:app --reload ───────────────────────
