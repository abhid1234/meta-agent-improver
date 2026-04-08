# Task 05 — CI/CD Build Farm

## Scenario
A software company with 150 engineers has outgrown their Jenkins build farm. Builds
are queuing during peak hours (10am-3pm), and engineers are frustrated with wait times.
They're migrating to a GCP-based build farm with ephemeral VMs (one VM per build job).

## Current Setup
- 8 physical build servers, each with 16 cores / 32GB RAM
- Average build time: 8-12 minutes for a full Maven/Gradle compile + test suite
- Peak concurrent builds: 20 simultaneous (they want to support this without queueing)
- Builds are IO-intensive (reading/writing many small files, Docker layer caching)

## Workload Characteristics
- Concurrent builds needed: 20 simultaneous without any queueing
- Build type: JVM compilation (Java/Kotlin) + Docker image builds
- CPU pattern: sustained 100% CPU during compile phase (not bursty — steady high CPU)
- Memory per build: 8-16GB needed (JVM heap + build tools + test containers)
- Local SSD preferred: Docker layer cache and Maven artifact cache benefit from fast I/O
- No GPU needed — pure compilation workload

## Constraints
- Each VM is ephemeral — spun up for one build job, terminated after
- High single-thread performance matters for compilation speed (not just core count)
- vCPU-to-memory ratio: need at least 4GB RAM per vCPU for JVM workloads
- Want to use Spot VMs to reduce cost (build jobs can be retried if preempted)

## What's Needed
Recommend a single machine type for each build VM (all 20 would use the same type).
The machine should be compute-optimized (high CPU frequency) with enough RAM for JVM builds.
Balance build speed (more vCPUs) vs cost (don't over-provision memory).
