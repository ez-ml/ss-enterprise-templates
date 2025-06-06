import json
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

from ..config import aws_config, settings

logger = logging.getLogger(__name__)


class PinpointHelper:
    """Helper class for Amazon Pinpoint operations in the retail personalization system."""
    
    def __init__(self):
        self.client = aws_config.pinpoint_client
        self.application_id = settings.pinpoint_application_id
        self.from_address = settings.pinpoint_from_address
    
    def create_segment(
        self, 
        tenant_id: str, 
        segment_name: str, 
        user_ids: List[str],
        segment_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Create a user segment for targeted campaigns.
        
        Args:
            tenant_id: Tenant identifier for isolation
            segment_name: Name of the segment
            user_ids: List of user IDs to include in segment
            segment_criteria: Optional additional segment criteria
            
        Returns:
            Dict with segment information
        """
        try:
            # Build segment dimensions
            dimensions = {
                'UserAttributes': {
                    'tenant_id': {
                        'AttributeType': 'INCLUSIVE',
                        'Values': [tenant_id]
                    }
                }
            }
            
            # Add user ID filter if provided
            if user_ids:
                dimensions['UserAttributes']['user_id'] = {
                    'AttributeType': 'INCLUSIVE',
                    'Values': user_ids
                }
            
            # Add custom criteria if provided
            if segment_criteria:
                for key, value in segment_criteria.items():
                    if key not in dimensions['UserAttributes']:
                        dimensions['UserAttributes'][key] = value
            
            segment_request = {
                'Name': f"{segment_name}-{tenant_id}",
                'Dimensions': dimensions,
                'tags': {
                    'TenantId': tenant_id,
                    'CreatedAt': datetime.utcnow().isoformat()
                }
            }
            
            response = self.client.create_segment(
                ApplicationId=self.application_id,
                WriteSegmentRequest=segment_request
            )
            
            segment_id = response['SegmentResponse']['Id']
            logger.info(f"Created segment {segment_id} for tenant {tenant_id}")
            
            return {
                'segment_id': segment_id,
                'segment_name': segment_name,
                'tenant_id': tenant_id,
                'status': 'CREATED'
            }
            
        except ClientError as e:
            logger.error(f"Failed to create segment for tenant {tenant_id}: {e}")
            raise Exception(f"Segment creation failed: {e}")
    
    def get_segment(self, segment_id: str) -> Dict[str, Any]:
        """
        Get segment information.
        
        Args:
            segment_id: Segment identifier
            
        Returns:
            Dict with segment information
        """
        try:
            response = self.client.get_segment(
                ApplicationId=self.application_id,
                SegmentId=segment_id
            )
            
            segment = response['SegmentResponse']
            
            return {
                'segment_id': segment['Id'],
                'name': segment['Name'],
                'creation_date': segment['CreationDate'],
                'last_modified_date': segment['LastModifiedDate'],
                'segment_type': segment['SegmentType'],
                'tags': segment.get('tags', {})
            }
            
        except ClientError as e:
            logger.error(f"Failed to get segment {segment_id}: {e}")
            raise Exception(f"Segment retrieval failed: {e}")
    
    def send_email_campaign(
        self, 
        tenant_id: str, 
        campaign_name: str,
        segment_id: str, 
        subject: str, 
        html_content: str,
        text_content: Optional[str] = None,
        schedule_time: Optional[datetime] = None
    ) -> Dict[str, str]:
        """
        Send an email campaign to a segment.
        
        Args:
            tenant_id: Tenant identifier for isolation
            campaign_name: Name of the campaign
            segment_id: Target segment ID
            subject: Email subject line
            html_content: HTML email content
            text_content: Optional plain text content
            schedule_time: Optional scheduled send time
            
        Returns:
            Dict with campaign information
        """
        try:
            # Build email message
            message_config = {
                'EmailMessage': {
                    'FromAddress': self.from_address,
                    'HtmlBody': html_content,
                    'Subject': subject
                }
            }
            
            if text_content:
                message_config['EmailMessage']['TextBody'] = text_content
            
            # Build campaign request
            campaign_request = {
                'Name': f"{campaign_name}-{tenant_id}",
                'SegmentId': segment_id,
                'MessageConfiguration': message_config,
                'tags': {
                    'TenantId': tenant_id,
                    'CampaignType': 'email',
                    'CreatedAt': datetime.utcnow().isoformat()
                }
            }
            
            # Create campaign
            response = self.client.create_campaign(
                ApplicationId=self.application_id,
                WriteCampaignRequest=campaign_request
            )
            
            campaign_id = response['CampaignResponse']['Id']
            
            # Schedule or send immediately
            if schedule_time:
                # Schedule campaign
                schedule_request = {
                    'StartTime': schedule_time.isoformat(),
                    'Timezone': 'UTC'
                }
                
                self.client.put_campaign_activities(
                    ApplicationId=self.application_id,
                    CampaignId=campaign_id,
                    WriteCampaignRequest={
                        'Schedule': schedule_request
                    }
                )
                
                status = 'SCHEDULED'
                logger.info(f"Scheduled email campaign {campaign_id} for {schedule_time}")
            else:
                # Send immediately
                self.client.send_messages(
                    ApplicationId=self.application_id,
                    MessageRequest={
                        'MessageConfiguration': message_config,
                        'Endpoints': {
                            segment_id: {}
                        }
                    }
                )
                
                status = 'SENT'
                logger.info(f"Sent email campaign {campaign_id} immediately")
            
            return {
                'campaign_id': campaign_id,
                'campaign_name': campaign_name,
                'tenant_id': tenant_id,
                'status': status,
                'segment_id': segment_id
            }
            
        except ClientError as e:
            logger.error(f"Failed to send email campaign for tenant {tenant_id}: {e}")
            raise Exception(f"Email campaign failed: {e}")
    
    def send_sms_campaign(
        self, 
        tenant_id: str, 
        campaign_name: str,
        segment_id: str, 
        message: str,
        schedule_time: Optional[datetime] = None
    ) -> Dict[str, str]:
        """
        Send an SMS campaign to a segment.
        
        Args:
            tenant_id: Tenant identifier for isolation
            campaign_name: Name of the campaign
            segment_id: Target segment ID
            message: SMS message content
            schedule_time: Optional scheduled send time
            
        Returns:
            Dict with campaign information
        """
        try:
            # Build SMS message
            message_config = {
                'SMSMessage': {
                    'Body': message,
                    'MessageType': 'PROMOTIONAL'
                }
            }
            
            # Build campaign request
            campaign_request = {
                'Name': f"{campaign_name}-{tenant_id}",
                'SegmentId': segment_id,
                'MessageConfiguration': message_config,
                'tags': {
                    'TenantId': tenant_id,
                    'CampaignType': 'sms',
                    'CreatedAt': datetime.utcnow().isoformat()
                }
            }
            
            # Create campaign
            response = self.client.create_campaign(
                ApplicationId=self.application_id,
                WriteCampaignRequest=campaign_request
            )
            
            campaign_id = response['CampaignResponse']['Id']
            
            # Schedule or send immediately
            if schedule_time:
                # Schedule campaign
                schedule_request = {
                    'StartTime': schedule_time.isoformat(),
                    'Timezone': 'UTC'
                }
                
                self.client.put_campaign_activities(
                    ApplicationId=self.application_id,
                    CampaignId=campaign_id,
                    WriteCampaignRequest={
                        'Schedule': schedule_request
                    }
                )
                
                status = 'SCHEDULED'
                logger.info(f"Scheduled SMS campaign {campaign_id} for {schedule_time}")
            else:
                # Send immediately
                self.client.send_messages(
                    ApplicationId=self.application_id,
                    MessageRequest={
                        'MessageConfiguration': message_config,
                        'Endpoints': {
                            segment_id: {}
                        }
                    }
                )
                
                status = 'SENT'
                logger.info(f"Sent SMS campaign {campaign_id} immediately")
            
            return {
                'campaign_id': campaign_id,
                'campaign_name': campaign_name,
                'tenant_id': tenant_id,
                'status': status,
                'segment_id': segment_id
            }
            
        except ClientError as e:
            logger.error(f"Failed to send SMS campaign for tenant {tenant_id}: {e}")
            raise Exception(f"SMS campaign failed: {e}")
    
    def send_personalized_recommendations(
        self, 
        tenant_id: str, 
        user_id: str,
        recommendations: List[Dict[str, Any]], 
        channel: str = 'email',
        template_name: str = 'recommendations'
    ) -> Dict[str, str]:
        """
        Send personalized recommendations to a user.
        
        Args:
            tenant_id: Tenant identifier for isolation
            user_id: Target user ID
            recommendations: List of recommendation items
            channel: Communication channel (email, sms, push)
            template_name: Message template to use
            
        Returns:
            Dict with send information
        """
        try:
            # Build personalized content
            if channel == 'email':
                subject = "Personalized Recommendations Just for You!"
                
                # Build HTML content with recommendations
                html_content = f"""
                <html>
                <body>
                    <h2>Hi there!</h2>
                    <p>We've found some great products you might like:</p>
                    <div style="display: flex; flex-wrap: wrap;">
                """
                
                for rec in recommendations[:5]:  # Limit to top 5
                    html_content += f"""
                        <div style="margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                            <h4>{rec.get('title', 'Recommended Item')}</h4>
                            <p>Score: {rec.get('score', 0):.2f}</p>
                            <p>{rec.get('description', 'Great product for you!')}</p>
                            <a href="{rec.get('url', '#')}" style="background: #007bff; color: white; padding: 8px 16px; text-decoration: none; border-radius: 3px;">View Product</a>
                        </div>
                    """
                
                html_content += """
                    </div>
                    <p>Happy shopping!</p>
                </body>
                </html>
                """
                
                message_config = {
                    'EmailMessage': {
                        'FromAddress': self.from_address,
                        'HtmlBody': html_content,
                        'Subject': subject
                    }
                }
                
            elif channel == 'sms':
                # Build SMS content
                message_text = f"Hi! We found {len(recommendations)} great products for you. "
                if recommendations:
                    message_text += f"Check out: {recommendations[0].get('title', 'our top pick')}!"
                
                message_config = {
                    'SMSMessage': {
                        'Body': message_text,
                        'MessageType': 'PROMOTIONAL'
                    }
                }
            
            else:
                raise ValueError(f"Unsupported channel: {channel}")
            
            # Send message to specific user
            response = self.client.send_messages(
                ApplicationId=self.application_id,
                MessageRequest={
                    'MessageConfiguration': message_config,
                    'Users': {
                        user_id: {
                            'UserId': user_id
                        }
                    }
                }
            )
            
            message_id = response['MessageResponse']['RequestId']
            
            logger.info(f"Sent personalized recommendations via {channel} to user {user_id}")
            
            return {
                'message_id': message_id,
                'user_id': user_id,
                'tenant_id': tenant_id,
                'channel': channel,
                'recommendations_count': len(recommendations),
                'status': 'SENT'
            }
            
        except ClientError as e:
            logger.error(f"Failed to send personalized recommendations to user {user_id}: {e}")
            raise Exception(f"Personalized message failed: {e}")
    
    def get_campaign_metrics(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get metrics for a campaign.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Dict with campaign metrics
        """
        try:
            response = self.client.get_campaign_activities(
                ApplicationId=self.application_id,
                CampaignId=campaign_id
            )
            
            activities = response['ActivitiesResponse']['Item']
            
            metrics = {
                'campaign_id': campaign_id,
                'total_activities': len(activities),
                'metrics': {}
            }
            
            for activity in activities:
                activity_metrics = activity.get('ExecutionMetrics', {})
                metrics['metrics'][activity['Id']] = {
                    'messages_sent': activity_metrics.get('MessagesPerSecond', 0),
                    'delivery_rate': activity_metrics.get('DeliveryRate', 0),
                    'bounce_rate': activity_metrics.get('BounceRate', 0),
                    'complaint_rate': activity_metrics.get('ComplaintRate', 0)
                }
            
            logger.info(f"Retrieved metrics for campaign {campaign_id}")
            return metrics
            
        except ClientError as e:
            logger.error(f"Failed to get campaign metrics for {campaign_id}: {e}")
            return {
                'campaign_id': campaign_id,
                'error': str(e)
            }
    
    def create_endpoint(
        self, 
        tenant_id: str, 
        user_id: str, 
        channel_type: str,
        address: str, 
        user_attributes: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, str]:
        """
        Create or update an endpoint for a user.
        
        Args:
            tenant_id: Tenant identifier for isolation
            user_id: User identifier
            channel_type: Channel type (EMAIL, SMS, PUSH, etc.)
            address: Contact address (email, phone, etc.)
            user_attributes: Optional user attributes
            
        Returns:
            Dict with endpoint information
        """
        try:
            endpoint_request = {
                'ChannelType': channel_type.upper(),
                'Address': address,
                'User': {
                    'UserId': user_id,
                    'UserAttributes': user_attributes or {}
                },
                'Attributes': {
                    'tenant_id': [tenant_id]
                }
            }
            
            # Add tenant_id to user attributes
            if 'tenant_id' not in endpoint_request['User']['UserAttributes']:
                endpoint_request['User']['UserAttributes']['tenant_id'] = [tenant_id]
            
            response = self.client.update_endpoint(
                ApplicationId=self.application_id,
                EndpointId=f"{tenant_id}-{user_id}-{channel_type.lower()}",
                EndpointRequest=endpoint_request
            )
            
            endpoint_id = response['MessageBody']['RequestID']
            
            logger.info(f"Created/updated {channel_type} endpoint for user {user_id}")
            
            return {
                'endpoint_id': endpoint_id,
                'user_id': user_id,
                'tenant_id': tenant_id,
                'channel_type': channel_type,
                'address': address,
                'status': 'ACTIVE'
            }
            
        except ClientError as e:
            logger.error(f"Failed to create endpoint for user {user_id}: {e}")
            raise Exception(f"Endpoint creation failed: {e}")
    
    def get_endpoint(self, endpoint_id: str) -> Dict[str, Any]:
        """
        Get endpoint information.
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            Dict with endpoint information
        """
        try:
            response = self.client.get_endpoint(
                ApplicationId=self.application_id,
                EndpointId=endpoint_id
            )
            
            endpoint = response['EndpointResponse']
            
            return {
                'endpoint_id': endpoint['Id'],
                'channel_type': endpoint['ChannelType'],
                'address': endpoint['Address'],
                'user_id': endpoint.get('User', {}).get('UserId'),
                'creation_date': endpoint['CreationDate'],
                'effective_date': endpoint['EffectiveDate'],
                'endpoint_status': endpoint['EndpointStatus'],
                'attributes': endpoint.get('Attributes', {}),
                'user_attributes': endpoint.get('User', {}).get('UserAttributes', {})
            }
            
        except ClientError as e:
            logger.error(f"Failed to get endpoint {endpoint_id}: {e}")
            raise Exception(f"Endpoint retrieval failed: {e}")
    
    def list_campaigns(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        List campaigns for a tenant.
        
        Args:
            tenant_id: Tenant identifier for isolation
            
        Returns:
            List of campaign information
        """
        try:
            response = self.client.get_campaigns(
                ApplicationId=self.application_id
            )
            
            campaigns = []
            for campaign in response['CampaignsResponse']['Item']:
                # Filter by tenant_id in tags
                if campaign.get('tags', {}).get('TenantId') == tenant_id:
                    campaigns.append({
                        'campaign_id': campaign['Id'],
                        'name': campaign['Name'],
                        'creation_date': campaign['CreationDate'],
                        'last_modified_date': campaign['LastModifiedDate'],
                        'campaign_status': campaign['State'],
                        'segment_id': campaign.get('SegmentId'),
                        'tags': campaign.get('tags', {})
                    })
            
            logger.info(f"Listed {len(campaigns)} campaigns for tenant {tenant_id}")
            return campaigns
            
        except ClientError as e:
            logger.error(f"Failed to list campaigns for tenant {tenant_id}: {e}")
            return []
    
    def delete_campaign(self, campaign_id: str) -> bool:
        """
        Delete a campaign.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            True if successful
        """
        try:
            self.client.delete_campaign(
                ApplicationId=self.application_id,
                CampaignId=campaign_id
            )
            
            logger.info(f"Deleted campaign {campaign_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete campaign {campaign_id}: {e}")
            return False


# Global Pinpoint helper instance
pinpoint_helper = PinpointHelper() 