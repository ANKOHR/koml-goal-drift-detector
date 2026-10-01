import json
import subprocess
import sys
import time
from pathlib import Path
import pytest
from koml_goal_drift_detector.cli import main, atomic_write, InputError
from koml_goal_drift_detector.fixtures import generate

ROOT = Path(__file__).resolve().parents[1]

def test_run_completes_on_fixture(tmp_path):
    generate(tmp_path)
    start = time.perf_counter()
    results = tmp_path / "results.json"
    assert main(["run", "--input", str(tmp_path), "--results", str(results)]) == 0
    assert main(["report", "--results", str(results), "--format", "md"]) == 0
    assert time.perf_counter() - start < 5

def test_empty_input_renders_without_traceback(tmp_path, capsys):
    results = tmp_path / "results.json"
    assert main(["run", "--input", str(tmp_path), "--results", str(results)]) == 0
    assert main(["report", "--results", str(results)]) == 0
    assert json.loads(results.read_text())["summary"]["records"] == 0
    assert "Traceback" not in capsys.readouterr().out

def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "activities.json").write_text('{\n invalid}')
    assert main(["check", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "activities.json" in error and "line 2" in error

def test_determinism_byte_identical(tmp_path):
    generate(tmp_path)
    original = (tmp_path / "activities.json").read_bytes()
    generate(tmp_path)
    assert original == (tmp_path / "activities.json").read_bytes()
    result = tmp_path / "results.json"
    report = tmp_path / "report.md"
    outputs = []
    for _ in range(2):
        assert main(["run", "--input", str(tmp_path), "--results", str(result)]) == 0
        assert main(["report", "--results", str(result), "--out", str(report)]) == 0
        outputs.append((result.read_bytes(), report.read_bytes()))
    assert outputs[0] == outputs[1]

def test_cli_smoke_all_subcommands(tmp_path):
    def run(*args):
        return subprocess.run([sys.executable, "-m", "koml_goal_drift_detector.cli", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert run("fixtures", "--out", str(tmp_path)).returncode == 0
    for name in ("fixtures", "run", "report", "check", "drift"):
        assert run(name, "--help").returncode == 0
    result = str(tmp_path / "result.json")
    for args in [("check", "--input", str(tmp_path)), ("drift", "--input", str(tmp_path)), ("run", "--input", str(tmp_path), "--results", result), ("report", "--results", result, "--format", "json")]:
        process = run(*args)
        assert process.returncode == 0, process.stderr
        assert chr(0x2014) not in process.stdout

def test_missing_input_and_write_failure(tmp_path, capsys):
    assert main(["check", "--input", str(tmp_path / "absent")]) == 2
    assert "MissingInput" in capsys.readouterr().err
    target = tmp_path / "directory"
    target.mkdir()
    before = set(tmp_path.iterdir())
    with pytest.raises(InputError, match="WriteError"):
        atomic_write(target, "content")
    assert set(tmp_path.iterdir()) == before

@pytest.mark.parametrize("content", ['{"synthetic": true, "synthetic": false}', '{"value": NaN}', '{"value": Infinity}'])
def test_rejects_ambiguous_json(tmp_path, capsys, content):
    (tmp_path / "activities.json").write_text(content)
    assert main(["check", "--input", str(tmp_path)]) == 2
    assert "ParseError" in capsys.readouterr().err

def test_schema_error_is_named(tmp_path, capsys):
    generate(tmp_path)
    data = json.loads((tmp_path / "activities.json").read_text())
    data["records"][0]["cost_cents"] = -10
    (tmp_path / "activities.json").write_text(json.dumps(data))
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "SchemaError" in error and "cost_cents" in error and "activities.json" in error


def test_missing_and_malformed_results_named(tmp_path, capsys):
    path = tmp_path / "missing.json"
    assert main(["report", "--results", str(path)]) == 2
    assert "MissingResult" in capsys.readouterr().err
    path.write_text('{"provenance": []}')
    assert main(["report", "--results", str(path)]) == 2
    assert "ResultError" in capsys.readouterr().err
