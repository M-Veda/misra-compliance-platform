import pathlib, json, hashlib, os, time

base = pathlib.Path(r'C:/Users/saite/OneDrive/Desktop/MISRA_Project/evidence')
records = []
for p in base.rglob('*'):
    if p.is_file():
        h = hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        stat = p.stat()
        records.append({
            'path': str(p),
            'sha256': h.hexdigest(),
            'size': stat.st_size,
            'ctime': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(stat.st_ctime)),
            'mtime': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(stat.st_mtime)),
            'purpose': 'evidence artifact'
        })

output_path = pathlib.Path(r'C:/Users/saite/OneDrive/Desktop/MISRA_Project/evidence_hashes.json')
output_path.write_text(json.dumps(records, indent=2), encoding='utf-8')
print(f'Wrote {len(records)} records to {output_path}')
