"""Deterministic rendering, including provenance and measurement boundaries."""
import json

def safe(text):
    return str(text).replace(chr(0x2014), "-").replace("\n", " ").replace("\r", " ").replace("|", "\\|")

def render(result, format="md"):
    # Escape em dash in JSON while preserving the original input value on decoding.
    if format == "json":
        return json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    p = result["provenance"]
    label = "SYNTHETIC FIXTURES" if p["synthetic"] else "REAL INPUT (operator-declared; authorship not independently verified)"
    lines = ["# KOML Goal Drift Detector", "", f"Provenance: {label}. Source: {safe(p['source'])}. As of: {p['as_of']}.", "", p["boundary"], "", "## Computed counts and entered costs", ""]
    lines += [f"- {key}: {value}" for key, value in result["summary"].items()]
    lines += ["", "## Comparison against supplied labels", "", "Labels are declared ground truth, not independently verified."]
    lines += [f"- {key}: {value}" for key, value in result["evaluation"].items()]
    lines += ["", "Savings: unmeasured. " + result["savings"]["explanation"], "", "## Flagged activities", ""]
    lines += [f"- {safe(f['id'])}: {', '.join(f['reasons'])}; entered cost {f['cost_cents']} cents" for f in result["findings"]]
    if not result["findings"]:
        lines.append("No activities flagged.")
    return "\n".join(lines) + "\n"
