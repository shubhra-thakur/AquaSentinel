
"use strict";

const API_URL = "/api/dashboard";
const HOUSEHOLD_API_URL = "/api/household-advisory";

document.addEventListener("DOMContentLoaded", () => {
    initializeDashboard();
    initializeNavigation();
    initializeHouseholdAdvisory();

    const refreshButton = document.getElementById("refreshBtn");

    if (refreshButton) {
        refreshButton.addEventListener("click", initializeDashboard);
    }
});


/* =====================================
   DASHBOARD INITIALIZATION
===================================== */

async function initializeDashboard() {
    showLoading(true);
    showError("");

    const refreshButton = document.getElementById("refreshBtn");

    if (refreshButton) {
        refreshButton.disabled = true;
    }

    try {
        const response = await fetch(API_URL);

        if (!response.ok) {
            throw new Error(`Server Error: ${response.status}`);
        }

        const data = await response.json();

        if (data.success !== true) {
            throw new Error(data.error || "Dashboard data unavailable.");
        }

        updateDashboard(data);

        const dashboard = document.getElementById("dashboardContent");

        if (dashboard) {
            dashboard.hidden = false;
        }

    } catch (error) {
        console.error("Dashboard Error:", error);
        showError(error.message);

    } finally {
        showLoading(false);

        if (refreshButton) {
            refreshButton.disabled = false;
        }
    }
}


/* =====================================
   UPDATE ALL SECTIONS
===================================== */

function updateDashboard(data) {
    updateOverview(data.summary || {});
    updateZones(data.zones || []);
    updateAnomalies(data.anomalies || []);
    updateRepairs(data.repair_validation || {});
    updateAdvisories(data.advisories || []);
    updateQuality(data.quality || {});
}


/* =====================================
   OVERVIEW
===================================== */

function updateOverview(summary) {
    setText("totalSupplied", formatNumber(summary.total_supplied));
    setText("totalConsumed", formatNumber(summary.total_consumed));
    setText("totalLoss", formatNumber(summary.total_loss));
    setText("lossPercentage", formatPercentage(summary.loss_percentage));
}


/* =====================================
   ZONE MONITORING
===================================== */

function updateZones(zones) {
    const body = document.getElementById("zoneTableBody");

    if (!body) return;

    body.replaceChildren();

    if (!zones.length) {
        showEmptyRow(body, 6, "No zone data available.");
        return;
    }

    zones.forEach(zone => {
        const row = document.createElement("tr");

        appendCell(row, zone.zone);
        appendCell(row, formatNumber(zone.total_supplied));
        appendCell(row, formatNumber(zone.total_consumed));
        appendCell(row, formatNumber(zone.total_loss));
        appendCell(row, formatPercentage(zone.overall_loss_percentage));
        appendCell(row, formatNumber(zone.average_pressure));

        body.appendChild(row);
    });
}


/* =====================================
   ANOMALY DETECTION
===================================== */

function updateAnomalies(anomalies) {
    const body = document.getElementById("anomalyTableBody");

    if (!body) return;

    body.replaceChildren();

    const normal = anomalies.filter(
        item => item.risk_level === "Normal"
    ).length;

    const suspicious = anomalies.filter(
        item => item.is_suspicious === true
    ).length;

    const high = anomalies.filter(
        item => item.risk_level === "High"
    ).length;

    setText("totalZones", anomalies.length);
    setText("suspiciousZones", suspicious);
    setText("highRiskZones", high);
    setText("normalZones", normal);

    if (!anomalies.length) {
        showEmptyRow(body, 6, "No anomaly records available.");
        return;
    }

    anomalies.forEach(item => {
        const row = document.createElement("tr");

        appendCell(row, item.zone);
        appendCell(row, formatPercentage(item.loss_percentage));
        appendCell(row, formatNumber(item.pressure));
        appendCell(row, formatNumber(item.flow_difference));

        const riskCell = document.createElement("td");
        riskCell.appendChild(createBadge(item.risk_level));
        row.appendChild(riskCell);

        const reasons = Array.isArray(item.anomaly_reasons)
            ? item.anomaly_reasons.join(", ")
            : "No anomalies detected";

        appendCell(row, reasons);

        body.appendChild(row);
    });
}


/* =====================================
   REPAIR VALIDATION
===================================== */

function updateRepairs(repairData) {
    const body = document.getElementById("repairTableBody");

    if (!body) return;

    body.replaceChildren();

    const repairs = repairData.results || [];

    setText(
        "confirmedRepairs",
        repairData.historically_confirmed_zones ?? 0
    );

    setText(
        "noRepairHistory",
        repairData.zones_without_history ?? 0
    );

    setText(
        "notConfirmed",
        repairData.zones_without_confirmed_leakage ?? 0
    );

    if (!repairs.length) {
        showEmptyRow(body, 5, "No repair validation records available.");
        return;
    }

    repairs.forEach(item => {
        const row = document.createElement("tr");

        appendCell(row, item.zone);
        appendCell(row, item.historical_records ?? 0);
        appendCell(row, item.confirmed_leakages ?? 0);
        appendCell(row, item.pending_repairs ?? 0);

        const statusCell = document.createElement("td");
        statusCell.appendChild(createBadge(item.validation_status));
        row.appendChild(statusCell);

        body.appendChild(row);
    });
}


/* =====================================
   CONSERVATION ADVISORIES
===================================== */

function updateAdvisories(advisories) {
    const container = document.getElementById("advisoryContainer");

    if (!container) return;

    container.replaceChildren();

    const critical = advisories.filter(
        item => item.utility_priority === "Critical"
    ).length;

    const high = advisories.filter(
        item => item.utility_priority === "High"
    ).length;

    const totalRecommendations = advisories.reduce(
        (total, item) =>
            total + (item.recommendations || []).length,
        0
    );

    setText("totalRecommendations", totalRecommendations);
    setText("criticalAdvisories", critical);
    setText("highAdvisories", high);

    if (!advisories.length) {
        appendMessage(container, "No recommendations available.");
        return;
    }

    advisories.forEach(item => {
        const card = document.createElement("article");

        card.className =
            `advisory-card ${getSafePriority(item.utility_priority)}`;

        // Zone heading
        const heading = document.createElement("h3");
        heading.textContent = item.zone || "Unknown Zone";

        // Utility priority
        const priority = document.createElement("p");
        priority.textContent =
            `Utility Priority: ${item.utility_priority || "N/A"}`;

        // Anomaly risk
        const risk = document.createElement("p");
        risk.textContent =
            `Risk Level: ${item.risk_level || "N/A"}`;

        // Historical evidence
        const history = document.createElement("p");
        history.textContent =
            `Historical Status: ${item.historical_status || "N/A"}`;

        // Utility score
        const score = document.createElement("p");
        score.className = "utility-score";
        score.textContent =
            `Utility Score: ${formatNumber(item.utility_score)} / 100`;

        card.append(
            heading,
            priority,
            risk,
            history,
            score
        );

        // Decision explanation
        if (item.decision_explanation) {
            const explanation = document.createElement("p");
            explanation.textContent =
                `Decision Explanation: ${item.decision_explanation}`;

            card.appendChild(explanation);
        }

        // Decision evidence
        if (Array.isArray(item.decision_evidence) &&
            item.decision_evidence.length) {

            const evidenceHeading = document.createElement("h4");
            evidenceHeading.textContent = "Decision Evidence";

            card.appendChild(evidenceHeading);

            const evidenceList = document.createElement("ul");

            item.decision_evidence.forEach(evidence => {
                const li = document.createElement("li");

                li.textContent =
                    `${evidence.indicator}: ${formatNumber(evidence.points)} points`;

                evidenceList.appendChild(li);
            });

            card.appendChild(evidenceList);
        }

        // Recommended actions
        const recommendationHeading = document.createElement("h4");
        recommendationHeading.textContent = "Conservation Recommendations";

        card.appendChild(recommendationHeading);

        (item.recommendations || []).forEach(recommendation => {
            const action = document.createElement("p");

            action.textContent =
                `${recommendation.action} (${recommendation.priority})`;

            card.appendChild(action);
        });

        // Utility actions
        if (Array.isArray(item.utility_actions) &&
            item.utility_actions.length) {

            const utilityHeading = document.createElement("h4");
            utilityHeading.textContent = "Suggested Utility Actions";

            card.appendChild(utilityHeading);

            const actionList = document.createElement("ul");

            item.utility_actions.forEach(actionItem => {
                const li = document.createElement("li");

                li.textContent =
                    `${actionItem.action} | Urgency: ${actionItem.urgency} | Effort: ${actionItem.effort}`;

                actionList.appendChild(li);
            });

            card.appendChild(actionList);
        }

        // Missing data information
        if (Array.isArray(item.missing_data) &&
            item.missing_data.length) {

            const missing = document.createElement("p");

            missing.textContent =
                `Missing Data: ${item.missing_data.join(", ")}`;

            card.appendChild(missing);
        }

        container.appendChild(card);
    });
}


/* =====================================
   HOUSEHOLD ADVISORY
===================================== */

function initializeHouseholdAdvisory() {
    const form = document.getElementById("householdAdvisoryForm");

    if (!form) return;

    form.addEventListener("submit", async event => {
        event.preventDefault();

        const input = document.getElementById("householdQuery");
        const button = document.getElementById("householdSubmitBtn");

        if (!input) return;

        const query = input.value.trim();

        if (!query) {
            showHouseholdError("Please enter a water-related question.");
            return;
        }

        if (query.length > 250) {
            showHouseholdError("Please keep your question within 250 characters.");
            return;
        }

        showHouseholdError("");
        showHouseholdLoading(true);

        if (button) {
            button.disabled = true;
        }

        try {
            const url = `${HOUSEHOLD_API_URL}?q=${encodeURIComponent(query)}`;

            const response = await fetch(url);

            const data = await response.json();

            if (!response.ok || data.success !== true) {
                throw new Error(
                    data.error || "Unable to retrieve recommendations."
                );
            }

            displayHouseholdAdvisory(data);

        } catch (error) {
            console.error("Household Advisory Error:", error);
            showHouseholdError(error.message);

        } finally {
            showHouseholdLoading(false);

            if (button) {
                button.disabled = false;
            }
        }
    });
}


function displayHouseholdAdvisory(data) {
    const container = document.getElementById("householdResult");

    if (!container) return;

    container.replaceChildren();

    const heading = document.createElement("h3");
    heading.textContent = "Recommended Water-Saving Actions";

    container.appendChild(heading);

    const recommendations = Array.isArray(data.recommendations)
        ? data.recommendations
        : [];

    if (!recommendations.length) {
        appendMessage(container, "No relevant recommendations found.");
        return;
    }

    const list = document.createElement("ul");

    recommendations.forEach(recommendation => {
        const item = document.createElement("li");
        item.textContent = recommendation;
        list.appendChild(item);
    });

    container.appendChild(list);

    // Knowledge base sources
    if (Array.isArray(data.sources) && data.sources.length) {
        const sourceHeading = document.createElement("h4");
        sourceHeading.textContent = "Knowledge Base References";

        container.appendChild(sourceHeading);

        const sourceList = document.createElement("ul");

        data.sources.forEach(source => {
            const item = document.createElement("li");

            item.textContent =
                `${source.title} | Category: ${source.category} | Priority: ${source.priority}`;

            sourceList.appendChild(item);
        });

        container.appendChild(sourceList);
    }
}


function showHouseholdLoading(show) {
    const element = document.getElementById("householdLoading");

    if (element) {
        element.hidden = !show;
    }
}


function showHouseholdError(message) {
    const element = document.getElementById("householdError");

    if (element) {
        element.textContent = message;
        element.hidden = !message;
    }
}


/* =====================================
   DATA QUALITY
===================================== */

function updateQuality(quality) {
    setText("qualityTotal", quality.total_records ?? 0);
    setText("qualityValid", quality.valid_records ?? 0);
    setText("qualityInvalid", quality.invalid_records ?? 0);
    setText("qualityIssues", quality.total_issues ?? 0);

    const status = document.getElementById("qualityStatus");

    if (!status) return;

    status.className = "quality-status";

    if (quality.is_valid === true) {
        status.textContent = "Data Quality: Valid";
        status.classList.add("quality-good");
    } else {
        status.textContent = "Data Quality: Issues Found";
        status.classList.add("quality-bad");
    }
}


/* =====================================
   NAVIGATION
===================================== */

function initializeNavigation() {
    const links = document.querySelectorAll(".nav-link");

    links.forEach(link => {
        link.addEventListener("click", () => {
            links.forEach(item => item.classList.remove("active"));
            link.classList.add("active");
        });
    });
}


/* =====================================
   HELPER FUNCTIONS
===================================== */

function setText(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = value ?? "0";
    }
}


function formatNumber(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) return "0";

    return number.toLocaleString("en-IN", {
        maximumFractionDigits: 2
    });
}


function formatPercentage(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) return "0%";

    return `${number.toFixed(2)}%`;
}


function appendCell(row, value) {
    const cell = document.createElement("td");

    cell.textContent = value ?? "N/A";

    row.appendChild(cell);
}


function showEmptyRow(body, columns, message) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");

    cell.colSpan = columns;
    cell.textContent = message;

    row.appendChild(cell);
    body.appendChild(row);
}


function appendMessage(container, message) {
    const paragraph = document.createElement("p");
    paragraph.textContent = message;
    container.appendChild(paragraph);
}


function createBadge(value) {
    const badge = document.createElement("span");

    const status = String(value || "unknown")
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, "");

    badge.className = `status-badge status-${status}`;
    badge.textContent = value || "Unknown";

    return badge;
}


function getSafePriority(priority) {
    const value = String(priority || "").toLowerCase();

    if (value === "critical" || value === "high") return "high";

    if (value === "moderate" || value === "medium") return "medium";

    return "low";
}


function showLoading(show) {
    const element = document.getElementById("loadingMessage");

    if (element) {
        element.hidden = !show;
    }
}


function showError(message) {
    const element = document.getElementById("errorMessage");

    if (element) {
        element.textContent = message;
        element.hidden = !message;
    }
}

