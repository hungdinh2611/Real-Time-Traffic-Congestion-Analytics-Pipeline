# Real-Time Traffic Congestion Analytics Pipeline - Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Components Explanation](#components-explanation)
4. [Data Flow](#data-flow)
5. [Setup Instructions](#setup-instructions)
6. [Running the Pipeline](#running-the-pipeline)
7. [Running the Dashboard](#running-the-dashboard)
8. [Future Enhancements](#future-enhancements)

---

## Project Overview

This project is a **real-time data pipeline** for collecting, processing, and analyzing live traffic data to detect congestion and predict traffic patterns. It simulates traffic sensor data, processes it in real-time using Apache Kafka, stores it in a data lake (Parquet format), and trains machine learning models to predict future traffic speeds.

### Key Technologies
- **Apache Kafka**: Real-time data streaming
- **Apache Zookeeper**: Kafka coordination
- **PySpark**: Stream processing (optional approach)
- **Pandas**: Data processing and feature engineering
- **scikit-learn**: Machine learning (Random Forest)
- **Parquet**: Columnar storage format for data lake

---

## Architecture

```
┌─────────────────┐
│   producer.py   │ ──> Generates simulated traffic data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Kafka Broker   │ ──> Streams data through 'traffic' topic
└────────┬────────┘
         │
         ├──────────────────┬────────────────────┐
         ▼                  ▼                    ▼
┌──────────────────┐  ┌─────────────────┐  ┌──────────────┐
│ consumer_to_     │  │ stream_to_      │  │ (Other       │
│ parquet.py       │  │ parquet.py      │  │ Consumers)   │
└────────┬─────────┘  └────────┬────────┘  └──────────────┘
         │                     │
         ▼                     ▼
┌─────────────────────────────────────┐
│   Data Lake (Parquet Files)         │
│   - data/bronze_py/  (Python)       │
│   - data/bronze/     (Spark)        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────┐
│   train_model.py        │ ──> Trains Random Forest model
└──────────────┬──────────┘
               │
               ▼
┌─────────────────────────┐
│   model.joblib          │ ──> Saved ML model
└─────────────────────────┘
```

---

## Components Explanation

### 1. **docker-compose.yaml**
Sets up the infrastructure for the pipeline:
- **Zookeeper** (port 2181): Manages Kafka cluster coordination
- **Kafka Broker** (port 9092): Handles message streaming

### 2. **producer.py**
Simulates traffic sensors on different roads:
- Generates random traffic data every 2 seconds
- Data includes:
  - `sensor`: Road identifier (roadA, roadB, roadC)
  - `speed`: Random speed between 10-60 km/h
  - `timestamp`: Unix timestamp
- Publishes data to Kafka topic `traffic`

### 3. **consumer_to_parquet.py** (Python-based Consumer)
Consumes data from Kafka and writes to Parquet files:
- Reads messages from `traffic` topic
- Buffers messages (batch size: 20 messages or 60 seconds)
- Writes batches to `data/bronze_py/` directory as Parquet files
- File naming: `traffic_YYYYMMDD_HHMMSS.parquet`

### 4. **stream_to_parquet.py** (Spark-based Consumer)
Alternative approach using PySpark Structured Streaming:
- Reads Kafka stream using Spark
- Parses JSON schema
- Writes continuous stream to `data/bronze/` directory
- Uses checkpointing for fault tolerance
- **Note**: Configured for Windows (HADOOP_HOME paths)

### 5. **train_model.py**
Machine learning pipeline for traffic prediction:
- **Data Loading**: Reads all Parquet files from `data/bronze_py/`
- **Feature Engineering**:
  - `speed_mean_3`: Rolling average of last 3 readings per sensor
  - `speed_lag1`: Previous reading's speed
  - One-hot encoding for sensor IDs
- **Target**: Predicts next reading's speed (`speed_next`)
- **Model**: Random Forest Regressor (100 trees)
- **Evaluation**: Mean Absolute Error (MAE)
- **Output**: Saves model to `model.joblib`

### 6. **inspect_model.py**
Utility script to load and inspect the trained model.

### 7. **inspect_features.py**
Utility script to check which features the model expects.

### 8. **XG_Boost_congestion_prediction.ipynb**
Jupyter notebook for experimenting with XGBoost model (alternative to Random Forest).

### 9. **app.py** (FastAPI Prediction API)
REST API service for real-time traffic predictions:
- **Framework**: FastAPI
- **Endpoint**: `POST /predict`
- **Input**: Traffic record (sensor, speed, timestamp)
- **Output**: Prediction + congestion level
- **Congestion Logic**:
  - **HIGH**: Speed ≤ 15 km/h or predicted drop > 20-40%
  - **MEDIUM**: Speed ≤ 30 km/h or predicted drop > 30%
  - **LOW**: Normal traffic flow
- **Port**: 8000

### 10. **dashboard.py** (Streamlit Dashboard)
Interactive web dashboard for traffic monitoring:
- **Framework**: Streamlit + PyDeck
- **Features**:
  - Sensor selection (roadA, roadB, roadC)
  - Speed input slider (0-100 km/h)
  - Real-time predictions via API calls
  - Prediction history table
  - Interactive 3D map with congestion visualization
  - Hanoi coordinates (Kim Mã, Giải Phóng, Nguyễn Trãi)
- **Color Coding**: Red (HIGH), Orange (MEDIUM), Green (LOW)
- **Port**: 8501

### 11. **consumer_to_silver.py** (Silver Layer Consumer)
Enriched data processing with ML predictions:
- Consumes from Kafka topic `traffic`
- Calls prediction API for each message
- Enriches data with predicted speed and congestion level
- Implements Medallion Architecture (Silver layer)
- Saves to `data/silver/` directory
- Batch size: 50 records

---

## Data Flow

1. **Data Generation** (producer.py)
   ```
   sensor: roadA, speed: 45, timestamp: 1703523600
   ```

2. **Streaming** (Kafka)
   ```
   Topic: traffic
   Partition: 0
   Offset: 12345
   ```

3. **Storage** (Bronze Layer)
   ```
   data/bronze_py/traffic_20231225_183000.parquet
   ├── sensor: [roadA, roadB, roadA, ...]
   ├── speed: [45, 32, 50, ...]
   └── timestamp: [1703523600, 1703523602, ...]
   ```

4. **Feature Engineering**
   ```
   Features: [speed_mean_3, speed_lag1, sensor_roadA, sensor_roadB, sensor_roadC]
   Target: speed_next
   ```

5. **Model Training**
   ```
   Random Forest → Trained Model → model.joblib
   ```

---

## Setup Instructions

### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- Git

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd Real-Time-Traffic-Congestion-Analytics-Pipeline
```

### Step 2: Install Python Dependencies
Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core dependencies
pip install kafka-python pandas pyarrow scikit-learn joblib

# Optional: For Spark-based consumer
pip install pyspark
```

**Note**: The `requirements.txt` currently contains PyTorch dependencies which may not be necessary for the core pipeline. Install only what you need.

### Step 3: Start Kafka and Zookeeper
```bash
docker-compose up -d
```

Verify services are running:
```bash
docker-compose ps
```

You should see:
- `zookeeper` running on port 2181
- `kafka` running on port 9092

### Step 4: Create Kafka Topic (Optional)
The topic will be auto-created, but you can create it manually:
```bash
docker exec -it <kafka-container-name> kafka-topics --create \
  --topic traffic \
  --bootstrap-server localhost:9092 \
  --partitions 1 \
  --replication-factor 1
```

---

## Running the Pipeline

### Terminal 1: Start the Producer
Generate simulated traffic data:
```bash
python producer.py
```

You should see output like:
```
Sending {'sensor': 'roadA', 'speed': 45, 'timestamp': 1703523600}
Sending {'sensor': 'roadB', 'speed': 32, 'timestamp': 1703523602}
...
```

### Terminal 2: Start the Consumer (Choose One)

**Option A: Python Consumer** (Recommended for simplicity)
```bash
python consumer_to_parquet.py
```

Output:
```
Wrote 20 records to data/bronze_py/traffic_20231225_183000.parquet
```

**Option B: Spark Consumer** (For high-throughput scenarios)
```bash
# Note: Requires Spark installation and HADOOP_HOME configuration
python stream_to_parquet.py
```

### Terminal 3: Train the Model
After collecting sufficient data (let the consumer run for a few minutes):
```bash
python train_model.py
```

Output:
```
Found 5 parquet files.
Training on 160 rows, testing on 40 rows.
Mean Absolute Error on test set: 8.45
Saved trained model to model.joblib
```

### Inspect the Model
```bash
# View model details
python inspect_model.py

# Check feature names
python inspect_features.py
```

---

## Running the Dashboard

The project now includes a complete dashboard system with FastAPI backend and Streamlit frontend.

### Architecture Overview
```
Producer → Kafka → Bronze Consumer → Bronze Layer → Train Model
                        ↓
                 Silver Consumer → FastAPI → Silver Layer (enriched)
                                      ↓
                               Streamlit Dashboard
```

### Prerequisites

Install additional dependencies:
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dashboard dependencies
pip install fastapi uvicorn streamlit pydeck requests
```

### Step-by-Step: Running the Complete System

**Terminal 1: Start Kafka Infrastructure**
```bash
docker-compose up -d
```

**Terminal 2: Start Data Producer**
```bash
python producer.py
```
Expected output:
```
Sending {'sensor': 'roadA', 'speed': 45, 'timestamp': 1703523600}
Sending {'sensor': 'roadB', 'speed': 32, 'timestamp': 1703523602}
...
```

**Terminal 3: Start Bronze Consumer**
```bash
python consumer_to_parquet.py
```
Expected output:
```
Wrote 20 records to data/bronze_py/traffic_20231225_183000.parquet
```

**Terminal 4: Train ML Model** (wait 2-3 minutes for data collection)
```bash
python train_model.py
```
Expected output:
```
Found 5 parquet files.
Training on 160 rows, testing on 40 rows.
Mean Absolute Error on test set: 8.45
Saved trained model to model.joblib
```

**Terminal 5: Start FastAPI Prediction Service**
```bash
uvicorn app:app --reload
```
Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Test the API:
```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sensor": "roadA", "speed": 25, "timestamp": 1703523600}'
```

Expected response:
```json
{
  "sensor": "roadA",
  "current_speed": 25,
  "predicted_speed_next": 28.5,
  "congestion": "MEDIUM",
  "timestamp": 1703523600
}
```

**Terminal 6: Start Streamlit Dashboard**
```bash
streamlit run dashboard.py
```
Expected output:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.1.x:8501
```

**Terminal 7: (Optional) Start Silver Consumer**
For enriched data with predictions:
```bash
python consumer_to_silver.py
```
This will create files in `data/silver/` with predictions and congestion levels.

### Using the Dashboard

1. **Open Browser**: Navigate to `http://localhost:8501`

2. **Select Sensor**: Choose from roadA, roadB, or roadC
   - roadA: Kim Mã Road, Hanoi
   - roadB: Giải Phóng Road, Hanoi
   - roadC: Nguyễn Trãi Road, Hanoi

3. **Adjust Speed**: Use slider (0-100 km/h)

4. **Get Prediction**: Click "Predict" button

5. **View Results**:
   - Predicted next speed
   - Congestion level (HIGH/MEDIUM/LOW)
   - Prediction history table
   - Interactive 3D map with color-coded markers

### Dashboard Features

**Sidebar Controls:**
- **Sensor dropdown**: Select which road sensor
- **Speed slider**: Simulate current traffic speed
- **Predict button**: Send request to API

**Main Display:**
- **Success message**: Shows prediction and congestion
- **Prediction History**: Table with all queries
- **Congestion Map**: Interactive Hanoi map
  - 🔴 Red markers: HIGH congestion (speed ≤ 15)
  - 🟠 Orange markers: MEDIUM congestion (speed 15-30)
  - 🟢 Green markers: LOW congestion (speed > 30)

### Quick Test Scenarios

**Test 1: High Congestion**
- Sensor: roadA
- Speed: 10 km/h
- Expected: HIGH congestion, red marker

**Test 2: Medium Congestion**
- Sensor: roadB
- Speed: 25 km/h
- Expected: MEDIUM congestion, orange marker

**Test 3: Low Congestion**
- Sensor: roadC
- Speed: 55 km/h
- Expected: LOW congestion, green marker

### API Endpoints

**Health Check:**
```bash
curl http://127.0.0.1:8000/ping
# Response: {"ping":"pong"}
```

**Prediction:**
```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sensor": "roadA",
    "speed": 45,
    "timestamp": 1703523600
  }'
```

### Data Flow with Dashboard

1. **Producer** generates traffic data → Kafka
2. **Bronze Consumer** saves raw data → `data/bronze_py/`
3. **Model Training** creates `model.joblib`
4. **FastAPI** loads model and serves predictions
5. **Dashboard** calls API and displays results
6. **Silver Consumer** (optional) enriches data → `data/silver/`

---

## Future Enhancements

### Short-term Improvements
1. **Add Dashboard** - Implement real-time visualization
2. **Congestion Detection** - Define speed thresholds for alerts
3. **Model Deployment** - Serve model via API for real-time predictions
4. **Data Validation** - Add schema validation for incoming data

### Long-term Enhancements
1. **Advanced Models** - Implement XGBoost/LSTM for better predictions
2. **Multi-source Data** - Integrate weather, events, holidays
3. **Anomaly Detection** - Detect unusual traffic patterns
4. **Historical Analysis** - Time-series analysis and reporting
5. **Scalability** - Deploy on Kubernetes with multiple Kafka partitions
6. **Silver/Gold Layers** - Add data transformation layers (Medallion Architecture)

---

## Troubleshooting

### Kafka Connection Issues
```bash
# Check if Kafka is running
docker-compose ps

# View Kafka logs
docker-compose logs kafka

# Restart services
docker-compose restart
```

### Python Package Issues
```bash
# Reinstall specific package
pip install --upgrade kafka-python

# Clear cache and reinstall
pip cache purge
pip install -r requirements.txt
```

### Parquet Files Not Created
- Ensure consumer is running
- Check write permissions in `data/` directory
- Verify producer is sending data (check terminal output)

### Model Training Fails
- Ensure sufficient data collected (at least 100+ records)
- Check Parquet files exist: `ls data/bronze_py/`
- Verify data quality: `python inspect_features.py`

---

## Project Structure
```
Real-Time-Traffic-Congestion-Analytics-Pipeline/
├── docker-compose.yaml          # Kafka/Zookeeper setup
├── producer.py                  # Data generator
├── consumer_to_parquet.py       # Bronze layer consumer (Python)
├── consumer_to_silver.py        # Silver layer consumer (enriched)
├── stream_to_parquet.py         # Spark-based consumer
├── train_model.py               # ML training pipeline
├── app.py                       # FastAPI prediction service
├── dashboard.py                 # Streamlit dashboard
├── inspect_model.py             # Model inspection utility
├── inspect_features.py          # Feature inspection utility
├── XG_Boost_congestion_prediction.ipynb  # Jupyter notebook
├── requirements.txt             # Python dependencies
├── PROJECT_DOCUMENTATION.md     # This file
├── data/
│   ├── bronze_py/              # Raw data (Python consumer)
│   ├── bronze/                 # Raw data (Spark consumer)
│   └── silver/                 # Enriched data with predictions
├── checkpoint/                  # Spark checkpoints
└── model.joblib                # Trained ML model
```

---

## Contact & Support

For issues or questions:
1. Check existing GitHub Issues
2. Review logs: `docker-compose logs`
3. Verify Python environment: `python --version`

---

**Last Updated**: December 25, 2025
**Version**: 1.0