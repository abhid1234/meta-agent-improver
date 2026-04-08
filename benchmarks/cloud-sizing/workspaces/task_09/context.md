# Task 09 — Low-Latency Gaming Backend on GKE

## Scenario
A mobile gaming company runs multiplayer match servers for a real-time battle royale
game. Each match server handles one game session (up to 100 players). The backend
orchestrates server allocation, matchmaking, and player session management.

## Current Setup
- Running on bare metal colocation (high cost, long procurement cycles)
- Moving to GCP for elasticity (player counts spike 5-10x on weekends and events)
- Using Agones (GKE-based game server framework) for server allocation

## Workload Characteristics
- Concurrent players at peak: 10,000 simultaneous (across all servers)
- Match server specs: 1 vCPU + 2GB RAM per server (100 players per match = 100 servers peak)
- Game server tick rate: 60 Hz (requires consistent CPU, no interference from noisy neighbors)
- Network: UDP-heavy (game state sync), high packet rate (~50K packets/second per node)
- p99 server-side latency: <50ms for game tick processing
- Session management layer: separate from game servers, handles matchmaking + lobby

## Scaling Pattern
- Baseline: 20 nodes handling 200 concurrent matches (steady state overnight)
- Peak: Scale to 100+ nodes during major events (Spot VMs for burst capacity)
- Scale-up must happen in <5 minutes (players abandon lobby after 5 min queue)
- Agones pre-warms 10% extra servers to minimize cold-start

## Constraints
- CPU isolation is critical: game servers are latency-sensitive, not throughput-sensitive
- c3 or c2 series preferred: higher GHz for consistent game tick processing
- Spot VMs for 40-60% of capacity during peak (Agones handles graceful eviction)
- 4 baseline nodes minimum; can scale to 20+ with Spot during events

## What's Needed
Recommend a GKE node machine type for the Agones game server node pool.
Each node should fit 15-20 game server pods (1 vCPU / 2GB each) with DaemonSet overhead.
Latency consistency (not raw throughput) is the primary metric — choose compute-optimized.
