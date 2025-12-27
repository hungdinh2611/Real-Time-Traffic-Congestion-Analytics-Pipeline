import json, time, requests
import pandas as pd
from kafka import KafkaConsumer
from pathlib import Path

def congestion_level(speed_now, speed_pred):

    if speed_now <= 5:
        return "HIGH"

    if speed_pred <= 15:
        return "HIGH"

    if speed_pred < speed_now * 0.6:
        return "MEDIUM"

    if speed_pred < 40:
        return "MEDIUM"

    return "LOW"

consumer = KafkaConsumer(
    "traffic",
    bootstrap_servers="127.0.0.1:9092",
    value_deserializer=lambda m: json.loads(m.decode())
)

Path("data/silver").mkdir(parents=True, exist_ok=True)
buffer = []

for msg in consumer:
    d = msg.value

    r = requests.post("http://127.0.0.1:8000/predict", json=d)
    result = r.json()

    buffer.append({
        "sensor": d["sensor"],
        "timestamp": d["timestamp"],
        "speed": d["speed"],
        "predicted_speed": result["predicted_speed_next"],
        "congestion": result["congestion"]
    })

    if len(buffer) >= 50:
        df = pd.DataFrame(buffer)
        df.to_parquet(f"data/silver/silver_{int(time.time())}.parquet")
        buffer.clear()
