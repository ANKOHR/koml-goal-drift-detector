import json
from koml_goal_drift_detector.fixtures import generate
from koml_goal_drift_detector.core import analyze

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    for file in tmp_path.iterdir():
        if file.suffix == ".json":
            assert json.loads(file.read_text())["synthetic"] is True
        else:
            assert file.read_text().startswith("<!-- synthetic: true -->")

def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    generate(tmp_path)
    expected = json.loads((tmp_path / "expectations.json").read_text())
    result = analyze(json.loads((tmp_path / "activities.json").read_text()))
    assert result["summary"] == expected["summary"]
    assert result["evaluation"] == expected["evaluation"]
    assert {f["id"] for f in result["findings"]} == {f"activity-{i:03}" for i in range(200) if i % 5 in (1, 2, 3)}
