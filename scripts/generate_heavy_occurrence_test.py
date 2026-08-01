import sys, os, pathlib
sys.path.insert(0, os.getcwd())

# Generate C file with 10+ valid occurrences for EVERY ONE of the 10 MISRA rules
lines = [
    "/* heavy_multi_occurrence_test.c — 10+ occurrences for all 10 MISRA C:2012 rules */",
    "#include <stdio.h>",
    ""
]

# 1. Rule 8.7 (Internal linkage) — 10 global variables used in only 1 function
for i in range(1, 11):
    lines.append(f"int g_single_var_{i} = {i}0;  /* Rule 8.7 occurrence {i} */")
lines.append("")

# 2. Rule 8.4 (Missing prototype) — 10 external functions without visible prototypes
for i in range(1, 11):
    lines.append(f"int ext_func_{i}(int val) {{ return val + g_single_var_{i}; }}  /* Rule 8.4 occurrence {i} */")
lines.append("")

# 3. Rule 2.7 (Unused parameter) — 10 functions with unused parameters
for i in range(1, 11):
    lines.append(f"int func_unused_param_{i}(int active, int unused_arg_{i}) {{  /* Rule 2.7 occurrence {i} */")
    lines.append(f"    return active + {i};")
    lines.append("}")
    lines.append("")

# 4. Rule 2.2 (Dead code) — 10 functions with unreachable code
for i in range(1, 11):
    lines.append(f"int func_dead_code_{i}(int x) {{")
    lines.append(f"    if (x > {i}) {{")
    lines.append("        return 1;")
    lines.append(f"        return {i+1};  /* Rule 2.2 occurrence {i} */")
    lines.append("    }")
    lines.append("    return 0;")
    lines.append("}")
    lines.append("")

# 5. Rule 7.1 (Octal constants) — 10 valid octal literal statements (using octal digits 0-7 only)
octal_literals = ["017", "027", "037", "047", "057", "067", "077", "0117", "0127", "0137"]
lines.append("int func_octal_constants(void) {")
lines.append("    int total = 0;")
for i, oct_val in enumerate(octal_literals, 1):
    lines.append(f"    total += {oct_val};  /* Rule 7.1 occurrence {i} */")
lines.append("    return total;")
lines.append("}")
lines.append("")

# 6. Rule 10.3 (Implicit narrowing) — 10 implicit narrowing assignments
lines.append("int func_implicit_narrowing(void) {")
lines.append("    unsigned int u = 50u;")
lines.append("    int sum = 0;")
for i in range(1, 11):
    lines.append(f"    int s_{i} = u + {i};  /* Rule 10.3 occurrence {i} */")
    lines.append(f"    sum += s_{i};")
lines.append("    return sum;")
lines.append("}")
lines.append("")

# 7. Rule 12.1 (Operator precedence) — 10 precedence statements
lines.append("int func_operator_precedence(int x, int y, int z) {")
lines.append("    int res = 0;")
for i in range(1, 11):
    lines.append(f"    res += x + y * z + {i};  /* Rule 12.1 occurrence {i} */")
lines.append("    return res;")
lines.append("}")
lines.append("")

# 8. Rule 14.4 (Non-boolean controlling expression) — 10 condition statements
lines.append("int func_non_bool_conditions(int c) {")
lines.append("    int acc = 0;")
for i in range(1, 11):
    lines.append(f"    if (c + {i}) {{ acc += {i}; }}  /* Rule 14.4 occurrence {i} */")
lines.append("    return acc;")
lines.append("}")
lines.append("")

# 9. Rule 16.3 (Switch missing break) & 10. Rule 16.4 (Switch missing default)
lines.append("int func_switch_rules(int mode) {")
lines.append("    int res = 0;")
for i in range(1, 11):
    lines.append(f"    switch (mode + {i}) {{  /* Rule 16.4 occurrence {i} */")
    lines.append(f"        case 1:")
    lines.append(f"            res += {i};  /* Rule 16.3 occurrence {i} */")
    lines.append(f"        case 2:")
    lines.append(f"            res += {i} * 2;")
    lines.append("            break;")
    lines.append("    }")
lines.append("    return res;")
lines.append("}")
lines.append("")

# Write to file
dest = pathlib.Path("perf_test/heavy_multi_occurrence_test.c")
dest.write_text("\n".join(lines), encoding="utf-8")
print(f"Generated {dest} with {len(lines)} lines.")
