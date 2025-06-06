# Retail Personalization Platform - AWS Infrastructure & API

A complete headless SaaS backend for retail personalization using AWS services. This system provides infrastructure-as-code (Terraform) and backend APIs for product recommendations, customer segmentation, and marketing campaigns.

## 🏗️ Architecture Overview

This platform consists of:

1. **Terraform Infrastructure** - Modular AWS services provisioning
2. **Backend API** - Headless SaaS control layer (Node.js/Python)
3. **Documentation** - Complete setup and usage guides

### AWS Services Used:
- **Amazon S3** - Dataset storage and model artifacts
- **Amazon DynamoDB** - Real-time recommendation cache
- **AWS AppSync** - GraphQL API for recommendations
- **Amazon Personalize** - ML-powered recommendation engine
- **Amazon Athena** - Data analytics and querying
- **Amazon ECS on Fargate** - Containerized microservices
- **AWS Step Functions** - Workflow orchestration
- **Amazon EventBridge** - Event-driven automation
- **Amazon Pinpoint** - Marketing campaign delivery
- **CloudWatch** - Monitoring and logging

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Terraform >= 1.0
- Node.js >= 16 or Python >= 3.8
- Docker (for ECS deployment)

### 1. Deploy Infrastructure
```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

### 2. Deploy Backend API
```bash
cd backend/
cp .env.example .env
# Edit .env with Terraform outputs
npm install  # or pip install -r requirements.txt
npm start    # or python main.py
```

### 3. Test the System
```bash
# Upload sample dataset
curl -X POST http://localhost:3000/upload \
  -H "x-api-key: your-api-key" \
  -H "x-tenant-id: tenant1" \
  -F "file=@sample_interactions.csv"

# Train model
curl -X POST http://localhost:3000/train \
  -H "x-api-key: your-api-key" \
  -H "x-tenant-id: tenant1"

# Get recommendations
curl "http://localhost:3000/recommendations?user_id=123" \
  -H "x-api-key: your-api-key" \
  -H "x-tenant-id: tenant1"
```

## 📁 Project Structure

```
retail-personalization/
├── terraform/                 # Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars
│   └── modules/
│       ├── s3/
│       ├── dynamodb/
│       ├── personalize/
│       ├── appsync/
│       ├── stepfunctions/
│       ├── eventbridge/
│       ├── pinpoint/
│       ├── ecs_fargate/
│       ├── athena/
│       ├── iam/
│       └── monitoring/
├── backend/                   # Headless SaaS API
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── config/
│   └── requirements.txt
├── docs/                      # Documentation
│   ├── API.md
│   ├── playbooks/
│   └── getting-started.md
└── scripts/                   # Deployment scripts
    ├── deploy.sh
    └── test-api.sh
```

## 🔐 Security & Multi-Tenancy

- **API Key Authentication** - Secure access control
- **Tenant Isolation** - Resource separation by tenant ID
- **IAM Roles** - Least privilege access
- **Encryption** - Data at rest and in transit
- **VPC Security** - Network isolation

## 📊 Monitoring & Observability

- CloudWatch dashboards for system health
- Custom metrics for recommendation performance
- Automated alerts for failures
- Cost monitoring and budgets

## 🤝 Contributing

See individual module READMEs for detailed documentation.

## 📄 License

MIT License - see LICENSE file for details. 