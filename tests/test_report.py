import json
from koml_goal_drift_detector.core import analyze
from koml_goal_drift_detector.fixtures import fixture_data
from koml_goal_drift_detector.report import render

def test_report_matches_ground_truth_exact():
    result = json.loads(render(analyze(fixture_data()), "json"))
    assert result["summary"] == {"records": 200, "drift_records": 120, "aligned_records": 80, "entered_cost_cents": 20000, "drift_entered_cost_cents": 12000}

def test_report_zero_false_positives():
    result = json.loads(render(analyze(fixture_data()), "json"))
    assert result["evaluation"] == {"labelled_records": 200, "true_positives": 120, "false_positives": 0, "false_negatives": 0, "true_negatives": 80}

def test_report_carries_provenance_banner():
    data = fixture_data()
    assert "Provenance: SYNTHETIC FIXTURES" in render(analyze(data))
    data["synthetic"] = False
    data["source"] = "Henry entered by hand"
    assert "REAL INPUT (operator-declared" in render(analyze(data))
    assert json.loads(render(analyze(data), "json"))["provenance"]["synthetic"] is False

def test_hypothetical_figures_labelled():
    for format in ("md", "json"):
        output = render(analyze(fixture_data()), format)
        assert "unmeasured" in output
        assert "no measured baseline" in output.lower()
    assert "SYNTHETIC" in render(analyze(fixture_data()))

def test_no_em_dashes_in_outputs():
    data = fixture_data()
    data["source"] = "Unicode " + chr(0x2014) + " source"
    data["records"][1]["id"] = "id" + chr(0x2014)
    for format in ("md", "json"):
        assert chr(0x2014) not in render(analyze(data), format)
