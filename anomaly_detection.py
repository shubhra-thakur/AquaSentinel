
import pandas as pd

from analyze_water import calculate_water_loss


# Configurable detection thresholds
DEFAULT_LOSS_THRESHOLD = 10.0
DEFAULT_PRESSURE_THRESHOLD = 30.0
DEFAULT_FLOW_DIFFERENCE_THRESHOLD = 15.0


def validate_thresholds(
    loss_threshold,
    pressure_threshold,
    flow_difference_threshold
):
    """Validate anomaly detection thresholds."""

    thresholds = {
        "loss_threshold": loss_threshold,
        "pressure_threshold": pressure_threshold,
        "flow_difference_threshold": flow_difference_threshold
    }

    for name, value in thresholds.items():
        if not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be numeric.")

        if value < 0:
            raise ValueError(f"{name} cannot be negative.")


def detect_water_loss_anomalies(
    df,
    loss_threshold=DEFAULT_LOSS_THRESHOLD
):
    """Detect records with unusually high water-loss percentages."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if loss_threshold < 0:
        raise ValueError("Loss threshold cannot be negative.")

    analyzed_data = calculate_water_loss(df)

    anomalies = analyzed_data[
        analyzed_data["loss_percentage"] > loss_threshold
    ].copy()

    anomalies["anomaly_reason"] = (
        "Water loss exceeds " + str(loss_threshold) + "%"
    )

    return anomalies


def detect_pressure_anomalies(
    df,
    pressure_threshold=DEFAULT_PRESSURE_THRESHOLD
):
    """Detect records with unusually low pressure."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if "pressure" not in df.columns:
        raise ValueError("Pressure column is missing.")

    if pressure_threshold < 0:
        raise ValueError("Pressure threshold cannot be negative.")

    data = df.copy()
    data["pressure"] = pd.to_numeric(
        data["pressure"],
        errors="coerce"
    )

    if data["pressure"].isna().any():
        raise ValueError("Invalid pressure readings found.")

    anomalies = data[
        data["pressure"] < pressure_threshold
    ].copy()

    anomalies["anomaly_reason"] = (
        "Pressure below " + str(pressure_threshold)
    )

    return anomalies


def detect_flow_anomalies(
    df,
    flow_difference_threshold=DEFAULT_FLOW_DIFFERENCE_THRESHOLD
):
    """Detect unusually large inlet and outlet flow differences."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    required = ["inlet_flow", "outlet_flow"]

    for column in required:
        if column not in df.columns:
            raise ValueError(f"Missing column: {column}")

    if flow_difference_threshold < 0:
        raise ValueError("Flow threshold cannot be negative.")

    data = df.copy()

    for column in required:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    if data[required].isna().any().any():
        raise ValueError("Invalid flow readings found.")

    if (data[required] < 0).any().any():
        raise ValueError("Flow readings cannot be negative.")

    data["flow_difference"] = (
        data["inlet_flow"] - data["outlet_flow"]
    )

    anomalies = data[
        data["flow_difference"] > flow_difference_threshold
    ].copy()

    anomalies["anomaly_reason"] = (
        "Inlet-outlet flow difference exceeds "
        + str(flow_difference_threshold)
    )

    return anomalies


def classify_risk(reasons):
    """Classify a zone based on the number of anomaly indicators."""

    if len(reasons) >= 3:
        return "High"

    if len(reasons) == 2:
        return "Medium"

    if len(reasons) == 1:
        return "Low"

    return "Normal"


def detect_anomalies(
    df,
    loss_threshold=DEFAULT_LOSS_THRESHOLD,
    pressure_threshold=DEFAULT_PRESSURE_THRESHOLD,
    flow_difference_threshold=DEFAULT_FLOW_DIFFERENCE_THRESHOLD
):
    """
    Detect suspicious zones using water loss, pressure and flow.

    Returns a DataFrame with:
    zone, loss_percentage, pressure, flow_difference,
    risk_level and anomaly_reasons.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    validate_thresholds(
        loss_threshold,
        pressure_threshold,
        flow_difference_threshold
    )

    analyzed_data = calculate_water_loss(df)

    required = ["pressure", "inlet_flow", "outlet_flow"]

    for column in required:
        if column not in analyzed_data.columns:
            raise ValueError(f"Missing column: {column}")

    data = analyzed_data.copy()

    for column in required:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    if data[required].isna().any().any():
        raise ValueError("Invalid pressure or flow readings found.")

    if (data[required] < 0).any().any():
        raise ValueError("Pressure and flow readings cannot be negative.")

    data["flow_difference"] = (
        data["inlet_flow"] - data["outlet_flow"]
    )

    zone_results = []

    for zone, group in data.groupby("zone"):

        reasons = []

        avg_loss = group["loss_percentage"].mean()
        avg_pressure = group["pressure"].mean()
        avg_flow_difference = group["flow_difference"].mean()

        if avg_loss > loss_threshold:
            reasons.append("High water loss")

        if avg_pressure < pressure_threshold:
            reasons.append("Low pressure")

        if avg_flow_difference > flow_difference_threshold:
            reasons.append("High flow difference")

        risk_level = classify_risk(reasons)

        zone_results.append({
            "zone": zone,
            "loss_percentage": round(float(avg_loss), 2),
            "pressure": round(float(avg_pressure), 2),
            "flow_difference": round(
                float(avg_flow_difference), 2
            ),
            "risk_level": risk_level,
            "anomaly_reasons": reasons,
            "is_suspicious": len(reasons) > 0
        })

    return pd.DataFrame(zone_results)


def get_suspicious_zones(df, **thresholds):
    """Return only zones identified as suspicious."""

    results = detect_anomalies(df, **thresholds)

    return results[
        results["is_suspicious"]
    ].reset_index(drop=True)


def generate_anomaly_report(df, **thresholds):
    """Generate a complete anomaly detection report."""

    results = detect_anomalies(df, **thresholds)

    suspicious = results[
        results["is_suspicious"]
    ]

    return {
        "total_zones": int(len(results)),
        "suspicious_zones": int(len(suspicious)),
        "normal_zones": int(
            len(results) - len(suspicious)
        ),
        "high_risk_zones": int(
            (results["risk_level"] == "High").sum()
        ),
        "medium_risk_zones": int(
            (results["risk_level"] == "Medium").sum()
        ),
        "low_risk_zones": int(
            (results["risk_level"] == "Low").sum()
        ),
        "results": results.to_dict(orient="records")
    }


if __name__ == "__main__":

    from pathlib import Path
    from data_quality import (
        load_water_data,
        validate_water_data
    )

    file_path = Path("data") / "water_data.csv"

    try:
        water_data = load_water_data(file_path)

        quality_report = validate_water_data(water_data)

        if not quality_report["is_valid"]:
            raise ValueError(
                "Data quality validation failed. "
                "Please correct the CSV before analysis."
            )

        report = generate_anomaly_report(water_data)

        print("\n========== AQUASENTINEL ANOMALY REPORT ==========")

        print("Total Zones:", report["total_zones"])
        print("Suspicious Zones:", report["suspicious_zones"])
        print("Normal Zones:", report["normal_zones"])
        print("High Risk:", report["high_risk_zones"])
        print("Medium Risk:", report["medium_risk_zones"])
        print("Low Risk:", report["low_risk_zones"])

        print("\nZone-wise Detection Results:")

        for result in report["results"]:
            print("\nZone:", result["zone"])
            print("Risk:", result["risk_level"])
            print("Loss:", result["loss_percentage"], "%")
            print("Pressure:", result["pressure"])
            print("Reasons:", result["anomaly_reasons"])

    except (FileNotFoundError, ValueError, TypeError) as error:
        print("Anomaly detection failed:", error)
