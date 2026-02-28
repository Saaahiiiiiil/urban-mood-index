#!/bin/bash
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.0 \
  --conf spark.sql.streaming.statefulOperator.stateStoreAssert.enabled=false \
  spark_stream.py
