# Zimbozapp: Meal Recipe Telegram Bot

## Overview
Zimbozapp is a data engineering project that demonstrates a modern data pipeline using Python, Kafka, PySpark, MinIO (S3-compatible), Elasticsearch, and Airflow. The end product is a Telegram bot that helps users find meal recipes based on their available groceries, meal type, preparation time, and dietary preferences.

## Architecture
- **Spoonacular API**: Source of meal recipes. Data is fetched via an Airflow DAG.
- **Kafka**: Message broker for streaming recipe data, both from live API calls and mock data.
- **PySpark**: The `spark_streaming.py` script consumes data from Kafka. It can operate in two modes:
    - **Batch mode**: Processes all available data from Kafka, suitable for scheduled execution by Airflow (though the DAG currently doesn't trigger Spark directly).
    - **Streaming mode**: For continuous real-time data processing from Kafka.
    It then processes this data and writes it to MinIO (data lake) and Elasticsearch (searchable store).
- **MinIO**: S3-compatible data lake for storing raw recipe data as JSON.
- **Elasticsearch**: Stores processed recipes for fast search and retrieval. The `elasticsearch/setup_index.py` script, run during initial setup, creates the `recipes` index with a predefined mapping tailored for the recipe data structure.
- **Telegram Bot**: Interacts with users, queries Elasticsearch, and returns recipe suggestions.
- **Airflow**: Orchestrates weekly data pulls from the Spoonacular API using the `fetch_spoonacular.py` DAG. This DAG includes a fallback mechanism to use mock recipe data if the live API is unavailable or fails, ensuring data flow for testing and development.

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
│   ├── dags/
│   │   └── fetch_spoonacular.py
│   └── requirements.txt
│
├── bot/
│   ├── Dockerfile
│   ├── bot.py
│   └── utils.py
│
├── config/
│   └── config.py
│
├── elasticsearch/
│   ├── check_elastic.py
│   └── setup_index.py
│
├── kafka/
│   ├── check_kafka.py
│   └── producer.py
│
├── spark/
│   ├── requirements.txt
│   ├── spark_streaming.py
│   └── user-jars/
│       └── commons-pool2-2.11.1.jar 
│       └── (other jars...)
│
└── zimboz_architectureV2.drawio
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
   - This command handles the setup of all services defined in `docker-compose.yml`. It builds the necessary Docker images (like for the Telegram bot, which uses its `bot/Dockerfile`) and starts all containers.
   - Python dependencies for Airflow (listed in `airflow/requirements.txt`) are automatically installed when the Airflow container starts.
   - Python dependencies for the Telegram bot (as defined in its `bot/Dockerfile` and potentially `requirements.txt` if used there) are installed during the image build process.

4. **Service-Specific Details:**
   - **Spark:**
     - Python dependencies for Spark scripts are listed in `spark/requirements.txt`. The `docker-compose.yml` makes these requirements available within the Spark container. If you plan to run Spark applications interactively or submit jobs manually inside the Spark container, you might need to install them explicitly:
       ```sh
       docker exec -it <spark_container_name_or_id> pip install -r /requirements.txt 
       # Replace <spark_container_name_or_id> with your actual Spark container name or ID
       ```
     - JAR files required for Spark, such as the Kafka connector, are located in the `spark/user-jars/` directory. These are automatically made available to the Spark service through a volume mount specified in `docker-compose.yml`.
     - Additionally, `spark_streaming.py` might define `PYSPARK_SUBMIT_ARGS` to specify packages like `org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0`. Both this environment variable and the `user-jars` directory are methods to provide Spark with necessary dependencies. For now, this README documents both approaches.
   - **Airflow:**
     - Python dependencies are managed via `airflow/requirements.txt` and installed automatically on container startup.
     - Access the Airflow UI at [http://localhost:8081](http://localhost:8081) to monitor and manage DAGs.

5. **Access Airflow UI (optional):**
   - Open [http://localhost:8081](http://localhost:8081) in your browser to monitor DAG runs. *(This is now consolidated under Service-Specific Details but kept here for quick access if preferred)*

6. **Start using the Telegram bot:**
   - Open Telegram and search for your bot (using the username you set up with BotFather).
   - Start a chat and follow the prompts to get recipe suggestions based on your groceries and preferences.

## Notes
- Designed for Apple Silicon (M1/ARM) compatibility.
- All services run locally via Docker Compose.
- See code comments for further explanations.

---

## Authors
- Orgad Salomon 