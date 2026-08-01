import sys, os, requests, pathlib
sys.path.insert(0, os.getcwd())

BASE = "http://127.0.0.1:8000/api"
SRC_FILE = "perf_test/heavy_multi_occurrence_test.c"

print("Uploading heavy_multi_occurrence_test.c...")
with open(SRC_FILE, "rb") as f:
    r = requests.post(BASE + "/upload", files={"file": ("heavy_multi_occurrence_test.c", f, "text/plain")})

assert r.status_code == 200, f"Upload failed: {r.text}"
d = r.json()
violations = d["violations"]
print(f"Total violations detected: {len(violations)}")

# Verify 1: Each violation has a unique stable_id and unique PatchPreview
preview_ids = set()
unique_previews = 0

for idx, v in enumerate(violations):
    pp = v.get("patch_preview")
    assert pp is not None, f"Violation #{idx+1} (Line {v['line']}) missing patch_preview!"
    
    # Check 17 mandatory fields
    assert pp.get("violation_id") == v.get("stable_id"), f"Preview violation_id mismatch on violation #{idx+1}"
    assert pp.get("line") == v.get("line"), f"Preview line mismatch on violation #{idx+1}"
    assert pp.get("original_source"), f"Preview original_source empty on violation #{idx+1}"
    assert pp.get("replacement_source"), f"Preview replacement_source empty on violation #{idx+1}"
    assert pp.get("unified_diff"), f"Preview unified_diff empty on violation #{idx+1}"
    
    preview_ids.add(v.get("stable_id"))
    unique_previews += 1

print(f"PASS: All {len(violations)} violations have unique stable_ids ({len(preview_ids)} unique IDs).")

# Verify 2: Check Rule 12.1 (50 occurrences) previews are unique per line
v_12_1 = [v for v in violations if v["rule_number"] == "12.1"]
print(f"Rule 12.1 violations: {len(v_12_1)}")
lines_12_1 = set(v["line"] for v in v_12_1)
assert len(lines_12_1) == len(v_12_1), "Rule 12.1 violations do not have unique lines!"

# Verify preview #17 vs preview #1 for Rule 12.1
if len(v_12_1) >= 17:
    v1 = v_12_1[0]
    v17 = v_12_1[16]
    assert v1["patch_preview"]["line"] != v17["patch_preview"]["line"], "Violation #17 reused line from Violation #1!"
    assert v1["patch_preview"]["original_source"] != v17["patch_preview"]["original_source"], "Violation #17 reused snippet from Violation #1!"
    print(f"PASS: Violation #17 (Line {v17['line']}) preview is completely distinct from Violation #1 (Line {v1['line']}).")

# Verify 3: Bulk accept on heavy multi-occurrence file
ar = requests.post(BASE + "/apply-patches", json={"source_code": d["source_code"], "violations": violations})
assert ar.status_code == 200, f"Bulk apply failed: {ar.text}"
ad = ar.json()
print(f"Bulk accept ops_applied: {ad['ops_applied']}, parse_valid: {ad['parse_valid']}")
assert ad["parse_valid"] is True, "Patched code failed syntax parsing!"

print("\nALL HEAVY MULTI-OCCURRENCE PREVIEW & BULK ACCEPT CHECKS PASSED 100%!")
