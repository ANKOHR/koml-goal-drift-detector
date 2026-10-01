import copy
import pytest
from koml_goal_drift_detector.core import analyze, SchemaError
from koml_goal_drift_detector.fixtures import fixture_data

@pytest.mark.parametrize("field,value", [("cost_cents", -1), ("cost_cents", True), ("cost_cents", 10**13), ("cost_cents", 1.5), ("date", "2026-10-01"), ("description", "x" * 20001), ("contributes", "yes")])
def test_rejects_adversarial_values(field, value):
    data = fixture_data(5)
    data["records"][0][field] = value
    with pytest.raises(SchemaError, match=field):
        analyze(data)

def test_duplicate_ids_and_schema_drift():
    data = fixture_data(5)
    data["records"][1]["id"] = data["records"][0]["id"]
    with pytest.raises(SchemaError, match="duplicate"):
        analyze(data)
    data = fixture_data(5)
    data["records"][0]["unexpected"] = 1
    with pytest.raises(SchemaError, match="expected"):
        analyze(data)

def test_handles_unicode_and_long_inputs():
    data = fixture_data(5)
    data["records"][0]["description"] = "漢字 café 🚀 C:\\Users\\henry " + "x" * 19000
    assert analyze(data)["summary"]["records"] == 5

def test_corrupted_ground_truth_and_activity_change_results():
    data = fixture_data()
    before = analyze(data)
    data["records"][0]["expected_drift"] = True
    assert analyze(data)["evaluation"]["false_negatives"] == 1
    assert analyze(data)["summary"] == before["summary"]
    data["records"][0]["contributes"] = False
    after = analyze(data)
    assert after["summary"]["drift_records"] == 121
    assert after["summary"]["drift_entered_cost_cents"] == 12100

def test_core_does_not_mutate_inputs():
    data = fixture_data(5)
    original = copy.deepcopy(data)
    analyze(data)
    assert data == original

def test_tiny_handwritten_input():
    data = {"synthetic": True, "source": "Handwritten synthetic example", "as_of": "2026-09-30", "objectives": [{"id": "ship", "description": "Ship the tool", "allowed_actions": ["code", "test"]}], "records": [
        {"id": "a", "objective_id": "ship", "action": "code", "description": "Implement", "date": "2026-09-30", "contributes": True, "cost_cents": 10},
        {"id": "b", "objective_id": "ship", "action": "test", "description": "Verify", "date": "2026-09-30", "contributes": True, "cost_cents": 20},
        {"id": "c", "objective_id": "other", "action": "code", "description": "Wrong goal", "date": "2026-09-30", "contributes": True, "cost_cents": 30},
        {"id": "d", "objective_id": "ship", "action": "browse", "description": "Unapproved", "date": "2026-09-30", "contributes": True, "cost_cents": 40},
        {"id": "e", "objective_id": "ship", "action": "code", "description": "No contribution", "date": "2026-09-30", "contributes": False, "cost_cents": 50}]}
    assert analyze(data)["summary"] == {"records": 5, "drift_records": 3, "aligned_records": 2, "entered_cost_cents": 150, "drift_entered_cost_cents": 120}
