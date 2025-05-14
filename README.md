# Zimbozapp: Meal Recipe Telegram Bot

## Overview
Zimbozapp is a data engineering project that demonstrates a modern data pipeline using Python, Kafka, PySpark, MinIO (S3-compatible), Elasticsearch, and Airflow. The end product is a Telegram bot that helps users find meal recipes based on their available groceries, meal type, preparation time, and dietary preferences.

## Architecture
- **Spoonacular API**: Source of meal recipes.
- **Kafka**: Message broker for streaming recipe data.
- **PySpark**: Consumes from Kafka, processes data, and writes to MinIO (data lake) and Elasticsearch (searchable store).
- **MinIO**: S3-compatible data lake for storing raw recipe data as JSON.
- **Elasticsearch**: Stores processed recipes for fast search and retrieval.
- **Telegram Bot**: Interacts with users, queries Elasticsearch, and returns recipe suggestions.
- **Airflow**: Orchestrates weekly data pulls from the Spoonacular API.

## Folder Structure
```
zimbozapp/
├── .env
├── README.md
├── docker-compose.yml
├── requirements.txt
│
├── airflow/
│   └── dags/
│       └── fetch_spoonacular.py
│
├── kafka/
│   └── producer.py
│
├── spark/
│   └── spark_streaming.py
│
├── minio/
│   └── (optional: scripts for setup or testing)
│
├── elasticsearch/
│   └── setup_index.py
│
├── bot/
│   ├── bot.py
│   └── utils.py
│
└── config/
    └── config.py
```

## Setup & Usage
1. **Clone the repo** and create a `.env` file with your secrets (see `.env.example`).
2. **Run `docker-compose up`** to start all services locally.
3. **Airflow** will fetch new recipes weekly and push to Kafka.
4. **PySpark** will process and store data in MinIO and Elasticsearch.
5. **Telegram Bot** will interact with users and fetch recipes from Elasticsearch.

## Notes
- Designed for Apple Silicon (M1/ARM) compatibility.
- All services run locally via Docker Compose.
- See code comments for further explanations.

---

## Authors
- Orgad Salomon 