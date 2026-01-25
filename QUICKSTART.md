# Quick Start Guide

## 🚀 Get Started in 5 Steps

This guide will get your MLOps project deployed to AWS EKS with ArgoCD in about 30-45 minutes.

### Prerequisites Check
- [ ] AWS account with EKS cluster running
- [ ] `kubectl` installed and configured
- [ ] `aws` CLI installed and configured  
- [ ] GitHub account and repository created
- [ ] ArgoCD installed on your EKS cluster

---

## Step 1: Clone and Setup Repository (5 min)

```bash
# Clone your repository (or initialize if new)
git clone https://github.com/<YOUR_USERNAME>/<YOUR_REPO>
cd <YOUR_REPO>

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: AWS Infrastructure (10 min)

```bash
# Set variables
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create ECR repository
aws ecr create-repository \
  --repository-name churn-model-api \
  --region $AWS_REGION \
  --image-scanning-configuration scanOnPush=true

# Create S3 bucket for DVC
aws s3 mb s3://churn-model-project-bucket --region $AWS_REGION

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket churn-model-project-bucket \
  --versioning-configuration Status=Enabled
```

**Note:** For OIDC setup for GitHub Actions, see [SETUP.md](SETUP.md) for detailed instructions.

---

## Step 3: Configure Project (5 min)

### Update Kubernetes manifests

```bash
# Update deployment.yaml with your AWS details
sed -i "s/<AWS_ACCOUNT_ID>/$AWS_ACCOUNT_ID/g" k8s/deployment.yaml
sed -i "s/<AWS_REGION>/$AWS_REGION/g" k8s/deployment.yaml

# Update kustomization.yaml
sed -i "s/<AWS_ACCOUNT_ID>/$AWS_ACCOUNT_ID/g" k8s/kustomization.yaml
sed -i "s/<AWS_REGION>/$AWS_REGION/g" k8s/kustomization.yaml
```

### Update ArgoCD config

Edit `argocd/application.yaml` and replace:
```yaml
repoURL: https://github.com/<YOUR_USERNAME>/<YOUR_REPO>
```

### Configure GitHub Secrets

Go to GitHub → Your Repo → Settings → Secrets and variables → Actions

Add these secrets:
- `AWS_ROLE_ARN` - Your GitHub Actions IAM role ARN
- `AWS_ACCESS_KEY_ID` - AWS access key (for DVC)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (for DVC)

---

## Step 4: Initialize Data and Model (10 min)

```bash
# Generate training data
python generate_data.py

# Train the model
python train.py

# Setup DVC (if not already configured)
dvc remote add -d s3churnremote s3://churn-model-project-bucket

# Add files to DVC
dvc add data/churn_data.csv
dvc add models/churn_model.pkl

# Configure AWS credentials for DVC
export AWS_ACCESS_KEY_ID=<your-key>
export AWS_SECRET_ACCESS_KEY=<your-secret>

# Push to S3
dvc push

# Commit everything
git add .
git commit -m "Initial setup: data, model, and infrastructure"
git push origin main
```

---

## Step 5: Deploy with ArgoCD (10 min)

```bash
# Apply ArgoCD application
kubectl apply -f argocd/application.yaml

# Watch the deployment
kubectl get pods -n churn-model -w

# Wait for pods to be Running (Ctrl+C to stop watching)

# Get LoadBalancer URL
export LB_URL=$(kubectl get svc churn-model-api -n churn-model \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "Your API is at: http://$LB_URL"
```

---

## ✅ Verify Deployment

```bash
# Test health endpoint
curl http://$LB_URL/health

# Expected output:
# {"status":"healthy","model_loaded":true,"version":"1.0.0"}

# Test prediction
curl -X POST "http://$LB_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "tenure_months": 24,
    "monthly_charges": 79.99,
    "total_charges": 1919.76,
    "num_support_calls": 3
  }'

# Expected output:
# {"churn":1,"churn_probability":0.73,"confidence":"medium","request_id":"..."}

# View API documentation
echo "Swagger docs at: http://$LB_URL/docs"

# Check logs
kubectl logs -f deployment/churn-model-api -n churn-model
```

---

## 🔄 Test CI/CD Pipeline

```bash
# Make a small change to trigger CI/CD
echo "# Test change" >> README.md
git add README.md
git commit -m "test: trigger CI/CD pipeline"
git push origin main
```

**Watch the pipeline:**
1. Go to GitHub → Actions tab
2. You should see "CI - Build and Push" workflow running
3. After CI succeeds, "CD - Update Image Tag" will run
4. ArgoCD will detect the change and deploy automatically

**Monitor ArgoCD:**
```bash
# Check ArgoCD application status
kubectl get application churn-model -n argocd

# Watch pods rolling update
kubectl get pods -n churn-model -w
```

---

## 📊 Monitor Your Application

```bash
# Check HPA status
kubectl get hpa -n churn-model

# View metrics
curl http://$LB_URL/metrics

# View logs with timestamps
kubectl logs -f deployment/churn-model-api -n churn-model --timestamps

# Check resource usage
kubectl top pods -n churn-model

# Check events
kubectl get events -n churn-model --sort-by='.lastTimestamp'
```

---

## 🎯 What's Next?

Now that your base deployment is working:

### Immediate Next Steps
1. **Review the deployment** - Check [CHECKLIST.md](CHECKLIST.md)
2. **Configure monitoring** - Set up Prometheus & Grafana (Phase 2)
3. **Add tests** - Implement unit and integration tests
4. **Review security** - Enable IRSA instead of static credentials

### Advanced Features (Phase 2 & 3)
- Implement blue/green deployments
- Add model registry (MLflow)
- Set up A/B testing
- Configure data drift detection
- Add automated retraining
- Implement canary releases

See [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md) for the complete roadmap.

---

## 🆘 Troubleshooting

### Pods not starting?
```bash
kubectl describe pod <pod-name> -n churn-model
kubectl logs <pod-name> -n churn-model
```

### LoadBalancer not getting external IP?
```bash
# Check service
kubectl describe svc churn-model-api -n churn-model

# Verify AWS Load Balancer Controller is installed
kubectl get deployment -n kube-system aws-load-balancer-controller
```

### ArgoCD not syncing?
```bash
# Check application status
kubectl describe application churn-model -n argocd

# Manual sync
kubectl patch application churn-model -n argocd \
  --type merge -p '{"operation":{"sync":{}}}'
```

### GitHub Actions failing?
- Check secrets are configured correctly
- Verify AWS IAM role has correct permissions
- Check workflow logs in GitHub Actions tab

---

## 📚 Additional Resources

- **[README.md](README.md)** - Complete project documentation
- **[SETUP.md](SETUP.md)** - Detailed setup instructions
- **[CHECKLIST.md](CHECKLIST.md)** - Production readiness checklist
- **[OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)** - What was optimized

---

## 💡 Pro Tips

1. **Cost Optimization**: Start with `t3.medium` nodes and 2 min replicas
2. **Security**: Enable IRSA as soon as possible (remove static credentials)
3. **Monitoring**: Install Prometheus stack early for better observability
4. **Testing**: Always test in a dev environment before production
5. **Backups**: DVC handles model versioning, but set up regular backups

---

**Congratulations! 🎉 Your production-ready MLOps pipeline is now live!**

For questions or issues, refer to the troubleshooting section or check the GitHub Issues.
