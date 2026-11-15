
import unittest

from app import app


class AquaSentinelTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def test_homepage_loads(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AquaSentinel", response.data)

    def test_dashboard_api(self):
        response = self.client.get("/api/dashboard")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertIsNotNone(data)
        self.assertTrue(data["success"])

    def test_water_summary(self):
        response = self.client.get("/api/dashboard")
        data = response.get_json()

        summary = data["summary"]

        self.assertEqual(summary["total_supplied"], 56000)
        self.assertEqual(summary["total_consumed"], 47200)
        self.assertEqual(summary["total_loss"], 8800)
        self.assertEqual(summary["loss_percentage"], 15.71)

    def test_zone_count(self):
        response = self.client.get("/api/dashboard")
        data = response.get_json()

        self.assertEqual(len(data["zones"]), 5)

    def test_anomaly_detection(self):
        response = self.client.get("/api/dashboard")
        data = response.get_json()

        anomalies = data["anomalies"]

        suspicious = [
            zone for zone in anomalies
            if zone["is_suspicious"] is True
        ]

        high_risk = [
            zone for zone in anomalies
            if zone["risk_level"] == "High"
        ]

        self.assertEqual(len(suspicious), 3)
        self.assertEqual(len(high_risk), 1)

    def test_data_quality(self):
        response = self.client.get("/api/dashboard")
        data = response.get_json()

        quality = data["quality"]

        self.assertTrue(quality["is_valid"])
        self.assertEqual(quality["valid_records"], 5)
        self.assertEqual(quality["invalid_records"], 0)

    def test_repair_validation(self):
        response = self.client.get("/api/dashboard")
        data = response.get_json()

        repair_data = data["repair_validation"]

        self.assertEqual(
            repair_data["historically_confirmed_zones"], 2
        )

        self.assertEqual(len(repair_data["results"]), 3)

    def test_advisory_generation(self):
        response = self.client.get("/api/dashboard")
        data = response.get_json()

        self.assertEqual(len(data["advisories"]), 5)
        self.assertEqual(
            data["advisory_summary"]["total_recommendations"], 10
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
