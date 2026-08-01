"""
live_api_verification.py -- Complete Live API Verification
Runs against http://127.0.0.1:8000 using the actual request/response
shapes matched to violation.py models and main.py endpoints.
"""
import json, sys, pathlib, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

BASE     = "http://127.0.0.1:8000/api"
SRC_FILE = "perf_test/multi_rule_test.c"
OUT_DIR  = pathlib.Path(__file__).parent
OUT_JSON = OUT_DIR / "live_evidence.json"
OUT_MD   = OUT_DIR / "live_evidence_report.md"
RULES    = ["2.2","2.7","7.1","8.4","8.7","10.3","12.1","14.4","16.3","16.4"]
FIELDS_17= ["violation_id","rule_number","file","line","column",
            "original_start_line","original_end_line",
            "original_source","replacement_source","unified_diff",
            "explanation","confidence","patch_type",
            "applies_cleanly","can_autopatch","affected_lines","compliance_gain"]

results  = []   # list of (PASS/FAIL, label, detail)
evidence = {}

def chk(cond, label, detail=""):
    icon = "PASS" if cond else "FAIL"
    results.append((icon, label, str(detail)))
    suffix = (": " + str(detail)) if detail else ""
    print("  [" + icon + "] " + label + suffix)
    return cond

def sep(title):
    print("\n" + "="*70)
    print(title)
    print("="*70)

# =========================================================
sep("STEP 1: Upload & analyse multi_rule_test.c")
with open(SRC_FILE, "rb") as f:
    r = requests.post(BASE + "/upload",
                      files={"file": ("multi_rule_test.c", f, "text/plain")})
assert r.status_code == 200, "Upload failed: " + r.text
d = r.json()
violations    = d["violations"]          # list of serialised RuleViolation dicts
source_code   = d["source_code"]        # NB: key is source_code, not original_source
detected_rules= sorted(set(v["rule_number"] for v in violations))

print("  Violations: " + str(len(violations)) + "  rules: " + str(detected_rules))
chk(len(violations) >= 10, "At least 10 violations detected", str(len(violations)))
for rule in RULES:
    chk(rule in detected_rules, "Rule " + rule + " violation detected")
evidence["step1"] = {"total": len(violations), "rules": detected_rules}

# =========================================================
sep("STEP 2: Per-rule patch preview (reading embedded patch_preview field)")
per_rule = {}
for v in violations:
    rule = v["rule_number"]
    if rule not in RULES or rule in per_rule:
        continue
    pp = v.get("patch_preview") or {}
    chk(bool(pp), "Rule " + rule + ": patch_preview embedded in violation")
    missing = [fi for fi in FIELDS_17 if fi not in pp]
    chk(not missing, "Rule " + rule + ": 17 mandatory fields", str(missing) if missing else "")
    orig = pp.get("original_source","").strip()
    repl = pp.get("replacement_source","").strip()
    chk(orig != repl, "Rule " + rule + ": original_source != replacement_source")
    chk(bool(pp.get("unified_diff","")), "Rule " + rule + ": unified_diff non-empty")
    chk(pp.get("patch_type") == "AUTO_PATCH", "Rule " + rule + ": patch_type=AUTO_PATCH", pp.get("patch_type",""))
    chk(pp.get("can_autopatch") is True, "Rule " + rule + ": can_autopatch=True")
    chk(pp.get("applies_cleanly") is True, "Rule " + rule + ": applies_cleanly=True")
    if rule == "14.4":
        found = any(k in repl for k in ["!= 0","!= NULL","== true","== 1"])
        chk(found, "Rule 14.4: explicit comparison in replacement", repl[:100])
    per_rule[rule] = {"violation": v, "preview": pp}
    sl, el, pt = pp.get("original_start_line"), pp.get("original_end_line"), pp.get("patch_type")
    print("  Rule " + rule + ": lines=" + str(sl) + "-" + str(el) + " type=" + str(pt))
evidence["per_rule"] = per_rule

MANUAL_ONLY_RULES = set()

# =========================================================
sep("STEP 3: /api/preview-patch endpoint (Accept decision)")
for rule in RULES[:5]:   # test first 5 rules to verify endpoint works
    rec = per_rule.get(rule)
    if not rec:
        continue
    payload = {
        "source_code": source_code,
        "violation": rec["violation"],
        "decision": "Accept",
    }
    pr = requests.post(BASE + "/preview-patch", json=payload)
    chk(pr.status_code == 200, "Rule " + rule + ": /preview-patch 200", str(pr.status_code))
    if pr.status_code == 200:
        pd = pr.json()
        chk(pd.get("success"), "Rule " + rule + ": preview success=True")
        chk(pd.get("can_autopatch"), "Rule " + rule + ": preview can_autopatch=True")
        chk(pd.get("patch_actually_changed"), "Rule " + rule + ": patch_actually_changed=True")

# =========================================================
sep("STEP 4: Bulk Accept (/api/apply-patches)")
ar = requests.post(BASE + "/apply-patches",
                   json={"source_code": source_code, "violations": violations})
chk(ar.status_code == 200, "apply-patches 200")
ad = ar.json()
patched      = ad.get("modified_code","")
ops_applied  = ad.get("ops_applied",0)
parse_valid  = ad.get("parse_valid",False)
chk(bool(patched), "patched modified_code non-empty")
chk(parse_valid, "parse_valid=True")
chk(patched != source_code, "patched differs from original")
print("  ops_applied=" + str(ops_applied) + " parse_valid=" + str(parse_valid) + " patched_len=" + str(len(patched)))
evidence["bulk_apply"] = {"ops": ops_applied, "parse_valid": parse_valid, "len": len(patched)}

# =========================================================
sep("STEP 5: Re-analysis (idempotency check)")
re_r = requests.post(BASE + "/upload",
                     files={"file": ("patched.c", patched.encode("utf-8"), "text/plain")})
chk(re_r.status_code == 200, "re-analysis upload 200")
remaining     = re_r.json().get("violations",[])
rem_rules     = sorted(set(v["rule_number"] for v in remaining))
print("  Remaining violations: " + str(len(remaining)) + "  rules: " + str(rem_rules))
for rule in RULES:
    chk(rule not in rem_rules, "Rule " + rule + ": auto-patchable eliminated after bulk patch")
evidence["reanalysis"] = {"remaining": len(remaining), "rules": rem_rules}

# =========================================================
sep("STEP 6: Per-rule single-accept + re-analyse (idempotency for auto-patchable rules)")
for v in violations:
    rule = v["rule_number"]
    if rule in MANUAL_ONLY_RULES or rule not in per_rule:
        continue
    sa = requests.post(BASE + "/apply-patches",
                       json={"source_code": source_code, "violations": [v]})
    if sa.status_code != 200:
        chk(False, "Rule " + rule + ": single-accept 200"); continue
    sp = sa.json().get("modified_code", source_code)
    re_s = requests.post(BASE + "/upload",
                         files={"file": ("idm.c", sp.encode("utf-8"), "text/plain")})
    if re_s.status_code != 200:
        chk(False, "Rule " + rule + ": idempotency re-analyse 200"); continue
    still = [rv for rv in re_s.json().get("violations",[])
             if rv["rule_number"] == rule and rv["line"] == v["line"]]
    chk(len(still) == 0, "Rule " + rule + ": idempotent at line " + str(v["line"]))

# =========================================================
sep("STEP 7: Report generation")
rpt_r = requests.post(BASE + "/generate-report",
                      json={"file_name":"multi_rule_test.c",
                            "original_code": source_code,
                            "corrected_code": patched,
                            "violations": violations,
                            "decisions": {},
                            "compliance_score": d.get("compliance_score", 0.0)})
chk(rpt_r.status_code == 200, "generate-report 200")
rpt_fn = rpt_r.json().get("report_filename","")
rpt_bytes = 0
if rpt_fn:
    dl = requests.get(BASE + "/download-pdf/" + rpt_fn)
    chk(dl.status_code == 200, "PDF download 200")
    rpt_bytes = len(dl.content)
    chk(rpt_bytes > 1000, "PDF size > 1KB", str(rpt_bytes) + " bytes")
evidence["report"] = {"file": rpt_fn, "bytes": rpt_bytes}

# =========================================================
sep("OUTPUT")
passed = sum(1 for icon,_,_ in results if icon=="PASS")
failed = sum(1 for icon,_,_ in results if icon=="FAIL")
print("\n  TOTAL: " + str(passed) + " PASS | " + str(failed) + " FAIL out of " + str(len(results)) + " checks")

# --- Write JSON evidence
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
ev_clean = {
    "step1": evidence["step1"],
    "bulk_apply": evidence["bulk_apply"],
    "reanalysis": evidence["reanalysis"],
    "report": evidence["report"],
    "per_rule": {
        rule: {
            "violation": {"rule_number": rec["violation"]["rule_number"],
                          "line": rec["violation"]["line"],
                          "message": rec["violation"]["message"],
                          "snippet": rec["violation"].get("code_snippet","")},
            "preview": {fi: rec["preview"].get(fi,"") for fi in FIELDS_17}
        }
        for rule, rec in per_rule.items()
    }
}
with open(OUT_JSON, "w", encoding="utf-8") as fh:
    json.dump(ev_clean, fh, indent=2, default=str)

# --- Write Markdown evidence report
md = []
md.append("# Live Application Verification — Evidence Report")
md.append("")
md.append("**Total checks**: " + str(len(results)) + " | **PASS**: " + str(passed) + " | **FAIL**: " + str(failed))
md.append("")
md.append("**Test file**: `multi_rule_test.c`  ")
md.append("**Backend endpoint**: `" + BASE + "`")
md.append("")
md.append("---")
md.append("")
md.append("## Summary Table")
md.append("")
md.append("| Status | Check | Detail |")
md.append("|---|---|---|")
for icon, label, detail in results:
    sym = "PASS" if icon == "PASS" else "FAIL"
    md.append("| " + sym + " | " + label + " | " + str(detail)[:120] + " |")

md.append("")
md.append("---")
md.append("")
md.append("## Per-Rule Patch Preview Evidence")
md.append("")
for rule in RULES:
    rec = per_rule.get(rule)
    md.append("### Rule " + rule)
    md.append("")
    if not rec:
        md.append("_Not captured_")
        md.append("")
        continue
    v2 = rec["violation"]
    p2 = rec["preview"]
    md.append("**Violation** (line " + str(v2["line"]) + "): " + str(v2["message"]))
    md.append("")
    md.append("**Code snippet**: `" + str(v2.get("code_snippet",""))[:100] + "`")
    md.append("")
    md.append("| Field | Value |")
    md.append("|---|---|")
    md.append("| patch_type | `" + str(p2.get("patch_type")) + "` |")
    md.append("| can_autopatch | `" + str(p2.get("can_autopatch")) + "` |")
    md.append("| applies_cleanly | `" + str(p2.get("applies_cleanly")) + "` |")
    md.append("| confidence | `" + str(p2.get("confidence")) + "` |")
    md.append("| original_start_line | `" + str(p2.get("original_start_line")) + "` |")
    md.append("| original_end_line | `" + str(p2.get("original_end_line")) + "` |")
    md.append("")
    md.append("**Original Source**:")
    md.append("")
    md.append("```c")
    md.append(str(p2.get("original_source","")))
    md.append("```")
    md.append("")
    md.append("**Replacement Source**:")
    md.append("")
    md.append("```c")
    md.append(str(p2.get("replacement_source","")))
    md.append("```")
    md.append("")
    md.append("**Unified Diff**:")
    md.append("")
    md.append("```diff")
    md.append(str(p2.get("unified_diff","")))
    md.append("```")
    md.append("")
    md.append("**Explanation**: " + str(p2.get("explanation","")))
    md.append("")
    md.append("---")
    md.append("")

md.append("## Bulk Accept & Re-analysis")
md.append("")
ba = evidence["bulk_apply"]
md.append("- Ops applied: **" + str(ba["ops"]) + "**")
md.append("- Parse valid: **" + str(ba["parse_valid"]) + "**")
md.append("- Patched source length: **" + str(ba["len"]) + " chars**")
md.append("")
ra = evidence["reanalysis"]
md.append("- Remaining violations after bulk patch: **" + str(ra["remaining"]) + "**")
md.append("- Remaining rules: **" + str(ra["rules"]) + "**")
md.append("")
md.append("## Report Generation")
md.append("")
rp = evidence["report"]
md.append("- PDF: `" + str(rp.get("file","N/A")) + "`")
md.append("- Size: **" + str(rp.get("bytes",0)) + " bytes**")

with open(OUT_MD, "w", encoding="utf-8") as fh:
    fh.write("\n".join(md))

print("  Evidence JSON   -> " + str(OUT_JSON))
print("  Evidence Report -> " + str(OUT_MD))
sys.exit(0 if failed == 0 else 1)
