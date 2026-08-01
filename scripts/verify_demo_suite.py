import os, sys, json, requests

BASE = 'http://127.0.0.1:8000/api'
project_root = os.path.abspath('C:/Users/saite/OneDrive/Desktop/MISRA_Project')
perf_dir = os.path.join(project_root, 'perf_test')
expected_files = {'small.c', 'medium.c', 'large.c', 'README.md'}
actual_files = {f for f in os.listdir(perf_dir) if os.path.isfile(os.path.join(perf_dir, f))}
print('Directory verification:')
print('Expected files:', expected_files)
print('Actual files  :', actual_files)
if actual_files != expected_files:
    print('ERROR: Unexpected files present or missing files')
    sys.exit(1)
# Line counts
print('\nLine counts:')
for fname in sorted(actual_files):
    with open(os.path.join(perf_dir, fname), 'r', encoding='utf-8') as fp:
        lines = fp.readlines()
    print(f'{fname}: {len(lines)} lines')
# Analyzer checks for each demo C file
for fname in ['small.c', 'medium.c', 'large.c']:
    path = os.path.join(perf_dir, fname)
    with open(path, 'rb') as fp:
        resp = requests.post(f'{BASE}/upload', files={'file': (fname, fp, 'text/plain')})
    if resp.status_code != 200:
        print(f'Upload failed for {fname}:', resp.text)
        sys.exit(1)
    data = resp.json()
    violations = data.get('violations', [])
    print(f'\n--- Analysis of {fname} ---')
    print('Total violations:', len(violations))
    rule_ids = {v.get('rule_number') for v in violations}
    print('Rule IDs detected:', sorted(rule_ids))
    for v in violations:
        print(f"Line {v.get('line')}: Rule {v.get('rule_number')} - {v.get('message')}")
    # Preview Accept for each violation
    for v in violations:
        pr = requests.post(f'{BASE}/preview-patch', json={'source_code': data['source_code'], 'violation': v, 'decision': 'Accept'}).json()
        print(f"Preview accept for rule {v.get('rule_number')}: can_autopatch={pr.get('can_autopatch')}, changed={pr.get('patch_actually_changed')}")
    # Bulk accept all violations
    bulk = requests.post(f'{BASE}/apply-patches', json={'source_code': data['source_code'], 'violations': violations}).json()
    print('Bulk apply result: success=', bulk.get('success'), 'ops_applied=', bulk.get('ops_applied'), 'parse_valid=', bulk.get('parse_valid'))
    # Re-analyze patched code
    temp_path = os.path.join(perf_dir, f'temp_{fname}')
    with open(temp_path, 'w', encoding='utf-8') as tf:
        tf.write(bulk.get('modified_code', ''))
    with open(temp_path, 'rb') as tf:
        resp2 = requests.post(f'{BASE}/upload', files={'file': (fname, tf, 'text/plain')})
    data2 = resp2.json()
    print(f'Reanalysis of {fname}: violations={len(data2.get("violations", []))}, score={data2.get("compliance_score")}%')
    os.remove(temp_path)
print('\nVerification completed successfully.')
