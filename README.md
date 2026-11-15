# AquaSentinel
### Urban Water-Loss Detection and Conservation Decision Support System

## 1. Project Overview

AquaSentinel is a Python-based water management system designed to analyze water distribution data, identify potential water losses, validate suspicious zones using historical repair records, and generate conservation recommendations.

The system provides a Flask-based web dashboard to display analytical results.

## 2. Project Objectives

- Analyze supplied and consumed water to estimate water loss.
- Identify suspicious zones using rule-based anomaly detection.
- Validate detected zones using historical leakage and repair records.
- Generate recommendations for water-loss investigation and conservation.
- Validate input data to improve data reliability.

## 3. Technologies Used

- Python
- Flask
- Pandas
- NumPy
- HTML
- CSS
- JavaScript

## 4. Main Features

### Water Analysis
Calculates total supplied water, consumed water, estimated water loss, and loss percentage.

### Anomaly Detection
Identifies suspicious zones using water-loss percentage, pressure, and flow difference.

### Historical Repair Validation
Compares suspicious zones with historical repair records.

### Conservation Advisory
Generates rule-based recommendations according to detected conditions.

### Data Quality Validation
Checks missing values, invalid readings, duplicate records, and other data-quality issues.

### Web Dashboard
Displays water statistics, zone monitoring, anomaly results, repair validation, recommendations, and data quality status.

## 5. Project Structure

```text
AquaSentinel/
│
├── app.py
├── data_quality.py
├── analyze_water.py
├── anomaly_detection.py
├── repair_validation.py
├── advisory.py
├── test_project.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── water_data.csv
│   └── historical_repairs.csv
│
├── templates/
│   └── index.html
│
└── static/
    ├── style.css
    └── script.js
```

## 6. Installation and Execution

### Step 1: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Run the application

```bash
python app.py
```

### Step 3: Open the dashboard

```text
http://127.0.0.1:5000
```

## 7. Testing

Run automated tests using:

```bash
python -m unittest test_project.py -v
```

The project currently includes 8 automated tests covering:

- Homepage loading
- Dashboard API
- Water summary calculations
- Zone count
- Anomaly detection
- Data quality
- Historical repair validation
- Advisory generation

**Test result:** 8/8 tests passed.

## 8. Sample Dataset Results

The current illustrative dataset contains five zones.

| Parameter | Result |
|---|---:|
| Total Supplied | 56,000 L |
| Total Consumed | 47,200 L |
| Estimated Water Loss | 8,800 L |
| Estimated Loss Percentage | 15.71% |
| Suspicious Zones | 3 |
| High-Risk Zones | 1 |
| Valid Records | 5 |

*Note: The current CSV records are illustrative sample data, not measurements from a live water distribution network.*

## 9. Limitations

- Analysis depends on the quality of the input dataset.
- Anomaly detection uses predefined rules and thresholds.
- Historical validation depends on available repair records.
- Recommendations are generated using predefined conditions.
- The current project does not connect to live water sensors.

## 10. Future Scope

- Integration with IoT-based water sensors.
- Real-time water monitoring.
- Improved anomaly detection techniques.
- Interactive data visualizations.
- Expanded household water conservation recommendations.

---

**AquaSentinel – Smart Water Monitoring and Conservation Support.**