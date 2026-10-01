"""Synthetic fixtures, no randomness. Expected counts derived independently."""
import json
from pathlib import Path

def fixture_data(count=200):
    records = []
    for i in range(count):
        category = i % 5
        records.append({"id": f"activity-{i:03}", "objective_id": "missing" if category == 1 else "deliver", "action": "browse" if category == 2 else "build", "description": f"Synthetic activity {i}", "date": "2026-09-30", "contributes": category != 3, "cost_cents": 100, "expected_drift": category in (1, 2, 3)})
    return {"synthetic": True, "source": "Labelled synthetic fixtures, not Henry's real data", "as_of": "2026-09-30", "objectives": [{"id": "deliver", "description": "Deliver a tested tool", "allowed_actions": ["build", "test"]}], "records": records}

def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "activities.json").write_text(json.dumps(fixture_data(), indent=2) + "\n", encoding="utf-8")
    expectations = {"synthetic": True, "summary": {"records": 200, "drift_records": 120, "aligned_records": 80, "entered_cost_cents": 20000, "drift_entered_cost_cents": 12000}, "evaluation": {"labelled_records": 200, "true_positives": 120, "false_positives": 0, "false_negatives": 0, "true_negatives": 80}, "derivation": "40 groups of five: 3 drift and 2 aligned per group; every record costs 100 entered cents."}
    (out / "expectations.json").write_text(json.dumps(expectations, indent=2) + "\n", encoding="utf-8")
    (out / "SYNTHETIC.md").write_text("<!-- synthetic: true -->\n# Synthetic fixture set\nNo real data. JSON uses synthetic:true because JSON does not allow header comments. No randomness or seed.\n", encoding="utf-8")
