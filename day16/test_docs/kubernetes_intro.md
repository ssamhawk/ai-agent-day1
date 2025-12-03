# Kubernetes Introduction

## What is Kubernetes?

Kubernetes (K8s) is an open-source container orchestration platform that automates deploying, scaling, and managing containerized applications. It was originally designed by Google and is now maintained by the Cloud Native Computing Foundation.

## Core Kubernetes Concepts

### Pods
A Pod is the smallest deployable unit in Kubernetes. It represents a single instance of a running process and can contain one or more containers.

### Deployments
A Deployment provides declarative updates for Pods. It manages the desired state of your application, including the number of replicas.

### Services
A Service is an abstraction that defines a logical set of Pods and a policy for accessing them. Types include:
- ClusterIP: Internal cluster access
- NodePort: External access via node IP
- LoadBalancer: Cloud provider load balancer

### Namespaces
Namespaces provide a scope for names and are used to divide cluster resources between multiple users.

## Basic kubectl Commands

```bash
# Get cluster info
kubectl cluster-info

# List pods
kubectl get pods

# Create deployment
kubectl create deployment nginx --image=nginx

# Scale deployment
kubectl scale deployment nginx --replicas=3

# Expose service
kubectl expose deployment nginx --port=80 --type=LoadBalancer

# Delete resources
kubectl delete deployment nginx
```

## Kubernetes Architecture

Kubernetes cluster consists of:
- **Control Plane**: Manages the cluster (API server, scheduler, controller manager)
- **Worker Nodes**: Run containerized applications (kubelet, kube-proxy, container runtime)

## ConfigMaps and Secrets

ConfigMaps store non-confidential configuration data, while Secrets store sensitive information like passwords and API keys.
