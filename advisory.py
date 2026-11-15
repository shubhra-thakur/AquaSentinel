
"""
AquaSentinel - Water Conservation Advisory Module

Combines:
1. Network-level recommendations
2. Household water-saving guidance
3. Local knowledge retrieval
4. Utility-based action prioritization
5. Historical repair evidence

This is a rule-based decision-support system.
It does not automatically control water infrastructure.
"""

import math
import pandas as pd

from anomaly_detection import detect_anomalies
from knowledge_retrieval import get_knowledge_response
from utility_agent import evaluate_zone


# Configurable advisory thresholds
HIGH_LOSS_THRESHOLD = 20.0
MEDIUM_LOSS_THRESHOLD = 10.0
LOW_PRESSURE_THRESHOLD = 30.0
HIGH_FLOW_DIFFERENCE_THRESHOLD = 15.0


def validate_advisory_input(df):
    """Validate input data before generating recommendations."""

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("Water dataset is empty.")

    required_columns = [
        "zone",
        "supplied_litres",
        "consumed_litres",
        "inlet_flow",
        "outlet_flow",
        "pressure"
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing)
        )

    return True


def get_priority(risk_level):
    """Convert risk classification into advisory priority."""

    priorities = {
        "High": "Critical",
        "Medium": "High",
        "Low": "Moderate",
        "Normal": "Routine"
    }

    return priorities.get(risk_level, "Review")


def validate_measurement(value, field_name):
    """Convert a measurement to a finite, non-negative float."""

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{field_name} must be a valid numeric value."
        )

    if not math.isfinite(number) or number < 0:
        raise ValueError(
            f"{field_name} must be finite and non-negative."
        )

    return number


def generate_recommendations(zone_data):
    """Generate explainable network-level recommendations."""

    recommendations = []

    loss = zone_data["loss_percentage"]
    pressure = zone_data["pressure"]
    flow_difference = zone_data["flow_difference"]

    if loss > HIGH_LOSS_THRESHOLD:
        recommendations.append({
            "action": "Conduct a detailed leakage investigation.",
            "reason": (
                "Water loss is above the configured high-loss threshold."
            ),
            "priority": "Critical"
        })

        recommendations.append({
            "action": "Inspect pipelines, joints and nearby connections.",
            "reason": (
                "High water loss may indicate leakage or measurement issues."
            ),
            "priority": "High"
        })

    elif loss > MEDIUM_LOSS_THRESHOLD:
        recommendations.append({
            "action": "Schedule a detailed water-loss inspection.",
            "reason": (
                "Water loss is above the normal project threshold."
            ),
            "priority": "High"
        })

    if pressure > 0 and pressure < LOW_PRESSURE_THRESHOLD:
        recommendations.append({
            "action": "Inspect pressure sensors, pumps and distribution lines.",
            "reason": (
                "Recorded pressure is below the configured threshold."
            ),
            "priority": "High"
        })

    if flow_difference > HIGH_FLOW_DIFFERENCE_THRESHOLD:
        recommendations.append({
            "action": "Verify inlet and outlet flow-meter readings.",
            "reason": (
                "A large flow difference requires investigation."
            ),
            "priority": "High"
        })

    if not recommendations:
        recommendations.append({
            "action": "Continue routine water-loss monitoring.",
            "reason": (
                "No significant network indicators crossed the "
                "configured advisory thresholds."
            ),
            "priority": "Routine"
        })

    return recommendations


def generate_zone_advisory(zone_data):
    """Generate a complete advisory for one network zone."""

    if not isinstance(zone_data, dict):
        raise TypeError("zone_data must be a dictionary.")

    required_fields = [
        "zone",
        "loss_percentage",
        "pressure",
        "flow_difference",
        "risk_level"
    ]

    for field in required_fields:
        if field not in zone_data:
            raise ValueError(
                f"Missing zone information: {field}"
            )

    zone = str(zone_data["zone"]).strip()

    if not zone:
        raise ValueError("Zone name cannot be empty.")

    loss = validate_measurement(
        zone_data["loss_percentage"], "loss_percentage"
    )

    pressure = validate_measurement(
        zone_data["pressure"], "pressure"
    )

    flow_difference = validate_measurement(
        zone_data["flow_difference"], "flow_difference"
    )

    risk_level = str(zone_data["risk_level"]).strip()

    if risk_level not in ["High", "Medium", "Low", "Normal"]:
        raise ValueError("Invalid risk level.")

    clean_zone_data = {
        "zone": zone,
        "loss_percentage": loss,
        "pressure": pressure,
        "flow_difference": flow_difference,
        "risk_level": risk_level
    }

    recommendations = generate_recommendations(clean_zone_data)

    # Utility agent provides an independent priority assessment.
    decision_support = evaluate_zone(clean_zone_data)

    return {
        "zone": zone,
        "risk_level": risk_level,
        "priority": get_priority(risk_level),
        "loss_percentage": round(loss, 2),
        "pressure": round(pressure, 2),
        "flow_difference": round(flow_difference, 2),
        "recommendations": recommendations,
        "utility_score": decision_support["utility_score"],
        "utility_priority": decision_support["priority"],
        "decision_evidence": decision_support["evidence"],
        "missing_data": decision_support["missing_data"],
        "utility_actions": decision_support["recommended_actions"],
        "decision_explanation": decision_support["explanation"]
    }


def generate_all_advisories(
    water_data,
    loss_threshold=10.0,
    pressure_threshold=30.0,
    flow_difference_threshold=15.0
):
    """Generate network recommendations for all detected zones."""

    validate_advisory_input(water_data)

    anomalies = detect_anomalies(
        water_data,
        loss_threshold=loss_threshold,
        pressure_threshold=pressure_threshold,
        flow_difference_threshold=flow_difference_threshold
    )

    advisories = []

    for _, row in anomalies.iterrows():
        advisories.append(
            generate_zone_advisory(row.to_dict())
        )

    return advisories


def generate_household_advisory(query):
    """
    Retrieve household water-saving guidance from the local
    knowledge base using keyword-based retrieval.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Please provide a valid household query.")

    try:
        result = get_knowledge_response(
            query,
            category="household"
        )

    except (FileNotFoundError, ValueError) as error:
        return {
            "success": False,
            "message": "Household knowledge guidance is unavailable.",
            "recommendations": [],
            "sources": [],
            "error": str(error)
        }

    return {
        "success": result["success"],
        "query": query,
        "message": result["message"],
        "recommendations": result["recommendations"],
        "sources": result["sources"]
    }


def add_repair_context(advisories, repair_validation):
    """
    Add historical repair evidence and update utility scores.

    Historical records support investigation priority but do not
    prove that a current leakage event exists.
    """

    if not isinstance(advisories, list):
        raise TypeError("Advisories must be a list.")

    if not isinstance(repair_validation, list):
        raise TypeError("Repair validation must be a list.")

    repair_lookup = {}

    for record in repair_validation:
        if not isinstance(record, dict) or "zone" not in record:
            continue

        key = str(record["zone"]).strip().casefold()

        if key:
            repair_lookup[key] = record

    updated_advisories = []

    for advisory in advisories:

        updated = advisory.copy()

        history = repair_lookup.get(
            str(advisory["zone"]).strip().casefold()
        )

        repair_context = {}

        if history is None:
            updated["historical_status"] = "No Historical Record"
            updated["historical_evidence"] = (
                "No matching repair information available."
            )

        else:
            updated["historical_status"] = history.get(
                "validation_status",
                "Unknown"
            )

            updated["historical_evidence"] = history.get(
                "evidence",
                "No additional evidence available."
            )

            # Support both possible pending-count field names.
            pending_count = history.get(
                "pending_count",
                history.get("pending_repairs", 0)
            )

            repair_context = {
                "validation_status": updated["historical_status"],
                "pending_count": pending_count
            }

            try:
                has_pending = int(pending_count) > 0
            except (TypeError, ValueError):
                has_pending = False

            if has_pending:
                updated["recommendations"].append({
                    "action": "Review and update the pending repair case.",
                    "reason": (
                        "A historical repair record is still pending."
                    ),
                    "priority": "High"
                })

        # Recalculate decision support with historical evidence.
        zone_data = {
            "zone": updated["zone"],
            "loss_percentage": updated["loss_percentage"],
            "pressure": updated["pressure"],
            "flow_difference": updated["flow_difference"]
        }

        decision = evaluate_zone(
            zone_data,
            repair_context if repair_context else None
        )

        updated["utility_score"] = decision["utility_score"]
        updated["utility_priority"] = decision["priority"]
        updated["decision_evidence"] = decision["evidence"]
        updated["missing_data"] = decision["missing_data"]
        updated["utility_actions"] = decision["recommended_actions"]
        updated["decision_explanation"] = decision["explanation"]

        updated_advisories.append(updated)

    return updated_advisories


def generate_advisory_summary(advisories):
    """Generate a summary of all network recommendations."""

    if not isinstance(advisories, list):
        raise TypeError("Advisories must be a list.")

    total_recommendations = sum(
        len(item.get("recommendations", []))
        for item in advisories
    )

    critical_zones = sum(
        item.get("priority") == "Critical"
        for item in advisories
    )

    high_priority_zones = sum(
        item.get("priority") == "High"
        for item in advisories
    )

    return {
        "total_zones": len(advisories),
        "total_recommendations": total_recommendations,
        "critical_priority_zones": critical_zones,
        "high_priority_zones": high_priority_zones
    }


if __name__ == "__main__":

    from pathlib import Path

    from data_quality import (
        load_water_data,
        validate_water_data
    )

    from repair_validation import (
        load_repair_data,
        generate_repair_validation_report
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

        repair_report = generate_repair_validation_report(
            water_data,
            repair_data
        )

        advisories = generate_all_advisories(water_data)

        advisories = add_repair_context(
            advisories,
            repair_report["validation_results"]
        )

        summary = generate_advisory_summary(advisories)

        print("\n========== AQUASENTINEL ADVISORY REPORT ==========")

        print("\nSummary:")
        for key, value in summary.items():
            print(f"{key}: {value}")

        for advisory in advisories:

            print("\n-----------------------------------")
            print("Zone:", advisory["zone"])
            print("Risk:", advisory["risk_level"])
            print("Advisory Priority:", advisory["priority"])
            print("Utility Score:", advisory["utility_score"])
            print("Utility Priority:", advisory["utility_priority"])
            print("Historical Status:", advisory["historical_status"])

            print("\nNetwork Recommendations:")

            for recommendation in advisory["recommendations"]:
                print(
                    f"- [{recommendation['priority']}] "
                    f"{recommendation['action']}"
                )
                print("  Reason:", recommendation["reason"])

            print("\nDecision Evidence:")

            for evidence in advisory["decision_evidence"]:
                print("-", evidence)

            print("\nPrioritized Actions:")

            for action in advisory["utility_actions"]:
                print(
                    f"- [{action['urgency']}] {action['action']} "
                    f"(Effort: {action['effort']})"
                )

        print("\n========== HOUSEHOLD ADVISORY TEST ==========")

        household_result = generate_household_advisory(
            "How can I reduce water usage at home?"
        )

        print("Status:", household_result["success"])

        for recommendation in household_result["recommendations"]:
            print("-", recommendation)

    except (FileNotFoundError, ValueError, TypeError) as error:
        print("Advisory generation failed:", error)

