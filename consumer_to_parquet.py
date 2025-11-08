import json
import pandas as pd
from kafka import KafkaConsumer
from pathlib import Path
from datetime import datetime

# 1️⃣ Set up the consumer
consumer = KafkaConsumer(
    'traffic',
    bootstrap_servers='127.0.0.1:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

# 2️⃣ Prepare an output folder
output_dir = Path('data/bronze_py')
output_dir.mkdir(parents=True, exist_ok=True)

buffer = []
BATCH_SIZE = 20           # write every 20 messages
BATCH_INTERVAL = 60       # or every minute, whichever comes first

last_write = datetime.now()

for msg in consumer:
    buffer.append(msg.value)

    # Time- or count-based flush
    now = datetime.now()
    if len(buffer) >= BATCH_SIZE or (now - last_write).seconds >= BATCH_INTERVAL:
        df = pd.DataFrame(buffer)
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        file_path = output_dir / f'traffic_{timestamp}.parquet'
        df.to_parquet(file_path, index=False)
        print(f"Wrote {len(buffer)} records to {file_path}")
        buffer.clear()
        last_write = now
