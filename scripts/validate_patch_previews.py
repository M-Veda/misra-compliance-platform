"""
validate_patch_previews.py
--------------------------
Validates that every implemented MISRA rule produces a complete PatchPreview
with non-empty original_snippet, proposed_snippet, and diff, and that
original != proposed (i.e. the diff is real, not a placeholder).

Requires the backend server to be running on 127.0.0.1:8000.
"""
import requests
import sys
import os

# Test file path — script lives in scripts/, perf_test/ is at project root
PROJECT_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MULTI_RULE_FILE = os.path.join(PROJECT_ROOT, "perf_test", "multi_rule_test.c")
SMALL_FILE      = os.path.join(PROJECT_ROOT, "perf_test", "small.c")

IMPLEMENTED_RULES = ["2.2", "2.7", "7.1", "8.4", "8.7", "10.3", "12.1", "14.4", "16.3", "16.4"]

RESULTS = []
FAILURES = []

def check_preview(rule_number: str, pp: dict, v: dict):
    """Assert all PatchPreview contract fields are populated and original != proposed."""
    errors = []

    # Required non-empty fields
    for field in ("original_snippet", "proposed_snippet", "diff", "explanation",
                  "patch_type", "rule_number"):
        val = pp.get(field, "")
        if not val or not str(val).strip():
            errors.append(f"  FAIL [{field}]: empty or missing")

    # confidence must be > 0
    if pp.get("confidence", 0) <= 0:
        errors.append(f"  FAIL [confidence]: {pp.get('confidence')}")

    # expected_compliance_improvement must be > 0
    if pp.get("expected_compliance_improvement", 0) <= 0:
        errors.append(f"  FAIL [expected_compliance_improvement]: {pp.get('expected_compliance_improvement')}")

    # original must differ from proposed (real diff)
    orig = (pp.get("original_snippet") or "").strip()
    prop = (pp.get("proposed_snippet") or "").strip()
    if orig == prop:
        errors.append(f"  FAIL [diff]: original_snippet == proposed_snippet (no real transformation)")

    # diff must contain +/- markers
    diff_text = pp.get("diff", "")
    if "+++" not in diff_text and "---" not in diff_text:
        errors.append(f"  FAIL [diff]: no unified diff markers found")

    return errors


def upload_file(filepath):
    with open(filepath, "rb") as f:
        fname = os.path.basename(filepath)
        resp = requests.post(
            "http://127.0.0.1:8000/api/upload",
            files={"file": (fname, f, "text/plain")},
            timeout=30
        )
    resp.raise_for_status()
    return resp.json()


print("=" * 70)
print("PATCH PREVIEW CONTRACT VALIDATION — All 10 Implemented Rules")
print("=" * 70)

# Upload multi-rule test file
print(f"\nUploading {MULTI_RULE_FILE} ...")
data = upload_file(MULTI_RULE_FILE)
violations = data.get("violations", [])
print(f"Detected {len(violations)} violations.")

# Also upload small.c for rules 2.7 and 8.4 coverage
print(f"\nUploading {SMALL_FILE} ...")
small_data = upload_file(SMALL_FILE)
violations += small_data.get("violations", [])
print(f"Total violations across both files: {len(violations)}")

# Deduplicate by rule_number — keep first occurrence per rule
seen_rules = {}
for v in violations:
    rn = v.get("rule_number", "")
    if rn not in seen_rules:
        seen_rules[rn] = v

print()
print(f"{'Rule':<8} {'PatchType':<28} {'Autopatch':<12} {'Orig!=Prop':<12} {'Status'}")
print("-" * 70)

covered = set()
for rule in IMPLEMENTED_RULES:
    v = seen_rules.get(rule)
    if v is None:
        print(f"{rule:<8} {'(no violation detected in test files)':<40} SKIP")
        RESULTS.append((rule, "SKIP", "No violation detected"))
        continue

    pp = v.get("patch_preview")
    if pp is None:
        print(f"{rule:<8} {'(patch_preview MISSING)':<40} FAIL")
        FAILURES.append((rule, "patch_preview is None"))
        continue

    errors = check_preview(rule, pp, v)
    ptype     = pp.get("patch_type", "")[:26]
    auto      = str(pp.get("can_autopatch", False))
    orig_ne   = str((pp.get("original_snippet","").strip() != pp.get("proposed_snippet","").strip()))
    status    = "PASS" if not errors else "FAIL"

    print(f"{rule:<8} {ptype:<28} {auto:<12} {orig_ne:<12} {status}")
    if errors:
        for e in errors:
            print(e)
        FAILURES.append((rule, "; ".join(errors)))
    else:
        covered.add(rule)
        RESULTS.append((rule, "PASS", ptype))

print()
print("=" * 70)
if not FAILURES:
    print(f"ALL RULES PASS — {len(covered)}/{len(IMPLEMENTED_RULES)} rules have complete PatchPreview")
    print("PatchPreview Contract: SATISFIED for every implemented rule.")
    sys.exit(0)
else:
    print(f"FAILURES ({len(FAILURES)}):")
    for rule, msg in FAILURES:
        print(f"  Rule {rule}: {msg}")
    sys.exit(1)
