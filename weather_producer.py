import requests
import json
import time
from datetime import datetime
from kafka import KafkaProducer

# -----------------------------
# CONFIG
# -----------------------------
API_KEY = "2390dff05a4a53443346892788851aa1"
KAFKA_TOPIC = "city-mood"

cities = ["Chennai", "Mumbai", "Bangalore"]

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def fetch_weather(city):
    url = (
        f"http://api.openweathermap.org/data/2.5/weather?"
        f"q={city}&appid={API_KEY}&units=metric"
    )

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print("Weather API error:", response.status_code)
        return None

print("Starting Weather Producer...")

while True:
    for city in cities:
        data = fetch_weather(city)

        if data:
            message = {
                "city": city,
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "weather_condition": data["weather"][0]["description"],
                "timestamp": datetime.utcnow().isoformat(),
                "source": "weather"
            }

            producer.send(KAFKA_TOPIC, value=message)
            producer.flush()

            print("Sent:", message)

    time.sleep(60)