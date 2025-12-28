# Real-Time-Traffic-Congestion-Analytics-Pipeline
A real-time data pipeline for collecting, processing, and analyzing live traffic data to detect congestion and visualize road conditions. The system ingests data streams from simulated or open APIs, processes them using Apache Kafka and Spark Streaming, and stores results in a data lake for visualization dashboards.

## How It Works

### Architecture Overview
The system follows a multi-stage pipeline with distinct layers for data collection, processing, and serving:

```
Producer → Kafka → Bronze Layer → Model Training
                ↓
         Silver Layer ← Prediction API ← Trained Model
                ↓
           Dashboard
```

### Component Details

#### 1. Data Generation (producer.py)
- Simulates traffic sensors at three locations: roadA, roadB, roadC
- Generates random speed readings between 10-60 km/h every 2 seconds
- Creates JSON messages with structure: `{sensor, speed, timestamp}`
- Sends messages to Kafka topic `traffic` using KafkaProducer
- Runs continuously to simulate real-time traffic monitoring

#### 2. Message Streaming (Kafka)
- Apache Kafka acts as the message broker between data producers and consumers
- Topic `traffic` receives all traffic sensor data
- Zookeeper manages Kafka cluster coordination
- Runs in Docker containers (ports: Kafka 9092, Zookeeper 2181)
- Decouples data generation from processing for scalability

#### 3. Bronze Layer - Raw Data Storage (consumer_to_parquet.py)
- Consumes messages from Kafka `traffic` topic in real-time
- Buffers incoming messages (batch size: 20 messages or 60 seconds)
- Writes batches to Parquet files in `data/bronze_py/` directory
- File naming: `traffic_YYYYMMDD_HHMMSS.parquet`
- Parquet format enables efficient columnar storage and fast analytics
- This layer preserves raw data for model training and reprocessing

#### 4. Model Training (train_model.py)
- Loads all Parquet files from `data/bronze_py/`
- Feature engineering:
  - `speed_mean_3`: Rolling average of last 3 speed readings per sensor
  - `speed_lag1`: Previous speed reading (lag-1 feature)
  - One-hot encoding of sensor IDs (roadA, roadB, roadC)
- Target variable: `speed_next` (next reading's speed)
- Algorithm: Random Forest Regressor with 100 estimators
- Splits data 80/20 for training/testing
- Evaluates using Mean Absolute Error (MAE)
- Saves trained model to `model.joblib` using joblib serialization

#### 5. Prediction API (app.py)
- FastAPI web service exposing REST endpoints
- Loads pre-trained model from `model.joblib` on startup
- Endpoint `/predict` accepts POST requests with traffic data
- Input validation using Pydantic models
- Feature reconstruction:
  - Creates same features used during training (speed_mean_3, speed_lag1, sensor one-hot)
  - Ensures feature order matches model expectations
- Prediction logic:
  - Predicts next speed using the model
  - Caps prediction at 1.5x current speed for reasonableness
  - Calculates congestion level: HIGH (≥2), MEDIUM (1), LOW (<1)
- Returns JSON: `{sensor, current_speed, predicted_speed_next, congestion, timestamp}`

#### 6. Silver Layer - Enriched Data (consumer_to_silver.py)
- Consumes from Kafka `traffic` topic in parallel with bronze layer
- For each message:
  - Calls prediction API (`POST http://127.0.0.1:8000/predict`)
  - Receives predicted speed and congestion level
  - Combines raw data with predictions
- Buffers 50 enriched records before writing
- Saves to `data/silver/silver_{timestamp}.parquet`
- Silver layer contains actionable intelligence (raw + predictions + congestion)
- Ready for analytics and visualization without further processing

#### 7. Dashboard (dashboard.py)
- Streamlit web application for real-time monitoring
- Interface components:
  - Sensor selector dropdown (roadA/B/C)
  - Speed input slider (0-100 km/h)
  - Predict button to trigger API call
- Displays prediction results:
  - Predicted next speed
  - Congestion level (HIGH/MEDIUM/LOW)
- Maintains session history of all predictions
- Data table showing timestamp, sensor, speeds, and congestion
- Interactive map visualization:
  - Uses PyDeck for 3D map rendering
  - Each sensor mapped to real Hanoi coordinates
  - Color coding: Red (HIGH), Orange (MEDIUM), Green (LOW)
  - Tooltip shows sensor details on hover
- Auto-refreshes with new predictions

## Setup and Run

### Prerequisites
- Docker and Docker Compose
- Python 3.9+

### Step 1: Start Kafka Infrastructure
```bash
docker-compose up -d
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run Producer (Terminal 1)
```bash
python producer.py
```
This generates simulated traffic data every 2 seconds.

### Step 4: Collect Bronze Data (Terminal 2)
```bash
python stream_to_parquet.py
```
Let this run for a few minutes to collect training data. Stop with `Ctrl+C` when you have enough data.

### Step 5: Train Model
```bash
python train_model.py
```
This creates `model.joblib` from bronze layer data.

### Step 6: Start Prediction API (Terminal 3)
```bash
uvicorn app:app --reload
```
API runs at `http://127.0.0.1:8000`

### Step 7: Process Silver Layer (Terminal 4)
```bash
python consumer_to_silver.py
```
This enriches streaming data with predictions and congestion levels.

### Step 8: Launch Dashboard (Terminal 5)
```bash
streamlit run dashboard.py
```
Dashboard opens at `http://localhost:8501`

The dashboard allows you to:
- Select sensor and input current speed
- Get predicted next speed and congestion level
- View prediction history table
- See congestion map with color-coded markers (red=high, orange=medium, green=low)
