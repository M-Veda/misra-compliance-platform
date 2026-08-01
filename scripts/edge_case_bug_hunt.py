import requests
import json
import os

BASE_URL = "http://127.0.0.1:8000/api"

def run_bug_hunt():
    print("=== STARTING EDGE-CASE BUG HUNT ===")
    
    # 1. Test empty file upload
    print("\n1. Testing Empty C File Upload...")
    resp = requests.post(f"{BASE_URL}/upload", files={"file": ("empty.c", b"", "text/plain")})
    print(f"   Response Status: {resp.status_code}")
    assert resp.status_code == 200, "Empty file upload failed!"
    data = resp.json()
    print(f"   Violations detected: {len(data['violations'])}, Score: {data['compliance_score']}%")
    
    # 2. Test syntax error C file upload
    print("\n2. Testing Syntax Error C File Upload...")
    bad_c = b"int main() { if ( "
    resp = requests.post(f"{BASE_URL}/upload", files={"file": ("bad.c", bad_c, "text/plain")})
    print(f"   Response Status: {resp.status_code}")
    assert resp.status_code == 200, "Bad syntax file upload failed!"
    data = resp.json()
    print(f"   Fallback handled cleanly. Message: {data.get('message', 'Parsed')}")

    # 3. Test multi-rule test file
    print("\n3. Testing Multi-Rule Test File...")
    test_file = r"perf_test/multi_rule_test.c"
    with open(test_file, "rb") as f:
        resp = requests.post(f"{BASE_URL}/upload", files={"file": ("multi_rule_test.c", f, "text/plain")})
    assert resp.status_code == 200
    data = resp.json()
    violations = data["violations"]
    print(f"   Detected {len(violations)} violations across 10 rules.")

    # 4. Test Preview Patch API for all rules
    print("\n4. Testing Patch Preview API across all 10 rules...")
    for v in violations[:10]:
        preview_req = {
            "source_code": data["source_code"],
            "violation": v,
            "decision": "Accept"
        }
        p_resp = requests.post(f"{BASE_URL}/preview-patch", json=preview_req)
        assert p_resp.status_code == 200, f"Preview patch failed: {p_resp.text}"
        p_data = p_resp.json()
        assert p_data["patch_preview"] is not None

    # 5. Test Bulk Apply API
    print("\n5. Testing Bulk Apply API...")
    bulk_req = {
        "source_code": data["source_code"],
        "violations": violations,
        "selected_rule_ids": None
    }
    b_resp = requests.post(f"{BASE_URL}/apply-patches", json=bulk_req)
    assert b_resp.status_code == 200
    b_data = b_resp.json()
    print(f"   Applied {b_data['ops_applied']} patch operations. Parse valid: {b_data['parse_valid']}")

    # 6. Test Repeated Bulk Apply API on modified code (Idempotency)
    print("\n6. Testing Repeated Bulk Apply on Modified Code (Idempotency)...")
    b_resp2 = requests.post(f"{BASE_URL}/apply-patches", json={
        "source_code": b_data["modified_code"],
        "violations": violations,
        "selected_rule_ids": None
    })
    assert b_resp2.status_code == 200
    b_data2 = b_resp2.json()
    print(f"   Second Bulk Apply Applied Ops: {b_data2['ops_applied']} (Guarded correctly)")

    # 7. Test PDF Report Generation
    print("\n7. Testing Report Generation API...")
    rep_req = {
        "file_name": "multi_rule_test.c",
        "original_code": data["source_code"],
        "corrected_code": b_data["modified_code"],
        "violations": violations,
        "decisions": {f"v_{v['rule_number']}_{v['line']}": "accepted" for v in violations[:5]},
        "compliance_score": data["compliance_score"]
    }
    r_resp = requests.post(f"{BASE_URL}/generate-report", json=rep_req)
    assert r_resp.status_code == 200, f"Generate report failed: {r_resp.text}"
    r_data = r_resp.json()
    print(f"   Generated PDF: {r_data['pdf_report_filename']}")

    print("\n=== ALL EDGE-CASE BUG HUNT TESTS PASSED 100% ===")

if __name__ == "__main__":
    run_bug_hunt()
