# Task 06 — Microservices Platform on GKE

## Scenario
A logistics SaaS company is migrating their monolith to microservices on GKE. They have
15 services with varied resource profiles (API gateways, business logic services, async
workers). The platform handles shipment tracking and routing for 3,000 enterprise customers.

## Current Setup
- Monolith running on 4x n1-standard-8 VMs (VM-based, no Kubernetes)
- Migration to GKE to enable independent service scaling and deployment velocity
- Services range from lightweight (256MB/0.25 vCPU) to heavy (4GB/2 vCPU)

## Service Breakdown (15 services)
- 3 API gateway services: 512MB / 0.5 vCPU each, 2 replicas
- 6 business logic services: 1GB / 0.5 vCPU each, 2 replicas
- 3 async worker services: 2GB / 1 vCPU each, 1 replica (scale to 3 during peak)
- 2 data aggregator services: 4GB / 2 vCPU each, 2 replicas
- 1 scheduler service: 512MB / 0.25 vCPU, 1 replica

## Workload Characteristics
- Total peak throughput: 500 RPS across all services
- Auto-scaling: HPA configured, scale from 3 nodes to 6 during peak
- Average pod CPU request: 0.75 vCPU, average memory request: 1.5GB
- Total resource requests at steady state: ~18 vCPUs, ~45GB memory
- Node capacity should allow 2x headroom for surge and rolling updates

## Constraints
- Multi-tenant isolation needed (namespace-level, not VM-level)
- Cluster must support auto-scaling between 3 and 6 nodes
- Need to fit DaemonSets: ~0.5 vCPU / 1GB per node for logging and monitoring agents
- Prefer e2 or n2 family for cost-efficiency (no GPU, no memory extremes needed)

## What's Needed
Recommend a GKE node machine type and the baseline node count.
The machine type should allow running 6-8 pods per node comfortably with headroom.
Baseline 3 nodes should handle steady-state load; 6 nodes should handle 2x peak.
