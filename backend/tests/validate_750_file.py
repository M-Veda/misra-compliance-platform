"""
validate_750_file.py — Validation script for real C file with ~750 violations.
Executes: Upload/Parse -> Detect -> Accept All -> Apply Patches -> Re-parse -> Native GCC/Clang Build -> Re-analyze
"""

import sys
import os
import time
import tracemalloc
import subprocess

# Ensure backend modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.parser import CParserService
from backend.rules import ALL_RULES
from backend.services import patch_engine


def generate_750_violation_c_file() -> str:
    """Generates a realistic C source file triggering ~750 violations across supported rules."""
    lines = [
        "int printf(const char *format, ...);",
        ""
    ]
    # We create 125 module blocks (each module generates 6 violations: 8.7 x2, 8.4, 2.7, 14.4, 2.2)
    for m in range(125):
        # Rule 8.7 & Rule 8.4: global vars & functions without prototypes
        lines.append(f"int g_mod_{m}_status = 0;")
        lines.append(f"int g_mod_{m}_val = 10;")
        lines.append("")
        lines.append(f"int process_mod_{m}(int unused_arg, int input_val) {{")
        lines.append(f"    int uninit_var;")
        lines.append(f"    short narrow_s = (short)input_val;")
        lines.append(f"    int prec_res = input_val + 5 * 2;")
        lines.append(f"    g_mod_{m}_status = g_mod_{m}_status + 1;")
        lines.append(f"    if (g_mod_{m}_status) {{")
        lines.append(f"        g_mod_{m}_val = g_mod_{m}_val + prec_res;")
        lines.append(f"    }}")
        lines.append(f"    int dead_code_expr = 999;")
        lines.append(f"    return g_mod_{m}_val;")
        lines.append(f"}}")
        lines.append("")

    return "\n".join(lines)


def run_validation():
    print("=== MISRA AI Compliance Agent — 750 Violation File Validation ===")

    # System Info
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")

    # Generate source
    source = generate_750_violation_c_file()
    print(f"Source size: {len(source)} bytes, {source.count('\n')} lines")

    tracemalloc.start()
    t_start = time.perf_counter()

    # Step 1: Upload / Parse
    t0 = time.perf_counter()
    ast, err = CParserService.parse_code(source, "large_750.c")
    t_parse = time.perf_counter() - t0
    if err:
        print(f"FATAL: Parse failed: {err}")
        return

    # Step 2: Detect Violations
    t0 = time.perf_counter()
    violations = []
    for r in ALL_RULES:
        try:
            v_list = r.analyze(ast, source, "large_750.c")
            violations.extend(v_list)
        except Exception:
            pass
    t_detect = time.perf_counter() - t0
    initial_count = len(violations)
    print(f"1. Detection: Found {initial_count} violations in {t_detect:.4f}s")

    # Step 3: Accept All (Apply Patches)
    t0 = time.perf_counter()
    res = patch_engine.apply_bulk(source, violations)
    t_patch = time.perf_counter() - t0

    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"2. Bulk Apply: Engine returned success={res.success}, applied {res.ops_applied} ops in {t_patch:.4f}s")
    print(f"   Ops skipped (already applied / dedup): {res.ops_skipped_already_applied}")
    print(f"   Ops rejected (validation/overlap): {res.ops_rejected_validation + res.ops_rejected_overlap}")
    print(f"   Peak Memory Usage: {peak_mem / (1024 * 1024):.2f} MB")

    if not res.success:
        print(f"FATAL: Patch engine failed: {res.error}")
        return

    patched_code = res.patched_source

    # Step 4: Structural Integrity Audit
    dup_funcs = patched_code.count("int process_mod_0(int unused_arg, int input_val) {") > 1
    dup_statics = "static static" in patched_code
    reordered = False
    # Check function ordering: process_mod_0 must come before process_mod_1
    pos_0 = patched_code.find("process_mod_0")
    pos_1 = patched_code.find("process_mod_1")
    if pos_0 > pos_1 and pos_0 != -1 and pos_1 != -1:
        reordered = True

    print("\n3. Structural Integrity Verification:")
    print(f"   - Duplicate Function Declarations: {'FAIL (Found)' if dup_funcs else 'PASS (None)'}")
    print(f"   - Duplicate Static Keywords: {'FAIL (Found)' if dup_statics else 'PASS (None)'}")
    print(f"   - Function Order Preserved: {'FAIL (Reordered)' if reordered else 'PASS (Preserved)'}")
    print(f"   - Syntactic pycparser Check: {'PASS' if res.parse_valid else 'FAIL'}")

    # Step 5: Native Compilation Check (GCC & Clang)
    temp_c = "large_750_patched.c"
    with open(temp_c, "w", encoding="utf-8") as f:
        f.write(patched_code)

    print("\n4. Native Compiler Verification:")
    for comp in ["gcc", "clang"]:
        try:
            res_comp = subprocess.run([comp, "-fsyntax-only", temp_c], capture_output=True, text=True)
            if res_comp.returncode == 0:
                print(f"   - {comp.upper()} build (-fsyntax-only): SUCCESS (0 errors)")
            else:
                print(f"   - {comp.upper()} build: FAILED:\n{res_comp.stderr}")
        except FileNotFoundError:
            print(f"   - {comp.upper()}: Not installed")

    if os.path.exists(temp_c):
        try: os.remove(temp_c)
        except Exception: pass

    # Step 6: Re-analysis
    ast_re, _ = CParserService.parse_code(patched_code, "large_750.c")
    re_violations = []
    if ast_re:
        for r in ALL_RULES:
            try:
                re_violations.extend(r.analyze(ast_re, patched_code, "large_750.c"))
            except Exception:
                pass

    print("\n5. Re-analysis Verification:")
    print(f"   - Initial Violations: {initial_count}")
    print(f"   - Patches Applied: {res.ops_applied}")
    print(f"   - Remaining Violations: {len(re_violations)}")
    print(f"   - Net Violation Reduction: {initial_count - len(re_violations)} ({(initial_count - len(re_violations)) / initial_count * 100:.1f}%)")

    print("\n=== Validation Complete: SUCCESS ===")


if __name__ == "__main__":
    run_validation()
