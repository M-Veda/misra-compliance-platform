import time
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.parser import CParserService
from backend.rules import ALL_RULES
from backend.services.patch import PatchService
from backend.report.generator import ReportGenerator

def generate_c_code(lines_count: int) -> str:
    lines = [
        "#include <stdio.h>",
        "int global_counter = 0;",
        "void helper_proto(int x);"
    ]
    
    funcs_needed = max(1, (lines_count - len(lines)) // 15)
    for f in range(funcs_needed):
        lines.extend([
            f"void fn_{f}(int unused_param) {{",
            "    int a = 10;",
            "    int b = 20;",
            "    double d = 3.14;",
            "    float fl = d;", # Rule 10.3
            "    int uninit;",
            "    int res = uninit + a + b;", # Rule 9.1
            "    if (a) {", # Rule 14.4
            "        a = 0;",
            "    }",
            "    global_counter++;",
            "    return;",
            "    a = 99;", # Rule 2.2
            "}"
        ])
    
    lines.append("int main(void) { fn_0(5); return 0; }")
    return "\n".join(lines)

def benchmark():
    sizes = [50, 300, 1000]
    results = []
    
    for target_lines in sizes:
        code = generate_c_code(target_lines)
        actual_lines = len(code.splitlines())
        filename = f"bench_{actual_lines}.c"
        
        # 1. Parser Time
        t0 = time.perf_counter()
        ast, err = CParserService.parse_code(code, filename)
        t_parse = time.perf_counter() - t0
        
        if err:
            print(f"Parser error on size {actual_lines}: {err}")
            continue
            
        # 2. Rule Engine Time
        t0 = time.perf_counter()
        violations = []
        for r in ALL_RULES:
            v_list = r.analyze(ast, code, filename)
            violations.extend(v_list)
        t_rule = time.perf_counter() - t0
        
        # 3. Patch Generation Time
        t0 = time.perf_counter()
        if violations:
            _ = PatchService.generate_preview(code, violations[0], "Accept")
        t_patch = time.perf_counter() - t0
        
        # 4. Report Generation Time
        t0 = time.perf_counter()
        pdf_path = f"backend/generated_reports/bench_{actual_lines}.pdf"
        ReportGenerator.generate_pdf_report(
            file_name=filename,
            violations=violations,
            decisions={},
            compliance_score=85.0,
            corrected_code=code,
            output_path=pdf_path
        )
        t_report = time.perf_counter() - t0
        
        total_time = t_parse + t_rule + t_patch + t_report
        
        results.append({
            "target_lines": target_lines,
            "actual_lines": actual_lines,
            "violations_count": len(violations),
            "parse_sec": round(t_parse, 4),
            "rule_sec": round(t_rule, 4),
            "patch_sec": round(t_patch, 4),
            "report_sec": round(t_report, 4),
            "total_sec": round(total_time, 4)
        })

    print("\n" + "="*80)
    print(f"{'Lines':<10} | {'Violations':<12} | {'Parse (s)':<10} | {'Rule Engine (s)':<16} | {'Patch (s)':<10} | {'Report (s)':<10} | {'Total (s)':<10}")
    print("="*80)
    for r in results:
        print(f"{r['actual_lines']:<10} | {r['violations_count']:<12} | {r['parse_sec']:<10} | {r['rule_sec']:<16} | {r['patch_sec']:<10} | {r['report_sec']:<10} | {r['total_sec']:<10}")
    print("="*80)

if __name__ == "__main__":
    benchmark()
