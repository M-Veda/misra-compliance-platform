import json, pathlib

EVIDENCE = pathlib.Path("evidence")
API_DIR = EVIDENCE / "api_responses"

for rule in ["2.2","2.7","7.1","8.4","8.7","10.3","12.1","14.4","16.3","16.4"]:
    fname = API_DIR / ("rule_" + rule.replace(".","_") + "_preview.json")
    if fname.exists():
        data = json.loads(fname.read_text(encoding="utf-8"))
        orig = data.get("original_source", data.get("original_snippet", ""))
        repl = data.get("replacement_source", data.get("proposed_snippet", ""))
        print(f"Rule {rule}:")
        print(f"  original  : {repr(orig[:80])}")
        print(f"  replacement: {repr(repl[:80])}")
        print()
