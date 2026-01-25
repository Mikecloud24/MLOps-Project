# Churn Prediction MLOps Project

A production-ready MLOps project for customer churn prediction using FastAPI, Kubernetes (EKS), ArgoCD, and GitHub Actions.

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   GitHub    │─────▶│ GitHub       │─────▶│   AWS ECR   │
│ Repository  │      │ Actions CI   │      │   (Images)  │
└─────────────┘      └──────────────┘      └─────────────┘
                              │                     │
                              ▼                     ▼
                     ┌──────────────┐      ┌─────────────┐
                     │ GitHub       │      │   ArgoCD    │
                     │ Actions CD   │─────▶│ (GitOps)    │
                     └──────────────┘      └─────────────┘
                                                   │
                                                   ▼
                                          ┌─────────────┐
                                          │  EKS Cluster│
                                          │  (K8s Apps) │
                                          └─────────────┘
```

## 📋 Features

- ✅ **FastAPI** inference server with Prometheus metrics
- ✅ **Docker** multi-stage builds for optimized images
- ✅ **Kubernetes** manifests with HPA, resource limits, and probes
- ✅ **GitHub Actions** CI/CD pipelines
- ✅ **ArgoCD** GitOps deployment
- ✅ **DVC** for data and model versioning
- ✅ **Security** scanning with Trivy
- ✅ **Observability** with logging and metrics
- ✅ **AWS EKS** ready deployment

## 🚀 Quick Start

### Prerequisites

- AWS Account with EKS cluster
- kubectl configured for your EKS cluster
- ArgoCD installed in your cluster
- GitHub repository
- AWS ECR repository created

### 1. Setup AWS Infrastructure

```bash
# Create ECR repository
aws ecr create-repository --repository-name churn-model-api --region us-east-1

# Create S3 bucket for DVC
aws s3 mb s3://churn-model-project-bucket

# Create IAM role for GitHub Actions (OIDC)
# Follow: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
```

### 2. Configure GitHub Secrets

Add these secrets to your GitHub repository:

```
AWS_ROLE_ARN=arn:aws:iam::YOUR_ACCOUNT:role/github-actions-role
AWS_ACCESS_KEY_ID=your_access_key  # For DVC
AWS_SECRET_ACCESS_KEY=your_secret_key  # For DVC
```

### 3. Update Manifests

Replace placeholders in `k8s/deployment.yaml`:
- `<AWS_ACCOUNT_ID>` with your AWS account ID
- `<AWS_REGION>` with your region (e.g., us-east-1)

Update `argocd/application.yaml`:
- `repoURL` with your GitHub repository URL

### 4. Deploy ArgoCD Application

```bash
kubectl apply -f argocd/application.yaml
```

### 5. Initial Model Training

```bash
# Generate data
python generate_data.py

# Train model
python train.py

# Push with DVC
dvc add models/churn_model.pkl
dvc push

# Commit and push
git add .
git commit -m "Initial model"
git push
```

## 🔄 CI/CD Workflow

### Continuous Integration (CI)

Triggered on push to `main` or `develop`:

1. **Lint & Test** - Code quality checks
2. **Security Scan** - Trivy filesystem scan
3. **Build** - Docker image build
4. **Push** - Push to AWS ECR
5. **Image Scan** - Trivy image vulnerability scan
6. **SBOM** - Generate Software Bill of Materials

### Continuous Deployment (CD)

Triggered after successful CI:

1. **Update Manifest** - Update image tag in `k8s/deployment.yaml`
2. **Commit** - Push changes to repository
3. **ArgoCD Sync** - ArgoCD detects changes and deploys

## 📊 API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /readiness` - Readiness check
- `GET /metrics` - Prometheus metrics
- `POST /predict` - Make churn prediction
- `GET /docs` - Swagger documentation

### Example Request

```bash
curl -X POST "http://your-loadbalancer/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "tenure_months": 24,
    "monthly_charges": 79.99,
    "total_charges": 1919.76,
    "num_support_calls": 3
  }'
```

### Example Response

```json
{
  "churn": 1,
  "churn_probability": 0.73,
  "confidence": "medium",
  "request_id": "1706131200-123456"
}
```

## 🛠️ Local Development

### Run API Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Train model
python train.py

# Run API
python api.py

# Test API
curl http://localhost:8000/health
```

### Build Docker Image

```bash
docker build -t churn-model-api:local .
docker run -p 8000:8000 churn-model-api:local
```

### Test Kubernetes Manifests

```bash
# Validate manifests
kubectl apply --dry-run=client -f k8s/

# Deploy to local kind cluster
kind create cluster
kubectl apply -f k8s/
```

## 📦 Project Structure

```
.
├── .github/
│   └── workflows/
│       ├── ci.yaml          # CI pipeline
│       ├── cd.yaml          # CD pipeline
│       └── train.yaml       # Model training pipeline
├── argocd/
│   └── application.yaml     # ArgoCD application config
├── data/
│   ├── churn_data.csv       # Training data (DVC tracked)
│   └── churn_data.csv.dvc   # DVC pointer
├── k8s/
│   ├── configmap.yaml       # Configuration
│   ├── deployment.yaml      # Main deployment
│   ├── hpa.yaml            # Horizontal Pod Autoscaler
│   ├── service.yaml        # LoadBalancer service
│   ├── serviceaccount.yaml # Service account & secrets
│   └── kustomization.yaml  # Kustomize config
├── models/
│   └── churn_model.pkl     # Trained model (DVC tracked)
├── api.py                  # FastAPI application
├── train.py               # Model training script
├── generate_data.py       # Synthetic data generator
├── Dockerfile            # Multi-stage Docker build
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🔐 Security Best Practices

- ✅ Non-root container user
- ✅ Read-only root filesystem (where applicable)
- ✅ Resource limits enforced
- ✅ Security scanning with Trivy
- ✅ IRSA for AWS access (recommended over static credentials)
- ✅ Network policies (add as needed)
- ✅ Pod Security Standards compliance

## 📈 Monitoring

### Prometheus Metrics

The API exposes Prometheus metrics at `/metrics`:

- `api_requests_total` - Total requests by endpoint
- `api_request_duration_seconds` - Request latency
- `predictions_total` - Total predictions made
- `model_load_time_seconds` - Model load time
- `active_requests` - Current active requests

### Logs

Structured JSON logs are written to stdout:

```bash
kubectl logs -f deployment/churn-model-api -n churn-model
```

## 🔧 Configuration

### Environment Variables

- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING, ERROR)
- `MODEL_PATH` - Path to model file
- `AWS_DEFAULT_REGION` - AWS region for S3 access

### Kubernetes ConfigMap

Edit `k8s/configmap.yaml` to change configuration values.

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## 📝 Next Steps (Phase 2 & 3)

- [ ] Add unit and integration tests
- [ ] Implement blue/green deployments
- [ ] Set up Grafana dashboards
- [ ] Add model registry (MLflow)
- [ ] Implement A/B testing
- [ ] Add data drift detection
- [ ] Set up automated retraining
- [ ] Add canary deployments
- [ ] Implement NetworkPolicies
- [ ] Add distributed tracing

## 📄 License

See [LICENSE](LICENSE) file for details.

## 👥 Support

For issues and questions, please open a GitHub issue.