#!/usr/bin/env python3
"""
Generates example JSON and PDF compliance reports using a synthetic
MISRA C:2012 violation to demonstrate the report format.
Run from the project root: python generate_example_reports.py
"""
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.report.generator import ReportGenerator
from backend.models.violation import RuleViolation

EXAMPLE_SOURCE = """\
void sensor_init(int pin, float threshold) {
    float f = 1.0;
    double non_comp = 2.0;
    float f2 = non_comp;

    int raw;
    if (pin > 0) {
        raw = pin * 10;
    }
    int scaled = raw + 5;

    int x = 5;
    char c = x;

    int mode;
    int y = mode + 1;
    return;
    scaled = 99;
}
"""

EXAMPLE_VIOLATIONS = [
    RuleViolation(
        rule_number="8.4", rule_name="Function prototype required",
        severity="Required", category="Declarations",
        file="sensor.c", line=1, column=0,
        message="Function 'sensor_init' defined without a visible prototype.",
        code_snippet="void sensor_init(int pin, float threshold) {",
        reason="External functions must have a compatible declaration visible at the point of definition.",
        suggested_fix="void sensor_init(int pin, float threshold);\nvoid sensor_init(int pin, float threshold) {",
        confidence=1.0
    ),
    RuleViolation(
        rule_number="10.3", rule_name="Implicit narrowing conversion",
        severity="Required", category="Expressions",
        file="sensor.c", line=4, column=0,
        message="Implicit conversion from 'Floating(64bit)' to narrower/different 'Floating(32bit)'.",
        code_snippet="    float f2 = non_comp;",
        reason="Assigning a double to a float loses precision (implicit narrowing).",
        suggested_fix="    float f2 = (float)non_comp;",
        confidence=1.0
    ),
    RuleViolation(
        rule_number="7.1", rule_name="Octal constants shall not be used",
        severity="Required", category="Literals",
        file="sensor.c", line=10, column=0,
        message="Octal constant '077' used in expression.",
        code_snippet="    int mask = 077;",
        reason="Octal constants and escape sequences can be easily mistaken for decimal constants.",
        suggested_fix="    int mask = 63;",
        confidence=1.0
    ),
    RuleViolation(
        rule_number="10.3", rule_name="Implicit narrowing conversion",
        severity="Required", category="Expressions",
        file="sensor.c", line=13, column=0,
        message="Implicit conversion from 'Signed(32bit)' to narrower/different 'Character(8bit)'.",
        code_snippet="    char c = x;",
        reason="int (32-bit) assigned to char (8-bit) may truncate value.",
        suggested_fix="    char c = (char)x;",
        confidence=1.0
    ),
    RuleViolation(
        rule_number="2.2", rule_name="No dead code",
        severity="Required", category="System",
        file="sensor.c", line=17, column=0,
        message="Unreachable code after return statement.",
        code_snippet="    scaled = 99;",
        reason="Statement follows a return and will never be executed.",
        suggested_fix="",
        confidence=1.0
    ),
]

PATCHED_SOURCE = """\
void sensor_init(int pin, float threshold);
void sensor_init(int pin, float threshold) {
    float f = 1.0;
    double non_comp = 2.0;
    float f2 = (float)non_comp;

    int raw = 0;
    if (pin > 0) {
        raw = pin * 10;
    }
    int scaled = raw + 5;

    int x = 5;
    char c = (char)x;

    int mode;
    int y = mode + 1;
    return;

}
"""

os.makedirs("backend/generated_reports", exist_ok=True)

json_report = ReportGenerator.generate_json_report(
    file_name="sensor.c",
    original_code=EXAMPLE_SOURCE,
    corrected_code=PATCHED_SOURCE,
    violations=EXAMPLE_VIOLATIONS,
    decisions={
        "8.4_1_0": "Accept",
        "10.3_4_0": "Accept",
        "9.1_10_0": "Accept",
        "10.3_13_0": "Accept",
        "2.2_17_0": "Reject",
    },
    compliance_score=50.0
)

json_path = "backend/generated_reports/example_report.json"
with open(json_path, "w") as f:
    json.dump(json_report, f, indent=2)
print(f"JSON report written to: {json_path}")

pdf_path = "backend/generated_reports/example_report.pdf"
ReportGenerator.generate_pdf_report(
    file_name="sensor.c",
    violations=EXAMPLE_VIOLATIONS,
    decisions={
        "8.4_1_0": "Accept",
        "10.3_4_0": "Accept",
        "9.1_10_0": "Accept",
        "10.3_13_0": "Accept",
        "2.2_17_0": "Reject",
    },
    compliance_score=50.0,
    corrected_code=PATCHED_SOURCE,
    output_path=pdf_path
)
print(f"PDF report written to: {pdf_path}")
print("Done.")
