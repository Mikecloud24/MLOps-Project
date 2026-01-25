# Setup Instructions

## Prerequisites Checklist

Before deploying this project, ensure you have:

- [ ] AWS Account with appropriate permissions
- [ ] AWS CLI installed and configured
- [ ] kubectl installed
- [ ] An EKS cluster running
- [ ] ArgoCD installed on the EKS cluster
- [ ] GitHub repository created
- [ ] Docker installed (for local testing)

## Step-by-Step Setup

### 1. AWS Infrastructure Setup

#### Create ECR Repository

```bash
# Set your AWS region
export AWS_REGION=us-east-1

# Create ECR repository for Docker images
aws ecr create-repository \
  --repository-name churn-model-api \
  --region $AWS_REGION \
  --image-scanning-configuration scanOnPush=true

# Note the repository URI from the output
```

#### Create S3 Bucket for DVC

```bash
# Create S3 bucket
aws s3 mb s3://churn-model-project-bucket --region $AWS_REGION

# Enable versioning (recommended)
aws s3api put-bucket-versioning \
  --bucket churn-model-project-bucket \
  --versioning-configuration Status=Enabled
```

#### Setup IAM Role for GitHub Actions (OIDC)

```bash
# Follow GitHub's official guide:
# https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services

# The role should have policies for:
# - ECR push/pull
# - EKS access (optional, for direct deployments)
# - STS AssumeRole
```

#### Setup IAM Role for Service Account (IRSA)

```bash
# Create IAM policy for S3 access
cat > s3-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::churn-model-project-bucket",
        "arn:aws:s3:::churn-model-project-bucket/*"
      ]
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name ChurnModelS3Access \
  --policy-document file://s3-policy.json

# Associate IAM OIDC provider with your EKS cluster
eksctl utils associate-iam-oidc-provider \
  --cluster <your-cluster-name> \
  --approve

# Create IAM role for service account
eksctl create iamserviceaccount \
  --name sa-s3-access \
  --namespace churn-model \
  --cluster <your-cluster-name> \
  --attach-policy-arn arn:aws:iam::<AWS_ACCOUNT_ID>:policy/ChurnModelS3Access \
  --approve
```

### 2. Configure GitHub Repository

#### Add GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions

Add the following secrets:

```
Name: AWS_ROLE_ARN
Value: arn:aws:iam::<YOUR_ACCOUNT_ID>:role/<github-actions-role-name>

Name: AWS_ACCESS_KEY_ID
Value: <your-access-key-id>  # For DVC operations

Name: AWS_SECRET_ACCESS_KEY
Value: <your-secret-access-key>  # For DVC operations
```

### 3. Update Project Configuration

#### Update Kubernetes Manifests

Edit [k8s/deployment.yaml](k8s/deployment.yaml):

```bash
# Replace placeholders
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1

# Update deployment.yaml
sed -i "s/<AWS_ACCOUNT_ID>/$AWS_ACCOUNT_ID/g" k8s/deployment.yaml
sed -i "s/<AWS_REGION>/$AWS_REGION/g" k8s/deployment.yaml
```

#### Update ArgoCD Application

Edit [argocd/application.yaml](argocd/application.yaml):

```yaml
spec:
  source:
    repoURL: https://github.com/<YOUR_USERNAME>/<YOUR_REPO>  # Update this
```

#### Update GitHub Actions Workflows

Edit `.github/workflows/ci.yaml` and `.github/workflows/cd.yaml`:

```yaml
env:
  AWS_REGION: us-east-1  # Update if different
  ECR_REPOSITORY: churn-model-api  # Update if different
```

### 4. Install ArgoCD (if not already installed)

```bash
# Create ArgoCD namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port-forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Login at https://localhost:8080
# Username: admin
# Password: <from above command>
```

### 5. Initial Data and Model Setup

```bash
# Generate synthetic data
python generate_data.py

# Train initial model
python train.py

# Initialize DVC (if not already done)
dvc init

# Add data and model to DVC
dvc add data/churn_data.csv
dvc add models/churn_model.pkl

# Configure DVC remote
dvc remote add -d s3churnremote s3://churn-model-project-bucket

# Push to S3
dvc push

# Commit DVC files
git add data/churn_data.csv.dvc models/churn_model.pkl.dvc data/.gitignore models/.gitignore .dvc/config
git commit -m "Add data and model with DVC"
git push
```

### 6. Deploy with ArgoCD

```bash
# Apply ArgoCD application
kubectl apply -f argocd/application.yaml

# Watch deployment
kubectl get pods -n churn-model -w

# Check ArgoCD application status
kubectl get application churn-model -n argocd
```

### 7. Verify Deployment

```bash
# Check pods
kubectl get pods -n churn-model

# Check service
kubectl get svc -n churn-model

# Get LoadBalancer URL
export LB_URL=$(kubectl get svc churn-model-api -n churn-model -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test health endpoint
curl http://$LB_URL/health

# Test prediction endpoint
curl -X POST "http://$LB_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "tenure_months": 24,
    "monthly_charges": 79.99,
    "total_charges": 1919.76,
    "num_support_calls": 3
  }'
```

## Troubleshooting

### Check ArgoCD Application Status

```bash
kubectl describe application churn-model -n argocd
```

### Check Pod Logs

```bash
kubectl logs -f deployment/churn-model-api -n churn-model
```

### Check Events

```bash
kubectl get events -n churn-model --sort-by='.lastTimestamp'
```

### ArgoCD Sync Issues

```bash
# Manual sync
kubectl patch application churn-model -n argocd --type merge -p '{"operation":{"sync":{}}}'

# Or use ArgoCD CLI
argocd app sync churn-model
```

### ECR Login Issues

```bash
# Manual ECR login
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

## Next Steps

After successful deployment:

1. Configure monitoring (Prometheus + Grafana)
2. Set up alerting
3. Configure backup strategy
4. Implement blue/green deployments
5. Add integration tests
6. Set up data drift monitoring

## Support

For issues:
- Check the [README.md](README.md)
- Review GitHub Actions logs
- Check ArgoCD application status
- Review Kubernetes events and logs
