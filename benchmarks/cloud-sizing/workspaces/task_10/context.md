# Task 10 — High-Throughput Log Pipeline on GKE

## Scenario
A cybersecurity company collects security logs from 5,000 enterprise customers.
The pipeline ingests events, enriches them with threat intelligence, and indexes
them for real-time search. The architecture uses Kafka for ingestion buffering and
Elasticsearch for indexing and search.

## Current Setup
- Kafka: 6 brokers on n1-standard-16 VMs (16 vCPU, 60GB RAM each)
- Elasticsearch: 12 data nodes on n1-standard-32 VMs (32 vCPU, 120GB RAM each)
- Both managed on bare GCE VMs, migrating to GKE for operational simplicity

## Kafka Tier Requirements (PRIMARY — what to size)
- Throughput: 1,000,000 events per second ingested
- Average event size: 1KB → ~1GB/s data throughput
- Kafka replication factor: 3 (3 replicas per partition)
- Network throughput per broker: ~500MB/s (3 replicas × 1GB/s ÷ 6 brokers)
- Memory: Kafka page cache needs 32GB per broker minimum (OS-managed, not JVM heap)
- JVM heap: 8GB per broker
- Total memory per broker: 48GB minimum
- Storage: Local SSD for write-ahead log (WAL) — Kafka is extremely I/O latency sensitive
- Retention: 24 hours of raw data per topic (5TB total across cluster)

## Elasticsearch Tier Requirements (for context, not the primary ask)
- Indexing rate: 1M events/second after Kafka consumer processing
- 90-day retention of processed events
- Search latency: <2 seconds for typical queries

## Constraints
- Kafka brokers must use local SSD (NVMe) — network-attached storage has too much latency
- Memory-optimized or balanced instances for Kafka (page cache is everything)
- GKE StatefulSets for both Kafka and Elasticsearch
- Number of Kafka broker pods: keep at 6 (same as current topology)

## What's Needed
Recommend a GKE node machine type for the Kafka broker StatefulSet.
Focus on the Kafka tier — 6 brokers, each needing 48GB RAM and local NVMe SSD.
The machine type must support local SSD attachment for Kafka WAL storage.
