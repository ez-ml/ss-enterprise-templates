# AppSync GraphQL API
resource "aws_appsync_graphql_api" "main" {
  authentication_type = "API_KEY"
  name                = "${var.project_name}-${var.tenant_id}-${var.environment}-api"

  schema = file("${path.module}/schema.graphql")

  log_config {
    cloudwatch_logs_role_arn = var.appsync_role_arn
    field_log_level          = "ALL"
  }

  xray_enabled = true

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-api"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# API Key
resource "aws_appsync_api_key" "main" {
  api_id      = aws_appsync_graphql_api.main.id
  description = "API Key for ${var.project_name}-${var.tenant_id}-${var.environment}"
  expires     = timeadd(timestamp(), "8760h") # 365 days in hours
}

# DynamoDB Data Source
resource "aws_appsync_datasource" "dynamodb" {
  api_id           = aws_appsync_graphql_api.main.id
  name             = "DynamoDBDataSource"
  service_role_arn = var.appsync_role_arn
  type             = "AMAZON_DYNAMODB"

  dynamodb_config {
    table_name = split("/", var.dynamodb_table_arn)[1]
    region     = data.aws_region.current.name
  }
}

# Data source for current region
data "aws_region" "current" {}

# Resolver for getRecommendations
resource "aws_appsync_resolver" "get_recommendations" {
  api_id      = aws_appsync_graphql_api.main.id
  field       = "getRecommendations"
  type        = "Query"
  data_source = aws_appsync_datasource.dynamodb.name

  request_template = <<EOF
{
    "version": "2017-02-28",
    "operation": "Query",
    "query": {
        "expression": "user_id = :user_id",
        "expressionValues": {
            ":user_id": {
                "S": "$ctx.args.userId"
            }
        }
    },
    "limit": $util.defaultIfNull($ctx.args.limit, 20),
    "scanIndexForward": false
}
EOF

  response_template = <<EOF
#if($ctx.error)
    $util.error($ctx.error.message, $ctx.error.type)
#end
{
    "items": [
        #foreach($item in $ctx.result.items)
        {
            "userId": "$item.user_id.S",
            "itemId": "$item.item_id.S",
            "score": $util.defaultIfNull($item.score.N, 0),
            "category": "$util.defaultIfNull($item.category.S, "")",
            "timestamp": $item.timestamp.N
        }#if($foreach.hasNext),#end
        #end
    ],
    "nextToken": "$util.defaultIfNull($ctx.result.nextToken, null)"
}
EOF
}

# Resolver for putRecommendation
resource "aws_appsync_resolver" "put_recommendation" {
  api_id      = aws_appsync_graphql_api.main.id
  field       = "putRecommendation"
  type        = "Mutation"
  data_source = aws_appsync_datasource.dynamodb.name

  request_template = <<EOF
{
    "version": "2017-02-28",
    "operation": "PutItem",
    "key": {
        "user_id": {
            "S": "$ctx.args.input.userId"
        },
        "item_id": {
            "S": "$ctx.args.input.itemId"
        }
    },
    "attributeValues": {
        "score": {
            "N": "$ctx.args.input.score"
        },
        "category": {
            "S": "$util.defaultIfNull($ctx.args.input.category, "")"
        },
        "timestamp": {
            "N": "$util.time.nowEpochSeconds()"
        },
        "ttl": {
            "N": "$util.time.nowEpochSeconds() + 2592000"
        }
    }
}
EOF

  response_template = <<EOF
#if($ctx.error)
    $util.error($ctx.error.message, $ctx.error.type)
#end
{
    "userId": "$ctx.result.user_id.S",
    "itemId": "$ctx.result.item_id.S",
    "score": $ctx.result.score.N,
    "category": "$util.defaultIfNull($ctx.result.category.S, "")",
    "timestamp": $ctx.result.timestamp.N
}
EOF
}

# Resolver for getRecommendationsByCategory
resource "aws_appsync_resolver" "get_recommendations_by_category" {
  api_id      = aws_appsync_graphql_api.main.id
  field       = "getRecommendationsByCategory"
  type        = "Query"
  data_source = aws_appsync_datasource.dynamodb.name

  request_template = <<EOF
{
    "version": "2017-02-28",
    "operation": "Query",
    "index": "CategoryIndex",
    "query": {
        "expression": "category = :category",
        "expressionValues": {
            ":category": {
                "S": "$ctx.args.category"
            }
        }
    },
    "limit": $util.defaultIfNull($ctx.args.limit, 20),
    "scanIndexForward": false
}
EOF

  response_template = <<EOF
#if($ctx.error)
    $util.error($ctx.error.message, $ctx.error.type)
#end
{
    "items": [
        #foreach($item in $ctx.result.items)
        {
            "userId": "$item.user_id.S",
            "itemId": "$item.item_id.S",
            "score": $util.defaultIfNull($item.score.N, 0),
            "category": "$item.category.S",
            "timestamp": $item.timestamp.N
        }#if($foreach.hasNext),#end
        #end
    ],
    "nextToken": "$util.defaultIfNull($ctx.result.nextToken, null)"
}
EOF
} 