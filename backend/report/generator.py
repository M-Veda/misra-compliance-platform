import json
import os
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from backend.models.violation import RuleViolation

def clean_code_for_pdf(text: str) -> str:
    """
    Strips non-printable characters, normalizes line endings (\r\n and \r -> \n),
    and converts non-breaking spaces (\xa0) to standard spaces to prevent black box
    characters (■) or glyph rendering artifacts in ReportLab PDF generation.
    """
    if not text:
        return ""
    # Normalize CRLF and CR to LF
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    cleaned = []
    for ch in text:
        if ch in ('\n', '\t'):
            cleaned.append(ch)
        elif 32 <= ord(ch) <= 126:
            cleaned.append(ch)
        elif ord(ch) == 160:  # Non-breaking space
            cleaned.append(' ')
        elif ch.isprintable() and ord(ch) < 256:
            cleaned.append(ch)
    return "".join(cleaned)

class ReportGenerator:
    @staticmethod
    def generate_json_report(
        file_name: str,
        original_code: str,
        corrected_code: str,
        violations: List[RuleViolation],
        decisions: Dict[str, str],
        compliance_score: float
    ) -> Dict[str, Any]:
        """
        Creates a JSON payload representation of the compliance report.

        METRIC CONTRACT (single source of truth):
          - compliance_score is passed in from the frontend's computeMetrics().
            It is NEVER independently recalculated here.
          - decisions dict is the same dict used by computeMetrics() in the frontend.
          - Counts derived here (accepted_cnt etc.) are derived from the same
            decisions dict — they are identically consistent with the frontend.
          - Counter invariant: accepted + rejected + skipped + manual + remaining == total
        """
        file_name = clean_code_for_pdf(file_name)
        original_code = clean_code_for_pdf(original_code)
        corrected_code = clean_code_for_pdf(corrected_code)

        total_violations = len(violations)
        mandatory_cnt = sum(1 for v in violations if v.severity == "Mandatory")
        required_cnt  = sum(1 for v in violations if v.severity == "Required")
        advisory_cnt  = sum(1 for v in violations if v.severity == "Advisory")

        accepted_cnt = sum(1 for d in decisions.values() if d == "Accept")
        rejected_cnt = sum(1 for d in decisions.values() if d == "Reject")
        skipped_cnt  = sum(1 for d in decisions.values() if d == "Skip")
        manual_cnt   = sum(1 for d in decisions.values() if d == "Manual")
        # Remaining = total - all decided (enforces counter invariant)
        remaining_cnt = max(0, total_violations - (accepted_cnt + rejected_cnt + skipped_cnt + manual_cnt))

        report_data = {
            "summary": {
                "file_name": file_name,
                "compliance_score": compliance_score,
                "total_violations_detected": total_violations,
                "severity_counts": {
                    "mandatory": mandatory_cnt,
                    "required": required_cnt,
                    "advisory": advisory_cnt
                },
                "decisions_applied": {
                    "accepted": accepted_cnt,
                    "rejected": rejected_cnt,
                    "skipped": skipped_cnt,
                    "manual_fix": manual_cnt,
                    "remaining": remaining_cnt,
                    # Invariant: accepted+rejected+skipped+manual+remaining == total_violations
                    "_invariant_check": accepted_cnt + rejected_cnt + skipped_cnt + manual_cnt + remaining_cnt
                }
            },
            "violations": [
                {
                    "rule_number": clean_code_for_pdf(v.rule_number),
                    "rule_name": clean_code_for_pdf(v.rule_name),
                    "severity": clean_code_for_pdf(v.severity),
                    "category": clean_code_for_pdf(v.category),
                    "line": v.line,
                    "column": v.column,
                    "message": clean_code_for_pdf(v.message),
                    "reason": clean_code_for_pdf(v.reason),
                    "suggested_fix": clean_code_for_pdf(v.suggested_fix),
                    "user_decision": decisions.get(v.stable_id or f"{v.rule_number}_{v.line}_{v.column}", "None")
                } for v in violations
            ],
            "original_source_code": original_code,
            "corrected_source_code": corrected_code if (accepted_cnt > 0 or manual_cnt > 0) else original_code
        }
        return report_data

    @staticmethod
    def generate_pdf_report(
        file_name: str,
        violations: List[RuleViolation],
        decisions: Dict[str, str],
        compliance_score: float,
        corrected_code: str,
        output_path: str
    ):
        """
        Generates a publication-quality PDF report using ReportLab.
        All input strings are sanitized to eliminate black square glyphs (■).
        """
        file_name = clean_code_for_pdf(file_name)
        corrected_code = clean_code_for_pdf(corrected_code)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        
        # Define Custom Color Palette (Modern Slate/Indigo)
        primary_color = colors.HexColor("#1e293b")   # Slate 800
        secondary_color = colors.HexColor("#4f46e5") # Indigo 600
        accent_color = colors.HexColor("#0f172a")    # Slate 900
        neutral_light = colors.HexColor("#f8fafc")   # Slate 50
        border_color = colors.HexColor("#e2e8f0")    # Slate 200
        success_color = colors.HexColor("#16a34a")   # Green 600
        alert_color = colors.HexColor("#dc2626")     # Red 600

        # Custom Styles
        title_style = ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            leading=28,
            textColor=primary_color,
            spaceAfter=15
        )
        
        subtitle_style = ParagraphStyle(
            name='ReportSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#64748b"), # Slate 500
            spaceAfter=30
        )

        h1_style = ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=16,
            leading=20,
            textColor=secondary_color,
            spaceBefore=18,
            spaceAfter=10,
            keepWithNext=True
        )

        body_style = ParagraphStyle(
            name='ReportBody',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155") # Slate 700
        )

        code_style = ParagraphStyle(
            name='CodeSnippet',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#0f172a"),
            backColor=neutral_light,
            borderColor=border_color,
            borderWidth=1,
            borderPadding=8,
            spaceBefore=6,
            spaceAfter=6
        )

        story = []

        # Cover/Header Section
        story.append(Paragraph("MISRA C:2012 Compliance Report", title_style))
        story.append(Paragraph(f"<b>Target File:</b> {file_name} | <b>Compliance Score:</b> {compliance_score:.1f}%", subtitle_style))
        story.append(Spacer(1, 10))

        # Executive Summary Section
        story.append(Paragraph("Executive Summary", h1_style))
        summary_text = (
            f"The C source file <b>{file_name}</b> has been analyzed against 10 specific rules "
            "of the MISRA C:2012 guidelines. Below is a breakdown of the detected violations "
            "and the human-in-the-loop review actions applied."
        )
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 15))

        # Metrics Table
        # METRIC CONTRACT: accepted/rejected/skipped/manual counts come from
        # the decisions dict passed in from the frontend's computeMetrics().
        # compliance_score is passed in from the frontend — never recalculated here.
        accepted = sum(1 for d in decisions.values() if d == "Accept")
        rejected = sum(1 for d in decisions.values() if d == "Reject")
        skipped  = sum(1 for d in decisions.values() if d == "Skip")
        manual   = sum(1 for d in decisions.values() if d == "Manual")
        remaining = max(0, len(violations) - (accepted + rejected + skipped + manual))
        
        mandatory_cnt = sum(1 for v in violations if v.severity == "Mandatory")
        required_cnt  = sum(1 for v in violations if v.severity == "Required")
        advisory_cnt  = sum(1 for v in violations if v.severity == "Advisory")

        metrics_data = [
            [Paragraph("<b>Metric</b>", body_style), Paragraph("<b>Value</b>", body_style)],
            [Paragraph("Total Violations Detected", body_style), Paragraph(str(len(violations)), body_style)],
            [Paragraph("  - Mandatory Severities", body_style), Paragraph(str(mandatory_cnt), body_style)],
            [Paragraph("  - Required Severities", body_style), Paragraph(str(required_cnt), body_style)],
            [Paragraph("  - Advisory Severities", body_style), Paragraph(str(advisory_cnt), body_style)],
            [Paragraph("Compliance Score", body_style), Paragraph(f"{compliance_score:.1f}%", body_style)],
            [Paragraph("Accepted Patches (Applied)", body_style), Paragraph(str(accepted), body_style)],
            [Paragraph("Rejected Violations (Retained)", body_style), Paragraph(str(rejected), body_style)],
            [Paragraph("Skipped (Pending Action)", body_style), Paragraph(str(skipped), body_style)],
            [Paragraph("Manual Fixes (Edited by User)", body_style), Paragraph(str(manual), body_style)],
            [Paragraph("Remaining (Undecided)", body_style), Paragraph(str(remaining), body_style)],
            [Paragraph("Invariant Check (= Total)", body_style),
             Paragraph(str(accepted + rejected + skipped + manual + remaining), body_style)],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[250, 150])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), neutral_light),
            ('TEXTCOLOR', (0,0), (1,0), primary_color),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 20))

        # Rule Statistics Section
        story.append(Paragraph("Rule Violation Details", h1_style))
        if not violations:
            story.append(Paragraph("No violations detected! The file is fully compliant with the implemented MISRA guidelines.", body_style))
        else:
            for idx, v in enumerate(violations):
                dec_key = f"{v.rule_number}_{v.line}_{v.column}"
                decision = decisions.get(dec_key, "No Decision")
                
                # Assign colored status based on decision
                if decision == "Accept":
                    decision_str = f"<font color='{success_color.hexval()}'><b>Accepted (Patched)</b></font>"
                elif decision == "Reject":
                    decision_str = f"<font color='{alert_color.hexval()}'><b>Rejected</b></font>"
                elif decision == "Manual":
                    decision_str = "<b>Manually Fixed</b>"
                else:
                    decision_str = "<b>No Action/Skipped</b>"

                clean_rule_num = clean_code_for_pdf(str(v.rule_number))
                clean_rule_name = clean_code_for_pdf(str(v.rule_name))
                clean_msg = clean_code_for_pdf(str(v.message))
                clean_reason = clean_code_for_pdf(str(v.reason))

                violation_details = [
                    f"<b>{idx+1}. Rule {clean_rule_num} - {clean_rule_name}</b>",
                    f"<b>Severity:</b> {v.severity} | <b>Category:</b> {v.category} | <b>Position:</b> Line {v.line}, Col {v.column}",
                    f"<b>Status:</b> {decision_str}",
                    f"<b>Description:</b> {clean_msg}",
                    f"<b>Reason:</b> {clean_reason}"
                ]
                
                v_story = []
                for detail in violation_details:
                    v_story.append(Paragraph(detail, body_style))
                    v_story.append(Spacer(1, 3))
                
                # Code snippet
                if v.code_snippet:
                    clean_snippet = clean_code_for_pdf(v.code_snippet)
                    v_story.append(Preformatted(clean_snippet, code_style))
                
                story.append(KeepTogether([
                    Spacer(1, 10),
                    *v_story,
                    Spacer(1, 10),
                    Table([[""]], colWidths=[400], rowHeights=[1], style=TableStyle([('LINEABOVE', (0,0), (-1,-1), 0.5, border_color)]))
                ]))
                
        # Corrected Code Section on a new page
        story.append(PageBreak())
        story.append(Paragraph("Final Corrected Code", h1_style))
        has_patches = (accepted > 0 or manual > 0)
        code_intro = (
            "The resulting source code, incorporating all accepted and manual fixes:"
            if has_patches else
            "No accepted patches were applied. Displaying original uploaded source code:"
        )
        story.append(Paragraph(code_intro, body_style))
        story.append(Spacer(1, 10))
        
        # Display code block using Preformatted (preserves layout, newlines, spaces)
        story.append(Preformatted(corrected_code if corrected_code else "// Source empty", code_style))

        # Build Document
        doc.build(story)

    @staticmethod
    def generate_project_pdf_report(
        folder_name: str,
        files_summary: List[Dict[str, Any]],
        overall_score: float,
        total_files: int,
        total_violations: int,
        output_path: str
    ):
        """
        Generates an overall project PDF compliance report for folder uploads.
        """
        folder_name = clean_code_for_pdf(folder_name)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        primary_color = colors.HexColor("#1e293b")
        secondary_color = colors.HexColor("#4f46e5")
        neutral_light = colors.HexColor("#f8fafc")
        border_color = colors.HexColor("#e2e8f0")

        title_style = ParagraphStyle(
            name='ProjTitle', parent=styles['Heading1'], fontSize=24, leading=28, textColor=primary_color, spaceAfter=15
        )
        subtitle_style = ParagraphStyle(
            name='ProjSubtitle', parent=styles['Normal'], fontSize=11, leading=14, textColor=colors.HexColor("#64748b"), spaceAfter=30
        )
        h1_style = ParagraphStyle(
            name='ProjH1', parent=styles['Heading2'], fontSize=16, leading=20, textColor=secondary_color, spaceBefore=18, spaceAfter=10, keepWithNext=True
        )
        body_style = ParagraphStyle(
            name='ProjBody', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor("#334155")
        )

        story = []
        story.append(Paragraph("MISRA C:2012 Project Compliance Report", title_style))
        story.append(Paragraph(f"<b>Folder:</b> {folder_name} | <b>Total C Files:</b> {total_files} | <b>Overall Score:</b> {overall_score:.1f}%", subtitle_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("Project Summary", h1_style))
        story.append(Paragraph(
            f"Static compliance audit summary for folder <b>{folder_name}</b>. A total of <b>{total_files}</b> C source files were analyzed across 10 MISRA C:2012 rules.",
            body_style
        ))
        story.append(Spacer(1, 15))

        table_data = [
            [Paragraph("<b>File Path</b>", body_style), Paragraph("<b>Violations</b>", body_style), Paragraph("<b>Accepted</b>", body_style), Paragraph("<b>Score</b>", body_style)]
        ]

        for f in files_summary:
            fname = clean_code_for_pdf(f.get("file_name", ""))
            viols = f.get("violations_count", 0)
            acc = f.get("accepted_count", 0)
            score = f.get("compliance_score", 100.0)
            table_data.append([
                Paragraph(fname, body_style),
                Paragraph(str(viols), body_style),
                Paragraph(str(acc), body_style),
                Paragraph(f"{score:.1f}%", body_style)
            ])

        summary_table = Table(table_data, colWidths=[200, 70, 70, 70])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), neutral_light),
            ('TEXTCOLOR', (0,0), (-1,0), primary_color),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ]))
        story.append(summary_table)

        doc.build(story)

