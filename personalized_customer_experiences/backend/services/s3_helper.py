import os
import json
import logging
from typing import Dict, List, Optional, Union, BinaryIO
from datetime import datetime, timedelta
import pandas as pd
from botocore.exceptions import ClientError, NoCredentialsError
from io import StringIO, BytesIO

from ..config import aws_config, settings

logger = logging.getLogger(__name__)


class S3Helper:
    """Helper class for S3 operations in the retail personalization system."""
    
    def __init__(self):
        self.client = aws_config.s3_client
        self.bucket_name = settings.s3_bucket_name
    
    def upload_file(
        self, 
        file_content: Union[str, bytes, BinaryIO], 
        key: str, 
        tenant_id: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Upload a file to S3 with tenant isolation.
        
        Args:
            file_content: File content to upload
            key: S3 object key (without tenant prefix)
            tenant_id: Tenant identifier for isolation
            content_type: MIME type of the content
            metadata: Additional metadata to store with the object
            
        Returns:
            Dict with upload information
        """
        try:
            # Add tenant prefix to key
            full_key = f"{tenant_id}/{key}"
            
            # Prepare metadata
            upload_metadata = {
                "tenant_id": tenant_id,
                "uploaded_at": datetime.utcnow().isoformat(),
                "content_type": content_type
            }
            if metadata:
                upload_metadata.update(metadata)
            
            # Handle different content types
            if isinstance(file_content, str):
                body = file_content.encode('utf-8')
            elif isinstance(file_content, bytes):
                body = file_content
            else:
                body = file_content.read()
            
            # Upload to S3
            response = self.client.put_object(
                Bucket=self.bucket_name,
                Key=full_key,
                Body=body,
                ContentType=content_type,
                Metadata=upload_metadata,
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Successfully uploaded {full_key} to S3")
            
            return {
                "bucket": self.bucket_name,
                "key": full_key,
                "etag": response.get("ETag", "").strip('"'),
                "version_id": response.get("VersionId"),
                "size": len(body),
                "url": f"s3://{self.bucket_name}/{full_key}"
            }
            
        except ClientError as e:
            logger.error(f"Failed to upload {key} to S3: {e}")
            raise Exception(f"S3 upload failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error uploading {key}: {e}")
            raise
    
    def download_file(self, key: str, tenant_id: str) -> bytes:
        """
        Download a file from S3 with tenant isolation.
        
        Args:
            key: S3 object key (without tenant prefix)
            tenant_id: Tenant identifier for isolation
            
        Returns:
            File content as bytes
        """
        try:
            full_key = f"{tenant_id}/{key}"
            
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=full_key
            )
            
            content = response['Body'].read()
            logger.info(f"Successfully downloaded {full_key} from S3")
            
            return content
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"File {key} not found for tenant {tenant_id}")
                raise FileNotFoundError(f"File {key} not found")
            else:
                logger.error(f"Failed to download {key} from S3: {e}")
                raise Exception(f"S3 download failed: {e}")
    
    def list_files(
        self, 
        prefix: str, 
        tenant_id: str, 
        max_keys: int = 1000
    ) -> List[Dict[str, Union[str, int, datetime]]]:
        """
        List files in S3 with tenant isolation.
        
        Args:
            prefix: Key prefix to filter files
            tenant_id: Tenant identifier for isolation
            max_keys: Maximum number of keys to return
            
        Returns:
            List of file information dictionaries
        """
        try:
            full_prefix = f"{tenant_id}/{prefix}"
            
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=full_prefix,
                MaxKeys=max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                # Remove tenant prefix from key for response
                clean_key = obj['Key'].replace(f"{tenant_id}/", "", 1)
                files.append({
                    "key": clean_key,
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'],
                    "etag": obj['ETag'].strip('"'),
                    "storage_class": obj.get('StorageClass', 'STANDARD')
                })
            
            logger.info(f"Listed {len(files)} files for tenant {tenant_id} with prefix {prefix}")
            return files
            
        except ClientError as e:
            logger.error(f"Failed to list files for tenant {tenant_id}: {e}")
            raise Exception(f"S3 list failed: {e}")
    
    def delete_file(self, key: str, tenant_id: str) -> bool:
        """
        Delete a file from S3 with tenant isolation.
        
        Args:
            key: S3 object key (without tenant prefix)
            tenant_id: Tenant identifier for isolation
            
        Returns:
            True if successful
        """
        try:
            full_key = f"{tenant_id}/{key}"
            
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=full_key
            )
            
            logger.info(f"Successfully deleted {full_key} from S3")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete {key} from S3: {e}")
            raise Exception(f"S3 delete failed: {e}")
    
    def upload_dataset(
        self, 
        data: pd.DataFrame, 
        dataset_type: str, 
        tenant_id: str,
        format: str = "csv"
    ) -> Dict[str, str]:
        """
        Upload a dataset (DataFrame) to S3 for Personalize.
        
        Args:
            data: Pandas DataFrame containing the dataset
            dataset_type: Type of dataset (interactions, users, items)
            tenant_id: Tenant identifier for isolation
            format: File format (csv, json, parquet)
            
        Returns:
            Dict with upload information
        """
        try:
            # Validate dataset type
            valid_types = ["interactions", "users", "items"]
            if dataset_type not in valid_types:
                raise ValueError(f"Invalid dataset type. Must be one of: {valid_types}")
            
            # Generate filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{settings.s3_data_prefix}/{dataset_type}/{timestamp}.{format}"
            
            # Convert DataFrame to specified format
            if format == "csv":
                buffer = StringIO()
                data.to_csv(buffer, index=False)
                content = buffer.getvalue()
                content_type = "text/csv"
            elif format == "json":
                buffer = StringIO()
                data.to_json(buffer, orient="records", lines=True)
                content = buffer.getvalue()
                content_type = "application/json"
            elif format == "parquet":
                buffer = BytesIO()
                data.to_parquet(buffer, index=False)
                content = buffer.getvalue()
                content_type = "application/octet-stream"
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Upload to S3
            metadata = {
                "dataset_type": dataset_type,
                "format": format,
                "rows": str(len(data)),
                "columns": str(len(data.columns))
            }
            
            return self.upload_file(
                file_content=content,
                key=filename,
                tenant_id=tenant_id,
                content_type=content_type,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to upload {dataset_type} dataset: {e}")
            raise
    
    def get_dataset_url(self, key: str, tenant_id: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for dataset access.
        
        Args:
            key: S3 object key (without tenant prefix)
            tenant_id: Tenant identifier for isolation
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL string
        """
        try:
            full_key = f"{tenant_id}/{key}"
            
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': full_key},
                ExpiresIn=expires_in
            )
            
            logger.info(f"Generated presigned URL for {full_key}")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {key}: {e}")
            raise Exception(f"Presigned URL generation failed: {e}")
    
    def copy_file(
        self, 
        source_key: str, 
        dest_key: str, 
        tenant_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Copy a file within S3 with tenant isolation.
        
        Args:
            source_key: Source S3 object key (without tenant prefix)
            dest_key: Destination S3 object key (without tenant prefix)
            tenant_id: Tenant identifier for isolation
            metadata: Additional metadata for the copied object
            
        Returns:
            Dict with copy information
        """
        try:
            source_full_key = f"{tenant_id}/{source_key}"
            dest_full_key = f"{tenant_id}/{dest_key}"
            
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': source_full_key
            }
            
            # Prepare metadata
            copy_metadata = {
                "tenant_id": tenant_id,
                "copied_at": datetime.utcnow().isoformat(),
                "source_key": source_key
            }
            if metadata:
                copy_metadata.update(metadata)
            
            self.client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_full_key,
                Metadata=copy_metadata,
                MetadataDirective='REPLACE',
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Successfully copied {source_full_key} to {dest_full_key}")
            
            return {
                "source_key": source_full_key,
                "dest_key": dest_full_key,
                "bucket": self.bucket_name,
                "url": f"s3://{self.bucket_name}/{dest_full_key}"
            }
            
        except ClientError as e:
            logger.error(f"Failed to copy {source_key} to {dest_key}: {e}")
            raise Exception(f"S3 copy failed: {e}")
    
    def get_file_metadata(self, key: str, tenant_id: str) -> Dict[str, Union[str, int, datetime]]:
        """
        Get metadata for a file in S3.
        
        Args:
            key: S3 object key (without tenant prefix)
            tenant_id: Tenant identifier for isolation
            
        Returns:
            Dict with file metadata
        """
        try:
            full_key = f"{tenant_id}/{key}"
            
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=full_key
            )
            
            metadata = {
                "key": key,
                "size": response['ContentLength'],
                "last_modified": response['LastModified'],
                "etag": response['ETag'].strip('"'),
                "content_type": response.get('ContentType', 'unknown'),
                "metadata": response.get('Metadata', {})
            }
            
            if 'VersionId' in response:
                metadata['version_id'] = response['VersionId']
            
            logger.info(f"Retrieved metadata for {full_key}")
            return metadata
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"File {key} not found for tenant {tenant_id}")
                raise FileNotFoundError(f"File {key} not found")
            else:
                logger.error(f"Failed to get metadata for {key}: {e}")
                raise Exception(f"S3 metadata retrieval failed: {e}")


# Global S3 helper instance
s3_helper = S3Helper() 