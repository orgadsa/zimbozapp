import json
from kafka import KafkaProducer
from config.config import KAFKA_BROKER, KAFKA_TOPIC

def send_to_kafka(data):
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    producer.send(KAFKA_TOPIC, data)
    producer.flush()

# Example usage:
# send_to_kafka({'example': 'data'}) 