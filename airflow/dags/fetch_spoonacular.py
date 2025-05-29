"""
Airflow DAG for Zimbozapp
- Fetches recipes from Spoonacular API (or uses mock data if unavailable)
- Sends recipes to Kafka
- Triggers Spark streaming job to process data end-to-end
"""
import os
import logging
import json
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from kafka import KafkaProducer
# Import configurations from the central config file
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..')) # Add project root to PYTHONPATH
from config.config import SPOONACULAR_API_KEY, KAFKA_BROKER, KAFKA_TOPIC


def fetch_and_send_to_kafka(**kwargs):
    """Fetch recipes from Spoonacular API and send to Kafka. Use mock data if API is unavailable or retries fail."""
    url = f'https://api.spoonacular.com/recipes/random?number=10&apiKey={SPOONACULAR_API_KEY}'
    recipes = []
    
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1  # e.g., sleep for 0s, 2s, 4s between retries
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        logging.info(f"Attempting to fetch recipes from Spoonacular API: {url}")
        response = session.get(url, timeout=10) # Added timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        logging.info(f"Spoonacular API response status: {response.status_code}")
        recipes = response.json().get('recipes', [])
        if not recipes: # Handles cases where API returns 200 but no recipes or empty list
             logging.warning("Spoonacular API returned 200 but no recipes found or recipes list is empty.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Spoonacular API request failed after retries: {e}")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON from Spoonacular API response: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}")
    except Exception as e: # Catch any other unexpected errors
        logging.error(f"An unexpected error occurred during Spoonacular API call: {e}")

    if not recipes:
        logging.warning("Failed to fetch recipes from Spoonacular API after retries or due to other errors. Using mock data.")
        recipes = [
            {
                "title": "Test Recipe",
                "ingredients": ["egg", "flour", "milk"],
                "instructions": "Mix all ingredients and cook in a pan."
            },
            {
                "title": "Sample Salad",
                "ingredients": ["lettuce", "tomato", "cucumber"],
                "instructions": "Chop all ingredients and toss with dressing."
            }
        ]
        logging.info(f"Using {len(recipes)} mock recipes.")
    else:
        logging.info(f"Fetched {len(recipes)} recipes from Spoonacular.")
    # Send recipes to Kafka with logging and error handling
    try:
        producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
        for recipe in recipes:
            logging.info(f"Sending recipe to Kafka: {recipe}")
            producer.send(KAFKA_TOPIC, json.dumps(recipe).encode('utf-8'))
        producer.flush()
        logging.info("Sent recipes to Kafka.")
    except Exception as e:
        logging.error(f"Failed to send recipes to Kafka: {e}")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'fetch_spoonacular_recipes',
    default_args=default_args,
    description='Fetch recipes from Spoonacular API and send to Kafka, then run Spark streaming job',
    schedule='@weekly',
    catchup=False,
)

fetch_task = PythonOperator(
    task_id='fetch_and_send_to_kafka',
    python_callable=fetch_and_send_to_kafka,
    dag=dag,
)

run_spark_streaming = BashOperator(
    task_id='run_spark_streaming',
    bash_command='docker exec spark bash -c "pip install --no-cache-dir -r /requirements.txt && env AIRFLOW_RUN=1 python /app/spark/spark_streaming.py"',
    dag=dag,
)

fetch_task >> run_spark_streaming 