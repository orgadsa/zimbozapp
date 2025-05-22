from kafka import KafkaConsumer

KAFKA_BROKER = 'localhost:9092'  # Use 'localhost:9092' if running outside Docker
KAFKA_TOPIC = 'recipes'

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',
    enable_auto_commit=False,
    consumer_timeout_ms=5000  # Stop after 5 seconds if no messages
)

print(f"Consuming messages from topic '{KAFKA_TOPIC}'...")
count = 0
for message in consumer:
    print(f"Message: {message.value.decode('utf-8')}")
    count += 1

if count == 0:
    print("No messages found in the topic.")
else:
    print(f"Total messages read: {count}") 