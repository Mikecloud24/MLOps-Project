# Production MLOps Checklist

Use this checklist to ensure you've completed all necessary setup steps.

## ☑️ Pre-Deployment Checklist

### AWS Setup
- [ ] EKS cluster created and accessible
- [ ] ECR repository created (`churn-model-api`)
- [ ] S3 bucket created (`churn-model-project-bucket`)
- [ ] IAM role for GitHub Actions (OIDC) configured
- [ ] IAM role for Service Account (IRSA) created
- [ ] AWS CLI configured locally

### GitHub Setup
- [ ] Repository created and code pushed
- [ ] GitHub Secrets configured:
  - [ ] `AWS_ROLE_ARN`
  - [ ] `AWS_ACCESS_KEY_ID`
  - [ ] `AWS_SECRET_ACCESS_KEY`
- [ ] Branch protection rules configured (optional)

### Kubernetes Setup
- [ ] kubectl configured for EKS cluster
- [ ] ArgoCD installed on cluster
- [ ] ArgoCD admin credentials obtained
- [ ] Metrics Server installed (for HPA)

### Code Configuration
- [ ] Updated `k8s/deployment.yaml` with AWS Account ID and Region
- [ ] Updated `argocd/application.yaml` with GitHub repo URL
- [ ] Updated `.github/workflows/*.yaml` with correct AWS region
- [ ] DVC configured with S3 remote

## ☑️ Initial Deployment Checklist

### Data & Model
- [ ] Generated training data (`python generate_data.py`)
- [ ] Trained initial model (`python train.py`)
- [ ] Added data to DVC (`dvc add data/churn_data.csv`)
- [ ] Added model to DVC (`dvc add models/churn_model.pkl`)
- [ ] Pushed to DVC remote (`dvc push`)
- [ ] Committed DVC files to Git

### ArgoCD Deployment
- [ ] Applied ArgoCD application (`kubectl apply -f argocd/application.yaml`)
- [ ] Verified ArgoCD application sync status
- [ ] Checked pods are running (`kubectl get pods -n churn-model`)
- [ ] Verified service is created (`kubectl get svc -n churn-model`)

### Testing
- [ ] Health endpoint responds (`/health`)
- [ ] Readiness endpoint responds (`/readiness`)
- [ ] Prediction endpoint works (`/predict`)
- [ ] Metrics endpoint accessible (`/metrics`)
- [ ] Swagger docs accessible (`/docs`)

## ☑️ CI/CD Pipeline Checklist

### GitHub Actions CI
- [ ] Workflow triggers on push to main/develop
- [ ] Linting passes
- [ ] Security scan completes
- [ ] Docker build succeeds
- [ ] Image pushed to ECR
- [ ] Image vulnerability scan passes
- [ ] SBOM generated

### GitHub Actions CD
- [ ] CD workflow triggers after successful CI
- [ ] Deployment manifest updated with new image tag
- [ ] Changes committed to repository
- [ ] ArgoCD detects and syncs changes

### Model Training Pipeline
- [ ] Manual workflow trigger works
- [ ] Data pulled from DVC
- [ ] Model trains successfully
- [ ] Model uploaded to S3
- [ ] Model committed with DVC

## ☑️ Security Checklist

### Container Security
- [ ] Running as non-root user
- [ ] Security scanning enabled (Trivy)
- [ ] No high/critical vulnerabilities
- [ ] SBOM generated for images

### Kubernetes Security
- [ ] Service account configured
- [ ] IRSA enabled (not using static credentials)
- [ ] Resource limits defined
- [ ] Security context configured
- [ ] Pod Security Standards compliance

### Access Control
- [ ] Namespace isolation configured
- [ ] RBAC policies defined (if needed)
- [ ] Network policies configured (optional)
- [ ] Secrets management strategy defined

## ☑️ Observability Checklist

### Logging
- [ ] Application logs visible in kubectl logs
- [ ] Log level configurable via ConfigMap
- [ ] Structured logging implemented

### Metrics
- [ ] Prometheus metrics endpoint working
- [ ] Key metrics being tracked:
  - [ ] Request count
  - [ ] Request duration
  - [ ] Predictions count
  - [ ] Active requests
  - [ ] Model load time

### Health Checks
- [ ] Liveness probe configured
- [ ] Readiness probe configured
- [ ] Health checks passing

## ☑️ High Availability Checklist

### Scaling
- [ ] HPA configured
- [ ] Resource requests/limits set
- [ ] Min/max replicas configured appropriately
- [ ] HPA metrics working

### Resilience
- [ ] Multiple replicas running
- [ ] Pod disruption budget configured (optional)
- [ ] Graceful shutdown implemented
- [ ] Rolling update strategy configured

## ☑️ Post-Deployment Checklist

### Monitoring
- [ ] Set up Prometheus (optional)
- [ ] Set up Grafana dashboards (optional)
- [ ] Configure alerting (optional)

### Documentation
- [ ] README.md reviewed and updated
- [ ] SETUP.md instructions followed
- [ ] Runbook created for incidents
- [ ] API documentation accessible

### Optimization
- [ ] Load testing performed (optional)
- [ ] Performance baseline established
- [ ] Cost optimization reviewed
- [ ] Auto-scaling tested

### Backup & Recovery
- [ ] DVC remote backup strategy
- [ ] Model versioning strategy
- [ ] Disaster recovery plan
- [ ] Rollback procedure tested

## 📊 Validation Commands

Run these commands to validate your deployment:

```bash
# Check cluster connectivity
kubectl cluster-info

# Check ArgoCD application
kubectl get application churn-model -n argocd

# Check deployment status
kubectl get deployment churn-model-api -n churn-model

# Check pods
kubectl get pods -n churn-model

# Check HPA
kubectl get hpa -n churn-model

# Check service
kubectl get svc churn-model-api -n churn-model

# Test API
export LB_URL=$(kubectl get svc churn-model-api -n churn-model -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$LB_URL/health

# Check logs
kubectl logs -f deployment/churn-model-api -n churn-model --tail=50

# Check metrics
kubectl top pods -n churn-model
```

## 🚨 Common Issues

### Pod Not Starting
- Check logs: `kubectl logs <pod-name> -n churn-model`
- Check events: `kubectl describe pod <pod-name> -n churn-model`
- Verify image exists in ECR
- Check IAM permissions

### ArgoCD Not Syncing
- Check application status: `kubectl describe application churn-model -n argocd`
- Verify repository URL is correct
- Check ArgoCD has access to repository
- Manual sync: `argocd app sync churn-model`

### API Not Responding
- Check LoadBalancer is created
- Verify security groups allow traffic
- Check pod is in Running state
- Verify health checks are passing

### HPA Not Scaling
- Check metrics-server is installed
- Verify resource requests are set
- Check HPA status: `kubectl describe hpa churn-model-api-hpa -n churn-model`

---

**Remember**: This is a production deployment. Always test changes in a development environment first!
