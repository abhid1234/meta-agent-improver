# Task 15 — HIPAA-Compliant Healthcare Workload

## Scenario
A digital health company processes Protected Health Information (PHI) for insurance
claims processing and prior authorization. They must comply with HIPAA and have signed
a Business Associate Agreement (BAA) with Google. Data residency is restricted to
us-central1 — no data can leave this region under any circumstance.

## Regulatory Requirements
- HIPAA compliance: PHI must be encrypted at rest and in transit
- Data residency: us-central1 only (Iowa) — no cross-region replication of PHI
- CMEK (Customer-Managed Encryption Keys): required for PHI data at rest
- VPC Service Controls: perimeter around all GCP services handling PHI
- Audit logging: Cloud Audit Logs for all data access (mandatory for HIPAA)
- Private Google Access: all GCP service calls must stay within VPC

## Application Profile
- Service: RESTful API for insurance claims processing
- Traffic: 500 RPS peak, 100 RPS steady state
- Processing: CPU-intensive claim validation and eligibility checks
- Memory: 8GB per instance (claim parsing + validation rules loaded in memory)
- Database: Cloud SQL for PostgreSQL (CMEK encrypted, private IP only)
- No GPU needed — pure CPU workload

## Security Architecture
- VPC-SC perimeter: compute, storage, Cloud SQL, KMS
- Private service access: no public IP addresses on any VM
- OS Config agent: mandatory for compliance patch management
- Shielded VMs: required (Secure Boot, vTPM, Integrity Monitoring)
- No external internet access from application VMs

## Constraints
- Must use regional resources only in us-central1 — no multi-region services
- Shielded VM is mandatory (adds slight performance overhead)
- 3 instances minimum for HA (Cloud Load Balancing with health checks)
- Machine type must be available in us-central1 with CMEK support (all n2 support CMEK)
- Prefer n2 family for predictable performance (no bursting that could affect latency)

## What's Needed
Recommend a single VM machine type for the claims processing application tier.
The machine must support Shielded VM, CMEK, and be available in us-central1.
Set num_instances=3 (minimum HA configuration). Address HIPAA requirements in rationale.
