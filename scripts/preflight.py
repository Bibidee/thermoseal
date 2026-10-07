from __future__ import annotations

import ast
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
EXPECTED_SOURCE = CONTRACTS / "thermoseal.py"
GENVM_VERSION = "v0.2.16"
SOURCES = sorted(CONTRACTS.glob("*.py"))

if SOURCES != [EXPECTED_SOURCE]:
    raise SystemExit(f"release gate requires exactly contracts/thermoseal.py; found {[p.name for p in SOURCES]}")

raw = EXPECTED_SOURCE.read_bytes()
source = raw.decode("utf-8")
lines = source.splitlines()
version_match = re.search(r'^VERSION\s*=\s*"(\d+\.\d+\.\d+)"\s*$', source, re.MULTILINE)
if not version_match:
    raise SystemExit("contract VERSION constant is missing or malformed")
header_version = re.fullmatch(r"# v(\d+\.\d+\.\d+)", lines[0]) if lines else None
if not header_version or header_version.group(1) != version_match.group(1):
    raise SystemExit("first contract header comment must be '# v<matching-version>'")
if len(lines) < 2 or not re.fullmatch(r'# \{ "Depends": "py-genlayer:[a-z0-9]+" \}', lines[1]):
    raise SystemExit("second contract header comment must pin the py-genlayer dependency")
ast.parse(source, filename=str(EXPECTED_SOURCE))
for requirements_line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
    if "rc" in requirements_line.lower() or "dev" in requirements_line.lower():
        raise SystemExit(f"preview dependency is not allowed for the Studionet release gate: {requirements_line}")

subprocess.run([sys.executable, "-m", "compileall", "-q", "contracts", "tests"], cwd=ROOT, check=True)

lint = shutil.which("genvm-lint") or shutil.which("genvm-lint.exe")
if not lint:
    candidate = Path(sys.executable).with_name("genvm-lint.exe" if sys.platform == "win32" else "genvm-lint")
    if candidate.exists():
        lint = str(candidate)
if not lint:
    raise SystemExit("genvm-lint is required; install requirements.txt")

# Lint only the deployable source. Test helpers and pytest plugins are not
# Intelligent Contract candidates and must never be passed to GenVM lint.
lint_env = os.environ.copy()
lint_env["GENVM_VERSION"] = GENVM_VERSION
subprocess.run(
    [lint, "check", str(EXPECTED_SOURCE), "--json"], cwd=ROOT, check=True, env=lint_env
)

tracked_abi = ROOT / "artifacts" / "thermoseal.abi.json"
if not tracked_abi.is_file():
    raise SystemExit("tracked ABI artifact is missing: artifacts/thermoseal.abi.json")
with tempfile.TemporaryDirectory(prefix="thermoseal-schema-") as temp_dir:
    generated = Path(temp_dir) / "thermoseal.abi.json"
    subprocess.run(
        [lint, "schema", str(EXPECTED_SOURCE), "--output", str(generated)],
        cwd=ROOT,
        check=True,
        env=lint_env,
    )
    if generated.read_bytes() != tracked_abi.read_bytes():
        raise SystemExit("generated schema differs from tracked artifacts/thermoseal.abi.json")

direct_test_env = os.environ.copy()
# Keep Direct Mode on the same released runner used by lint and schema.  The
# pinned test package otherwise falls back to an archived prerelease bundle
# when its process environment is not propagated by a hosted runner.
direct_test_env["GENVM_VERSION"] = GENVM_VERSION
test = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/direct", "-q"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    env=direct_test_env,
)
print(test.stdout, end="")
print(test.stderr, end="", file=sys.stderr)
if test.returncode:
    raise SystemExit(test.returncode)
summary = test.stdout + "\n" + test.stderr
match = re.search(r"(?:^|\s)(\d+) passed(?:,\s*(\d+) skipped)?(?:,\s*(\d+) failed)?\s+in\s", summary)
if not match:
    raise SystemExit("could not verify pytest count summary")
passed, skipped, failed = (int(value or 0) for value in match.groups())
if passed < 1 or skipped or failed:
    raise SystemExit(f"release gate requires tests and no skips/failures: passed={passed}, skipped={skipped}, failed={failed}")

print("contract_version=" + version_match.group(1))
print("contract_sha256=" + hashlib.sha256(raw).hexdigest())
print("contract_source_bytes=" + str(len(raw)))
print("direct_mode_tests=" + str(passed))
print("tests_skipped=" + str(skipped))
print("tests_failed=" + str(failed))
print("deployable_contract_sources=1")
print("lint=PASS")
print("schema_matches=PASS")
print("preflight=PASS")
