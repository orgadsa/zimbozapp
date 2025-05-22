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
├── .env.example
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

## First Time Setup & Usage
1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd zimbozapp
   ```
2. **Create your `.env` file:**
   - Copy the example file and fill in your secrets:
     ```sh
     cp .env.example .env
     # Edit .env and add your TELEGRAM_BOT_TOKEN and SPOONACULAR_API_KEY
     ```
3. **Build and start all services with Docker Compose:**
   ```sh
   docker-compose up --build
   ```
   - This will start Kafka, MinIO, Elasticsearch, Spark, Airflow, and the Telegram bot.
4. **Access Airflow UI (optional):**
   - Open [http://localhost:8081](http://localhost:8081) in your browser to monitor DAG runs.
5. **Start using the Telegram bot:**
   - Open Telegram and search for your bot (using the username you set up with BotFather).
   - Start a chat and follow the prompts to get recipe suggestions based on your groceries and preferences.

## Notes
- Designed for Apple Silicon (M1/ARM) compatibility.
- All services run locally via Docker Compose.
- See code comments for further explanations.

---

## Authors
- Orgad Salomon 