import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    pass


def validate_schema(df, mandatory_columns):
    """Check that all mandatory columns exist."""
    missing = [col for col in mandatory_columns if col not in df.columns]
    if missing:
        raise ValidationError(f"Missing mandatory columns: {missing}")
    return True


def validate_data(df, mandatory_columns):
    """
    Applies column-specific validation rules.
    Returns (valid_df, invalid_df, report)
    """
    validate_schema(df, mandatory_columns)

    df = df.copy()
    df["_is_valid"] = True
    report = {}

    # 1. Datetime checks
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"], errors="coerce")
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"], errors="coerce")

    invalid_dates = df["tpep_pickup_datetime"].isna() | df["tpep_dropoff_datetime"].isna()
    df.loc[invalid_dates, "_is_valid"] = False
    report["invalid_datetimes"] = int(invalid_dates.sum())

    # dropoff must be after pickup
    bad_order = df["tpep_dropoff_datetime"] <= df["tpep_pickup_datetime"]
    df.loc[bad_order, "_is_valid"] = False
    report["dropoff_before_pickup"] = int(bad_order.sum())

    # Trips within January 2025 only (sanity check against dataset date range)
    out_of_range = (
        (df["tpep_pickup_datetime"].dt.year != 2025) |
        (df["tpep_pickup_datetime"].dt.month != 1)
    )
    df.loc[out_of_range, "_is_valid"] = False
    report["pickup_out_of_month_range"] = int(out_of_range.sum())

    # 2. passenger_count: must be > 0 and reasonable (<=8)
    invalid_passengers = ~df["passenger_count"].between(1, 8, inclusive="both")
    invalid_passengers = invalid_passengers | df["passenger_count"].isna()
    df.loc[invalid_passengers, "_is_valid"] = False
    report["invalid_passenger_count"] = int(invalid_passengers.sum())

    # 3. trip_distance: must be > 0 and < 500 (sanity cap for NYC)
    invalid_distance = ~df["trip_distance"].between(0.01, 500, inclusive="both")
    invalid_distance = invalid_distance | df["trip_distance"].isna()
    df.loc[invalid_distance, "_is_valid"] = False
    report["invalid_trip_distance"] = int(invalid_distance.sum())

    # 4. PULocationID / DOLocationID: valid NYC zone IDs (1-263)
    for col in ["PULocationID", "DOLocationID"]:
        invalid_zone = ~df[col].between(1, 263, inclusive="both") | df[col].isna()
        df.loc[invalid_zone, "_is_valid"] = False
        report[f"invalid_{col}"] = int(invalid_zone.sum())

    # 5. payment_type: must be in known set (1-6)
    valid_payment_types = [1, 2, 3, 4, 5, 6]
    invalid_payment = ~df["payment_type"].isin(valid_payment_types)
    df.loc[invalid_payment, "_is_valid"] = False
    report["invalid_payment_type"] = int(invalid_payment.sum())

    # 6. fare_amount: must be >= 0 (allow 0, reject negative or absurd values)
    invalid_fare = ~df["fare_amount"].between(0, 2000, inclusive="both") | df["fare_amount"].isna()
    df.loc[invalid_fare, "_is_valid"] = False
    report["invalid_fare_amount"] = int(invalid_fare.sum())

    # 7. total_amount: must be >= 0
    invalid_total = ~df["total_amount"].between(0, 2000, inclusive="both") | df["total_amount"].isna()
    df.loc[invalid_total, "_is_valid"] = False
    report["invalid_total_amount"] = int(invalid_total.sum())

    # 8. Non-mandatory columns: only validate if present, don't invalidate row on missing
    optional_numeric_cols = ["tip_amount", "tolls_amount", "extra",
                              "airport_fee", "congestion_surcharge", "cbd_congestion_fee"]
    for col in optional_numeric_cols:
        if col in df.columns:
            invalid_val = df[col] < 0
            df.loc[invalid_val.fillna(False), "_is_valid"] = False
            report[f"invalid_{col}"] = int(invalid_val.fillna(False).sum())

    valid_df = df[df["_is_valid"]].drop(columns=["_is_valid"])
    invalid_df = df[~df["_is_valid"]].drop(columns=["_is_valid"])

    report["total_rows"] = len(df)
    report["valid_rows"] = len(valid_df)
    report["invalid_rows"] = len(invalid_df)

    logger.info(f"Validation report: {report}")

    return valid_df, invalid_df, report

def backup_validate(df):
    errors = []
    if (df["trip_duration_minutes"] < 0).any():
        errors.append("Negative trip durations found post-processing")
    if df["trip_time_of_day"].isnull().any():
        errors.append("Null trip_time_of_day values found")
    if errors:
        raise ValueError(f"Backup validation failed: {errors}")
    return True