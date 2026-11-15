
"""
AquaSentinel - Utility-Based Decision Support Agent

Ranks suggested actions using:
1. Water-loss severity
2. Pressure condition
3. Flow difference
4. Historical repair evidence

The score is a decision-support priority score, not a
measured estimate of water saved.
"""


def get_number(data, keys):
    """Return the first valid numeric value found for the given keys."""

    for key in keys:
        value = data.get(key)

        if value is None:
            continue

        try:
            number = float(value)

            if number == number and number not in (float("inf"), float("-inf")):
                return number
        except (TypeError, ValueError):
            continue

    return None


def calculate_utility_score(zone_data, repair_context=None):
    """
    Calculate a transparent priority score between 0 and 100.

    Missing measurements do not receive risk points.
    """

    if not isinstance(zone_data, dict):
        raise TypeError("zone_data must be a dictionary.")

    score = 0
    evidence = []
    missing_data = []

    loss = get_number(
        zone_data,
        ["loss_percentage", "loss_percent", "water_loss_percentage"]
    )

    pressure = get_number(zone_data, ["pressure", "avg_pressure"])

    flow_difference = get_number(
        zone_data,
        ["flow_difference", "avg_flow_difference"]
    )

    # Water-loss severity: maximum 40 points.
    if loss is not None and loss >= 0:
        loss_score = min(loss / 40 * 40, 40)
        score += loss_score

        evidence.append({
            "indicator": "Water loss",
            "value": round(loss, 2),
            "points": round(loss_score, 2)
        })
    else:
        missing_data.append("Water-loss percentage unavailable.")

    # Low pressure: maximum 20 points.
    if pressure is not None and pressure > 0:
        if pressure <= 30:
            score += 20
            evidence.append({
                "indicator": "Low pressure",
                "value": pressure,
                "points": 20
            })
        else:
            evidence.append({
                "indicator": "Pressure",
                "value": pressure,
                "points": 0
            })
    else:
        missing_data.append("Valid pressure reading unavailable.")

    # Flow difference: maximum 20 points.
    if flow_difference is not None and flow_difference >= 0:
        if flow_difference > 15:
            flow_score = min(flow_difference / 30 * 20, 20)
            score += flow_score

            evidence.append({
                "indicator": "High flow difference",
                "value": round(flow_difference, 2),
                "points": round(flow_score, 2)
            })
        else:
            evidence.append({
                "indicator": "Flow difference",
                "value": round(flow_difference, 2),
                "points": 0
            })
    else:
        missing_data.append("Valid flow difference unavailable.")

    # Historical repair evidence: maximum 20 points.
    # Historical evidence increases investigation priority;
    # it does not prove a current leak.
    if isinstance(repair_context, dict):

        status = str(
            repair_context.get("validation_status", "")
        ).lower()

        if "historical leakage confirmed" in status:
            score += 10
            evidence.append({
                "indicator": "Historical leakage confirmed",
                "value": status,
                "points": 10
            })

        pending = repair_context.get("pending_count", 0)

        try:
            pending = int(pending)
        except (TypeError, ValueError):
            pending = 0

        if pending > 0:
            score += 10
            evidence.append({
                "indicator": "Pending repair record",
                "value": pending,
                "points": 10
            })

    score = round(min(score, 100), 2)

    if len(missing_data) == 3:
        priority = "Insufficient Data"
    elif score >= 60:
        priority = "Critical"
    elif score >= 35:
        priority = "High"
    elif score >= 15:
        priority = "Moderate"
    else:
        priority = "Routine"

    return {
        "utility_score": score,
        "priority": priority,
        "evidence": evidence,
        "missing_data": missing_data,
        "explanation": (
            "Priority is based on available measurements and "
            "historical repair evidence."
        )
    }


def rank_actions(zone_data, repair_context=None):
    """Return recommended actions in priority order."""

    result = calculate_utility_score(zone_data, repair_context)

    actions = []

    if result["priority"] == "Insufficient Data":
        actions.append({
            "action": "Verify missing measurements before making a decision.",
            "urgency": "High",
            "effort": "Low"
        })

    loss = get_number(
        zone_data,
        ["loss_percentage", "loss_percent", "water_loss_percentage"]
    )

    pressure = get_number(zone_data, ["pressure", "avg_pressure"])

    flow_difference = get_number(
        zone_data,
        ["flow_difference", "avg_flow_difference"]
    )

    if loss is not None and loss > 10:
        actions.append({
            "action": "Inspect pipelines and connections for possible leakage.",
            "urgency": "High" if loss >= 20 else "Medium",
            "effort": "Medium"
        })

    if pressure is not None and 0 < pressure <= 30:
        actions.append({
            "action": "Inspect pressure sensors, pumps and pipeline conditions.",
            "urgency": "High",
            "effort": "Medium"
        })

    if flow_difference is not None and flow_difference > 15:
        actions.append({
            "action": "Verify inlet and outlet flow meter readings.",
            "urgency": "High",
            "effort": "Low"
        })

    if isinstance(repair_context, dict):
        status = str(
            repair_context.get("validation_status", "")
        ).lower()

        if "historical leakage confirmed" in status:
            actions.append({
                "action": (
                    "Review historical leakage and repair records "
                    "before deciding on further inspection."
                ),
                "urgency": "High",
                "effort": "Low"
            })

    if not actions:
        actions.append({
            "action": "Continue routine monitoring of water readings.",
            "urgency": "Low",
            "effort": "Low"
        })

    urgency_order = {
        "High": 1,
        "Medium": 2,
        "Low": 3
    }

    actions.sort(
        key=lambda item: urgency_order[item["urgency"]]
    )

    return actions


def evaluate_zone(zone_data, repair_context=None):
    """Generate a complete decision-support result for one zone."""

    utility = calculate_utility_score(zone_data, repair_context)
    actions = rank_actions(zone_data, repair_context)

    return {
        "zone": zone_data.get("zone", "Unknown"),
        "utility_score": utility["utility_score"],
        "priority": utility["priority"],
        "evidence": utility["evidence"],
        "missing_data": utility["missing_data"],
        "explanation": utility["explanation"],
        "recommended_actions": actions
    }


if __name__ == "__main__":

    sample_zone = {
        "zone": "Zone D",
        "loss_percentage": 40,
        "pressure": 25,
        "flow_difference": 50
    }

    sample_repair = {
        "validation_status": "Historical Leakage Confirmed",
        "pending_count": 1
    }

    result = evaluate_zone(sample_zone, sample_repair)

    print("\n========== AQUASENTINEL UTILITY AGENT ==========")
    print("Zone:", result["zone"])
    print("Utility Score:", result["utility_score"])
    print("Priority:", result["priority"])

    print("\nEvidence:")
    for item in result["evidence"]:
        print("-", item)

    print("\nRecommended Actions:")
    for index, action in enumerate(
        result["recommended_actions"], start=1
    ):
        print(
            f"{index}. {action['action']} "
            f"| Urgency: {action['urgency']} "
            f"| Effort: {action['effort']}"
        )

    print("\nMissing Data:")
    for item in result["missing_data"]:
        print("-", item)

    print("\n================================================")
