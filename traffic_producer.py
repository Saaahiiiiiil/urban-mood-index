from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

cities = {
    "Chennai": 1.0,
    "Mumbai": 1.2,
    "Bangalore": 1.1
}

def simulate_traffic(city):
    hour = datetime.now().hour
    base = 0

    # Peak logic
    if 6 <= hour <= 10:
        base = random.uniform(6, 9)
    elif 17 <= hour <= 21:
        base = random.uniform(7, 10)
    elif 10 < hour < 17:
        base = random.uniform(3, 6)
    else:
        base = random.uniform(1, 3)

    multiplier = cities[city]
    traffic_index = min(base * multiplier, 10)

    if traffic_index > 7:
        level = "Heavy"
    elif traffic_index > 4:
        level = "Moderate"
    else:
        level = "Light"

    return round(traffic_index, 2), level

print("Starting Traffic Producer...")

while True:
    for city in cities.keys():
        index, level = simulate_traffic(city)

        message = {
            "city": city,
            "traffic_index": index,
            "congestion_level": level,
            "timestamp": datetime.now().isoformat(),
            "source": "traffic"
        }

        producer.send("city-mood", value=message)
        producer.flush()

        print("Sent:", message)

    time.sleep(10)