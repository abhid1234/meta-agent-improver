# Task 08 — Highly Available Stateful Service on GKE

## Scenario
A healthcare technology company runs their core patient data platform on PostgreSQL.
This is the system of record for 8 million patient profiles and appointment scheduling
for 500 hospital partners. Downtime is unacceptable — the SLA is 99.99% (52 minutes
downtime per year maximum).

## Current Setup
- PostgreSQL 15 running on a single AWS RDS db.r6g.4xlarge (16 vCPU, 128GB RAM)
- Migrating to GCP using self-managed PostgreSQL on GKE with Patroni for HA
- Decision to self-manage: need custom PostgreSQL extensions not available in Cloud SQL
- Current DB size: 1.2TB, growing at ~50GB/month

## Database Characteristics
- Peak OLTP load: 8,000 transactions per second (read-heavy, 85% reads)
- Read replicas: 2 read replicas for reporting queries (not in scope for this task)
- Working set (hot data): ~80GB fits in memory (PostgreSQL shared_buffers)
- WAL write rate: ~200MB/s during peak
- Patroni requires: primary + 2 standby nodes, each in a different zone

## Workload Characteristics
- Must survive zone failure without data loss (synchronous replication to 1 standby)
- Storage: Regional Persistent Disk (SSD) for automatic zone replication
- I/O: ~15,000 IOPS sustained, 50,000 IOPS peak
- Memory: PostgreSQL shared_buffers = 32GB; OS page cache = 64GB (total ~100GB needed)
- CPU: moderate — 8 vCPUs sufficient at peak

## Constraints
- 99.99% SLA requires multi-zone deployment with automatic failover < 30 seconds
- Must be a regional GKE cluster (3 zones minimum)
- Each PostgreSQL pod must be on a separate zone (pod anti-affinity rules)
- Patroni needs at least 3 nodes (1 primary + 2 standbys) for proper quorum

## What's Needed
Recommend a GKE node machine type for the PostgreSQL/Patroni node pool.
Each of the 3 Patroni pods will be on a separate node in a separate zone.
The machine must support >= 128GB RAM for the PostgreSQL working set + OS buffers.
