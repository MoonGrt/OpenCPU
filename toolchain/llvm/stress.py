#!/usr/bin/env python3
"""Run reproducible compiler, software CPU and UART/RTL stress workloads."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "toolchain/llvm/tests"
PROFILES = {
    "quick": {"simulator": (25, 20000), "rtl": 8, "compilers": (8, 8, 3)},
    "full": {"simulator": (1000, 1000000), "rtl": 250, "compilers": (300, 250, 50)},
}


def _git(directory, *args):
    result = subprocess.run(["git", "-C", str(directory), *args],
                            capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def _commands(profile, seed, output):
    counts = PROFILES[profile]
    common = ["--seed", str(seed)]
    return {
        "simulator": [sys.executable, "-B", str(TESTS / "stress_simulator.py"), *common,
                      "--cases", str(counts["simulator"][0]),
                      "--steps", str(counts["simulator"][1]),
                      "--output", str(output / "simulator")],
        "rtl": [sys.executable, "-B", str(TESTS / "stress_rtl.py"), *common,
                "--cases", str(counts["rtl"]), "--output", str(output / "rtl")],
        "compilers": [sys.executable, "-B", str(TESTS / "stress_compilers.py"), *common,
                      "--simple-cases", str(counts["compilers"][0]),
                      "--c-cases", str(counts["compilers"][1]),
                      "--rtl-cases", str(counts["compilers"][2]),
                      "--output", str(output / "compilers")],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=tuple(PROFILES), default="full")
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=20261030)
    parser.add_argument("--component", choices=("all", "simulator", "rtl", "compilers"), default="all")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--collect-only", action="store_true",
                        help="aggregate existing component reports without executing workloads")
    args = parser.parse_args(argv)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    default = ROOT / "build/stress" / ("latest" if args.collect_only else stamp)
    output = (args.output or default).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    commands = _commands(args.profile, args.seed, output)
    names = tuple(commands) if args.component == "all" else (args.component,)
    if not args.collect_only:
        # An interrupted rerun must not leave older success reports for work
        # that has not started yet.
        (output / "summary.json").unlink(missing_ok=True)
        for name in names:
            (output / name / "summary.json").unlink(missing_ok=True)
    started = time.monotonic()
    summary = {
        "seed": args.seed, "profile": "collected" if args.collect_only else args.profile,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "platform": platform.platform(),
        "main_head": _git(ROOT, "rev-parse", "HEAD"),
        "llvm_head": _git(ROOT / "thirdpartys/llvm-project", "rev-parse", "HEAD"),
        "main_dirty": bool(_git(ROOT, "status", "--porcelain")),
        "llvm_dirty": bool(_git(ROOT / "thirdpartys/llvm-project", "status", "--porcelain")),
        "components": {},
    }
    failed = False
    for name in names:
        directory = output / name
        directory.mkdir(parents=True, exist_ok=True)
        report = directory / "summary.json"
        code = 0
        if not args.collect_only:
            print(f"[{name}] running; log: {directory / 'runner.log'}", flush=True)
            with (directory / "runner.log").open("w", encoding="utf-8") as log:
                code = subprocess.run(commands[name], cwd=ROOT, stdout=log,
                                      stderr=subprocess.STDOUT).returncode
        item = {"command": None if args.collect_only else commands[name],
                "returncode": None if args.collect_only else code, "report_path": str(report)}
        try:
            item["report"] = json.loads(report.read_text(encoding="utf-8"))
            if not isinstance(item["report"], dict):
                raise ValueError("component report must be a JSON object")
            if item["report"].get("seed") != args.seed:
                raise ValueError("component seed differs from requested seed")
            component = item["report"]
            problems = component.get("failed", 0)
            if isinstance(problems, (list, dict)):
                problems = len(problems)
            unexpected_limits = component.get("resource_limits", 0)
            if isinstance(unexpected_limits, (list, dict)):
                unexpected_limits = len(unexpected_limits)
            rejected = component.get("status") in ("failed", "incomplete") or component.get("passed") is False
            item["status"] = "failed" if code or problems or unexpected_limits or rejected else "passed"
        except (OSError, ValueError) as error:
            item["status"] = "failed"
            item["error"] = f"No valid completed report: {error}"
        failed |= item["status"] != "passed"
        summary["components"][name] = item
        print(f"[{name}] {item['status']}", flush=True)
    summary["duration_seconds"] = round(time.monotonic() - started, 3)
    summary["status"] = "failed" if failed else "passed"
    destination = output / "summary.json"
    destination.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"{summary['status']}: {destination}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
