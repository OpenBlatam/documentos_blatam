#!/usr/bin/env python3
"""
Utilidades para cloud storage.

Incluye:
- AWS S3
- Google Cloud Storage
- Azure Blob Storage
"""

from typing import Dict, Any, Optional, Union, BinaryIO
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    from google.cloud import storage as gcs_storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

try:
    from azure.storage.blob import BlobServiceClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

from .utils import setup_logger
from .error_handling import safe_execute, retry, RetryStrategy

logger = setup_logger(__name__)


class S3Client:
    """Cliente para AWS S3."""
    
    def __init__(self, bucket_name: str, aws_access_key_id: Optional[str] = None, 
                 aws_secret_access_key: Optional[str] = None, region_name: str = 'us-east-1'):
        """
        Inicializa cliente S3.
        
        Args:
            bucket_name: Nombre del bucket
            aws_access_key_id: AWS access key (opcional, puede usar variables de entorno)
            aws_secret_access_key: AWS secret key (opcional)
            region_name: Región de AWS
        """
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 no está instalado. Instala con: pip install boto3")
        
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
    
    def upload_file(self, local_path: Union[str, Path], s3_key: str) -> bool:
        """
        Sube un archivo a S3.
        
        Args:
            local_path: Ruta local del archivo
            s3_key: Clave S3 (ruta en el bucket)
        
        Returns:
            True si fue exitoso
        """
        def _upload():
            self.s3_client.upload_file(str(local_path), self.bucket_name, s3_key)
        
        @retry(
            max_attempts=3,
            delay=1.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            exceptions=(Exception,)
        )
        def _upload_with_retry():
            _upload()
        
        result, error = safe_execute(_upload_with_retry, default_value=False, log_errors=True)
        if result:
            logger.info("Archivo subido a S3", bucket=self.bucket_name, key=s3_key)
        elif error:
            logger.error("Error subiendo archivo a S3", error=str(error))
        return result
    
    def download_file(self, s3_key: str, local_path: Union[str, Path]) -> bool:
        """
        Descarga un archivo de S3.
        
        Args:
            s3_key: Clave S3
            local_path: Ruta local donde guardar
        
        Returns:
            True si fue exitoso
        """
        def _download():
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            self.s3_client.download_file(self.bucket_name, s3_key, str(local_path))
        
        @retry(
            max_attempts=3,
            delay=1.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            exceptions=(Exception,)
        )
        def _download_with_retry():
            _download()
        
        result, error = safe_execute(_download_with_retry, default_value=False, log_errors=True)
        if result:
            logger.info("Archivo descargado de S3", bucket=self.bucket_name, key=s3_key)
        elif error:
            logger.error("Error descargando archivo de S3", error=str(error))
        return result


class GCSClient:
    """Cliente para Google Cloud Storage."""
    
    def __init__(self, bucket_name: str, project: Optional[str] = None):
        """
        Inicializa cliente GCS.
        
        Args:
            bucket_name: Nombre del bucket
            project: ID del proyecto (opcional)
        """
        if not GCS_AVAILABLE:
            raise ImportError("google-cloud-storage no está instalado")
        
        self.bucket_name = bucket_name
        self.client = gcs_storage.Client(project=project)
        self.bucket = self.client.bucket(bucket_name)
    
    def upload_file(self, local_path: Union[str, Path], blob_name: str) -> bool:
        """Sube un archivo a GCS."""
        def _upload():
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(str(local_path))
        
        @retry(max_attempts=3, delay=1.0, strategy=RetryStrategy.EXPONENTIAL_BACKOFF)
        def _upload_with_retry():
            _upload()
        
        result, error = safe_execute(_upload_with_retry, default_value=False, log_errors=True)
        if result:
            logger.info("Archivo subido a GCS", bucket=self.bucket_name, blob=blob_name)
        elif error:
            logger.error("Error subiendo archivo a GCS", error=str(error))
        return result
    
    def download_file(self, blob_name: str, local_path: Union[str, Path]) -> bool:
        """Descarga un archivo de GCS."""
        def _download():
            blob = self.bucket.blob(blob_name)
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(local_path))
        
        @retry(max_attempts=3, delay=1.0, strategy=RetryStrategy.EXPONENTIAL_BACKOFF)
        def _download_with_retry():
            _download()
        
        result, error = safe_execute(_download_with_retry, default_value=False, log_errors=True)
        if result:
            logger.info("Archivo descargado de GCS", bucket=self.bucket_name, blob=blob_name)
        elif error:
            logger.error("Error descargando archivo de GCS", error=str(error))
        return result


class AzureBlobClient:
    """Cliente para Azure Blob Storage."""
    
    def __init__(self, connection_string: str, container_name: str):
        """
        Inicializa cliente Azure Blob.
        
        Args:
            connection_string: Cadena de conexión de Azure
            container_name: Nombre del contenedor
        """
        if not AZURE_AVAILABLE:
            raise ImportError("azure-storage-blob no está instalado")
        
        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)
    
    def upload_file(self, local_path: Union[str, Path], blob_name: str) -> bool:
        """Sube un archivo a Azure Blob."""
        def _upload():
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=blob_name
            )
            with open(local_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
        
        @retry(max_attempts=3, delay=1.0, strategy=RetryStrategy.EXPONENTIAL_BACKOFF)
        def _upload_with_retry():
            _upload()
        
        result, error = safe_execute(_upload_with_retry, default_value=False, log_errors=True)
        if result:
            logger.info("Archivo subido a Azure", container=self.container_name, blob=blob_name)
        elif error:
            logger.error("Error subiendo archivo a Azure", error=str(error))
        return result
    
    def download_file(self, blob_name: str, local_path: Union[str, Path]) -> bool:
        """Descarga un archivo de Azure Blob."""
        def _download():
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=blob_name
            )
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
        
        @retry(max_attempts=3, delay=1.0, strategy=RetryStrategy.EXPONENTIAL_BACKOFF)
        def _download_with_retry():
            _download()
        
        result, error = safe_execute(_download_with_retry, default_value=False, log_errors=True)
        if result:
            logger.info("Archivo descargado de Azure", container=self.container_name, blob=blob_name)
        elif error:
            logger.error("Error descargando archivo de Azure", error=str(error))
        return result

