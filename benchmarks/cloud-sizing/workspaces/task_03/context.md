# Task 03 — Batch Data Processing Pipeline

## Scenario
A large e-commerce company runs nightly batch jobs that process the previous day's
clickstream data, generate product recommendations, and update their data warehouse.
The pipeline uses Apache Spark on a single high-memory VM (no managed Spark cluster).

## Current Setup
- Running on bare metal with 128GB RAM and 32 cores
- Migrating to GCP for elasticity — want to spin up/down daily
- Pipeline is a series of PySpark jobs (not streaming, pure batch)
- Data is read from Cloud Storage (GCS), processed in memory, written back to GCS

## Workload Characteristics
- Daily data volume: 10TB of raw clickstream events (Parquet format)
- Processing window: must complete within 4 hours (midnight to 4am)
- Memory intensive: Spark shuffle operations require large executor heap
- Minimum 96GB RAM for the largest shuffle stage (empirically measured)
- CPU utilization during processing: 85-95% across all cores
- No GPU needed — pure CPU data processing

## Constraints
- Single VM approach (no cluster manager overhead for this team)
- Must finish in 4-hour window — throughput is the primary metric
- The job runs once per night — cost of a larger machine is justified
- Data stays in us-central1 (legal requirement)

## What's Needed
Recommend a single high-memory VM machine type for this nightly batch job.
The instance can be Spot/Preemptible since it restarts if interrupted (checkpointing is enabled).
Prioritize RAM >= 96GB and high core count for parallel Spark tasks.
