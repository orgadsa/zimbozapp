from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import json
from kafka import KafkaProducer
import os
from dotenv import load_dotenv
import logging

# Load config
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY')
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'recipes')

# Function to fetch recipes and send to Kafka
def fetch_and_send_to_kafka(**kwargs):
    url = f'https://api.spoonacular.com/recipes/random?number=10&apiKey={SPOONACULAR_API_KEY}'
    response = requests.get(url)
    logging.info(f"Spoonacular API response status: {response.status_code}")
    recipes = []
    if response.status_code == 200:
        try:
            recipes = response.json().get('recipes', [])
        except Exception as e:
            logging.error(f"Failed to parse JSON: {e}")
            recipes = []
    if not recipes:
        logging.warning(f"No recipes fetched. Response content: {response.text}")
        # Use mock data if API is unavailable or returns no recipes
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
    producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER, value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    # Send recipes to Kafka with logging and error handling
    try:
        for recipe in recipes:
            logging.info(f"Sending recipe to Kafka: {recipe}")
            producer.send(KAFKA_TOPIC, json.dumps(recipe).encode('utf-8'))
        producer.flush()
        logging.info("Sent recipes to Kafka.")
    except Exception as e:
        logging.error(f"Failed to send recipes to Kafka: {e}")

# Airflow DAG definition
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
    description='Fetch recipes from Spoonacular API and send to Kafka',
    schedule='@weekly',
    catchup=False,
)

fetch_task = PythonOperator(
    task_id='fetch_and_send_to_kafka',
    python_callable=fetch_and_send_to_kafka,
    dag=dag,
) 