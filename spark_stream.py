from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, window, current_timestamp, coalesce
from pyspark.sql.types import StructType, StringType, FloatType

# -----------------------------------
# Create Spark Session
# -----------------------------------
spark = SparkSession.builder \
    .appName("UrbanMoodIndex") \
    .config("spark.sql.adaptive.enabled", "false") \
    .config("spark.sql.streaming.statefulOperator.stateStoreAssert.enabled", "false") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# -----------------------------------
# PostgreSQL — Supabase
# -----------------------------------
DB_URL = "jdbc:postgresql://db.ifuouugzeqbfdpzchxtw.supabase.co:5432/postgres"
DB_PROPERTIES = {
    "user":     "postgres",
    "password": "Sahilmh9539292202",
    "driver":   "org.postgresql.Driver",
    "ssl":      "true",
    "sslmode":  "require"
}

# -----------------------------------
# Schema
# -----------------------------------
schema = StructType() \
    .add("city", StringType()) \
    .add("text", StringType()) \
    .add("sentiment", FloatType()) \
    .add("temperature", FloatType()) \
    .add("humidity", FloatType()) \
    .add("weather_condition", StringType()) \
    .add("timestamp", StringType()) \
    .add("source", StringType()) \
    .add("traffic_index", FloatType()) \
    .add("congestion_level", StringType())

# -----------------------------------
# Read from Kafka
# -----------------------------------
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "city-mood") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

json_df = df.selectExpr("CAST(value AS STRING)")

parsed_df = json_df.select(
    from_json(col("value"), schema).alias("data")
).select("data.*")

# Convert timestamp string to proper event_time
parsed_df = parsed_df.withColumn(
    "event_time",
    to_timestamp(col("timestamp"), "yyyy-MM-dd'T'HH:mm:ss.SSSSSS")
)

# Fall back to current_timestamp if parsing fails
parsed_df = parsed_df.withColumn(
    "event_time",
    coalesce(col("event_time"), current_timestamp())
)

# -----------------------------------
# TEXT / MOOD EVENTS
# -----------------------------------
text_df = parsed_df.filter(
    (col("source") != "weather") &
    (col("source") != "traffic") &
    col("sentiment").isNotNull()
)

mood_df = text_df \
    .withWatermark("event_time", "2 minutes") \
    .groupBy(
        window(col("event_time"), "30 seconds"),
        col("city"),
        col("source")
    ) \
    .avg("sentiment") \
    .withColumnRenamed("avg(sentiment)", "mood_score")

# -----------------------------------
# WEATHER EVENTS
# -----------------------------------
weather_df = parsed_df.filter(col("source") == "weather")

# -----------------------------------
# TRAFFIC EVENTS
# -----------------------------------
traffic_df = parsed_df.filter(col("source") == "traffic")

# -----------------------------------
# Write Functions
# -----------------------------------
def write_mood(batch_df, batch_id):
    try:
        batch_df.cache()
        count = batch_df.count()

        if count > 0:
            flattened = batch_df.select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("city"),
                col("source"),
                col("mood_score")
            )
            flattened.write \
                .mode("append") \
                .jdbc(DB_URL, "mood_data", properties=DB_PROPERTIES)
            print(f"[Mood] Batch {batch_id}: ✅ Wrote {count} rows")
        else:
            print(f"[Mood] Batch {batch_id}: Empty, skipping")

        batch_df.unpersist()
    except Exception as e:
        print(f"[Mood] Batch {batch_id}: ❌ Error - {str(e)}")
        try:
            batch_df.unpersist()
        except:
            pass


def write_weather(batch_df, batch_id):
    try:
        batch_df.cache()
        count = batch_df.count()

        if count > 0:
            weather_out = batch_df.select(
                col("city"),
                col("temperature"),
                col("humidity"),
                col("weather_condition"),
                col("timestamp")
            )
            weather_out.write \
                .mode("append") \
                .jdbc(DB_URL, "weather_data", properties=DB_PROPERTIES)
            print(f"[Weather] Batch {batch_id}: ✅ Wrote {count} rows")
        else:
            print(f"[Weather] Batch {batch_id}: Empty, skipping")

        batch_df.unpersist()
    except Exception as e:
        print(f"[Weather] Batch {batch_id}: ❌ Error - {str(e)}")
        try:
            batch_df.unpersist()
        except:
            pass


def write_traffic(batch_df, batch_id):
    try:
        batch_df.cache()
        count = batch_df.count()

        if count > 0:
            traffic_out = batch_df.select(
                col("city"),
                col("traffic_index"),
                col("congestion_level"),
                col("timestamp")
            )
            traffic_out.write \
                .mode("append") \
                .jdbc(DB_URL, "traffic_data", properties=DB_PROPERTIES)
            print(f"[Traffic] Batch {batch_id}: ✅ Wrote {count} rows")
        else:
            print(f"[Traffic] Batch {batch_id}: Empty, skipping")

        batch_df.unpersist()
    except Exception as e:
        print(f"[Traffic] Batch {batch_id}: ❌ Error - {str(e)}")
        try:
            batch_df.unpersist()
        except:
            pass


# -----------------------------------
# Start Streams
# -----------------------------------
print("=" * 60)
print("🚀 Starting Urban Mood Index Streaming Pipeline")
print("📡 Database: Supabase (cloud PostgreSQL)")
print("=" * 60)

mood_query = mood_df.writeStream \
    .outputMode("append") \
    .foreachBatch(write_mood) \
    .option("checkpointLocation", "data/checkpoint_mood") \
    .trigger(processingTime="10 seconds") \
    .start()

weather_query = weather_df.writeStream \
    .outputMode("append") \
    .foreachBatch(write_weather) \
    .option("checkpointLocation", "data/checkpoint_weather") \
    .trigger(processingTime="10 seconds") \
    .start()

traffic_query = traffic_df.writeStream \
    .outputMode("append") \
    .foreachBatch(write_traffic) \
    .option("checkpointLocation", "data/checkpoint_traffic") \
    .trigger(processingTime="10 seconds") \
    .start()

print("⏳ Waiting for data from Kafka...")
spark.streams.awaitAnyTermination()