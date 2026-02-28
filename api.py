import os
from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime

# --------------------------------------------------
# Absolute paths — fixes white screen on all systems
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
CORS(app)

# --------------------------------------------------
# DB Connection — Supabase
# --------------------------------------------------
DB_URI = "postgresql://postgres:Sahilmh9539292202@db.ifuouugzeqbfdpzchxtw.supabase.co:5432/postgres"

def get_conn():
    return psycopg2.connect(DB_URI)

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def compute_stress(mood_score, traffic_index=None):
    negative_component = max(0, min(1, (1 - mood_score) / 2))
    traffic_component  = min(1, traffic_index / 10) if traffic_index else 0.5
    stress = (
        0.4 * negative_component +
        0.3 * traffic_component  +
        0.2 * 0.3 +
        0.1 * 0.4
    )
    return round(min(max(stress, 0), 1), 3)

def forecast_stress(scores):
    if len(scores) < 3:
        return None
    y      = np.array([(1 - s) / 2 for s in scores[-10:]])
    x      = np.arange(len(y))
    coeffs = np.polyfit(x, y, 1)
    value  = np.poly1d(coeffs)(len(y))
    return round(float(np.clip(value, 0, 1)), 3)

# --------------------------------------------------
# Serve the website
# --------------------------------------------------
@app.route("/")
def index():
    html_path = os.path.join(BASE_DIR, 'templates', 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace("{{ url_for('static', filename='style.css') }}", "/static/style.css")
    content = content.replace("{{ url_for('static', filename='app.js') }}", "/static/app.js")
    return content, 200, {'Content-Type': 'text/html; charset=utf-8'}

# --------------------------------------------------
# /api/mood
# --------------------------------------------------
@app.route("/api/mood")
def mood():
    try:
        conn = get_conn()
        mood_df = pd.read_sql("""
            SELECT window_start, city, mood_score
            FROM mood_data ORDER BY window_start DESC LIMIT 300
        """, conn)
        try:
            traffic_df  = pd.read_sql("""
                SELECT DISTINCT ON (city) city, traffic_index
                FROM traffic_data ORDER BY city, timestamp DESC
            """, conn)
            traffic_map = dict(zip(traffic_df["city"], traffic_df["traffic_index"]))
        except Exception:
            traffic_map = {}
        conn.close()

        if mood_df.empty:
            return jsonify({"cities": [], "updated": None})

        mood_df["window_start"] = pd.to_datetime(mood_df["window_start"], errors="coerce")
        mood_df = mood_df.dropna(subset=["window_start", "mood_score"])
        mood_df = mood_df[(mood_df["mood_score"] >= -1) & (mood_df["mood_score"] <= 1)]
        latest  = mood_df.sort_values("window_start").groupby("city").last().reset_index()

        cities = []
        for _, row in latest.iterrows():
            score  = float(row["mood_score"])
            stress = compute_stress(score, traffic_map.get(row["city"]))
            status = "positive" if score > 0.2 else ("negative" if score < -0.2 else "neutral")
            cities.append({
                "city": row["city"], "mood_score": round(score, 3),
                "status": status, "stress_score": stress,
                "updated": row["window_start"].isoformat()
            })

        return jsonify({"cities": cities, "updated": datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------------------------------------------
# /api/trend
# --------------------------------------------------
@app.route("/api/trend")
def trend():
    try:
        conn = get_conn()
        df   = pd.read_sql("""
            SELECT window_start, city, mood_score
            FROM mood_data ORDER BY window_start DESC LIMIT 200
        """, conn)
        conn.close()

        if df.empty:
            return jsonify({"series": {}})

        df["window_start"] = pd.to_datetime(df["window_start"], errors="coerce")
        df = df.dropna(subset=["window_start", "mood_score"])
        df = df[(df["mood_score"] >= -1) & (df["mood_score"] <= 1)]
        df = df.drop_duplicates(subset=["window_start", "city"]).sort_values("window_start")

        series = {}
        for city, group in df.groupby("city"):
            tail = group.tail(20)
            series[city] = {
                "labels": [t.strftime("%H:%M:%S") for t in tail["window_start"]],
                "values": [round(float(v), 3) for v in tail["mood_score"]]
            }
        return jsonify({"series": series})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------------------------------------------
# /api/forecast
# --------------------------------------------------
@app.route("/api/forecast")
def forecast():
    try:
        conn = get_conn()
        df   = pd.read_sql("""
            SELECT window_start, city, mood_score
            FROM mood_data ORDER BY window_start DESC LIMIT 300
        """, conn)
        conn.close()

        if df.empty:
            return jsonify({"forecasts": []})

        df["window_start"] = pd.to_datetime(df["window_start"], errors="coerce")
        df = df.dropna(subset=["window_start", "mood_score"])

        results = []
        for city, group in df.groupby("city"):
            scores    = list(group.sort_values("window_start")["mood_score"])
            current   = compute_stress(scores[-1]) if scores else None
            predicted = forecast_stress(scores)
            if current is not None and predicted is not None:
                delta     = predicted - current
                direction = "increase" if delta > 0.05 else ("decrease" if delta < -0.05 else "stable")
                results.append({
                    "city": city, "current_stress": current,
                    "predicted_stress": predicted, "direction": direction
                })
        return jsonify({"forecasts": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------------------------------------------
# /api/weather
# --------------------------------------------------
@app.route("/api/weather")
def weather():
    try:
        conn = get_conn()
        df   = pd.read_sql("""
            SELECT DISTINCT ON (city)
                city, temperature, humidity, weather_condition, timestamp
            FROM weather_data ORDER BY city, timestamp DESC
        """, conn)
        conn.close()
        return jsonify({"weather": df.to_dict(orient="records")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------------------------------------------
# /api/traffic
# --------------------------------------------------
@app.route("/api/traffic")
def traffic():
    try:
        conn = get_conn()
        df   = pd.read_sql("""
            SELECT DISTINCT ON (city)
                city, traffic_index, congestion_level, timestamp
            FROM traffic_data ORDER BY city, timestamp DESC
        """, conn)
        conn.close()
        return jsonify({"traffic": df.to_dict(orient="records")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print(f"BASE_DIR:  {BASE_DIR}")
    print(f"Templates: {os.path.join(BASE_DIR, 'templates')}")
    print(f"Static:    {os.path.join(BASE_DIR, 'static')}")
    print(f"Database:  Supabase ({DB_URI.split('@')[1]})")
    app.run(port=5050, debug=True)