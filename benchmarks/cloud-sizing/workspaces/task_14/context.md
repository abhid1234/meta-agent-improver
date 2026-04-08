# Task 14 — Cost Optimization Review

## Scenario
A Series B startup has accumulated significant cloud waste after rapid growth. Their
GCP bill is $50,000/month — up from $12,000/month 18 months ago. A new VP of Engineering
has mandated a 40% cost reduction without impacting availability or performance.

## Current Infrastructure (over-provisioned)
- Application tier: 20x n2-standard-32 VMs (32 vCPU / 128GB each)
  → Running at: 12% avg CPU, 25% avg memory utilization
  → Monthly cost: ~$38,000 (on-demand pricing)
- Batch processing tier: 5x n2-standard-32 VMs (same spec)
  → Running at: 70% CPU during batch windows (6pm-2am), 5% otherwise
  → Monthly cost: ~$9,500 (on-demand pricing)
- Database tier: Cloud SQL (out of scope — already optimized)
- Total: ~$50,000/month

## Usage Analysis
- App tier peak CPU: 35% (n2-standard-32 is massively over-provisioned)
- App tier effective need: 4 vCPUs per VM at steady state (12% of 32 = 3.8 vCPUs)
- App tier memory need: 32GB per VM (25% of 128GB = 32GB)
- Batch tier: should use Spot/Preemptible (fully interruptible, retryable jobs)

## Optimization Recommendations (guidance for the agent)
- Application tier: Downsize from n2-standard-32 → n2-standard-8 (saves ~75% per VM)
- Keep 20 instances (same count) — headroom for traffic spikes
- Switch batch tier to Spot VMs (n2-standard-8 spot = 70% cheaper)
- Apply 1-year Committed Use Discounts on app tier (25-55% savings on top)

## Constraints
- Cannot reduce availability — must maintain 20 application instances (HA requirement)
- Batch jobs can use Spot (they have retry logic and checkpoint support)
- No architectural changes — same VM count, different machine types
- Must stay in us-central1 for data residency

## What's Needed
Recommend the right-sized machine type for the APPLICATION tier (20 instances).
Set num_instances=20. The batch tier recommendation goes in the rationale.
Expected monthly savings should be mentioned — target is $20K+ reduction.
