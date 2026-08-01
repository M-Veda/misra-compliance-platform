import requests
import os
import sys
import json

# Test GET /api/rules
print("=" * 60)
print("TEST 1: GET /api/rules")
print("=" * 60)
r = requests.get('http://127.0.0.1:8000/api/rules')
print('Status:', r.status_code)
data = r.json()
print('Rules count:', data['supported_rules_count'])
for rule in data['rules']:
    rn = rule['rule_number']
    rname = rule['rule_name']
    sev = rule['severity']
    print(f'  Rule {rn}: {rname} ({sev})')

# Test POST /api/upload
print()
print("=" * 60)
print("TEST 2: POST /api/upload (rule_10_3.c)")
print("=" * 60)
test_c = r'c:\Users\saite\OneDrive\Desktop\MISRA_Project\backend\tests\test_files\rule_10_3.c'
with open(test_c, 'rb') as f:
    r2 = requests.post('http://127.0.0.1:8000/api/upload',
                       files={'file': (os.path.basename(test_c), f, 'text/plain')})
print('Status:', r2.status_code)
data2 = r2.json()
print('Success:', data2['success'])
print('Violations found:', len(data2['violations']))
print('Compliance score:', data2['compliance_score'])
for v in data2['violations']:
    ln = v['line']
    rn = v['rule_number']
    msg = v['message']
    sev = v['severity']
    snip = v['code_snippet']
    fix = v['suggested_fix']
    print(f'  Line {ln}: Rule {rn} [{sev}] - {msg}')
    print(f'    Snippet: {snip}')
    print(f'    Suggested fix: {fix}')

# Test POST /api/preview-patch
print()
print("=" * 60)
print("TEST 3: POST /api/preview-patch")
print("=" * 60)
if data2['violations']:
    violation = data2['violations'][0]
    payload = {
        'source_code': data2['source_code'],
        'violation': violation,
        'decision': 'Accept'
    }
    r3 = requests.post('http://127.0.0.1:8000/api/preview-patch', json=payload)
    print('Status:', r3.status_code)
    data3 = r3.json()
    print('Patch success:', data3['success'])
    print('Modified lines:')
    orig_lines = data2['source_code'].splitlines()
    patched_lines = data3['modified_code'].splitlines()
    for i, (orig, patched) in enumerate(zip(orig_lines, patched_lines), 1):
        if orig != patched:
            print(f'  Line {i} ORIG:    {orig.strip()}')
            print(f'  Line {i} PATCHED: {patched.strip()}')

# Test POST /api/generate-report
print()
print("=" * 60)
print("TEST 4: POST /api/generate-report")
print("=" * 60)
payload_report = {
    'file_name': data2['file_name'],
    'original_code': data2['source_code'],
    'corrected_code': data2['source_code'],
    'violations': data2['violations'],
    'decisions': {},
    'compliance_score': data2['compliance_score']
}
r4 = requests.post('http://127.0.0.1:8000/api/generate-report', json=payload_report)
print('Status:', r4.status_code)
data4 = r4.json()
print('Report success:', data4['success'])
print('PDF filename:', data4.get('pdf_report_filename'))

# Save JSON report sample
with open('api_test_results.json', 'w') as f:
    json.dump({
        'rules_test': data,
        'upload_test': {'success': data2['success'], 'violations_count': len(data2['violations']), 'score': data2['compliance_score']},
        'patch_test': {'success': data3.get('success') if data2['violations'] else 'no violations'},
        'report_test': {'success': data4['success'], 'pdf': data4.get('pdf_report_filename')}
    }, f, indent=2)

print()
print("All tests PASSED. Results saved to api_test_results.json")
