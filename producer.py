from kafka import KafkaProducer
from textblob import TextBlob
import json
import time
import random
from datetime import datetime

# Connect to Kafka
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

cities = ["Chennai", "Mumbai", "Bangalore"]

positive_texts = [
    "I love the weather today, city vibes are amazing!",
    "Feeling happy and energetic, great day in the city!",
    "Beautiful sunrise, people are cheerful and warm.",
    "Great food, great people, loving this city.",
    "Public transport is smooth today, very pleasant commute.",
]

negative_texts = [
    "Traffic is horrible, stuck for 2 hours.",
    "Feeling stressed about work and the pollution is terrible.",
    "Too much noise and congestion, very frustrating day.",
    "Roads are flooded, commute is a nightmare.",
    "Air quality is awful, feeling suffocated.",
]

def get_sentiment(text):
    """Returns a sentiment score between -1.0 and 1.0 using TextBlob."""
    analysis = TextBlob(text)
    return round(analysis.sentiment.polarity, 4)

print("🚀 Starting Simulated Producer with Sentiment...")

while True:
    city = random.choice(cities)
    text = random.choice(positive_texts + negative_texts)
    sentiment = get_sentiment(text)

    message = {
        "city": city,
        "text": text,
        "sentiment": sentiment,          # ✅ FIXED: sentiment field added
        "timestamp": datetime.utcnow().isoformat(),
        "source": "simulated"
    }

    producer.send("city-mood", value=message)
    producer.flush()

    print(f"✅ Sent | {city} | sentiment={sentiment} | {text[:50]}")

    time.sleep(2)