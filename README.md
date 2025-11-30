# Real-Time-Traffic-Congestion-Analytics-Pipeline
A real-time data pipeline for collecting, processing, and analyzing live traffic data to detect congestion and visualize road conditions. The system ingests data streams from simulated or open APIs, processes them using Apache Kafka and Spark Streaming, and stores results in a data lake for visualization dashboards.

## Project Overview
- Real-time traffic data simulation using Kafka
- Stream processing with PySpark Structured Streaming or pure‑Python consumer
- Parquet-based data lake (bronze layer)
- Train a RFC model for prediction
