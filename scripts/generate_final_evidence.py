"""
generate_final_evidence.py — Produces the complete final review package.

Outputs:
  evidence/api_responses/   — Raw API JSON for each rule
  evidence/reports/         — PDF and JSON compliance reports
  evidence/code/            — Original, patched, re-analysis code for each rule
  evidence/summary.json     — Machine-readable full audit

Usage:
  python scripts/generate_final_evidence.py
"""
import json
import os
import sys
import pathlib
import requests
import textwrap

BASE = "http://127.0.0.1:8000/api"
PROJECT = pathlib.Path(r"c:\Users\saite\OneDrive\Desktop\MISRA_Project")
EVIDENCE = PROJECT / "evidence"
API_DIR = EVIDENCE / "api_responses"
CODE_DIR = EVIDENCE / "code"
REPORT_DIR = EVIDENCE / "reports"

for d in [API_DIR, CODE_DIR, REPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

RULES = ["2.2", "2.7", "7.1", "8.4", "8.7", "10.3", "12.1", "14.4", "16.3", "16.4"]

RULE_SAMPLES = {
    "2.2": textwrap.dedent("""\
        #include <stdio.h>
        int dead_code_func(int x) {
            if (x > 0) {
                return 1;
                return 99;   /* dead */
            }
            return 0;
        }
        int main(void) { return dead_code_func(1); }
    """),
    "2.7": textwrap.dedent("""\
        #include <stdio.h>
        int func_with_unused(int active, int unused_param) {
            return active + 5;
        }
        int main(void) { return func_with_unused(1, 2); }
    """),
    "7.1": textwrap.dedent("""\
        #include <stdio.h>
        int func_octal(void) {
            int x = 017;
            return x;
        }
        int main(void) { return func_octal(); }
    """),
    "8.4": textwrap.dedent("""\
        #include <stdio.h>
        int no_proto_func(int val) { return val + 1; }
        int main(void) { return no_proto_func(5); }
    """),
    "8.7": textwrap.dedent("""\
        #include <stdio.h>
        int global_single_use = 42;
        int func_internal(void) { return global_single_use; }
        int main(void) { return func_internal(); }
    """),
    "10.3": textwrap.dedent("""\
        #include <stdio.h>
        int func_narrowing(void) {
            unsigned int u = 300u;
            int s = u;
            return s;
        }
        int main(void) { return func_narrowing(); }
    """),
    "12.1": textwrap.dedent("""\
        #include <stdio.h>
        int func_precedence(int x, int y, int z) {
            int res = x + y * z;
            return res;
        }
        int main(void) { return func_precedence(1, 2, 3); }
    """),
    "14.4": textwrap.dedent("""\
        #include <stdio.h>
        int func_nonbool(int count) {
            if (count) {
                return 1;
            }
            return 0;
        }
        int main(void) { return func_nonbool(5); }
    """),
    "16.3": textwrap.dedent("""\
        #include <stdio.h>
        int func_no_break(int mode) {
            int res = 0;
            switch (mode) {
                case 1:
                    res = 10;
                case 2:
                    res = 20;
                    break;
                default:
                    res = 0;
                    break;
            }
            return res;
        }
        int main(void) { return func_no_break(1); }
    """),
    "16.4": textwrap.dedent("""\
        #include <stdio.h>
        int func_no_default(int mode) {
            int res = 0;
            switch (mode) {
                case 1:
                    res = 10;
                    break;
                case 2:
                    res = 20;
                    break;
            }
            return res;
        }
        int main(void) { return func_no_default(1); }
    """),
}

summary = {}
all_pass = True

print("=" * 70)
print("FINAL EVIDENCE GENERATION - 10 MISRA C:2012 Rules")
print("=" * 70)

for rule in RULES:
    print(f"\n{'-'*50}")
    print(f"Rule {rule}")
    print(f"{'-'*50}")
    sample = RULE_SAMPLES[rule]
    filename = f"rule_{rule.replace('.', '_')}_sample.c"
    code_bytes = sample.encode("utf-8")

    # --- Step 1: Upload & detect ---
    resp = requests.post(BASE + "/upload",
                         files={"file": (filename, code_bytes, "text/plain")})
    assert resp.status_code == 200, f"Upload failed: {resp.text}"
    upload_data = resp.json()
    violations = upload_data["violations"]
    rule_viols = [v for v in violations if v["rule_number"] == rule]
    print(f"  Violations detected: {len(violations)} total, {len(rule_viols)} for Rule {rule}")
    if not rule_viols:
        print(f"  [WARN] No violations for Rule {rule}")
        all_pass = False

    # Save raw API response
    (API_DIR / f"rule_{rule.replace('.','_')}_upload.json").write_text(
        json.dumps(upload_data, indent=2), encoding="utf-8")

    # --- Step 2: Patch preview for first violation ---
    if rule_viols:
        v = rule_viols[0]
        # patch_preview is already embedded in each violation from the upload response
        pp = v.get("patch_preview", {})
        has_preview = bool(pp and pp.get("original_source") and pp.get("replacement_source"))
        print(f"  Patch preview: {'PRESENT' if has_preview else 'MISSING'}")
        print(f"    original_start_line: {pp.get('original_start_line')}")
        print(f"    original_end_line:   {pp.get('original_end_line')}")
        print(f"    original_source:     {repr(pp.get('original_source','')[:60])}")
        print(f"    replacement_source:  {repr(pp.get('replacement_source','')[:60])}")
        if not has_preview:
            all_pass = False
        (API_DIR / f"rule_{rule.replace('.','_')}_preview.json").write_text(
            json.dumps(pp, indent=2), encoding="utf-8")

    # --- Step 3: Accept single patch ---
    if rule_viols:
        apply_resp = requests.post(BASE + "/apply-patches", json={
            "source_code": upload_data["source_code"],
            "violations": [rule_viols[0]]
        })
        assert apply_resp.status_code == 200, f"Apply failed: {apply_resp.text}"
        apply_data = apply_resp.json()
        patched_code = apply_data.get("modified_code", "")
        ops = apply_data.get("ops_applied", 0)
        print(f"  Accept Patch: ops_applied={ops}, parse_valid={apply_data.get('parse_valid')}")

        # Re-analyze patched code
        reanalysis_resp = requests.post(BASE + "/upload", files={
            "file": (filename, patched_code.encode("utf-8"), "text/plain")
        })
        reanalysis_data = reanalysis_resp.json()
        re_viols_for_rule = [v for v in reanalysis_data["violations"] if v["rule_number"] == rule]
        decreased = len(re_viols_for_rule) < len(rule_viols)
        print(f"  Re-analysis after Accept Patch: {len(rule_viols)} -> {len(re_viols_for_rule)} violations for Rule {rule} ({'PASS' if decreased else 'FAIL'})")
        if not decreased:
            all_pass = False

        (CODE_DIR / f"rule_{rule.replace('.','_')}_original.c").write_text(sample, encoding="utf-8")
        (CODE_DIR / f"rule_{rule.replace('.','_')}_patched.c").write_text(patched_code, encoding="utf-8")
        (API_DIR / f"rule_{rule.replace('.','_')}_accept.json").write_text(
            json.dumps(apply_data, indent=2), encoding="utf-8")
        (API_DIR / f"rule_{rule.replace('.','_')}_reanalysis.json").write_text(
            json.dumps(reanalysis_data, indent=2), encoding="utf-8")

    summary[rule] = {
        "total_violations_detected": len(violations),
        "rule_violations_detected": len(rule_viols),
        "has_patch_preview": has_preview if rule_viols else False,
        "accept_patch_ops_applied": ops if rule_viols else 0,
        "reanalysis_violation_count": len(re_viols_for_rule) if rule_viols else 0,
        "reanalysis_decreased": decreased if rule_viols else False,
    }

print("\n" + "=" * 70)
print("BULK ACCEPT ALL — heavy_multi_occurrence_test.c")
print("=" * 70)

heavy_path = PROJECT / "perf_test" / "heavy_multi_occurrence_test.c"
heavy_code = heavy_path.read_bytes()
bulk_upload = requests.post(BASE + "/upload",
                            files={"file": ("heavy.c", heavy_code, "text/plain")}).json()
heavy_violations = bulk_upload["violations"]
print(f"  Total violations in heavy file: {len(heavy_violations)}")
for rule in RULES:
    count = sum(1 for v in heavy_violations if v["rule_number"] == rule)
    print(f"    Rule {rule}: {count} violations")

# Bulk Accept All
bulk_apply = requests.post(BASE + "/apply-patches", json={
    "source_code": bulk_upload["source_code"],
    "violations": heavy_violations
}).json()
print(f"  Bulk apply: ops_applied={bulk_apply.get('ops_applied')}, parse_valid={bulk_apply.get('parse_valid')}")

# Re-analysis after Accept All
heavy_patched = bulk_apply.get("modified_code", "")
re_bulk = requests.post(BASE + "/upload", files={
    "file": ("heavy_patched.c", heavy_patched.encode("utf-8"), "text/plain")
}).json()
remaining = len(re_bulk["violations"])
score = re_bulk.get("compliance_score", 0)
print(f"  Re-analysis after Accept All: {remaining} violations remaining ({'PASS' if remaining == 0 else 'FAIL'})")
print(f"  Compliance score: {score}% ({'PASS' if score == 100 else 'FAIL'})")

(API_DIR / "bulk_upload.json").write_text(json.dumps(bulk_upload, indent=2), encoding="utf-8")
(API_DIR / "bulk_accept_all.json").write_text(json.dumps(bulk_apply, indent=2), encoding="utf-8")
(API_DIR / "bulk_reanalysis.json").write_text(json.dumps(re_bulk, indent=2), encoding="utf-8")
(CODE_DIR / "heavy_patched_final.c").write_text(heavy_patched, encoding="utf-8")

# --- PDF + JSON reports ---
print("\n" + "=" * 70)
print("COMPLIANCE REPORTS")
print("=" * 70)

report_resp = requests.post(BASE + "/generate-report", json={
    "source_code": bulk_upload["source_code"],
    "violations": heavy_violations,
    "file_name": "heavy.c",
    "format": "json"
}).json()
print(f"  JSON report: {list(report_resp.keys())}")
(REPORT_DIR / "compliance_report.json").write_text(
    json.dumps(report_resp, indent=2), encoding="utf-8")

pdf_report_resp = requests.post(BASE + "/generate-report", json={
    "source_code": bulk_upload["source_code"],
    "violations": heavy_violations,
    "file_name": "heavy.c"
}).json()
pdf_name = pdf_report_resp.get("pdf_report_filename") or pdf_report_resp.get("pdf_filename") or pdf_report_resp.get("report_filename")
print(f"  PDF generated: {pdf_name}")
if pdf_name:
    dl = requests.get(BASE + f"/download-pdf/{pdf_name}")
    if dl.status_code == 200:
        (REPORT_DIR / pdf_name).write_bytes(dl.content)
        print(f"  PDF saved: {pdf_name} ({len(dl.content)} bytes)")
    else:
        print(f"  PDF download failed: {dl.status_code}")

# Confirm old rules absent in API
print("\n" + "=" * 70)
print("CHECKING OLD RULES (9.1, 15.5, 17.7) NOT IN API RESPONSE")
print("=" * 70)
old_rules_in_api = [v for v in heavy_violations if v["rule_number"] in {"9.1", "15.5", "17.7"}]
if old_rules_in_api:
    print(f"  [FAIL] Old rules found in API response: {[v['rule_number'] for v in old_rules_in_api]}")
    all_pass = False
else:
    print("  [PASS] No old rules (9.1, 15.5, 17.7) in any API response (PASS)")

# Final summary
summary["bulk_accept_all"] = {
    "total_violations": len(heavy_violations),
    "ops_applied": bulk_apply.get("ops_applied"),
    "parse_valid": bulk_apply.get("parse_valid"),
    "remaining_violations": remaining,
    "compliance_score": score,
    "old_rules_in_response": len(old_rules_in_api),
}

(EVIDENCE / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

print("\n" + "=" * 70)
result = "ALL CHECKS PASSED" if all_pass else "SOME CHECKS FAILED"
print(f"FINAL RESULT: {result}")
print("=" * 70)
print(f"\nEvidence written to: {EVIDENCE}")

sys.exit(0 if all_pass else 1)
