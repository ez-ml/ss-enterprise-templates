# Retail Personalization Platform - Quick Reference

## 🚀 Essential Commands

### Get Your API Key
```bash
cd terraform && terraform output appsync_api_key
```

### Upload Data to S3
```bash
# Upload interaction data (triggers ML workflow)
aws s3 cp interactions.csv s3://retail-personalization-acme-corp-dev-data/datasets/interactions.csv

# Upload user metadata
aws s3 cp users.csv s3://retail-personalization-acme-corp-dev-data/datasets/users.csv

# Upload item catalog
aws s3 cp items.csv s3://retail-personalization-acme-corp-dev-data/datasets/items.csv
```

### Check ML Workflow Status
```bash
# List recent executions
aws stepfunctions list-executions \
  --state-machine-arn "arn:aws:states:us-east-1:545009852657:stateMachine:retail-personalization-acme-corp-dev-ml-workflow" \
  --max-items 5

# Get execution details
aws stepfunctions describe-execution --execution-arn "EXECUTION_ARN"
```

## 📊 GraphQL API Examples

### Get Recommendations
```graphql
query GetRecommendations($userId: String!) {
  getRecommendations(userId: $userId, limit: 10) {
    items {
      userId
      itemId
      score
      category
      timestamp
    }
  }
}
```

### Store Recommendation
```graphql
mutation PutRecommendation($input: RecommendationInput!) {
  putRecommendation(input: $input) {
    userId
    itemId
    score
    category
  }
}
```

## 🔍 Monitoring Commands

### View Recent Logs
```bash
# AppSync API logs
aws logs filter-log-events \
  --log-group-name "/aws/retail-personalization/acme-corp/dev" \
  --start-time $(date -d '1 hour ago' +%s)000

# Step Functions logs
aws logs filter-log-events \
  --log-group-name "/aws/stepfunctions/retail-personalization-acme-corp-dev" \
  --start-time $(date -d '1 hour ago' +%s)000
```

### Check Resource Status
```bash
# DynamoDB table
aws dynamodb describe-table --table-name "retail-personalization-acme-corp-dev-recommendations"

# S3 bucket contents
aws s3 ls s3://retail-personalization-acme-corp-dev-data/datasets/

# Pinpoint app
aws pinpoint get-app --application-id "c2cb7bf620d149feb9338c4c0ba0b943"
```

## 🎯 Key Resources

| Resource | Value |
|----------|-------|
| **AppSync API** | `https://4wwv3n7ht5fhpigvf4c2xigtma.appsync-api.us-east-1.amazonaws.com/graphql` |
| **S3 Data Bucket** | `retail-personalization-acme-corp-dev-data` |
| **DynamoDB Table** | `retail-personalization-acme-corp-dev-recommendations` |
| **Step Function** | `retail-personalization-acme-corp-dev-ml-workflow` |
| **Pinpoint App ID** | `c2cb7bf620d149feb9338c4c0ba0b943` |
| **CloudWatch Dashboard** | `retail-personalization-acme-corp-dev` |

## 📋 Data Format Templates

### interactions.csv
```csv
USER_ID,ITEM_ID,EVENT_TYPE,TIMESTAMP,EVENT_VALUE
user123,item456,purchase,1640995200,29.99
user123,item789,view,1640995300,
user456,item123,add_to_cart,1640995400,15.50
```

### users.csv
```csv
USER_ID,AGE,GENDER,MEMBERSHIP_TYPE
user123,25,M,premium
user456,34,F,standard
```

### items.csv
```csv
ITEM_ID,CATEGORY,PRICE,BRAND
item123,electronics,299.99,TechBrand
item456,clothing,49.99,FashionCorp
```

## 🚨 Troubleshooting

### Common Issues
- **401 Unauthorized**: Check API key and headers
- **Empty recommendations**: Verify ML model training completed
- **Step Function failures**: Check CloudWatch logs for errors
- **High costs**: Review DynamoDB capacity settings

### Emergency Commands
```bash
# Stop all Step Function executions
aws stepfunctions list-executions --state-machine-arn "ARN" --status-filter RUNNING | \
jq -r '.executions[].executionArn' | \
xargs -I {} aws stepfunctions stop-execution --execution-arn {}

# Scale down DynamoDB (if costs are high)
aws dynamodb update-table \
  --table-name "retail-personalization-acme-corp-dev-recommendations" \
  --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1
```

## 📞 Support
- **Full Documentation**: See `USER_MANUAL.md`
- **AWS Console**: [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=retail-personalization-acme-corp-dev)
- **Terraform State**: `cd terraform && terraform show` 