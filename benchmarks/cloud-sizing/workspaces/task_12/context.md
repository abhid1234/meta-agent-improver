# Task 12 — Enterprise Lift-and-Shift Migration

## Scenario
A manufacturing company with 8,000 employees is migrating 100 on-premise servers to GCP.
The servers run a mix of ERP applications (SAP), internal web apps, file servers, and
middleware. This is a lift-and-shift (rehost) — no re-architecture at this stage.

## Current On-Premise Inventory (Application Tier — 60 of 100 servers)
- Hardware: Dell PowerEdge R740, 2x Intel Xeon Gold 6154 (36 cores total)
- RAM: 128GB per server (but average utilization: 30-40%)
- Storage: SAN-attached, migrating to Persistent Disk
- OS: Windows Server 2019 and RHEL 8 (mixed)
- Average CPU utilization: 25% (over-provisioned, typical enterprise)
- Peak CPU utilization: 65% (during batch jobs, end-of-month processing)

## Migration Strategy
- Right-size based on actual utilization (not provisioned capacity)
- Industry rule: GCP VMs at 50-60% average utilization is the target
- On-prem 36 cores at 25% util → effective 9 cores needed → round up to 16 vCPUs (headroom)
- On-prem 128GB at 35% util → effective 45GB needed → round up to 64GB (headroom)
- Use Committed Use Discounts (1-year CUDs) — company has budget approval for 1-year commitment
- Recommend the n2 family (better performance-per-dollar than n1 for this workload type)

## Financial Targets
- Target: 30% TCO reduction vs on-premise (including software licensing savings)
- CUD commitment will cover 100% of base capacity (no on-demand premiums)
- Spot VMs will NOT be used for this workload (ERP requires predictable availability)

## Constraints
- Windows Server licensing: must use BYOL or license included (factor into recommendation)
- Some SAP workloads need NUMA-aware instances (n2 or m2 family)
- General application servers (60 of 100): recommend n2 family for best price-performance
- Migration timeline: 18 months, phased by application group

## What's Needed
Recommend the target GCP machine type for the general application tier (60 servers).
Right-size from the on-prem specs (128GB/36 cores at 25-35% utilization).
Set num_instances=60 (full tier count). Mention CUD strategy in rationale.
