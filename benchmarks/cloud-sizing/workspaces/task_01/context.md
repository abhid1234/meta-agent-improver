# Task 01 — Low-Traffic Web Application

## Scenario
A B2B SaaS startup is launching their first product: a project management web app with a Django
backend and React frontend. They expect low but growing traffic over the next 6 months.

## Current Setup
- Running locally on a developer's machine
- Moving to GCP for the first time
- No existing cloud infrastructure

## Workload Characteristics
- Peak traffic: 50 requests per second
- p99 latency target: 200ms (mostly CRUD operations, simple SQL queries)
- Database is managed separately via Cloud SQL (not in scope for this sizing)
- Storage: 2GB of static assets in Cloud Storage (not in scope)
- CPU-only workload — no GPU or accelerator needed
- Traffic is bursty but predictable (US business hours)

## Constraints
- Team has no GCP expertise — prefer simple, well-documented instance types
- Budget-conscious but not constrained — optimize for cost-efficiency
- Need at least 2 vCPUs to handle concurrent requests during peak
- Django app is single-threaded per worker; they'll run 4 gunicorn workers

## What's Needed
Recommend a single VM machine type for the web/application tier.
A load balancer and autoscaling can be added later, but for MVP a single VM is fine.
The machine should comfortably handle 50 RPS with headroom for growth.
