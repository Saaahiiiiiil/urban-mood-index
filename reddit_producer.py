import requests
import json
import time
from datetime import datetime
from kafka import KafkaProducer
from textblob import TextBlob

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

KAFKA_TOPIC = "city-mood"
cities = ["Chennai", "Mumbai", "Bangalore"]

def get_sentiment(text):
    """Returns a sentiment score between -1.0 and 1.0 using TextBlob."""
    analysis = TextBlob(text)
    return round(analysis.sentiment.polarity, 4)

def fetch_reddit(city):
    url = f"https://www.reddit.com/search.json?q={city}&limit=5&sort=new"
    headers = {"User-Agent": "UrbanMoodIndex/1.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        print(f"❌ Request error: {e}")
        return []

    if response.status_code == 200:
        return response.json()["data"]["children"]
    else:
        print(f"❌ Error fetching Reddit: {response.status_code}")
        return []

print("🚀 Starting Reddit Producer (with Sentiment)...")

while True:
    for city in cities:
        print(f"\n🔍 Fetching Reddit posts for {city}...")
        posts = fetch_reddit(city)

        for post in posts:
            data = post["data"]
            text = (
                (data.get("title") or "") + " " +
                (data.get("selftext") or "")
            ).strip()

            if text:
                sentiment = get_sentiment(text)  # ✅ FIXED: compute sentiment

                message = {
                    "city": city,
                    "text": text,
                    "sentiment": sentiment,       # ✅ FIXED: included in message
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "reddit"
                }

                producer.send(KAFKA_TOPIC, value=message)
                producer.flush()

                print(f"✅ Sent | {city} | sentiment={sentiment} | {text[:60]}...")

    print("\n💤 Sleeping 60 seconds...\n")
    time.sleep(60)