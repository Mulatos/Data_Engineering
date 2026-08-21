from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "input" / "yellow_tripdata_2025-01.parquet"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

MANDATORY_COLUMNS = [
    "tpep_pickup_datetime", "tpep_dropoff_datetime", "passenger_count",
    "trip_distance", "PULocationID", "DOLocationID", "payment_type",
    "fare_amount", "total_amount"
]

NON_MANDATORY_COLUMNS = [
    "tip_amount", "tolls_amount", "extra", "airport_fee",
    "congestion_surcharge", "cbd_congestion_fee",
    "store_and_fwd_flag", "RatecodeID"
]

COLUMNS_TO_DROP = ["VendorID", "store_and_fwd_flag", "RatecodeID"]

AZURE_CONN_STRING = "your_connection_string_here"  # use env var in practice!
AZURE_CONTAINER_NAME = "taxi-data"