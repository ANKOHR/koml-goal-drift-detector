"""Pure rule evaluation. Costs are entered amounts, never inferred savings."""
from datetime import date

class SchemaError(ValueError):
    """An explicit input contract was violated."""

def validate(data):
    def fail(field, message):
        raise SchemaError(f"field {field}: {message}")
    def text(value, field):
        if not isinstance(value, str) or not value.strip() or len(value) > 20000:
            fail(field, "must be nonempty text of at most 20000 characters")
    if not isinstance(data, dict):
        fail("root", "must be an object")
    required = {"synthetic", "source", "as_of", "objectives", "records"}
    if set(data) != required:
        fail("root", f"expected fields {sorted(required)}, got {sorted(data)}")
    if type(data["synthetic"]) is not bool:
        fail("synthetic", "must be boolean")
    text(data["source"], "source")
    def day(value, field):
        try:
            if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                fail(field, "must be ISO date YYYY-MM-DD")
            return date.fromisoformat(value)
        except (ValueError, TypeError):
            fail(field, "must be ISO date YYYY-MM-DD")
    as_of = day(data["as_of"], "as_of")
    if not isinstance(data["objectives"], list) or not isinstance(data["records"], list):
        fail("objectives/records", "must be arrays")
    objectives = {}
    for i, obj in enumerate(data["objectives"]):
        field = f"objectives[{i}]"
        if not isinstance(obj, dict) or set(obj) != {"id", "description", "allowed_actions"}:
            fail(field, "expected id, description, allowed_actions")
        for key in ("id", "description"):
            text(obj[key], f"{field}.{key}")
        actions = obj["allowed_actions"]
        if not isinstance(actions, list) or not actions:
            fail(field + ".allowed_actions", "must be a nonempty array")
        for action in actions:
            text(action, field + ".allowed_actions")
        if len(set(actions)) != len(actions) or obj["id"] in objectives:
            fail(field, "duplicate objective ID or action")
        objectives[obj["id"]] = obj
    seen = set()
    for i, record in enumerate(data["records"]):
        field = f"records[{i}]"
        required = {"id", "objective_id", "action", "description", "date", "contributes", "cost_cents"}
        if not isinstance(record, dict) or not required <= set(record) or set(record) - required - {"expected_drift"}:
            fail(field, "expected id, objective_id, action, description, date, contributes, cost_cents; optional expected_drift")
        for key in ("id", "objective_id", "action", "description"):
            text(record[key], field + "." + key)
        if record["id"] in seen:
            fail(field + ".id", "duplicate ID")
        seen.add(record["id"])
        if day(record["date"], field + ".date") > as_of:
            fail(field + ".date", "future date relative to as_of")
        if type(record["contributes"]) is not bool:
            fail(field + ".contributes", "must be boolean")
        if type(record["cost_cents"]) is not int or not 0 <= record["cost_cents"] <= 10**12:
            fail(field + ".cost_cents", "must be integer between 0 and 1000000000000")
        if "expected_drift" in record and type(record["expected_drift"]) is not bool:
            fail(field + ".expected_drift", "must be boolean")
    return data

def analyze(data):
    validate(data)
    objectives = {obj["id"]: obj for obj in data["objectives"]}
    findings = []
    tp = fp = fn = tn = labelled = drift_cost = 0
    for record in data["records"]:
        reasons = []
        objective = objectives.get(record["objective_id"])
        if objective is None:
            reasons.append("unknown_objective")
        elif record["action"] not in objective["allowed_actions"]:
            reasons.append("action_outside_objective")
        if not record["contributes"]:
            reasons.append("declared_no_contribution")
        drift = bool(reasons)
        if drift:
            drift_cost += record["cost_cents"]
            findings.append({"id": record["id"], "objective_id": record["objective_id"], "reasons": reasons, "cost_cents": record["cost_cents"]})
        if "expected_drift" in record:
            labelled += 1
            expected = record["expected_drift"]
            tp += int(drift and expected)
            fp += int(drift and not expected)
            fn += int(not drift and expected)
            tn += int(not drift and not expected)
    return {"schema_version": 1, "provenance": {"synthetic": data["synthetic"], "source": data["source"], "as_of": data["as_of"], "boundary": "Computed from declared inputs only; no inferred intent or measured savings."}, "summary": {"records": len(data["records"]), "drift_records": len(findings), "aligned_records": len(data["records"]) - len(findings), "entered_cost_cents": sum(r["cost_cents"] for r in data["records"]), "drift_entered_cost_cents": drift_cost}, "evaluation": {"labelled_records": labelled, "true_positives": tp, "false_positives": fp, "false_negatives": fn, "true_negatives": tn}, "findings": sorted(findings, key=lambda f: f["id"]), "savings": {"status": "unmeasured", "explanation": "Time and money saved are not reported: no measured baseline provided."}}
