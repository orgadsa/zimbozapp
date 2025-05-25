"""
Spark Job for Zimbozapp
- Batch mode for Airflow: processes all available Kafka data and exits
- Streaming mode for real-time: runs indefinitely
"""
import os
os.environ["PYSPARK_SUBMIT_ARGS"] = (
    "--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 pyspark-shell"
)
import sys
sys.path.append('/app')
import io
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
        print(f"Failed to write to MinIO: {e}")

def write_to_elasticsearch(batch_df, batch_id):
    """Index each row in the batch to Elasticsearch."""
    es = Elasticsearch([{'host': ELASTICSEARCH_HOST, 'port': ELASTICSEARCH_PORT}])
    for row in batch_df.collect():
        doc = row.asDict()
        try:
            es.index(index=ELASTICSEARCH_INDEX, body=doc)
        except Exception as e:
            print(f"Failed to index document in Elasticsearch: {e}")

# Batch mode for Airflow: process all available Kafka data and exit
if os.environ.get('AIRFLOW_RUN', '0') == '1':
    df = spark.read \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .option("endingOffsets", "latest") \
        .load()
    recipes = df.selectExpr("CAST(value AS STRING) as json") \
        .select(from_json(col("json"), schema).alias("data")).select("data.*")
    write_to_minio(recipes, 0)
    write_to_elasticsearch(recipes, 0)
    print("Batch processing complete. Exiting.")
else:
    # Streaming mode: run indefinitely
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .load()
    recipes = df.selectExpr("CAST(value AS STRING) as json") \
        .select(from_json(col("json"), schema).alias("data")).select("data.*")
    recipes.writeStream \
        .foreachBatch(lambda df, epochId: (write_to_minio(df, epochId), write_to_elasticsearch(df, epochId))) \
        .start() \
        .awaitTermination() 