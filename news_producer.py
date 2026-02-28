import requests
import json
import time
import os
from datetime import datetime
from kafka import KafkaProducer
from textblob import TextBlob

# ===== CONFIG =====
# ✅ FIXED: Set your API key directly here (or use environment variable)
# Get a free key at https://newsapi.org
API_KEY = os.getenv("NEWS_API_KEY", "YOUR_NEWSAPI_KEY_HERE")
KAFKA_TOPIC = "city-mood"

cities = ["Chennai", "Mumbai", "Bangalore"]

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

last_city_index = 0

def get_sentiment(text):
    """Returns a sentiment score between -1.0 and 1.0 using TextBlob."""
    analysis = TextBlob(text)
    return round(analysis.sentiment.polarity, 4)

def fetch_news(city):
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={city}&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"pageSize=3&"
        f"apiKey={API_KEY}"
    )

    try:
        response = requests.get(url, timeout=10)
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return []

    if response.status_code == 429:
        print("⚠️ Rate limit hit. Sleeping 5 minutes...")
        time.sleep(300)
        return []

    if response.status_code != 200:
        print(f"❌ Error fetching news: {response.status_code} - {response.text}")
        return []

    return response.json().get("articles", [])


print("🚀 Starting News Producer (with Sentiment)...")

while True:
    city = cities[last_city_index]

    print(f"\n📰 Fetching news for {city}...")

    articles = fetch_news(city)

    for article in articles:
        text = (
            (article.get("title") or "") + " " +
            (article.get("description") or "")
        ).strip()

        if text:
            sentiment = get_sentiment(text)  # ✅ FIXED: compute sentiment before sending

            message = {
                "city": city,
                "text": text,
                "sentiment": sentiment,       # ✅ FIXED: included in message
                "timestamp": datetime.utcnow().isoformat(),
                "source": "news"
            }

            producer.send(KAFKA_TOPIC, value=message)
            print(f"✅ Sent | {city} | sentiment={sentiment} | {text[:60]}...")

    producer.flush()

    # Rotate city each cycle
    last_city_index = (last_city_index + 1) % len(cities)

    print("💤 Sleeping 5 minutes (NewsAPI rate limit)...\n")
    time.sleep(300)