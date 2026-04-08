# Task 11 — Startup Budget-Constrained Web Stack

## Scenario
A two-person startup is launching a B2C productivity app. They have $500/month total
cloud budget (everything: compute, database, cache, networking, monitoring). They need
to ship fast, keep costs minimal, and only scale when revenue justifies it.

## Current Setup
- Running on a $20/month DigitalOcean Droplet (not scalable enough, poor GCP integration)
- Migrating to GCP to access ecosystem tools (Vertex AI, BigQuery free tier, Firebase)
- Stack: Node.js/Express API, PostgreSQL database, Redis session cache

## Proposed Architecture (must fit in $500/month total)
- Web/API tier: GCE VM (this task) — budget: ~$80-100/month
- Database: Cloud SQL for PostgreSQL (Basic tier) — ~$50/month
- Cache: Cloud Memorystore for Redis (Basic, 1GB) — ~$30/month
- Networking/DNS/Monitoring: ~$20/month
- Remaining for compute: $80-100/month max

## Workload Characteristics
- Current traffic: 5-10 RPS (launch traffic, not yet at scale)
- Expected 90-day peak: 50 RPS (after Product Hunt launch)
- p99 latency: <500ms acceptable (startup user base is forgiving)
- Memory needed: 2GB minimum for Node.js process + OS
- Disk: 20GB standard persistent disk is sufficient

## Constraints
- Hard budget cap: $100/month for the compute VM
- e2-small (~$14/month) or e2-medium (~$28/month) are within budget
- n1 or n2 standard instances are too expensive for this budget tier
- Must be in us-central1 (lowest GCP pricing region)
- No managed services that add cost — keep it simple with a single VM

## What's Needed
Recommend the most cost-effective GCP machine type for the web/API tier.
The machine must cost less than $100/month and handle 50 RPS for the Node.js app.
Recommend num_instances=1 (single VM, no HA at this budget level).
