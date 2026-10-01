"""Local JSON workflow. Errors are named and writes replace atomically."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import analyze, SchemaError
from .fixtures import generate
from .report import render

class InputError(ValueError):
    pass

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field {key}")
        result[key] = value
    return result

def read_input(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}; use kgdd fixtures --out <dir> or supply an input directory")
    path = directory / "activities.json"
    if not path.exists():
        if any(directory.iterdir()):
            raise InputError(f"MissingInput: {path}; expected activities.json")
        return {"synthetic": False, "source": "Empty local input directory; no records", "as_of": "1970-01-01", "objectives": [], "records": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"invalid JSON constant {value}")))
    except json.JSONDecodeError as exc:
        raise InputError(f"ParseError: {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    except (UnicodeError, ValueError) as exc:
        raise InputError(f"ParseError: {path}: line 1: {exc}") from exc
    try:
        analyze(data)
    except SchemaError as exc:
        raise InputError(f"SchemaError: {path}: line 1 (schema location): {exc}") from exc
    return data

def atomic_write(path, content):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, path)
    except OSError as exc:
        raise InputError(f"WriteError: {path}: {exc}") from exc
    finally:
        if temporary and temporary.exists():
            temporary.unlink()

def main(argv=None):
    parser = argparse.ArgumentParser(description="Detect rule-based goal drift from declared local inputs.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("fixtures", help="Generate 200 labelled synthetic records", epilog="Example: kgdd fixtures --out demo")
    p.add_argument("--out", required=True)
    for command, help_text in [("run", "Analyze activity against objectives"), ("check", "Validate the objective and activity schema"), ("drift", "Print flagged activities and explicit reasons")]:
        p = sub.add_parser(command, help=help_text, description=help_text, epilog=f"Example: kgdd {command} --input demo")
        p.add_argument("--input", required=True)
        if command == "run":
            p.add_argument("--results", default=".kgdd-results.json")
    p = sub.add_parser("report", help="Render saved computed results with provenance", epilog="Example: kgdd report --format md")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--results", default=".kgdd-results.json")
    p.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 labelled SYNTHETIC records; entered costs are illustrative, savings unmeasured.")
        elif args.command in ("run", "check", "drift"):
            result = analyze(read_input(args.input))
            if args.command == "run":
                atomic_write(args.results, render(result, "json"))
                print(f"Computed {result['summary']['records']} records; provenance: " + ("SYNTHETIC" if result['provenance']['synthetic'] else "operator-declared REAL input") + "; savings unmeasured.")
            elif args.command == "check":
                print("Schema valid; provenance: " + ("SYNTHETIC" if result['provenance']['synthetic'] else "operator-declared REAL input"))
            else:
                print(render(result, "md"), end="")
        else:
            path = Path(args.results)
            try:
                result = json.loads(path.read_text(encoding="utf-8"))
                output = render(result, args.format)
            except FileNotFoundError as exc:
                raise InputError(f"MissingResult: {path}; use kgdd run --input <dir> first") from exc
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                raise InputError(f"ResultError: {path}: {exc}; rerun kgdd run --input <dir>") from exc
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        return 0
    except (InputError, OSError) as exc:
        message = str(exc) if isinstance(exc, InputError) else f"IOError: {exc}"
        print(message.replace(chr(0x2014), "-"), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
