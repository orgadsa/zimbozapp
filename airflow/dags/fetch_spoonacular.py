from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import json
from kafka import KafkaProducer
import os
from dotenv import load_dotenv

# Load config
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY')
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'recipes')

# Function to fetch recipes and send to Kafka
def fetch_and_send_to_kafka(**kwargs):
    url = f'https://api.spoonacular.com/recipes/random?number=10&apiKey={SPOONACULAR_API_KEY}'
    response = requests.get(url)
    recipes = response.json().get('recipes', [])
    producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER, value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    for recipe in recipes:
        producer.send(KAFKA_TOPIC, recipe)
    producer.flush()

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