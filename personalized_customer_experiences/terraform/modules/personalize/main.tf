# Amazon Personalize Dataset Group
resource "aws_personalize_dataset_group" "main" {
  name     = "${var.project_name}-${var.tenant_id}-${var.environment}"
  role_arn = var.personalize_role

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Interactions Schema
resource "aws_personalize_schema" "interactions" {
  name   = "${var.project_name}-${var.tenant_id}-interactions-schema"
  domain = "ECOMMERCE"

  schema = jsonencode({
    type = "record"
    name = "Interactions"
    namespace = "com.amazonaws.personalize.schema"
    fields = [
      {
        name = "USER_ID"
        type = "string"
      },
      {
        name = "ITEM_ID"
        type = "string"
      },
      {
        name = "TIMESTAMP"
        type = "long"
      },
      {
        name = "EVENT_TYPE"
        type = "string"
      },
      {
        name = "EVENT_VALUE"
        type = ["null", "float"]
        default = null
      }
    ]
    version = "1.0"
  })

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-interactions-schema"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Users Schema
resource "aws_personalize_schema" "users" {
  name   = "${var.project_name}-${var.tenant_id}-users-schema"
  domain = "ECOMMERCE"

  schema = jsonencode({
    type = "record"
    name = "Users"
    namespace = "com.amazonaws.personalize.schema"
    fields = [
      {
        name = "USER_ID"
        type = "string"
      },
      {
        name = "AGE"
        type = ["null", "int"]
        default = null
      },
      {
        name = "GENDER"
        type = ["null", "string"]
        default = null
      },
      {
        name = "MEMBERSHIP_TYPE"
        type = ["null", "string"]
        default = null
      },
      {
        name = "LOCATION"
        type = ["null", "string"]
        default = null
      }
    ]
    version = "1.0"
  })

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-users-schema"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Items Schema
resource "aws_personalize_schema" "items" {
  name   = "${var.project_name}-${var.tenant_id}-items-schema"
  domain = "ECOMMERCE"

  schema = jsonencode({
    type = "record"
    name = "Items"
    namespace = "com.amazonaws.personalize.schema"
    fields = [
      {
        name = "ITEM_ID"
        type = "string"
      },
      {
        name = "CATEGORY_L1"
        type = ["null", "string"]
        default = null
      },
      {
        name = "CATEGORY_L2"
        type = ["null", "string"]
        default = null
      },
      {
        name = "BRAND"
        type = ["null", "string"]
        default = null
      },
      {
        name = "PRICE"
        type = ["null", "float"]
        default = null
      },
      {
        name = "CREATION_TIMESTAMP"
        type = ["null", "long"]
        default = null
      }
    ]
    version = "1.0"
  })

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-items-schema"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Interactions Dataset
resource "aws_personalize_dataset" "interactions" {
  name           = "${var.project_name}-${var.tenant_id}-interactions"
  dataset_group_arn = aws_personalize_dataset_group.main.arn
  dataset_type   = "Interactions"
  schema_arn     = aws_personalize_schema.interactions.arn

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-interactions"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Users Dataset
resource "aws_personalize_dataset" "users" {
  name           = "${var.project_name}-${var.tenant_id}-users"
  dataset_group_arn = aws_personalize_dataset_group.main.arn
  dataset_type   = "Users"
  schema_arn     = aws_personalize_schema.users.arn

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-users"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Items Dataset
resource "aws_personalize_dataset" "items" {
  name           = "${var.project_name}-${var.tenant_id}-items"
  dataset_group_arn = aws_personalize_dataset_group.main.arn
  dataset_type   = "Items"
  schema_arn     = aws_personalize_schema.items.arn

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-items"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
} 