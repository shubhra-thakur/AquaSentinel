
import pandas as pd
from pathlib import Path


# Required columns in water_data.csv
REQUIRED_COLUMNS = [
    "zone",
    "date",
    "supplied_litres",
    "consumed_litres",
    "inlet_flow",
    "outlet_flow",
    "pressure"
]

# Columns that must contain numeric values
NUMERIC_COLUMNS = [
    "supplied_litres",
    "consumed_litres",
    "inlet_flow",
    "outlet_flow",
    "pressure"
]


def load_water_data(file_path):
    """Load water data from a CSV file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        raise ValueError("The CSV file is empty.")
    except pd.errors.ParserError as error:
        raise ValueError(f"Invalid CSV format: {error}")


def check_required_columns(df):
    """Check whether all required columns are present."""
    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    return missing


def validate_water_data(df):
    """
    Validate water dataset and return a detailed quality report.

    Checks:
    - Missing columns
    - Missing values
    - Duplicate records
    - Invalid dates
    - Invalid numeric values
    - Negative readings
    - Zero or negative supplied water
    - Consumption greater than supply
    - Invalid flow readings
    - Invalid pressure readings
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    issues = []
    issue_rows = set()

    total_records = len(df)

    if df.empty:
        return {
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "total_issues": 0,
            "is_valid": False,
            "issues": ["Dataset contains no records."],
            "issue_summary": {}
        }

    missing_columns = check_required_columns(df)

    if missing_columns:
        return {
            "total_records": total_records,
            "valid_records": 0,
            "invalid_records": total_records,
            "total_issues": len(missing_columns),
            "is_valid": False,
            "issues": [
                f"Missing required column: {column}"
                for column in missing_columns
            ],
            "issue_summary": {
                "missing_columns": len(missing_columns)
            }
        }

    # Work on a copy to avoid changing the original dataset
    data = df.copy()

    # 1. Check missing values
    for column in REQUIRED_COLUMNS:
        missing_indices = data[
            data[column].isnull()
        ].index

        for index in missing_indices:
            issues.append(
                f"Row {index + 1}: Missing value in {column}"
            )
            issue_rows.add(index)

    # 2. Check duplicate records
    duplicate_indices = data[
        data.duplicated()
    ].index

    for index in duplicate_indices:
        issues.append(f"Row {index + 1}: Duplicate record")
        issue_rows.add(index)

    # 3. Validate zone names
    invalid_zones = (
        data["zone"].isna()
        | data["zone"].astype(str).str.strip().eq("")
    )

    for index in data[invalid_zones].index:
        issues.append(f"Row {index + 1}: Invalid zone name")
        issue_rows.add(index)

    # 4. Validate dates
    parsed_dates = pd.to_datetime(
        data["date"],
        errors="coerce"
    )

    for index in parsed_dates[parsed_dates.isna()].index:
        issues.append(f"Row {index + 1}: Invalid date")
        issue_rows.add(index)

    # 5. Convert and validate numeric columns
    for column in NUMERIC_COLUMNS:
        numeric_values = pd.to_numeric(
            data[column],
            errors="coerce"
        )

        invalid_values = numeric_values.isna()

        for index in numeric_values[invalid_values].index:
            issues.append(
                f"Row {index + 1}: Invalid numeric value in {column}"
            )
            issue_rows.add(index)

        data[column] = numeric_values

        # Negative readings
        negative_values = numeric_values < 0

        for index in numeric_values[negative_values].index:
            issues.append(
                f"Row {index + 1}: Negative value in {column}"
            )
            issue_rows.add(index)

    # 6. Supplied water must be greater than zero
    invalid_supply = data["supplied_litres"] <= 0

    for index in data[invalid_supply].index:
        if pd.notna(data.loc[index, "supplied_litres"]):
            issues.append(
                f"Row {index + 1}: Supplied water must be greater than zero"
            )
            issue_rows.add(index)

    # 7. Consumption cannot exceed supplied water
    invalid_consumption = (
        data["consumed_litres"] > data["supplied_litres"]
    )

    for index in data[invalid_consumption].index:
        issues.append(
            f"Row {index + 1}: Consumption exceeds supplied water"
        )
        issue_rows.add(index)

    # 8. Outlet flow cannot exceed inlet flow
    invalid_flow = data["outlet_flow"] > data["inlet_flow"]

    for index in data[invalid_flow].index:
        issues.append(
            f"Row {index + 1}: Outlet flow exceeds inlet flow"
        )
        issue_rows.add(index)

    # 9. Pressure must be greater than zero
    invalid_pressure = data["pressure"] <= 0

    for index in data[invalid_pressure].index:
        if pd.notna(data.loc[index, "pressure"]):
            issues.append(
                f"Row {index + 1}: Pressure must be greater than zero"
            )
            issue_rows.add(index)

    invalid_records = len(issue_rows)
    valid_records = total_records - invalid_records

    # Count issues by category
    issue_summary = {}

    for issue in issues:
        category = issue.split(": ", 1)[-1].split(" ")[0]

        issue_summary[category] = (
            issue_summary.get(category, 0) + 1
        )

    return {
        "total_records": total_records,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "total_issues": len(issues),
        "is_valid": len(issues) == 0,
        "issues": issues,
        "issue_summary": issue_summary
    }


def generate_quality_report(file_path):
    """Load data and generate its quality report."""
    df = load_water_data(file_path)
    return validate_water_data(df)


if __name__ == "__main__":

    file_path = Path("data") / "water_data.csv"

    try:
        report = generate_quality_report(file_path)

        print("\n========== AQUASENTINEL DATA QUALITY REPORT ==========")
        print("Total Records:", report["total_records"])
        print("Valid Records:", report["valid_records"])
        print("Invalid Records:", report["invalid_records"])
        print("Total Issues:", report["total_issues"])
        print("Dataset Valid:", report["is_valid"])

        print("\nIssue Details:")

        if report["issues"]:
            for issue in report["issues"]:
                print("-", issue)
        else:
            print("No data quality issues found.")

        print("\nIssue Summary:", report["issue_summary"])

    except (FileNotFoundError, ValueError, TypeError) as error:
        print("Data validation failed:", error)
