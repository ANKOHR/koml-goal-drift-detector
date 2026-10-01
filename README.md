# KOML Goal Drift Detector

`kgdd` notices when declared activity violates the stated objective's explicit rules. CPU only, Python standard library at runtime, local JSON only, no network calls and no language-model calls.

## Hypothesis and outcome

A deterministic rule checker can give KOML trustworthy supervision when its objective, permitted actions and contribution assertions are explicit. Acceptance on 200 planted synthetic records: all 120 planted drift cases found, zero false positives, entered costs reconcile exactly, report under five seconds, and no tracebacks. This validates rule implementation on synthetic data. It does not establish semantic accuracy on real agent activity.

## Quickstart

From this repository, with Python 3.10+ and setuptools installed:

```powershell
python -m pip install --no-index --no-build-isolation -e .
kgdd fixtures --out demo
kgdd run --input demo
kgdd report --format md
python -m pytest -q
```

If a Windows user installation puts kgdd.exe outside PATH, add the Scripts directory printed by pip to PATH, or use the module entry point below.

Install pytest separately in your environment if it is absent. No runtime dependencies. The module entry point also works without installation: `python -m koml_goal_drift_detector.cli` followed by the same arguments. On shells supporting `&&`, the demo is `kgdd fixtures --out demo && kgdd run --input demo && kgdd report --format md`.

Results default to `.kgdd-results.json` in the working directory. Report reads that saved snapshot, so rerun `run` after changing input. Use separate `--results` paths for separate jobs. No times, random IDs, directory paths or performance measurements are injected into computed results. Same input and format yield identical bytes. Fixtures use a fixed arithmetic pattern, no randomness and no seed.

## Input reference

An input directory contains one UTF-8 `activities.json`. Other files, including fixture expectations, are not read by the engine. JSON is the supported input format; CSV and YAML are not accepted. A nonempty directory without this file is a named missing-input error. An empty directory produces an empty report with zero counts and an explicit empty-input provenance statement.

The top-level object has exactly these fields:

| Field | Contract |
| --- | --- |
| synthetic | Boolean. True for any synthetic or illustrative dataset. Do not mix real and synthetic records in one dataset. |
| source | Nonempty description of who entered the data and its provenance. Real input should identify Henry's own hand-entered data when that is true. Authorship is operator-declared, not verified. |
| as_of | ISO date YYYY-MM-DD. Explicit cutoff used for future-date validation, independent of wall clock. |
| objectives | Array of objects with unique id, description, and nonempty unique allowed_actions array. |
| records | Array of activity objects, detailed below. |

Every record requires `id`, `objective_id`, `action`, `description`, `date`, `contributes`, and `cost_cents`. Optional `expected_drift` is a boolean hand-checked label for evaluation only. IDs must be unique. Text must be nonempty and at most 20,000 characters. Unicode and Windows paths are supported. Dates cannot exceed `as_of`. `contributes` is strictly boolean. Costs are entered integer cents from 0 through 1,000,000,000,000; negative amounts, booleans, floats and larger values are rejected. There is no currency conversion: all input cents must use the same operator-selected currency. Missing/extra fields, duplicate JSON keys, NaN, and Infinity are rejected. No records are silently dropped.

A tiny handwritten five-record synthetic input:

```json
{
  "synthetic": true,
  "source": "Handwritten illustrative example, not real activity",
  "as_of": "2026-09-30",
  "objectives": [{"id": "ship", "description": "Ship a tested tool", "allowed_actions": ["code", "test"]}],
  "records": [
    {"id": "a", "objective_id": "ship", "action": "code", "description": "Implement", "date": "2026-09-30", "contributes": true, "cost_cents": 10},
    {"id": "b", "objective_id": "ship", "action": "test", "description": "Verify", "date": "2026-09-30", "contributes": true, "cost_cents": 20},
    {"id": "c", "objective_id": "other", "action": "code", "description": "Wrong goal", "date": "2026-09-30", "contributes": true, "cost_cents": 30},
    {"id": "d", "objective_id": "ship", "action": "browse", "description": "Outside rules", "date": "2026-09-30", "contributes": true, "cost_cents": 40},
    {"id": "e", "objective_id": "ship", "action": "code", "description": "No contribution", "date": "2026-09-30", "contributes": false, "cost_cents": 50}
  ]
}
```

Expected: 5 activities, 3 flagged, 2 aligned, 150 entered cents, 120 entered cents attached to flagged activity. These are illustrative input amounts, not savings.

## Rules and traceability

A record is flagged if its objective ID is unknown (`unknown_objective`), its action is outside the known objective's exact allowed-action strings (`action_outside_objective`), or its contribution assertion is false (`declared_no_contribution`). Multiple reasons can apply; a record and its cost count once. String comparisons are case-sensitive. An aligned record only means these explicit checks passed. Free-text descriptions do not affect classification.

Every finding includes the original activity ID, objective ID, reasons and entered cost. Total entered cost sums every record; drift entered cost sums flagged records only. Evaluation compares decisions with supplied `expected_drift` labels; unlabelled records are not evaluated. Zero false positives on an unlabelled dataset is not evidence of accuracy. Missing labels are reflected in `labelled_records`.

## Subcommand catalogue

All subcommands have `--help` and examples.

| Command | Example | Purpose |
| --- | --- | --- |
| fixtures | `kgdd fixtures --out demo` | Generate labelled 200-record synthetic input and independent expectations. Overwrites its three named fixture files. |
| run | `kgdd run --input demo --results result.json` | Validate and compute, atomically save a deterministic result snapshot. |
| check | `kgdd check --input demo` | Validate objective and activity contracts without writing results. |
| drift | `kgdd drift --input demo` | Compute and display flagged activities with reasons and provenance. |
| report | `kgdd report --results result.json --format json --out report.json` | Render saved results as JSON or Markdown. Output parents must already exist. |

Success returns 0; named input, schema or write errors return 2. Argument errors include usage. Bad JSON reports file, line and column. Duplicate JSON keys and schema errors report file and line 1 with the offending schema location, rather than claiming a precise field line. Missing input includes a usage hint. Report write failures clean temporary files and preserve existing destinations. Report snapshots are generated by `run`; they are local operator-controlled artifacts, not cryptographically verified evidence.

## Architecture

```text
activities.json -> cli.read_input -> core.validate -> core.analyze
                                                      |
                                                      v
                                              result snapshot
                                                      |
                                                      v
                                               report.render
                                              /             
                                        Markdown           JSON
fixtures.generate -> activities.json + expectations.json + SYNTHETIC.md
```

Core functions perform no I/O and do not mutate input. CLI handles local reads, named errors and atomic report/result writes. Fixtures and rendering are separate modules.

## Honesty boundary

The tool computes only from explicit input assertions. It does not discover intent, predict outcomes, estimate contribution, verify authorship or measure savings. Synthetic and illustrative costs are synthetic entered amounts, not real expenditure. Real costs are operator-entered amounts, not independently audited measurements. Time and money saved are refused because no measured baseline is provided. Reports explicitly mark savings as unmeasured. No hypothetical savings figure is emitted.

Markdown has a visible provenance banner. JSON carries a provenance object with synthetic status, source, cutoff and honesty boundary. Synthetic CLI commands label their provenance. Input text containing an em dash is rendered with a hyphen in Markdown; JSON escapes non-ASCII characters and preserves the original value when decoded. The repository and emitted output contain no literal em dashes.

## Fixture labelling and independent ground truth

Every fixture JSON file contains `synthetic: true`. JSON cannot contain header comments, so its label is a field. The Markdown fixture has a synthetic header comment. No real trial records are shipped. Forty groups of five contain two aligned records and three drift records: unknown objective, unapproved action, and no contribution. All 200 costs are illustrative 100 cents each. Thus 120 drift, 80 aligned, 20,000 total entered cents and 12,000 drift entered cents. The expectations file stores this independently derived arithmetic; runtime never reads it. Tests assert the exact finding IDs as well as totals. Corrupting labels changes evaluation; changing activity changes decisions and costs.

## Failure modes and limits

Stale or poorly chosen allowed actions can flag useful work. A dishonest `contributes: true` can pass the checks. Unknown objectives are flagged, not discarded, to surface undeclared goal switches. Declared cutoff dates can be stale; future means later than that cutoff. This design requires operator discipline and hand checks; it cannot judge semantic relevance. A saved result can become stale relative to input. No false promise of semantic supervision is made.

## Evidence-based improvement hook and verdict

Start a private trial with Henry's own hand-entered real data. After 14 days, hand-check all records if fewer than 30, otherwise a reproducible sample of 30 sorted activity IDs spaced across the trial. Record sample IDs, expected decisions, actual decisions and disagreement count. Primary metric is disagreements divided by checked records. Also record daily run counts to establish actual use. Do not ship the real trial data.

If error exceeds 10 percent, fix the top documented failure cause and retest or kill with the reason. If never used, kill with the reason. No two-week evidence is yet available: verdict is pending, not an invented completed outcome. Record the final verdict and measured reason in a private trial log and a public redacted verdict note. Choose expand for daily use or revenue, integrate for heavy sibling overlap, commercialise if an actual buyer would pay as-is, maintain as portfolio evidence otherwise, or kill for no use or unmet acceptance criteria. Baseline savings may only be claimed after a separate measured comparison; this version does not emit them.

See EVIDENCE.md for local acceptance results and LESSONS.md for operating lessons.
