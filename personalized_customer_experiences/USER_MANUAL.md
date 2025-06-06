# Retail Personalization Platform - User Manual

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Data Management](#data-management)
4. [API Usage](#api-usage)
5. [ML Workflow Operations](#ml-workflow-operations)
6. [Marketing Campaigns](#marketing-campaigns)
7. [Analytics & Monitoring](#analytics--monitoring)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Overview

The Retail Personalization Platform is a comprehensive AWS-based solution that provides:
- **Real-time recommendation engine** powered by Amazon Personalize
- **GraphQL API** for seamless integration with applications
- **Automated ML workflows** for model training and deployment
- **Marketing campaign management** through Amazon Pinpoint
- **Analytics capabilities** with Amazon Athena
- **Comprehensive monitoring** via CloudWatch

### Architecture Components
- **Data Layer**: S3 buckets for data storage, DynamoDB for real-time cache
- **API Layer**: AppSync GraphQL API with authentication
- **ML Layer**: Step Functions orchestrating Amazon Personalize workflows
- **Application Layer**: ECS Fargate for containerized services
- **Analytics Layer**: Athena for data analysis and reporting
- **Monitoring Layer**: CloudWatch dashboards, alarms, and logging

## Getting Started

### Prerequisites
- AWS CLI configured with appropriate permissions
- Access to the deployed infrastructure outputs
- Understanding of GraphQL for API interactions

### Environment Information
```bash
# Your deployment details
Project: retail-personalization
Tenant: acme-corp
Environment: dev
Region: us-east-1
```

### Key Resources
- **S3 Data Bucket**: `retail-personalization-acme-corp-dev-data`
- **DynamoDB Table**: `retail-personalization-acme-corp-dev-recommendations`
- **AppSync API**: `https://4wwv3n7ht5fhpigvf4c2xigtma.appsync-api.us-east-1.amazonaws.com/graphql`
- **Step Function**: `retail-personalization-acme-corp-dev-ml-workflow`
- **Pinpoint App**: `c2cb7bf620d149feb9338c4c0ba0b943`

## Data Management

### 1. Data Upload to S3

#### User Interaction Data
Upload user interaction data to trigger ML workflows:

```bash
# Upload interaction data
aws s3 cp interactions.csv s3://retail-personalization-acme-corp-dev-data/datasets/interactions.csv

# Upload user data
aws s3 cp users.csv s3://retail-personalization-acme-corp-dev-data/datasets/users.csv

# Upload item data
aws s3 cp items.csv s3://retail-personalization-acme-corp-dev-data/datasets/items.csv
```

#### Data Format Requirements

**Interactions Data (interactions.csv)**:
```csv
USER_ID,ITEM_ID,EVENT_TYPE,TIMESTAMP,EVENT_VALUE
user123,item456,purchase,1640995200,29.99
user123,item789,view,1640995300,
user456,item123,add_to_cart,1640995400,15.50
```

**Users Data (users.csv)**:
```csv
USER_ID,AGE,GENDER,MEMBERSHIP_TYPE
user123,25,M,premium
user456,34,F,standard
```

**Items Data (items.csv)**:
```csv
ITEM_ID,CATEGORY,PRICE,BRAND
item123,electronics,299.99,TechBrand
item456,clothing,49.99,FashionCorp
```

### 2. Automated Data Processing

When data is uploaded to S3, the system automatically:
1. **Triggers EventBridge rule** for S3 object creation
2. **Starts Step Function workflow** for ML processing
3. **Creates Personalize datasets** and import jobs
4. **Trains ML models** using the uploaded data
5. **Deploys campaigns** for real-time recommendations

## API Usage

### 1. Authentication

Obtain your API key from Terraform outputs:
```bash
terraform output appsync_api_key
```

### 2. GraphQL Operations

#### Get Recommendations for a User
```graphql
query GetRecommendations($userId: String!, $limit: Int) {
  getRecommendations(userId: $userId, limit: $limit) {
    items {
      userId
      itemId
      score
      category
      timestamp
    }
    nextToken
  }
}
```

**Variables:**
```json
{
  "userId": "user123",
  "limit": 10
}
```

#### Store New Recommendation
```graphql
mutation PutRecommendation($input: RecommendationInput!) {
  putRecommendation(input: $input) {
    userId
    itemId
    score
    category
    timestamp
  }
}
```

**Variables:**
```json
{
  "input": {
    "userId": "user123",
    "itemId": "item456",
    "score": 0.95,
    "category": "electronics"
  }
}
```

#### Get Recommendations by Category
```graphql
query GetRecommendationsByCategory($category: String!, $limit: Int) {
  getRecommendationsByCategory(category: $category, limit: $limit) {
    items {
      userId
      itemId
      score
      category
      timestamp
    }
    nextToken
  }
}
```

### 3. API Integration Examples

#### JavaScript/Node.js
```javascript
const AWS = require('aws-sdk');
const AWSAppSyncClient = require('aws-appsync').default;

const client = new AWSAppSyncClient({
  url: 'https://4wwv3n7ht5fhpigvf4c2xigtma.appsync-api.us-east-1.amazonaws.com/graphql',
  region: 'us-east-1',
  auth: {
    type: 'API_KEY',
    apiKey: 'YOUR_API_KEY'
  }
});

// Get recommendations
const getRecommendations = async (userId) => {
  const query = gql`
    query GetRecommendations($userId: String!) {
      getRecommendations(userId: $userId) {
        items {
          itemId
          score
          category
        }
      }
    }
  `;
  
  const result = await client.query({
    query,
    variables: { userId }
  });
  
  return result.data.getRecommendations.items;
};
```

#### Python
```python
import boto3
import requests
import json

def get_recommendations(user_id, api_key):
    url = "https://4wwv3n7ht5fhpigvf4c2xigtma.appsync-api.us-east-1.amazonaws.com/graphql"
    
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key
    }
    
    query = """
    query GetRecommendations($userId: String!) {
      getRecommendations(userId: $userId) {
        items {
          itemId
          score
          category
        }
      }
    }
    """
    
    payload = {
        'query': query,
        'variables': {'userId': user_id}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
```

## ML Workflow Operations

### 1. Manual Workflow Execution

Trigger ML workflows manually using Step Functions:

```bash
# Start ML workflow
aws stepfunctions start-execution \
  --state-machine-arn "arn:aws:states:us-east-1:545009852657:stateMachine:retail-personalization-acme-corp-dev-ml-workflow" \
  --input '{
    "datasetArn": "/datasets/interactions",
    "dataLocation": "s3://retail-personalization-acme-corp-dev-data/datasets/interactions.csv",
    "jobName": "manual-import-job",
    "solutionName": "manual-solution",
    "campaignName": "manual-campaign",
    "datasetGroupArn": "",
    "personalizeRoleArn": "arn:aws:iam::545009852657:role/PersonalizeServiceRole-retail-personalization-acme-corp"
  }'
```

### 2. Monitoring Workflow Progress

```bash
# List executions
aws stepfunctions list-executions \
  --state-machine-arn "arn:aws:states:us-east-1:545009852657:stateMachine:retail-personalization-acme-corp-dev-ml-workflow"

# Get execution details
aws stepfunctions describe-execution \
  --execution-arn "EXECUTION_ARN"
```

### 3. Scheduled Retraining

The system automatically retrains models:
- **Daily at 2 AM UTC** via EventBridge scheduled rule
- **On new data upload** via S3 event triggers
- **Manual trigger** via Step Functions console

## Marketing Campaigns

### 1. Pinpoint Integration

The platform includes Amazon Pinpoint for marketing campaigns:

```bash
# Get Pinpoint app details
aws pinpoint get-app \
  --application-id "c2cb7bf620d149feb9338c4c0ba0b943"
```

### 2. Campaign Management

#### Create User Segments
```bash
# Create a segment for high-value users
aws pinpoint create-segment \
  --application-id "c2cb7bf620d149feb9338c4c0ba0b943" \
  --write-segment-request '{
    "Name": "HighValueUsers",
    "Dimensions": {
      "UserAttributes": {
        "PurchaseValue": {
          "AttributeType": "INCLUSIVE",
          "Values": ["100", "1000"]
        }
      }
    }
  }'
```

#### Send Targeted Campaigns
```bash
# Create a campaign
aws pinpoint create-campaign \
  --application-id "c2cb7bf620d149feb9338c4c0ba0b943" \
  --write-campaign-request '{
    "Name": "PersonalizedRecommendations",
    "SegmentId": "SEGMENT_ID",
    "MessageConfiguration": {
      "DefaultMessage": {
        "Body": "Check out these personalized recommendations just for you!"
      }
    },
    "Schedule": {
      "StartTime": "2024-01-01T10:00:00Z"
    }
  }'
```

## Analytics & Monitoring

### 1. CloudWatch Dashboard

Access your monitoring dashboard:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=retail-personalization-acme-corp-dev
```

**Key Metrics Monitored:**
- AppSync API errors and latency
- DynamoDB read/write capacity and throttling
- Step Functions execution success/failure rates
- Lambda function duration and errors

### 2. Athena Analytics

#### Query User Interactions
```sql
-- Analyze user interaction patterns
SELECT 
    user_id,
    COUNT(*) as interaction_count,
    COUNT(DISTINCT item_id) as unique_items,
    AVG(event_value) as avg_event_value
FROM interactions 
WHERE event_type = 'purchase'
GROUP BY user_id
ORDER BY interaction_count DESC
LIMIT 100;
```

#### Query Item Popularity
```sql
-- Analyze item popularity and engagement
SELECT 
    item_id,
    COUNT(*) as interaction_count,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(event_value) as avg_event_value
FROM interactions 
WHERE event_type IN ('view', 'purchase', 'add_to_cart')
GROUP BY item_id
ORDER BY interaction_count DESC
LIMIT 100;
```

### 3. Log Analysis

#### View Application Logs
```bash
# AppSync logs
aws logs describe-log-streams \
  --log-group-name "/aws/retail-personalization/acme-corp/dev"

# Step Functions logs
aws logs describe-log-streams \
  --log-group-name "/aws/stepfunctions/retail-personalization-acme-corp-dev"

# ECS logs
aws logs describe-log-streams \
  --log-group-name "/ecs/retail-personalization-acme-corp-dev"
```

## Troubleshooting

### Common Issues

#### 1. API Authentication Errors
**Problem**: 401 Unauthorized errors
**Solution**: 
- Verify API key is correct
- Check API key expiration date
- Ensure proper headers are set

#### 2. Step Function Failures
**Problem**: ML workflow fails
**Solution**:
- Check CloudWatch logs for detailed error messages
- Verify data format in S3 matches requirements
- Ensure IAM roles have proper permissions

#### 3. No Recommendations Returned
**Problem**: Empty recommendation results
**Solution**:
- Verify ML model training completed successfully
- Check if campaign is active in Personalize
- Ensure user has sufficient interaction history

#### 4. High DynamoDB Costs
**Problem**: Unexpected DynamoDB charges
**Solution**:
- Review read/write capacity settings
- Implement TTL for old recommendations
- Use DynamoDB on-demand pricing if traffic is unpredictable

### Debugging Commands

```bash
# Check Step Function execution status
aws stepfunctions list-executions \
  --state-machine-arn "arn:aws:states:us-east-1:545009852657:stateMachine:retail-personalization-acme-corp-dev-ml-workflow" \
  --status-filter FAILED

# View recent CloudWatch logs
aws logs filter-log-events \
  --log-group-name "/aws/retail-personalization/acme-corp/dev" \
  --start-time $(date -d '1 hour ago' +%s)000

# Check DynamoDB table status
aws dynamodb describe-table \
  --table-name "retail-personalization-acme-corp-dev-recommendations"
```

## Best Practices

### 1. Data Management
- **Regular Data Updates**: Upload fresh interaction data daily
- **Data Quality**: Ensure data follows the required schema
- **Data Retention**: Implement lifecycle policies for cost optimization
- **Backup Strategy**: Enable point-in-time recovery for DynamoDB

### 2. Performance Optimization
- **Caching**: Use DynamoDB for frequently accessed recommendations
- **Batch Operations**: Use batch GraphQL operations for bulk updates
- **Connection Pooling**: Implement connection pooling for database connections
- **CDN**: Use CloudFront for static content delivery

### 3. Security
- **API Key Rotation**: Regularly rotate AppSync API keys
- **IAM Policies**: Follow principle of least privilege
- **Encryption**: Ensure all data is encrypted at rest and in transit
- **VPC**: Deploy sensitive components in private subnets

### 4. Cost Optimization
- **Reserved Capacity**: Use reserved capacity for predictable workloads
- **Auto Scaling**: Enable auto-scaling for DynamoDB tables
- **Lifecycle Policies**: Implement S3 lifecycle policies for data archival
- **Monitoring**: Set up billing alerts and cost monitoring

### 5. Monitoring & Alerting
- **Custom Metrics**: Create custom CloudWatch metrics for business KPIs
- **Alerting**: Set up SNS notifications for critical failures
- **Log Retention**: Configure appropriate log retention periods
- **Performance Baselines**: Establish performance baselines for monitoring

### 6. Development Workflow
- **Environment Separation**: Use separate environments for dev/staging/prod
- **Infrastructure as Code**: Maintain all infrastructure in Terraform
- **CI/CD Pipeline**: Implement automated deployment pipelines
- **Testing**: Include integration tests for API endpoints

## Support and Resources

### Documentation Links
- [Amazon Personalize Developer Guide](https://docs.aws.amazon.com/personalize/)
- [AWS AppSync Developer Guide](https://docs.aws.amazon.com/appsync/)
- [Amazon Pinpoint User Guide](https://docs.aws.amazon.com/pinpoint/)
- [AWS Step Functions Developer Guide](https://docs.aws.amazon.com/step-functions/)

### Getting Help
- **AWS Support**: Contact AWS Support for infrastructure issues
- **Community Forums**: AWS Developer Forums for community support
- **Documentation**: Refer to AWS service documentation for detailed guides

---

*This user manual provides comprehensive guidance for utilizing the Retail Personalization Platform. For additional support or questions, please refer to the AWS documentation or contact your system administrator.* 