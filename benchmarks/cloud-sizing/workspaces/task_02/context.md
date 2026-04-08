# Task 02 — ML Inference API

## Scenario
A computer vision company runs a real-time object detection API used by retail partners
for inventory management. The model is a fine-tuned YOLOv8 (medium) that processes
images and returns bounding boxes with class labels.

## Current Setup
- Running on a single on-premise server with an NVIDIA RTX 3080
- Moving to GCP to improve reliability and enable global scale
- Average batch size: 1-4 images per request
- Model size: ~52MB, fits comfortably in 8GB GPU VRAM

## Workload Characteristics
- Peak traffic: 200 requests per second (each request is 1-4 images)
- p99 latency target: 100ms end-to-end (model inference is ~20ms on T4)
- GPU memory required: minimum 8GB VRAM (16GB preferred for safety margin)
- CPU is used only for pre/post-processing (relatively light)
- Traffic peaks during business hours across US timezones

## Constraints
- GPU is mandatory — CPU inference is 10x too slow to meet SLA
- Must use NVIDIA GPU (CUDA-based PyTorch model)
- Auto-scaling group will handle traffic spikes — size for steady state
- Cost efficiency matters — avoid over-provisioning GPU memory

## What's Needed
Recommend a single GPU VM machine type for the inference tier.
The recommended type will be used in a managed instance group behind a load balancer.
Focus on the right GPU SKU and the appropriate CPU/memory configuration to pair with it.
