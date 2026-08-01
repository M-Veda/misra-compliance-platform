import sys
import os
# Add parent directory of 'backend' to path to ensure backend modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json

from backend.models.violation import (
    RuleViolation, AnalysisResult,
    PatchRequest, PatchResponse,
    BulkPatchRequest, BulkPatchResponse,
    ReportRequest,
)
from backend.services.parser import CParserService
from backend.rules import ALL_RULES
from backend.services.llm import LLMService
from backend.services.patch import PatchService
from backend.services import patch_engine
from backend.report.generator import ReportGenerator

app = FastAPI(
    title="AI-Powered MISRA C:2012 Compliance Agent API",
    description="Backend API for static C analysis and human-in-the-loop compliance reviews."
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExplainRequest(BaseModel):
    violation: RuleViolation
    source_code: str

class ChatRequest(BaseModel):
    question: str
    source_code: str
    violations: List[RuleViolation]

# Directory structure to save generated reports and artifacts inside project
BASE_BACKEND_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR        = os.path.join(BASE_BACKEND_DIR, "generated_reports")
GENERATED_CODE_DIR = os.path.join(BASE_BACKEND_DIR, "generated_code")
GENERATED_JSON_DIR = os.path.join(BASE_BACKEND_DIR, "generated_json")
GENERATED_PDFS_DIR = os.path.join(BASE_BACKEND_DIR, "generated_pdfs")
GENERATED_ZIPS_DIR = os.path.join(BASE_BACKEND_DIR, "generated_zips")

for d in [REPORTS_DIR, GENERATED_CODE_DIR, GENERATED_JSON_DIR, GENERATED_PDFS_DIR, GENERATED_ZIPS_DIR]:
    os.makedirs(d, exist_ok=True)

@app.get("/api/rules")
def get_rules():
    """
    Returns metadata about the 10 supported MISRA C:2012 rules.
    """
    rules_data = []
    for r in ALL_RULES:
        rules_data.append({
            "rule_number": r.rule_number,
            "rule_name": r.rule_name,
            "severity": r.severity,
            "category": r.category,
            "description": r.description
        })
    return {
        "supported_rules_count": len(rules_data),
        "rules": rules_data
    }

@app.post("/api/upload")
async def upload_c_file(file: UploadFile = File(...)):
    """
    Uploads a C source file, parses its AST, runs the rule engine,
    and returns detected violations and the initial compliance score.
    """
    if not file.filename.endswith('.c'):
        raise HTTPException(status_code=400, detail="Only .c source files are supported.")
        
    try:
        content = await file.read()
        # Try UTF-8 first, then UTF-16 (Windows BOM), then latin-1 fallback
        if content.startswith(b'\xff\xfe') or content.startswith(b'\xfe\xff'):
            source_code = content.decode('utf-16')
        else:
            try:
                source_code = content.decode('utf-8')
            except UnicodeDecodeError:
                source_code = content.decode('latin-1')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # 1. Parse using Parser Service
    ast, err = CParserService.parse_code(source_code, file.filename)
    if err:
        return {
            "success": False,
            "error": err,
            "file_name": file.filename,
            "source_code": source_code,
            "violations": [],
            "compliance_score": 0.0
        }

    # 2. Analyze using deterministic rule engine
    violations = []
    for rule in ALL_RULES:
        try:
            v_list = rule.analyze(ast, source_code, file.filename)
            for v in v_list:
                v.patch_preview = patch_engine.generate_patch_preview(source_code, v)
            violations.extend(v_list)
        except Exception as e:
            # Continue if one rule analyzer encounters an error
            pass

    # 3. Calculate Compliance Score
    violated_rules = set(v.rule_number for v in violations)
    compliance_score = max(0.0, 100.0 - (len(violated_rules) * 10.0))

    return {
        "success": True,
        "file_name": file.filename,
        "source_code": source_code,
        "violations": violations,
        "compliance_score": compliance_score
    }

@app.post("/api/explain")
def explain_violation(request: ExplainRequest):
    """
    Calls AI engine to explain why a violation exists and how the proposed fix resolves it.
    Returns structured JSON with rule-specific engineering analysis.
    """
    structured_data = LLMService.get_structured_explanation(request.violation, request.source_code)
    return {
        "explanation": json.dumps(structured_data, indent=2),
        "structured": structured_data
    }

@app.post("/api/preview-patch")
def preview_patch(request: PatchRequest):
    """
    Applies the patch (Accept/Reject/Skip/Manual) and returns the preview of the
    modified code without saving to disk.

    The response always includes a complete PatchPreview object.
    """
    preview = patch_engine.generate_patch_preview(request.source_code, request.violation)

    if request.decision in ("Reject", "Skip"):
        return PatchResponse(
            success=True,
            modified_code=request.source_code,
            can_autopatch=False,
            patch_actually_changed=False,
            no_patch_reason="Decision is Reject/Skip — source unchanged.",
            patch_preview=preview,
        )

    if request.decision == "Manual":
        manual = request.manual_code or request.source_code
        changed = manual != request.source_code
        return PatchResponse(
            success=True,
            modified_code=manual,
            can_autopatch=False,
            patch_actually_changed=changed,
            no_patch_reason="" if changed else "Manual code provided is identical to current source.",
            patch_preview=preview,
        )

    # decision == 'Accept'
    try:
        result = patch_engine.apply_single(request.source_code, request.violation)
        changed = result.patched_source != request.source_code
        return PatchResponse(
            success=result.success,
            modified_code=result.patched_source,
            can_autopatch=True,
            patch_actually_changed=changed,
            no_patch_reason="" if result.success else (result.error or ""),
            error=result.error if not result.success else None,
            patch_preview=preview,
        )
    except Exception as e:
        return PatchResponse(
            success=False,
            modified_code=request.source_code,
            can_autopatch=True,
            patch_actually_changed=False,
            no_patch_reason=str(e),
            error=str(e),
            patch_preview=preview,
        )

@app.post("/api/apply-patches", response_model=BulkPatchResponse)
def apply_patches(request: BulkPatchRequest):
    """
    Applies all approved violations as a single, safe, bottom-up pass.

    Steps executed by the patch engine:
      1. Build offset-based PatchOps for every auto-patchable violation.
      2. Validate each op against the original source text.
      3. Deduplicate by content-hash.
      4. Resolve overlapping ops (keep higher severity).
      5. Apply all remaining ops in descending offset order (bottom-up).
      6. Re-parse the result with pycparser; reject if invalid.

    All 10 implemented rules (2.2, 2.7, 7.1, 8.4, 8.7, 10.3, 12.1, 14.4, 16.3, 16.4) are auto-patchable.
    """
    result = patch_engine.apply_bulk(
        source=request.source_code,
        violations=request.violations,
    )
    return BulkPatchResponse(
        success=result.success,
        modified_code=result.patched_source,
        ops_applied=result.ops_applied,
        ops_skipped_already_applied=result.ops_skipped_already_applied,
        ops_rejected_validation=result.ops_rejected_validation,
        ops_rejected_overlap=result.ops_rejected_overlap,
        parse_valid=result.parse_valid,
        conflicts=result.conflicts,
        error=result.error,
    )

@app.post("/api/chat")
def chat_with_agent(request: ChatRequest):
    """
    Chats interactively with TinyLlama about the source code and detected violations.
    """
    summary = "\n".join([
        f"- Rule {v.rule_number} ({v.rule_name}) at line {v.line}: {v.message}" 
        for v in request.violations
    ])
    answer = LLMService.answer_question(request.question, request.source_code, summary)
    return {"answer": answer}

@app.post("/api/generate-report")
def generate_report(request: ReportRequest):
    """
    Generates PDF & JSON compliance reports and saves artifacts inside project directories.
    """
    clean_base = request.file_name.replace('.', '_')
    pdf_filename = f"MISRA_Report_{clean_base}.pdf"
    json_filename = f"MISRA_Report_{clean_base}.json"
    code_filename = f"{clean_base}_fixed.c"
    
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
    pdf_project_path = os.path.join(GENERATED_PDFS_DIR, pdf_filename)
    json_project_path = os.path.join(GENERATED_JSON_DIR, json_filename)
    code_project_path = os.path.join(GENERATED_CODE_DIR, code_filename)
    
    try:
        # Generate JSON summary
        json_report = ReportGenerator.generate_json_report(
            file_name=request.file_name,
            original_code=request.original_code,
            corrected_code=request.corrected_code,
            violations=request.violations,
            decisions=request.decisions,
            compliance_score=request.compliance_score
        )
        
        # Save JSON inside project directory
        with open(json_project_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2)

        # Save corrected code inside project directory
        with open(code_project_path, 'w', encoding='utf-8') as f:
            f.write(request.corrected_code)
        
        # Generate PDF report (save to both generated_reports/ and generated_pdfs/)
        ReportGenerator.generate_pdf_report(
            file_name=request.file_name,
            violations=request.violations,
            decisions=request.decisions,
            compliance_score=request.compliance_score,
            corrected_code=request.corrected_code,
            output_path=pdf_path
        )

        ReportGenerator.generate_pdf_report(
            file_name=request.file_name,
            violations=request.violations,
            decisions=request.decisions,
            compliance_score=request.compliance_score,
            corrected_code=request.corrected_code,
            output_path=pdf_project_path
        )
        
        return {
            "success": True,
            "json_report": json_report,
            "pdf_report_filename": pdf_filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate reports: {str(e)}")

@app.get("/api/download-pdf/{filename}")
def download_pdf(filename: str):
    """
    Downloads the generated PDF compliance report.
    """
    file_path = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(file_path):
        file_path = os.path.join(GENERATED_PDFS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF report not found.")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)

class FixedFilePayload(BaseModel):
    file_name: str
    corrected_code: str

class DownloadZipRequest(BaseModel):
    folder_name: str
    files: List[FixedFilePayload]

@app.post("/api/download-zip")
def download_zip(request: DownloadZipRequest):
    """
    Packages all corrected C files into a downloadable ZIP archive inside project directories.
    """
    import zipfile
    clean_folder = request.folder_name.replace(" ", "_")
    zip_filename = f"{clean_folder}_fixed.zip"
    zip_path = os.path.join(REPORTS_DIR, zip_filename)
    zip_project_path = os.path.join(GENERATED_ZIPS_DIR, zip_filename)
    
    for zpath in [zip_path, zip_project_path]:
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for f in request.files:
                fname = f.file_name.replace('\\', '/')
                if fname.endswith('.c'):
                    fixed_name = fname[:-2] + "_fixed.c"
                else:
                    fixed_name = fname + "_fixed.c"
                zipf.writestr(fixed_name, f.corrected_code)
                # Also save individual corrected file into generated_code
                code_path = os.path.join(GENERATED_CODE_DIR, os.path.basename(fixed_name))
                with open(code_path, 'w', encoding='utf-8') as cf:
                    cf.write(f.corrected_code)
            
    return FileResponse(zip_path, media_type="application/zip", filename=zip_filename)

class ProjectReportRequest(BaseModel):
    folder_name: str
    files_summary: List[Dict[str, Any]]
    overall_score: float
    total_files: int
    total_violations: int

@app.post("/api/generate-project-report")
def generate_project_report(request: ProjectReportRequest):
    """
    Generates an overall project PDF compliance report.
    """
    clean_folder = request.folder_name.replace('.', '_').replace(' ', '_')
    pdf_filename = f"MISRA_Project_Report_{clean_folder}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
    pdf_project_path = os.path.join(GENERATED_PDFS_DIR, pdf_filename)
    try:
        ReportGenerator.generate_project_pdf_report(
            folder_name=request.folder_name,
            files_summary=request.files_summary,
            overall_score=request.overall_score,
            total_files=request.total_files,
            total_violations=request.total_violations,
            output_path=pdf_path
        )
        ReportGenerator.generate_project_pdf_report(
            folder_name=request.folder_name,
            files_summary=request.files_summary,
            overall_score=request.overall_score,
            total_files=request.total_files,
            total_violations=request.total_violations,
            output_path=pdf_project_path
        )
        return {
            "success": True,
            "pdf_report_filename": pdf_filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate project report: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

