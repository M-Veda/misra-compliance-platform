import { useState } from 'react';
import { Download, FileJson, FileText, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAppContext } from '../context/AppContext';

const Reports = () => {
  const {
    analysisResult,
    workingCode,
    allViolations,
    decisions,
    isFolderMode,
    folderName,
    fileList,
    getAnalysisMetrics,
  } = useAppContext();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Builds the synchronized report payload for a single file.
   * Guarantee #9: Reports serialize finalized session data — never recompute independently.
   */
  const buildPayload = () => {
    if (!analysisResult) return null;
    const metrics = getAnalysisMetrics();
    const currentWorkingCode = workingCode || analysisResult.source_code;

    return {
      file_name: analysisResult.file_name,
      original_code: analysisResult.source_code,
      corrected_code: currentWorkingCode,
      violations: allViolations.length > 0 ? allViolations : analysisResult.violations,
      decisions: decisions,
      compliance_score: metrics.compliance_score,
      accepted_count: metrics.accepted,
      remaining_count: metrics.remaining,
      total_detected: metrics.total_detected,
    };
  };

  const generateReport = async () => {
    const payload = buildPayload();
    if (!payload) {
      setError('No analysis results available. Upload and analyze a file first.');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/generate-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to generate report.');
      }

      const data = await response.json();
      return data;
    } catch (err: any) {
      setError(err.message || 'An error occurred during report generation.');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = async () => {
    const data = await generateReport();
    if (data?.success) {
      const url = `http://localhost:8000/api/download-pdf/${data.pdf_report_filename}`;
      window.open(url, '_blank');
    }
  };

  const downloadProjectPDF = async () => {
    if (!isFolderMode || fileList.length === 0) return;
    setLoading(true);
    setError(null);

    try {
      const files_summary = fileList.map(f => ({
        file_name: f.file_name,
        violations_count: f.all_violations.length > 0 ? f.all_violations.length : f.violations.length,
        accepted_count: Object.values(f.decisions).filter(d => d === 'Accept').length,
        compliance_score: f.compliance_score,
      }));

      const overall_score = Math.round(
        fileList.reduce((acc, f) => acc + f.compliance_score, 0) / fileList.length
      );

      const total_violations = fileList.reduce(
        (acc, f) => acc + (f.all_violations.length > 0 ? f.all_violations.length : f.violations.length),
        0
      );

      const response = await fetch('http://localhost:8000/api/generate-project-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_name: folderName || 'Project',
          files_summary,
          overall_score,
          total_files: fileList.length,
          total_violations,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate project PDF report.');
      }

      const data = await response.json();
      if (data.success) {
        const url = `http://localhost:8000/api/download-pdf/${data.pdf_report_filename}`;
        window.open(url, '_blank');
      }
    } catch (err: any) {
      setError(err.message || 'Error generating project PDF.');
    } finally {
      setLoading(false);
    }
  };

  const downloadJSON = async () => {
    if (isFolderMode) {
      const projectSummary = {
        folder_name: folderName,
        total_files: fileList.length,
        overall_compliance_score: Math.round(fileList.reduce((acc, f) => acc + f.compliance_score, 0) / fileList.length),
        files: fileList.map(f => ({
          file_name: f.file_name,
          compliance_score: f.compliance_score,
          total_violations: f.all_violations.length,
          remaining_violations: f.violations.length,
          decisions: f.decisions,
        }))
      };
      const jsonStr = JSON.stringify(projectSummary, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `MISRA_Project_Report_${(folderName || 'Project').replace('.', '_')}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      return;
    }

    const data = await generateReport();
    if (data?.success) {
      const jsonStr = JSON.stringify(data.json_report, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `MISRA_Report_${analysisResult?.file_name.replace('.', '_')}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  const handleDefaultGenerate = async () => {
    if (isFolderMode) {
      await downloadProjectPDF();
    } else {
      await downloadPDF();
    }
  };

  // Guarantee #9: Serialize finalized session — never independently recompute
  let accepted = 0, rejected = 0, skipped = 0, manual = 0, totalViol = 0, overallScoreVal = 100;
  if (isFolderMode && fileList.length > 0) {
    for (let i = 0; i < fileList.length; i++) {
      const m = getAnalysisMetrics(i);
      accepted      += m.accepted;
      rejected      += m.rejected;
      skipped       += m.skipped;
      manual        += m.manual;
      totalViol     += m.total_detected;
    }
    overallScoreVal = Math.round(fileList.reduce((acc, f) => acc + f.compliance_score, 0) / fileList.length);
  } else {
    const m = getAnalysisMetrics();
    accepted       = m.accepted;
    rejected       = m.rejected;
    skipped        = m.skipped;
    manual         = m.manual;
    totalViol      = m.total_detected;
    overallScoreVal = m.compliance_score;
  }

  return (
    <div className="h-full flex flex-col gap-6 p-2">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white mb-1">Compliance Reports</h2>
          <p className="text-slate-400">Generate and download official MISRA C verification artifacts.</p>
        </div>
        {analysisResult && (
          <button
            onClick={handleDefaultGenerate}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 bg-violet-600 hover:bg-violet-500 text-white font-semibold rounded-xl text-sm transition-colors shadow-lg shadow-violet-500/20 disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Generate Report ({isFolderMode ? 'PROJECT PDF' : 'PDF'})
          </button>
        )}
      </div>

      {error && (
        <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-400 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Report Summary Card */}
      {analysisResult ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          {/* Card 1: Single File Report */}
          <div className="glass-panel p-6 flex flex-col justify-between gap-6">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center text-violet-400">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-lg">Single File Executive PDF</h3>
                  <p className="text-xs text-slate-400 font-mono">{analysisResult.file_name}</p>
                </div>
              </div>
              <p className="text-sm text-slate-300 mb-4">
                Official PDF compliance report containing violation audit trails, patch diffs, compliance metrics, and score validation.
              </p>
              <div className="bg-slate-800/50 p-4 rounded-xl space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-400">Target File:</span>
                  <span className="text-white font-bold">{analysisResult.file_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Compliance Score:</span>
                  <span className="text-emerald-400 font-bold">{overallScoreVal}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Baseline Violations:</span>
                  <span className="text-white font-bold">{totalViol}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Accepted Fixes:</span>
                  <span className="text-emerald-400 font-bold">{accepted}</span>
                </div>
              </div>
            </div>

            <button
              onClick={downloadPDF}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 bg-violet-600 hover:bg-violet-500 text-white font-semibold rounded-xl text-sm transition-colors shadow-lg shadow-violet-500/20 disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              Download Single File PDF
            </button>
          </div>

          {/* Card 2: JSON Artifact */}
          <div className="glass-panel p-6 flex flex-col justify-between gap-6">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-sky-500/20 flex items-center justify-center text-sky-400">
                  <FileJson className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-lg">Machine-Readable JSON</h3>
                  <p className="text-xs text-slate-400 font-mono">Structure Data Payload</p>
                </div>
              </div>
              <p className="text-sm text-slate-300 mb-4">
                JSON compliance payload suitable for CI/CD pipelines, automated security scanning, and external auditing systems.
              </p>
              <div className="bg-slate-800/50 p-4 rounded-xl space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-400">Format:</span>
                  <span className="text-sky-400 font-bold">JSON 2.0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Scope:</span>
                  <span className="text-white font-bold">{isFolderMode ? 'Multi-File Folder' : 'Single Source File'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Status:</span>
                  <span className="text-emerald-400 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Validated
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={downloadJSON}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-xl text-sm transition-colors disabled:opacity-50"
            >
              <FileJson className="w-4 h-4 text-sky-400" />
              Download JSON Report
            </button>
          </div>
        </motion.div>
      ) : (
        <div className="h-full flex items-center justify-center text-slate-500 flex-col gap-4">
          <FileText className="w-12 h-12 text-slate-700" />
          <p>No analysis result found. Please upload a C file or folder first.</p>
        </div>
      )}
    </div>
  );
};

export default Reports;
