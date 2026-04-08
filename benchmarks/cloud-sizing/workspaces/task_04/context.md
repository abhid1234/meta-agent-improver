# Task 04 — In-Memory Cache Layer

## Scenario
A fintech company runs a high-frequency trading data feed aggregator. Their backend
serves real-time market data to thousands of connected clients. The cache holds the
latest tick data for 500,000 instruments, with frequent reads and writes.

## Current Setup
- Redis 7.x running on a physical server with 256GB RAM
- Migrating to GCP while maintaining Redis (not using Cloud Memorystore — need custom config)
- Current Redis working set: ~40GB (instruments + order books + session data)
- Planning headroom: want 64GB free for growth over 12 months

## Workload Characteristics
- Peak throughput: 50,000 Redis operations per second (70% reads, 30% writes)
- p99 latency target: <1ms for all operations (critical — SLA with trading partners)
- Memory requirement: minimum 128GB RAM (64GB Redis + 64GB OS buffer + headroom)
- Network throughput: ~2Gbps sustained during market hours
- Local SSD preferred for Redis AOF persistence (AOF rewrite every 30 minutes)
- No GPU needed — pure in-memory key-value workload

## Constraints
- Sub-millisecond latency is non-negotiable — NUMA-aware scheduling is required
- Must support high network bandwidth for data feed distribution
- Local SSD (NVMe) for AOF persistence to minimize write latency spikes
- Single VM (Redis is single-threaded per instance; sharding is handled at app layer)

## What's Needed
Recommend a single high-memory VM with local SSD support.
The machine must have >= 128GB RAM and fast NVMe local storage.
Sub-1ms p99 is the primary constraint — memory bandwidth and NUMA topology matter.
