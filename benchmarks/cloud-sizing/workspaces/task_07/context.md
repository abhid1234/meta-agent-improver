# Task 07 — GPU Training Cluster on GKE

## Scenario
An AI research team at a mid-size tech company is building their own LLM fine-tuning
infrastructure. They need to run distributed training jobs for fine-tuning 7B and 13B
parameter language models on proprietary data. Training runs typically take 6-24 hours.

## Current Setup
- Currently renting time on a third-party GPU cloud (expensive, no control)
- Moving to GCP to build persistent training infrastructure
- Using PyTorch with FSDP (Fully Sharded Data Parallelism) for multi-GPU training

## Training Requirements
- Model sizes: 7B parameters (primary), 13B parameters (occasional)
- 7B training: requires 4x 80GB GPUs (A100 or H100 equivalent) for FSDP
- 13B training: requires 8x 80GB GPUs (needs 2 nodes)
- GPU topology: need NVLink or fast GPU interconnect for FSDP communication
- GPU memory: minimum 80GB per GPU (bfloat16 + optimizer states + activations)
- High-bandwidth networking: 400Gbps+ between nodes for multi-node training

## Workload Characteristics
- Training jobs: 2-3 concurrent jobs per day on average
- Each job: 4-8 GPUs, 6-24 hours duration
- Idle time between jobs: 1-3 hours (GPUs fully idle)
- Storage: training checkpoints written to GCS every 30 minutes
- CPU per GPU node: at least 12 vCPUs per GPU (for data loading)

## Constraints
- Must support both 4-GPU (single-node) and 8-GPU (two-node) configurations
- Consider using Spot for 60-70% cost reduction (FSDP supports checkpointing)
- GKE with GPU node pool is the target platform
- us-central1-a or us-central1-b for A100 availability

## What's Needed
Recommend a GKE node machine type for the GPU training node pool.
The machine should support 4x or 8x A100 80GB GPUs per node (or the GCP equivalent).
Specify whether to use a2-ultragpu or a3 series and why.
