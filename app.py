
"""
AquaSentinel - Main Flask Application

Connects all project modules and provides API endpoints
for the interactive water monitoring dashboard.
"""

from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request

from data_quality import (
    load_water_data,
    validate_water_data
)

from analyze_water import (
    analyze_water_data
)

from anomaly_detection import (
    detect_anomalies
)

from repair_validation import (
    load_repair_data,
    generate_repair_validation_report
)

from advisory import (
    generate_all_advisories,
    add_repair_context,
    generate_advisory_summary,
    generate_household_advisory
)


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

WATER_FILE = DATA_DIR / "water_data.csv"

REPAIR_FILE = DATA_DIR / "historical_repairs.csv"

app = Flask(__name__)

app.config["JSON_SORT_KEYS"] = False


# --------------------------------------------------
# JSON CONVERSION
# --------------------------------------------------

def make_json_safe(value):
    """Convert pandas and NumPy values into JSON-safe values."""

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if value is None:
        return None

    if hasattr(value, "item"):
        return make_json_safe(value.item())

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return value


# --------------------------------------------------
# DATA LOADING AND VALIDATION
# --------------------------------------------------

def load_project_data():
    """Load and validate both project datasets."""

    water_data = load_water_data(WATER_FILE)

    quality_report = validate_water_data(water_data)

    if not quality_report["is_valid"]:
        raise ValueError(
            "Water data validation failed. "
            f"{quality_report['invalid_records']} invalid records found."
        )

    repair_data = load_repair_data(REPAIR_FILE)

    return water_data, repair_data, quality_report


# --------------------------------------------------
# DASHBOARD DATA GENERATION
# --------------------------------------------------

def build_dashboard_data():
    """Generate all information required by the dashboard."""

    water_data, repair_data, quality_report = load_project_data()

    # Water analysis
    analysis = analyze_water_data(WATER_FILE)

    # Anomaly detection
    anomalies = detect_anomalies(water_data)

    suspicious_zones = anomalies[
        anomalies["is_suspicious"]
    ].copy()

    # Historical repair validation
    repair_report = generate_repair_validation_report(
        water_data,
        repair_data
    )

    # Network recommendations and utility scoring
    advisories = generate_all_advisories(water_data)

    advisories = add_repair_context(
        advisories,
        repair_report["validation_results"]
    )

    advisory_summary = generate_advisory_summary(advisories)

    # Remove detailed repair records from dashboard response.
    repair_results = [
        {
            key: value
            for key, value in record.items()
            if key != "repair_records"
        }
        for record in repair_report["validation_results"]
    ]

    return {
        "success": True,

        "quality": {
            "total_records": quality_report["total_records"],
            "valid_records": quality_report["valid_records"],
            "invalid_records": quality_report["invalid_records"],
            "total_issues": quality_report["total_issues"],
            "is_valid": quality_report["is_valid"]
        },

        "summary": analysis["overall_summary"],

        "zones": analysis["zone_summary"].to_dict(
            orient="records"
        ),

        "anomalies": anomalies.to_dict(
            orient="records"
        ),

        "suspicious_zones": suspicious_zones.to_dict(
            orient="records"
        ),

        "repair_validation": {
            "total_zones_analyzed": repair_report[
                "total_zones_analyzed"
            ],
            "total_suspicious_zones": repair_report[
                "total_suspicious_zones"
            ],
            "historically_confirmed_zones": repair_report[
                "historically_confirmed_zones"
            ],
            "zones_without_history": repair_report[
                "zones_without_history"
            ],
            "zones_without_confirmed_leakage": repair_report[
                "zones_without_confirmed_leakage"
            ],
            "results": repair_results
        },

        "advisories": advisories,

        "advisory_summary": advisory_summary
    }


# --------------------------------------------------
# MAIN DASHBOARD ROUTE
# --------------------------------------------------

@app.route("/")
def home():
    """Display the main dashboard."""

    return render_template("index.html")


# --------------------------------------------------
# HEALTH CHECK API
# --------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    """Check whether the Flask application is running."""

    return jsonify({
        "success": True,
        "message": "AquaSentinel API is running."
    }), 200


# --------------------------------------------------
# COMPLETE DASHBOARD API
# --------------------------------------------------

@app.route("/api/dashboard", methods=["GET"])
def dashboard_api():
    """Return complete dashboard information."""

    try:
        data = build_dashboard_data()

        return jsonify(make_json_safe(data)), 200

    except FileNotFoundError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 404

    except (ValueError, TypeError) as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Dashboard API failed.")

        return jsonify({
            "success": False,
            "error": "An unexpected server error occurred."
        }), 500


# --------------------------------------------------
# ZONE-WISE DATA API
# --------------------------------------------------

@app.route("/api/zones", methods=["GET"])
def zones_api():
    """Return zone-wise water analysis."""

    try:
        data = build_dashboard_data()

        return jsonify({
            "success": True,
            "zones": data["zones"]
        }), 200

    except (FileNotFoundError, ValueError, TypeError) as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Zone API failed.")

        return jsonify({
            "success": False,
            "error": "Unable to retrieve zone data."
        }), 500


# --------------------------------------------------
# ANOMALY DETECTION API
# --------------------------------------------------

@app.route("/api/anomalies", methods=["GET"])
def anomalies_api():
    """Return suspicious and normal zones."""

    try:
        data = build_dashboard_data()

        return jsonify({
            "success": True,
            "anomalies": data["anomalies"],
            "suspicious_zones": data["suspicious_zones"]
        }), 200

    except (FileNotFoundError, ValueError, TypeError) as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Anomaly API failed.")

        return jsonify({
            "success": False,
            "error": "Unable to retrieve anomaly data."
        }), 500


# --------------------------------------------------
# REPAIR VALIDATION API
# --------------------------------------------------

@app.route("/api/repairs", methods=["GET"])
def repairs_api():
    """Return historical repair validation results."""

    try:
        data = build_dashboard_data()

        return jsonify({
            "success": True,
            "repair_validation": data["repair_validation"]
        }), 200

    except (FileNotFoundError, ValueError, TypeError) as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Repair API failed.")

        return jsonify({
            "success": False,
            "error": "Unable to retrieve repair data."
        }), 500


# --------------------------------------------------
# NETWORK ADVISORY API
# --------------------------------------------------

@app.route("/api/advisories", methods=["GET"])
def advisories_api():
    """
    Return network recommendations, utility scores,
    decision evidence and prioritized actions.
    """

    try:
        data = build_dashboard_data()

        return jsonify({
            "success": True,
            "summary": data["advisory_summary"],
            "advisories": data["advisories"]
        }), 200

    except (FileNotFoundError, ValueError, TypeError) as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Advisory API failed.")

        return jsonify({
            "success": False,
            "error": "Unable to generate advisories."
        }), 500


# --------------------------------------------------
# HOUSEHOLD ADVISORY API
# --------------------------------------------------

@app.route("/api/household-advisory", methods=["GET"])
def household_advisory_api():
    """
    Retrieve household water-saving recommendations.

    Example:
    /api/household-advisory?q=How%20can%20I%20save%20water
    """

    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({
            "success": False,
            "error": "Please provide a household query using the q parameter."
        }), 400

    try:
        result = generate_household_advisory(query)

        status_code = 200 if result["success"] else 503

        return jsonify(
            make_json_safe(result)
        ), status_code

    except (ValueError, TypeError) as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Household advisory API failed.")

        return jsonify({
            "success": False,
            "error": "Unable to generate household recommendations."
        }), 500


# --------------------------------------------------
# APPLICATION ERROR HANDLERS
# --------------------------------------------------

@app.errorhandler(404)
def page_not_found(error):
    """Handle unavailable routes."""

    return jsonify({
        "success": False,
        "error": "Requested page or API endpoint was not found."
    }), 404


@app.errorhandler(500)
def internal_server_error(error):
    """Handle unexpected application errors."""

    return jsonify({
        "success": False,
        "error": "Internal server error."
    }), 500


# --------------------------------------------------
# APPLICATION START
# --------------------------------------------------

if __name__ == "__main__":

    print("\n========================================")
    print("       AQUASENTINEL STARTING")
    print("========================================")

    print("Dashboard: http://127.0.0.1:5000")
    print("Health API: http://127.0.0.1:5000/api/health")
    print("Dashboard API: http://127.0.0.1:5000/api/dashboard")
    print("Advisory API: http://127.0.0.1:5000/api/advisories")
    print("Household API: http://127.0.0.1:5000/api/household-advisory?q=save water")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )

