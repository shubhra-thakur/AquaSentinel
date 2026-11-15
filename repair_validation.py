
import pandas as pd
from pathlib import Path

from anomaly_detection import detect_anomalies


REQUIRED_REPAIR_COLUMNS = [
    "zone",
    "repair_date",
    "issue_type",
    "leakage_confirmed",
    "repair_status"
]


def load_repair_data(file_path):
    """Load historical repair records from a CSV file."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Repair file not found: {path}")

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        raise ValueError("Historical repair file is empty.")
    except pd.errors.ParserError as error:
        raise ValueError(f"Invalid repair CSV format: {error}")


def validate_repair_data(df):
    """Validate the structure and contents of repair records."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("Historical repair dataset is empty.")

    missing_columns = [
        column for column in REQUIRED_REPAIR_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing repair columns: "
            + ", ".join(missing_columns)
        )

    data = df.copy()

    # Check missing values
    for column in REQUIRED_REPAIR_COLUMNS:
        if data[column].isna().any():
            raise ValueError(
                f"Missing values found in {column}."
            )

    # Normalize text fields
    text_columns = [
        "zone",
        "issue_type",
        "leakage_confirmed",
        "repair_status"
    ]

    for column in text_columns:
        data[column] = data[column].astype(str).str.strip()

        if data[column].eq("").any():
            raise ValueError(
                f"Empty values found in {column}."
            )

    # Validate dates
    data["repair_date"] = pd.to_datetime(
        data["repair_date"],
        errors="coerce"
    )

    if data["repair_date"].isna().any():
        raise ValueError("Invalid repair dates found.")

    # Validate confirmation values
    valid_confirmation = {"yes", "no"}

    confirmations = (
        data["leakage_confirmed"].str.lower()
    )

    if not confirmations.isin(valid_confirmation).all():
        raise ValueError(
            "leakage_confirmed must contain Yes or No."
        )

    # Validate repair status
    valid_statuses = {
        "repaired",
        "pending",
        "investigated",
        "in progress",
        "not repaired"
    }

    statuses = data["repair_status"].str.lower()

    if not statuses.isin(valid_statuses).all():
        raise ValueError("Unknown repair status found.")

    data["leakage_confirmed"] = (
        confirmations.map({"yes": "Yes", "no": "No"})
    )

    return data


def match_repair_records(suspicious_zones, repair_data):
    """Match suspicious zones with their historical repair records."""

    if not isinstance(suspicious_zones, pd.DataFrame):
        raise TypeError("Suspicious zones must be a DataFrame.")

    if "zone" not in suspicious_zones.columns:
        raise ValueError("Zone column missing in anomaly results.")

    repairs = validate_repair_data(repair_data)

    if suspicious_zones["zone"].isna().any():
        raise ValueError("Suspicious zones contain missing zone names.")

    results = []

    for zone in suspicious_zones["zone"].unique():

        zone_repairs = repairs[
            repairs["zone"].str.casefold()
            == str(zone).strip().casefold()
        ].copy()

        confirmed_count = int(
            (zone_repairs["leakage_confirmed"] == "Yes").sum()
        )

        pending_count = int(
            (zone_repairs["repair_status"].str.lower() == "pending").sum()
        )

        if zone_repairs.empty:
            validation_status = "No Historical Record"
            evidence = "No matching repair record found."

        elif confirmed_count > 0:
            validation_status = "Historical Leakage Confirmed"

            evidence = (
                f"{confirmed_count} historical record(s) "
                "confirm leakage."
            )

        else:
            validation_status = "No Confirmed Leakage"
            evidence = (
                "Historical records exist, but leakage "
                "has not been confirmed."
            )

        results.append({
            "zone": zone,
            "historical_records": int(len(zone_repairs)),
            "confirmed_leakages": confirmed_count,
            "pending_repairs": pending_count,
            "validation_status": validation_status,
            "evidence": evidence,
            "repair_records": zone_repairs.to_dict(orient="records")
        })

    return pd.DataFrame(results)


def validate_suspicious_zones(
    water_data,
    repair_data,
    **thresholds
):
    """Detect anomalies and compare them with repair history."""

    anomalies = detect_anomalies(
        water_data,
        **thresholds
    )

    suspicious_zones = anomalies[
        anomalies["is_suspicious"]
    ].copy()

    matched_records = match_repair_records(
        suspicious_zones,
        repair_data
    )

    if suspicious_zones.empty:
        return anomalies, matched_records

    final_results = suspicious_zones.merge(
        matched_records.drop(columns=["repair_records"]),
        on="zone",
        how="left"
    )

    return anomalies, final_results


def generate_repair_validation_report(
    water_data,
    repair_data,
    **thresholds
):
    """Generate a complete historical repair validation report."""

    anomalies, validation_results = validate_suspicious_zones(
        water_data,
        repair_data,
        **thresholds
    )

    confirmed = int(
        (
            validation_results["validation_status"]
            == "Historical Leakage Confirmed"
        ).sum()
    )

    no_history = int(
        (
            validation_results["validation_status"]
            == "No Historical Record"
        ).sum()
    )

    not_confirmed = int(
        (
            validation_results["validation_status"]
            == "No Confirmed Leakage"
        ).sum()
    )

    return {
        "total_zones_analyzed": int(len(anomalies)),
        "total_suspicious_zones": int(
            anomalies["is_suspicious"].sum()
        ),
        "historically_confirmed_zones": confirmed,
        "zones_without_history": no_history,
        "zones_without_confirmed_leakage": not_confirmed,
        "validation_results": validation_results.to_dict(
            orient="records"
        )
    }


if __name__ == "__main__":

    from data_quality import (
        load_water_data,
        validate_water_data
    )

    water_file = Path("data") / "water_data.csv"
    repair_file = Path("data") / "historical_repairs.csv"

    try:
        water_data = load_water_data(water_file)
        repair_data = load_repair_data(repair_file)

        quality_report = validate_water_data(water_data)

        if not quality_report["is_valid"]:
            raise ValueError(
                "Water data quality validation failed."
            )

        report = generate_repair_validation_report(
            water_data,
            repair_data
        )

        print("\n========== AQUASENTINEL REPAIR VALIDATION ==========")

        print("Zones Analyzed:", report["total_zones_analyzed"])
        print("Suspicious Zones:", report["total_suspicious_zones"])
        print(
            "Historically Confirmed:",
            report["historically_confirmed_zones"]
        )
        print("No Historical Record:", report["zones_without_history"])
        print(
            "Not Confirmed:",
            report["zones_without_confirmed_leakage"]
        )

        print("\nDetailed Validation Results:")

        for result in report["validation_results"]:
            print("\nZone:", result["zone"])
            print("Risk:", result["risk_level"])
            print("Validation:", result["validation_status"])
            print("Evidence:", result["evidence"])
            print("Pending Repairs:", result["pending_repairs"])

    except (FileNotFoundError, ValueError, TypeError) as error:
        print("Repair validation failed:", error)
