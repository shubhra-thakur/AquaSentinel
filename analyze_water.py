
import pandas as pd
from pathlib import Path

from data_quality import load_water_data, validate_water_data


REQUIRED_COLUMNS = [
    "zone",
    "date",
    "supplied_litres",
    "consumed_litres",
    "inlet_flow",
    "outlet_flow",
    "pressure"
]


def validate_analysis_input(df):
    """Check whether the input DataFrame is suitable for water analysis."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("Water dataset is empty.")

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {', '.join(missing_columns)}"
        )

    return True


def calculate_water_loss(df):
    """
    Calculate water loss and loss percentage for every record.

    Water loss = Supplied water - Consumed water
    Loss percentage = (Water loss / Supplied water) * 100
    """

    validate_analysis_input(df)

    result = df.copy()

    numeric_columns = [
        "supplied_litres",
        "consumed_litres"
    ]

    for column in numeric_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce"
        )

    if result[numeric_columns].isna().any().any():
        raise ValueError("Invalid numeric values found in water readings.")

    if (result["supplied_litres"] <= 0).any():
        raise ValueError("Supplied water must be greater than zero.")

    if (result["consumed_litres"] < 0).any():
        raise ValueError("Consumed water cannot be negative.")

    if (
        result["consumed_litres"] > result["supplied_litres"]
    ).any():
        raise ValueError("Consumed water cannot exceed supplied water.")

    result["loss_litres"] = (
        result["supplied_litres"] -
        result["consumed_litres"]
    )

    result["loss_percentage"] = (
        result["loss_litres"] /
        result["supplied_litres"]
    ) * 100

    result["loss_litres"] = result["loss_litres"].round(2)
    result["loss_percentage"] = result["loss_percentage"].round(2)

    return result


def calculate_flow_difference(df):
    """Calculate the difference between inlet and outlet flow."""

    validate_analysis_input(df)

    result = df.copy()

    for column in ["inlet_flow", "outlet_flow"]:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce"
        )

    if result[["inlet_flow", "outlet_flow"]].isna().any().any():
        raise ValueError("Invalid flow readings found.")

    if (result[["inlet_flow", "outlet_flow"]] < 0).any().any():
        raise ValueError("Flow readings cannot be negative.")

    result["flow_difference"] = (
        result["inlet_flow"] - result["outlet_flow"]
    ).round(2)

    return result


def get_zone_summary(df):
    """Generate water-loss summary for each zone."""

    analyzed_data = calculate_water_loss(df)

    summary = analyzed_data.groupby("zone").agg(
        total_supplied=("supplied_litres", "sum"),
        total_consumed=("consumed_litres", "sum"),
        total_loss=("loss_litres", "sum"),
        average_loss_percentage=("loss_percentage", "mean"),
        average_pressure=("pressure", "mean"),
        total_records=("zone", "count")
    ).reset_index()

    summary["overall_loss_percentage"] = (
        summary["total_loss"] /
        summary["total_supplied"]
    ) * 100

    summary["average_loss_percentage"] = (
        summary["average_loss_percentage"].round(2)
    )

    summary["overall_loss_percentage"] = (
        summary["overall_loss_percentage"].round(2)
    )

    summary["average_pressure"] = (
        summary["average_pressure"].round(2)
    )

    return summary


def get_overall_summary(df):
    """Generate overall water distribution summary."""

    analyzed_data = calculate_water_loss(df)

    total_supplied = analyzed_data["supplied_litres"].sum()
    total_consumed = analyzed_data["consumed_litres"].sum()
    total_loss = analyzed_data["loss_litres"].sum()

    loss_percentage = (
        (total_loss / total_supplied) * 100
        if total_supplied > 0 else 0
    )

    return {
        "total_supplied": round(float(total_supplied), 2),
        "total_consumed": round(float(total_consumed), 2),
        "total_loss": round(float(total_loss), 2),
        "loss_percentage": round(float(loss_percentage), 2),
        "total_zones": int(analyzed_data["zone"].nunique()),
        "total_records": int(len(analyzed_data))
    }


def analyze_water_data(file_path):
    """Load, validate and analyze water data from a CSV file."""

    df = load_water_data(file_path)

    quality_report = validate_water_data(df)

    if not quality_report["is_valid"]:
        raise ValueError(
            "Data quality validation failed. "
            f"Found {quality_report['invalid_records']} invalid records."
        )

    analyzed_data = calculate_water_loss(df)
    flow_data = calculate_flow_difference(analyzed_data)

    return {
        "analyzed_data": analyzed_data,
        "zone_summary": get_zone_summary(df),
        "overall_summary": get_overall_summary(df),
        "flow_data": flow_data
    }


if __name__ == "__main__":

    file_path = Path("data") / "water_data.csv"

    try:
        results = analyze_water_data(file_path)

        print("\n========== AQUASENTINEL WATER ANALYSIS ==========")

        print("\nOverall Summary:")
        for key, value in results["overall_summary"].items():
            print(f"{key}: {value}")

        print("\nZone-wise Summary:")
        print(results["zone_summary"].to_string(index=False))

        print("\nDetailed Water Loss:")
        print(
            results["analyzed_data"][
                ["zone", "supplied_litres", "consumed_litres",
                 "loss_litres", "loss_percentage"]
            ].to_string(index=False)
        )

    except (FileNotFoundError, ValueError, TypeError) as error:
        print("Water analysis failed:", error)
