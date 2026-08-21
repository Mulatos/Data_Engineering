import os
import logging
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)

def write_local(df, output_path):
    df.to_parquet(output_path, engine="pyarrow", index=False)
    logger.info(f"Data written locally to {output_path}")

def write_azure(local_file_path, container_name, blob_name, connection_string):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()
        with open(local_file_path, "rb") as data:
            container_client.upload_blob(name=blob_name, data=data, overwrite=True)
        logger.info(f"Uploaded {blob_name} to Azure container {container_name}")
    except Exception as e:
        logger.error(f"Azure upload failed: {e}")
        raise