import pathlib, py_compile, sys
errors = []
for py in pathlib.Path('.').rglob('*.py'):
    try:
        py_compile.compile(str(py), doraise=True)
    except Exception as e:
        errors.append((py, e))
if errors:
    for f, e in errors:
        print('FAIL', f, e)
    sys.exit(1)
else:
    print('ALL COMPILED')
