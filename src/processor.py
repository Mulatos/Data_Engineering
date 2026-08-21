import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def process_data(df, columns_to_drop):
    df = df.copy()

    # Drop unwanted columns (only if they exist)
    df = df.drop(columns=[c for c in columns_to_drop if c in df.columns], errors="ignore")

    # trip_duration_minutes
    df["trip_duration_minutes"] = (
        (df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]).dt.total_seconds() / 60
    )

    # average_speed_mph - guard against division by zero
    df["average_speed_mph"] = np.where(
        df["trip_duration_minutes"] > 0,
        df["trip_distance"] / (df["trip_duration_minutes"] / 60),
        np.nan
    )

    # pickup_year / pickup_month
    df["pickup_year"] = df["tpep_pickup_datetime"].dt.year
    df["pickup_month"] = df["tpep_pickup_datetime"].dt.month

    # revenue_per_mile - guard against division by zero
    df["revenue_per_mile"] = np.where(
        df["trip_distance"] > 0,
        df["total_amount"] / df["trip_distance"],
        np.nan
    )

    # trip_distance_category
    df["trip_distance_category"] = pd.cut(
        df["trip_distance"],
        bins=[-np.inf, 2, 10, np.inf],
        labels=["Short", "Medium", "Long"]
    )

    # fare_category
    df["fare_category"] = pd.cut(
        df["fare_amount"],
        bins=[-np.inf, 20, 50, np.inf],
        labels=["Low", "Medium", "High"],
        right=False
    )

    # trip_time_of_day based on pickup hour
    hour = df["tpep_pickup_datetime"].dt.hour
    conditions = [
        (hour >= 0) & (hour < 6),
        (hour >= 6) & (hour < 12),
        (hour >= 12) & (hour < 18),
        (hour >= 18) & (hour <= 23),
    ]
    choices = ["Night", "Morning", "Afternoon", "Evening"]
    df["trip_time_of_day"] = np.select(conditions, choices, default="Unknown")

    logger.info(f"Processing complete. Output shape: {df.shape}")
    return df