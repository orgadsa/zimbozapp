"""
Spark Job for Zimbozapp
- Batch mode for Airflow: processes all available Kafka data and exits
- Streaming mode for real-time: runs indefinitely
"""
import os
import sys
sys.path.append('/app')
import io
import logging # Import logging module
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, ArrayType, IntegerType
from minio import Minio
from elasticsearch import Elasticsearch
import json
from config.config import (
    KAFKA_BROKER, KAFKA_TOPIC, MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET,
    ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ELASTICSEARCH_INDEX
)

# Define schema for recipes
schema = StructType()\
    .add("id", IntegerType())\
    .add("title", StringType())\
    .add("ingredients", ArrayType(StringType()))\
    .add("instructions", StringType())

# Initialize Spark session
spark = SparkSession.builder \
    .appName("RecipeKafkaSparkStreaming") \
    .getOrCreate()

def write_to_minio(batch_df, batch_id):
    """Write each batch as a JSON file to MinIO."""
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    data = batch_df.toJSON().collect()
    if not data:
        return
    file_data = '\n'.join(data).encode('utf-8')
    file_name = f"recipes_batch_{batch_id}.json"
    try:
        minio_client.put_object(
            MINIO_BUCKET, file_name, data=io.BytesIO(file_data), length=len(file_data), content_type='application/json'
        )
    except Exception as e:
        logging.error(f"Failed to write to MinIO for batch {batch_id}: {e}") # Use logging.error

def write_to_elasticsearch(batch_df, batch_id):
    """Index each row in the batch to Elasticsearch."""
    es = Elasticsearch([{'host': ELASTICSEARCH_HOST, 'port': ELASTICSEARCH_PORT}])
    for row in batch_df.collect():
        doc = row.asDict()
        try:
            es.index(index=ELASTICSEARCH_INDEX, body=doc)
        except Exception as e:
            logging.error(f"Failed to index document in Elasticsearch for batch {batch_id}, document: {doc.get('id', 'N/A')}: {e}") # Use logging.error

def process_and_write_recipes(kafka_df, batch_id):
    """Transforms Kafka messages and writes them to MinIO and Elasticsearch."""
    # Transform the Kafka message value (JSON string) into a structured DataFrame
    recipes_df = kafka_df.selectExpr("CAST(value AS STRING) as json") \
        .select(from_json(col("json"), schema).alias("data")).select("data.*")
    
    # Filter out rows where the transformation failed (data column is null)
    # This can happen if the JSON message doesn't match the schema
    recipes_df = recipes_df.filter(col("id").isNotNull()) # Assuming 'id' is a non-nullable part of your schema

    if recipes_df.count() == 0:
        print(f"Batch {batch_id}: No valid recipes to process after schema transformation.")
        return

    print(f"Batch {batch_id}: Processing {recipes_df.count()} recipes.")
    write_to_minio(recipes_df, batch_id)
    write_to_elasticsearch(recipes_df, batch_id)

# Batch mode for Airflow: process all available Kafka data and exit
if os.environ.get('AIRFLOW_RUN', '0') == '1':
    print("Starting Spark job in batch mode for Airflow run.")
    kafka_input_df = spark.read \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .option("endingOffsets", "latest") \
        .load()
    
    process_and_write_recipes(kafka_input_df, "airflow_batch_0")
    print("Batch processing complete. Exiting.")
else:
    # Streaming mode: run indefinitely
    print("Starting Spark job in streaming mode.")
    kafka_input_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .load()

    query = kafka_input_df.writeStream \
        .foreachBatch(process_and_write_recipes) \
        .start()
    
    query.awaitTermination()