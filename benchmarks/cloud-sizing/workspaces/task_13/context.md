# Task 13 — Multi-Region Global Deployment

## Scenario
A media streaming company serves video content and live events to a global audience.
They need to deploy their streaming API and content delivery infrastructure across
three GCP regions (US, EU, APAC) to serve 10,000 RPS per region with low latency.

## Current Setup
- Single region (us-east1) serving 8,000 RPS — latency complaints from EU and APAC users
- Expanding to multi-region: us-central1 (US), europe-west1 (EU), asia-southeast1 (APAC)
- Architecture: GKE regional clusters per region, Cloud CDN for static/cached content
- Global load balancer: Cloud Load Balancing (GCLB) for anycast routing

## Per-Region Workload (each region is identical)
- Regional RPS: 10,000 requests per second
- p99 latency: <100ms for API responses (CDN serves static content separately)
- Workload: media metadata API, playlist generation, DRM token generation
- Memory: 2GB per pod, CPU: 1 vCPU per pod at steady state
- Auto-scaling: 3 node minimum, 12 node maximum per region
- Estimated pods per node: 8 pods (leaving headroom for DaemonSets)

## Architecture Components (for context)
- Cloud CDN: handles 80% of requests (cached video segments, thumbnails)
- GKE Regional Cluster: serves 20% of requests (dynamic API, DRM tokens)
- Cloud Load Balancing: global anycast, routes to nearest healthy region
- Total effective RPS (post-CDN): 2,000 dynamic API calls per region

## Constraints
- Use the same machine type across all 3 regions (operational simplicity)
- Must support regional GKE clusters (3 zones per region)
- Prefer n2 or e2 family (CPU workload, no GPU, no extreme memory needs)
- Budget: each region's cluster should cost <$5,000/month for the GKE nodes

## What's Needed
Recommend a GKE node machine type for all three regional clusters.
The same machine type will be used in us-central1, europe-west1, and asia-southeast1.
Size for the minimum node count (3 per region) with HPA to scale to 12.
