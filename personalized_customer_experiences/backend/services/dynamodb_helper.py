import json
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from decimal import Decimal
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from ..config import aws_config, settings

logger = logging.getLogger(__name__)


class DynamoDBHelper:
    """Helper class for DynamoDB operations in the retail personalization system."""
    
    def __init__(self):
        self.client = aws_config.dynamodb_client
        self.resource = aws_config.dynamodb_resource
        
        # Table references
        self.recommendations_table = self.resource.Table(settings.dynamodb_recommendations_table)
        self.user_profiles_table = self.resource.Table(settings.dynamodb_user_profiles_table)
        self.campaign_tracking_table = self.resource.Table(settings.dynamodb_campaign_tracking_table)
    
    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """Convert float values to Decimal for DynamoDB compatibility."""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(v) for v in obj]
        return obj
    
    def _convert_decimals_to_float(self, obj: Any) -> Any:
        """Convert Decimal values to float for JSON serialization."""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimals_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals_to_float(v) for v in obj]
        return obj
    
    # Recommendations Cache Operations
    def cache_recommendations(
        self, 
        tenant_id: str, 
        user_id: str, 
        recommendations: List[Dict[str, Union[str, float]]],
        ttl_hours: int = 24
    ) -> bool:
        """
        Cache recommendations for a user.
        
        Args:
            tenant_id: Tenant identifier for isolation
            user_id: User identifier
            recommendations: List of recommendation dictionaries
            ttl_hours: Time to live in hours
            
        Returns:
            True if successful
        """
        try:
            # Calculate TTL timestamp
            ttl_timestamp = int((datetime.utcnow() + timedelta(hours=ttl_hours)).timestamp())
            
            # Convert floats to Decimal for DynamoDB
            recommendations_decimal = self._convert_floats_to_decimal(recommendations)
            
            item = {
                'tenant_id': tenant_id,
                'user_id': user_id,
                'recommendations': recommendations_decimal,
                'cached_at': datetime.utcnow().isoformat(),
                'ttl': ttl_timestamp
            }
            
            self.recommendations_table.put_item(Item=item)
            
            logger.info(f"Cached {len(recommendations)} recommendations for user {user_id} in tenant {tenant_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to cache recommendations for user {user_id}: {e}")
            raise Exception(f"Recommendations caching failed: {e}")
    
    def get_cached_recommendations(
        self, 
        tenant_id: str, 
        user_id: str
    ) -> Optional[List[Dict[str, Union[str, float]]]]:
        """
        Get cached recommendations for a user.
        
        Args:
            tenant_id: Tenant identifier for isolation
            user_id: User identifier
            
        Returns:
            List of recommendations or None if not found/expired
        """
        try:
            response = self.recommendations_table.get_item(
                Key={
                    'tenant_id': tenant_id,
                    'user_id': user_id
                }
            )
            
            if 'Item' not in response:
                logger.info(f"No cached recommendations found for user {user_id}")
                return None
            
            item = response['Item']
            
            # Check if TTL has expired
            current_timestamp = int(datetime.utcnow().timestamp())
            if item.get('ttl', 0) < current_timestamp:
                logger.info(f"Cached recommendations expired for user {user_id}")
                # Clean up expired item
                self.recommendations_table.delete_item(
                    Key={
                        'tenant_id': tenant_id,
                        'user_id': user_id
                    }
                )
                return None
            
            # Convert Decimal back to float
            recommendations = self._convert_decimals_to_float(item['recommendations'])
            
            logger.info(f"Retrieved {len(recommendations)} cached recommendations for user {user_id}")
            return recommendations
            
        except ClientError as e:
            logger.error(f"Failed to get cached recommendations for user {user_id}: {e}")
            return None
    
    def invalidate_recommendations_cache(self, tenant_id: str, user_id: str) -> bool:
        """
        Invalidate cached recommendations for a user.
        
        Args:
            tenant_id: Tenant identifier for isolation
            user_id: User identifier
            
        Returns:
            True if successful
        """
        try:
            self.recommendations_table.delete_item(
                Key={
                    'tenant_id': tenant_id,
                    'user_id': user_id
                }
            )
            
            logger.info(f"Invalidated recommendations cache for user {user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to invalidate cache for user {user_id}: {e}")
            return False
    
    # User Profile Operations
    def create_user_profile(
        self, 
        tenant_id: str, 
        user_id: str, 
        profile_data: Dict[str, Any]
    ) -> bool:
        """
        Create or update a user profile.
        
        Args:
            tenant_id: Tenant identifier for isolation
            user_id: User identifier
            profile_data: User profile information
            
        Returns:
            True if successful
        """
        try:
            # Convert floats to Decimal
            profile_data_decimal = self._convert_floats_to_decimal(profile_data)
            
            item = {
                'tenant_id': tenant_id,
                'user_id': user_id,
                'profile_data': profile_data_decimal,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            self.user_profiles_table.put_item(Item=item)
            
            logger.info(f"Created/updated user profile for user {user_id} in tenant {tenant_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create user profile for user {user_id}: {e}")
            raise Exception(f"User profile creation failed: {e}")
    
    def get_user_profile(
        self, 
        tenant_id: str, 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user profile information.
        
        Args:
            tenant_id: Tenant identifier for isolation
            user_id: User identifier
            
        Returns:
            User profile data or None if not found
        """
        try:
            response = self.user_profiles_table.get_item(
                Key={
                    'tenant_id': tenant_id,
                    'user_id': user_id
                }
            )
            
            if 'Item' not in response:
                logger.info(f"User profile not found for user {user_id}")
                return None
            
            item = response['Item']
            
            # Convert Decimal back to float
            profile_data = self._convert_decimals_to_float(item.get('profile_data', {}))
            
            return {
                'user_id': item['user_id'],
                'profile_data': profile_data,
                'created_at': item.get('created_at'),
                'updated_at': item.get('updated_at')
            }
            
        except ClientError as e:
            logger.error(f"Failed to get user profile for user {user_id}: {e}")
            return None
    
    def update_user_profile(
        self, 
        tenant_id: str, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update specific fields in a user profile.
        
        Args:
            tenant_id: Tenant identifier for isolation
            user_id: User identifier
            updates: Dictionary of fields to update
            
        Returns:
            True if successful
        """
        try:
            # Convert floats to Decimal
            updates_decimal = self._convert_floats_to_decimal(updates)
            
            # Build update expression
            update_expression = "SET updated_at = :updated_at"
            expression_attribute_values = {
                ':updated_at': datetime.utcnow().isoformat()
            }
            
            for key, value in updates_decimal.items():
                update_expression += f", profile_data.{key} = :{key}"
                expression_attribute_values[f":{key}"] = value
            
            self.user_profiles_table.update_item(
                Key={
                    'tenant_id': tenant_id,
                    'user_id': user_id
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            logger.info(f"Updated user profile for user {user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to update user profile for user {user_id}: {e}")
            return False
    
    def list_user_profiles(
        self, 
        tenant_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List user profiles for a tenant.
        
        Args:
            tenant_id: Tenant identifier for isolation
            limit: Maximum number of profiles to return
            
        Returns:
            List of user profile summaries
        """
        try:
            response = self.user_profiles_table.query(
                KeyConditionExpression=Key('tenant_id').eq(tenant_id),
                Limit=limit
            )
            
            profiles = []
            for item in response.get('Items', []):
                profiles.append({
                    'user_id': item['user_id'],
                    'created_at': item.get('created_at'),
                    'updated_at': item.get('updated_at')
                })
            
            logger.info(f"Listed {len(profiles)} user profiles for tenant {tenant_id}")
            return profiles
            
        except ClientError as e:
            logger.error(f"Failed to list user profiles for tenant {tenant_id}: {e}")
            return []
    
    # Campaign Tracking Operations
    def track_campaign_event(
        self, 
        tenant_id: str, 
        campaign_id: str, 
        user_id: str,
        event_type: str, 
        event_data: Dict[str, Any]
    ) -> bool:
        """
        Track a campaign-related event.
        
        Args:
            tenant_id: Tenant identifier for isolation
            campaign_id: Campaign identifier
            user_id: User identifier
            event_type: Type of event (sent, opened, clicked, converted)
            event_data: Additional event information
            
        Returns:
            True if successful
        """
        try:
            # Convert floats to Decimal
            event_data_decimal = self._convert_floats_to_decimal(event_data)
            
            # Generate unique event ID
            event_id = f"{campaign_id}#{user_id}#{int(datetime.utcnow().timestamp())}"
            
            item = {
                'tenant_id': tenant_id,
                'event_id': event_id,
                'campaign_id': campaign_id,
                'user_id': user_id,
                'event_type': event_type,
                'event_data': event_data_decimal,
                'timestamp': datetime.utcnow().isoformat(),
                'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())  # 90 days retention
            }
            
            self.campaign_tracking_table.put_item(Item=item)
            
            logger.info(f"Tracked {event_type} event for campaign {campaign_id}, user {user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to track campaign event: {e}")
            return False
    
    def get_campaign_metrics(
        self, 
        tenant_id: str, 
        campaign_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get metrics for a campaign.
        
        Args:
            tenant_id: Tenant identifier for isolation
            campaign_id: Campaign identifier
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with campaign metrics
        """
        try:
            # Query campaign events
            query_params = {
                'IndexName': 'campaign-index',
                'KeyConditionExpression': Key('tenant_id').eq(tenant_id) & Key('campaign_id').eq(campaign_id)
            }
            
            if start_date or end_date:
                filter_expression = None
                if start_date:
                    filter_expression = Attr('timestamp').gte(start_date.isoformat())
                if end_date:
                    if filter_expression:
                        filter_expression = filter_expression & Attr('timestamp').lte(end_date.isoformat())
                    else:
                        filter_expression = Attr('timestamp').lte(end_date.isoformat())
                
                if filter_expression:
                    query_params['FilterExpression'] = filter_expression
            
            response = self.campaign_tracking_table.query(**query_params)
            
            # Calculate metrics
            metrics = {
                'campaign_id': campaign_id,
                'total_events': 0,
                'unique_users': set(),
                'events_by_type': {},
                'conversion_rate': 0.0,
                'click_through_rate': 0.0
            }
            
            for item in response.get('Items', []):
                event_type = item['event_type']
                user_id = item['user_id']
                
                metrics['total_events'] += 1
                metrics['unique_users'].add(user_id)
                
                if event_type not in metrics['events_by_type']:
                    metrics['events_by_type'][event_type] = 0
                metrics['events_by_type'][event_type] += 1
            
            # Convert set to count
            metrics['unique_users'] = len(metrics['unique_users'])
            
            # Calculate rates
            sent_count = metrics['events_by_type'].get('sent', 0)
            clicked_count = metrics['events_by_type'].get('clicked', 0)
            converted_count = metrics['events_by_type'].get('converted', 0)
            
            if sent_count > 0:
                metrics['click_through_rate'] = (clicked_count / sent_count) * 100
                metrics['conversion_rate'] = (converted_count / sent_count) * 100
            
            logger.info(f"Retrieved metrics for campaign {campaign_id}")
            return metrics
            
        except ClientError as e:
            logger.error(f"Failed to get campaign metrics for {campaign_id}: {e}")
            return {
                'campaign_id': campaign_id,
                'error': str(e)
            }
    
    def get_user_campaign_history(
        self, 
        tenant_id: str, 
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get campaign interaction history for a user.
        
        Args:
            tenant_id: Tenant identifier for isolation
            user_id: User identifier
            limit: Maximum number of events to return
            
        Returns:
            List of campaign events for the user
        """
        try:
            response = self.campaign_tracking_table.query(
                IndexName='user-index',
                KeyConditionExpression=Key('tenant_id').eq(tenant_id) & Key('user_id').eq(user_id),
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
            
            events = []
            for item in response.get('Items', []):
                event_data = self._convert_decimals_to_float(item.get('event_data', {}))
                events.append({
                    'event_id': item['event_id'],
                    'campaign_id': item['campaign_id'],
                    'event_type': item['event_type'],
                    'event_data': event_data,
                    'timestamp': item['timestamp']
                })
            
            logger.info(f"Retrieved {len(events)} campaign events for user {user_id}")
            return events
            
        except ClientError as e:
            logger.error(f"Failed to get campaign history for user {user_id}: {e}")
            return []
    
    # Utility Operations
    def cleanup_expired_items(self, tenant_id: str) -> Dict[str, int]:
        """
        Clean up expired items across all tables for a tenant.
        
        Args:
            tenant_id: Tenant identifier for isolation
            
        Returns:
            Dictionary with cleanup counts
        """
        try:
            cleanup_counts = {
                'recommendations': 0,
                'campaigns': 0
            }
            
            current_timestamp = int(datetime.utcnow().timestamp())
            
            # Clean up expired recommendations
            response = self.recommendations_table.query(
                KeyConditionExpression=Key('tenant_id').eq(tenant_id),
                FilterExpression=Attr('ttl').lt(current_timestamp)
            )
            
            for item in response.get('Items', []):
                self.recommendations_table.delete_item(
                    Key={
                        'tenant_id': item['tenant_id'],
                        'user_id': item['user_id']
                    }
                )
                cleanup_counts['recommendations'] += 1
            
            # Clean up expired campaign events (handled by DynamoDB TTL automatically)
            # This is just for reporting
            response = self.campaign_tracking_table.query(
                KeyConditionExpression=Key('tenant_id').eq(tenant_id),
                FilterExpression=Attr('ttl').lt(current_timestamp)
            )
            cleanup_counts['campaigns'] = response.get('Count', 0)
            
            logger.info(f"Cleaned up {cleanup_counts} expired items for tenant {tenant_id}")
            return cleanup_counts
            
        except ClientError as e:
            logger.error(f"Failed to cleanup expired items for tenant {tenant_id}: {e}")
            return {'error': str(e)}


# Global DynamoDB helper instance
dynamodb_helper = DynamoDBHelper() 