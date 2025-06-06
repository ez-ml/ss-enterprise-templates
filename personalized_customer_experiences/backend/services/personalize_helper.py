import json
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import time
from botocore.exceptions import ClientError

from ..config import aws_config, settings

logger = logging.getLogger(__name__)


class PersonalizeHelper:
    """Helper class for Amazon Personalize operations."""
    
    def __init__(self):
        self.client = aws_config.personalize_client
        self.runtime_client = aws_config.personalize_runtime_client
        self.events_client = aws_config.personalize_events_client
    
    def create_dataset_group(self, tenant_id: str) -> Dict[str, str]:
        """
        Create a dataset group for a tenant.
        
        Args:
            tenant_id: Tenant identifier for isolation
            
        Returns:
            Dict with dataset group information
        """
        try:
            dataset_group_name = f"{settings.personalize_dataset_group_name}-{tenant_id}"
            
            response = self.client.create_dataset_group(
                name=dataset_group_name,
                roleArn=f"arn:aws:iam::{aws_config.session.get_credentials().access_key}:role/PersonalizeRole",
                tags=[
                    {
                        'tagKey': 'TenantId',
                        'tagValue': tenant_id
                    },
                    {
                        'tagKey': 'Environment',
                        'tagValue': 'production'
                    }
                ]
            )
            
            dataset_group_arn = response['datasetGroupArn']
            logger.info(f"Created dataset group {dataset_group_arn} for tenant {tenant_id}")
            
            return {
                "dataset_group_arn": dataset_group_arn,
                "name": dataset_group_name,
                "status": "CREATING"
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                logger.info(f"Dataset group already exists for tenant {tenant_id}")
                return self.get_dataset_group(tenant_id)
            else:
                logger.error(f"Failed to create dataset group for tenant {tenant_id}: {e}")
                raise Exception(f"Dataset group creation failed: {e}")
    
    def get_dataset_group(self, tenant_id: str) -> Dict[str, str]:
        """
        Get dataset group information for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dict with dataset group information
        """
        try:
            dataset_group_name = f"{settings.personalize_dataset_group_name}-{tenant_id}"
            
            # List dataset groups and find the one for this tenant
            response = self.client.list_dataset_groups(maxResults=100)
            
            for dg in response.get('datasetGroups', []):
                if dg['name'] == dataset_group_name:
                    return {
                        "dataset_group_arn": dg['datasetGroupArn'],
                        "name": dg['name'],
                        "status": dg['status']
                    }
            
            raise Exception(f"Dataset group not found for tenant {tenant_id}")
            
        except ClientError as e:
            logger.error(f"Failed to get dataset group for tenant {tenant_id}: {e}")
            raise Exception(f"Dataset group retrieval failed: {e}")
    
    def create_dataset(
        self, 
        dataset_type: str, 
        schema_arn: str, 
        tenant_id: str
    ) -> Dict[str, str]:
        """
        Create a dataset within a dataset group.
        
        Args:
            dataset_type: Type of dataset (INTERACTIONS, USERS, ITEMS)
            schema_arn: ARN of the dataset schema
            tenant_id: Tenant identifier
            
        Returns:
            Dict with dataset information
        """
        try:
            dataset_group_info = self.get_dataset_group(tenant_id)
            dataset_group_arn = dataset_group_info['dataset_group_arn']
            
            dataset_name = f"{dataset_type.lower()}-{tenant_id}"
            
            response = self.client.create_dataset(
                name=dataset_name,
                schemaArn=schema_arn,
                datasetGroupArn=dataset_group_arn,
                datasetType=dataset_type.upper(),
                tags=[
                    {
                        'tagKey': 'TenantId',
                        'tagValue': tenant_id
                    },
                    {
                        'tagKey': 'DatasetType',
                        'tagValue': dataset_type
                    }
                ]
            )
            
            dataset_arn = response['datasetArn']
            logger.info(f"Created {dataset_type} dataset {dataset_arn} for tenant {tenant_id}")
            
            return {
                "dataset_arn": dataset_arn,
                "name": dataset_name,
                "type": dataset_type,
                "status": "CREATING"
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                logger.info(f"{dataset_type} dataset already exists for tenant {tenant_id}")
                return self.get_dataset(dataset_type, tenant_id)
            else:
                logger.error(f"Failed to create {dataset_type} dataset for tenant {tenant_id}: {e}")
                raise Exception(f"Dataset creation failed: {e}")
    
    def get_dataset(self, dataset_type: str, tenant_id: str) -> Dict[str, str]:
        """
        Get dataset information.
        
        Args:
            dataset_type: Type of dataset (INTERACTIONS, USERS, ITEMS)
            tenant_id: Tenant identifier
            
        Returns:
            Dict with dataset information
        """
        try:
            dataset_group_info = self.get_dataset_group(tenant_id)
            dataset_group_arn = dataset_group_info['dataset_group_arn']
            
            response = self.client.list_datasets(
                datasetGroupArn=dataset_group_arn,
                maxResults=100
            )
            
            dataset_name = f"{dataset_type.lower()}-{tenant_id}"
            
            for dataset in response.get('datasets', []):
                if dataset['name'] == dataset_name:
                    return {
                        "dataset_arn": dataset['datasetArn'],
                        "name": dataset['name'],
                        "type": dataset_type,
                        "status": dataset['status']
                    }
            
            raise Exception(f"{dataset_type} dataset not found for tenant {tenant_id}")
            
        except ClientError as e:
            logger.error(f"Failed to get {dataset_type} dataset for tenant {tenant_id}: {e}")
            raise Exception(f"Dataset retrieval failed: {e}")
    
    def import_data(
        self, 
        dataset_arn: str, 
        s3_data_source: str, 
        role_arn: str,
        tenant_id: str
    ) -> Dict[str, str]:
        """
        Import data into a dataset from S3.
        
        Args:
            dataset_arn: ARN of the target dataset
            s3_data_source: S3 path to the data file
            role_arn: IAM role ARN for Personalize
            tenant_id: Tenant identifier
            
        Returns:
            Dict with import job information
        """
        try:
            job_name = f"import-{tenant_id}-{int(time.time())}"
            
            response = self.client.create_dataset_import_job(
                jobName=job_name,
                datasetArn=dataset_arn,
                dataSource={
                    'dataLocation': s3_data_source
                },
                roleArn=role_arn,
                tags=[
                    {
                        'tagKey': 'TenantId',
                        'tagValue': tenant_id
                    }
                ]
            )
            
            import_job_arn = response['datasetImportJobArn']
            logger.info(f"Started data import job {import_job_arn} for tenant {tenant_id}")
            
            return {
                "import_job_arn": import_job_arn,
                "job_name": job_name,
                "status": "CREATING",
                "data_source": s3_data_source
            }
            
        except ClientError as e:
            logger.error(f"Failed to start data import for tenant {tenant_id}: {e}")
            raise Exception(f"Data import failed: {e}")
    
    def create_solution(
        self, 
        recipe_arn: str, 
        tenant_id: str,
        solution_config: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Create a solution (ML model configuration).
        
        Args:
            recipe_arn: ARN of the recipe to use
            tenant_id: Tenant identifier
            solution_config: Optional solution configuration
            
        Returns:
            Dict with solution information
        """
        try:
            dataset_group_info = self.get_dataset_group(tenant_id)
            dataset_group_arn = dataset_group_info['dataset_group_arn']
            
            solution_name = f"{settings.personalize_solution_name}-{tenant_id}"
            
            create_params = {
                'name': solution_name,
                'datasetGroupArn': dataset_group_arn,
                'recipeArn': recipe_arn,
                'tags': [
                    {
                        'tagKey': 'TenantId',
                        'tagValue': tenant_id
                    }
                ]
            }
            
            if solution_config:
                create_params['solutionConfig'] = solution_config
            
            response = self.client.create_solution(**create_params)
            
            solution_arn = response['solutionArn']
            logger.info(f"Created solution {solution_arn} for tenant {tenant_id}")
            
            return {
                "solution_arn": solution_arn,
                "name": solution_name,
                "status": "CREATING",
                "recipe_arn": recipe_arn
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                logger.info(f"Solution already exists for tenant {tenant_id}")
                return self.get_solution(tenant_id)
            else:
                logger.error(f"Failed to create solution for tenant {tenant_id}: {e}")
                raise Exception(f"Solution creation failed: {e}")
    
    def get_solution(self, tenant_id: str) -> Dict[str, str]:
        """
        Get solution information for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dict with solution information
        """
        try:
            dataset_group_info = self.get_dataset_group(tenant_id)
            dataset_group_arn = dataset_group_info['dataset_group_arn']
            
            response = self.client.list_solutions(
                datasetGroupArn=dataset_group_arn,
                maxResults=100
            )
            
            solution_name = f"{settings.personalize_solution_name}-{tenant_id}"
            
            for solution in response.get('solutions', []):
                if solution['name'] == solution_name:
                    return {
                        "solution_arn": solution['solutionArn'],
                        "name": solution['name'],
                        "status": solution['status'],
                        "recipe_arn": solution.get('recipeArn', '')
                    }
            
            raise Exception(f"Solution not found for tenant {tenant_id}")
            
        except ClientError as e:
            logger.error(f"Failed to get solution for tenant {tenant_id}: {e}")
            raise Exception(f"Solution retrieval failed: {e}")
    
    def create_solution_version(self, solution_arn: str, tenant_id: str) -> Dict[str, str]:
        """
        Create a solution version (train the model).
        
        Args:
            solution_arn: ARN of the solution
            tenant_id: Tenant identifier
            
        Returns:
            Dict with solution version information
        """
        try:
            response = self.client.create_solution_version(
                solutionArn=solution_arn,
                tags=[
                    {
                        'tagKey': 'TenantId',
                        'tagValue': tenant_id
                    },
                    {
                        'tagKey': 'CreatedAt',
                        'tagValue': datetime.utcnow().isoformat()
                    }
                ]
            )
            
            solution_version_arn = response['solutionVersionArn']
            logger.info(f"Started training solution version {solution_version_arn} for tenant {tenant_id}")
            
            return {
                "solution_version_arn": solution_version_arn,
                "solution_arn": solution_arn,
                "status": "CREATING"
            }
            
        except ClientError as e:
            logger.error(f"Failed to create solution version for tenant {tenant_id}: {e}")
            raise Exception(f"Solution version creation failed: {e}")
    
    def create_campaign(
        self, 
        solution_version_arn: str, 
        tenant_id: str,
        min_provisioned_tps: int = 1
    ) -> Dict[str, str]:
        """
        Create a campaign for real-time recommendations.
        
        Args:
            solution_version_arn: ARN of the trained solution version
            tenant_id: Tenant identifier
            min_provisioned_tps: Minimum provisioned transactions per second
            
        Returns:
            Dict with campaign information
        """
        try:
            campaign_name = f"{settings.personalize_campaign_name}-{tenant_id}"
            
            response = self.client.create_campaign(
                name=campaign_name,
                solutionVersionArn=solution_version_arn,
                minProvisionedTPS=min_provisioned_tps,
                tags=[
                    {
                        'tagKey': 'TenantId',
                        'tagValue': tenant_id
                    }
                ]
            )
            
            campaign_arn = response['campaignArn']
            logger.info(f"Created campaign {campaign_arn} for tenant {tenant_id}")
            
            return {
                "campaign_arn": campaign_arn,
                "name": campaign_name,
                "status": "CREATING",
                "solution_version_arn": solution_version_arn
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                logger.info(f"Campaign already exists for tenant {tenant_id}")
                return self.get_campaign(tenant_id)
            else:
                logger.error(f"Failed to create campaign for tenant {tenant_id}: {e}")
                raise Exception(f"Campaign creation failed: {e}")
    
    def get_campaign(self, tenant_id: str) -> Dict[str, str]:
        """
        Get campaign information for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dict with campaign information
        """
        try:
            response = self.client.list_campaigns(maxResults=100)
            
            campaign_name = f"{settings.personalize_campaign_name}-{tenant_id}"
            
            for campaign in response.get('campaigns', []):
                if campaign['name'] == campaign_name:
                    return {
                        "campaign_arn": campaign['campaignArn'],
                        "name": campaign['name'],
                        "status": campaign['status'],
                        "solution_version_arn": campaign.get('solutionVersionArn', '')
                    }
            
            raise Exception(f"Campaign not found for tenant {tenant_id}")
            
        except ClientError as e:
            logger.error(f"Failed to get campaign for tenant {tenant_id}: {e}")
            raise Exception(f"Campaign retrieval failed: {e}")
    
    def get_recommendations(
        self, 
        campaign_arn: str, 
        user_id: str,
        num_results: int = 10,
        filter_arn: Optional[str] = None,
        context: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Union[str, float]]]:
        """
        Get real-time recommendations for a user.
        
        Args:
            campaign_arn: ARN of the campaign
            user_id: User identifier
            num_results: Number of recommendations to return
            filter_arn: Optional filter ARN
            context: Optional context for recommendations
            
        Returns:
            List of recommendation dictionaries
        """
        try:
            params = {
                'campaignArn': campaign_arn,
                'userId': user_id,
                'numResults': num_results
            }
            
            if filter_arn:
                params['filterArn'] = filter_arn
            
            if context:
                params['context'] = context
            
            response = self.runtime_client.get_recommendations(**params)
            
            recommendations = []
            for item in response.get('itemList', []):
                recommendations.append({
                    'item_id': item['itemId'],
                    'score': float(item.get('score', 0.0))
                })
            
            logger.info(f"Retrieved {len(recommendations)} recommendations for user {user_id}")
            return recommendations
            
        except ClientError as e:
            logger.error(f"Failed to get recommendations for user {user_id}: {e}")
            raise Exception(f"Recommendations retrieval failed: {e}")
    
    def put_events(
        self, 
        tracking_id: str, 
        session_id: str, 
        user_id: str,
        event_list: List[Dict]
    ) -> bool:
        """
        Send real-time events to Personalize.
        
        Args:
            tracking_id: Event tracker ID
            session_id: Session identifier
            user_id: User identifier
            event_list: List of event dictionaries
            
        Returns:
            True if successful
        """
        try:
            self.events_client.put_events(
                trackingId=tracking_id,
                userId=user_id,
                sessionId=session_id,
                eventList=event_list
            )
            
            logger.info(f"Sent {len(event_list)} events for user {user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to send events for user {user_id}: {e}")
            raise Exception(f"Event sending failed: {e}")
    
    def get_training_status(self, tenant_id: str) -> Dict[str, str]:
        """
        Get the overall training status for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dict with training status information
        """
        try:
            status_info = {
                "tenant_id": tenant_id,
                "overall_status": "UNKNOWN",
                "components": {}
            }
            
            # Check dataset group status
            try:
                dg_info = self.get_dataset_group(tenant_id)
                status_info["components"]["dataset_group"] = dg_info["status"]
            except:
                status_info["components"]["dataset_group"] = "NOT_FOUND"
            
            # Check solution status
            try:
                solution_info = self.get_solution(tenant_id)
                status_info["components"]["solution"] = solution_info["status"]
            except:
                status_info["components"]["solution"] = "NOT_FOUND"
            
            # Check campaign status
            try:
                campaign_info = self.get_campaign(tenant_id)
                status_info["components"]["campaign"] = campaign_info["status"]
            except:
                status_info["components"]["campaign"] = "NOT_FOUND"
            
            # Determine overall status
            component_statuses = list(status_info["components"].values())
            if "CREATING" in component_statuses or "CREATE_IN_PROGRESS" in component_statuses:
                status_info["overall_status"] = "TRAINING"
            elif all(status == "ACTIVE" for status in component_statuses):
                status_info["overall_status"] = "READY"
            elif "CREATE_FAILED" in component_statuses or "FAILED" in component_statuses:
                status_info["overall_status"] = "FAILED"
            else:
                status_info["overall_status"] = "INCOMPLETE"
            
            return status_info
            
        except Exception as e:
            logger.error(f"Failed to get training status for tenant {tenant_id}: {e}")
            return {
                "tenant_id": tenant_id,
                "overall_status": "ERROR",
                "error": str(e)
            }


# Global Personalize helper instance
personalize_helper = PersonalizeHelper() 