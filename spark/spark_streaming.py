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
import os
from config.config import (
    KAFKA_BROKER, KAFKA_TOPIC, MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET,
    ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ELASTICSEARCH_INDEX
)

# Define schema for recipes (simplified example)
schema = StructType()\
    .add("id", IntegerType())\
    .add("title", StringType())\
    .add("ingredients", ArrayType(StringType()))\
    .add("instructions", StringType())

# Initialize Spark session
spark = SparkSession.builder \
    .appName("RecipeKafkaSparkStreaming") \
    .getOrCreate()

# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "earliest") \
    .load()

# Parse the value as JSON
recipes = df.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), schema).alias("data")).select("data.*")

# Debug print function
def debug_print(batch_df, batch_id):
    print(f"Batch {batch_id} row count: {batch_df.count()}")
    batch_df.show()

# Write raw data to MinIO (S3)
def write_to_minio(batch_df, batch_id):
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    # Save each batch as a JSON file
    data = batch_df.toJSON().collect()
    file_data = '\n'.join(data).encode('utf-8')
    file_name = f"recipes_batch_{batch_id}.json"
    minio_client.put_object(
        MINIO_BUCKET, file_name, data=io.BytesIO(file_data), length=len(file_data), content_type='application/json'
    )

# Write processed data to Elasticsearch
def write_to_elasticsearch(batch_df, batch_id):
    es = Elasticsearch([{'host': ELASTICSEARCH_HOST, 'port': ELASTICSEARCH_PORT}])
    for row in batch_df.collect():
        doc = row.asDict()
        es.index(index=ELASTICSEARCH_INDEX, body=doc)

# Start streaming queries
recipes.writeStream \
    .foreachBatch(lambda df, epochId: (debug_print(df, epochId), write_to_minio(df, epochId), write_to_elasticsearch(df, epochId))) \
    .start() \
    .awaitTermination() 