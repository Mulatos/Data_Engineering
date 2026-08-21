import pandas as pd
import logging

logger = logging.getLogger(__name__)

def read_data(file_path):
    """Reads parquet file using pandas + pyarrow engine."""
    try:
        df = pd.read_parquet(file_path, engine="pyarrow")
        logger.info(f"Successfully read {len(df)} rows from {file_path}")
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise