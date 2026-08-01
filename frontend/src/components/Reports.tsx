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
    settings,
  } = useAppContext();


  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastReport, setLastReport] = useState<{ pdfFilename: string; jsonData: object } | null>(null);

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
      if (data.success) {
        setLastReport({ pdfFilename: data.pdf_report_filename, jsonData: data.json_report });
      }
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
        setLastReport({ pdfFilename: data.pdf_report_filename, jsonData: { folderName, files_summary } });
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
      return;
    }
    if (settings.defaultReportFormat === 'pdf') {
      await downloadPDF();
    } else if (settings.defaultReportFormat === 'json') {
      await downloadJSON();
    } else {
      await downloadPDF();
      await downloadJSON();
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
            Generate Report ({isFolderMode ? 'PROJECT PDF' : settings.defaultReportFormat.toUpperCase()})
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
      {analysisResult && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-5 grid grid-cols-2 md:grid-cols-4 gap-4 text-center"
        >
          <div>
            <p className="text-slate-400 text-xs mb-1">Total Files Analyzed</p>
            <p className="text-2xl font-bold text-sky-400">{isFolderMode ? fileList.length : 1}</p>
          </div>
          <div>
            <p className="text-slate-400 text-xs mb-1">Total Violations</p>
            <p className="text-2xl font-bold text-white">{totalViol}</p>
          </div>
          <div>
            <p className="text-slate-400 text-xs mb-1">Overall Compliance Score</p>
            <p className="text-2xl font-bold text-emerald-400">{overallScoreVal.toFixed(1)}%</p>
          </div>
          <div>
            <p className="text-slate-400 text-xs mb-1">Accepted Patches</p>
            <p className="text-2xl font-bold text-emerald-400">{accepted}</p>
          </div>
          <div>
            <p className="text-slate-400 text-xs mb-1">Rejected</p>
            <p className="text-xl font-bold text-red-400">{rejected}</p>
          </div>
          <div>
            <p className="text-slate-400 text-xs mb-1">Skipped</p>
            <p className="text-xl font-bold text-slate-400">{skipped}</p>
          </div>
          <div>
            <p className="text-slate-400 text-xs mb-1">Manual Fixes</p>
            <p className="text-xl font-bold text-amber-400">{manual}</p>
          </div>
          <div>
            <p className="text-slate-400 text-xs mb-1">Target</p>
            <p className="text-sm font-bold text-slate-200 truncate">{isFolderMode ? folderName : analysisResult.file_name}</p>
          </div>
        </motion.div>
      )}

      {lastReport && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 flex items-center gap-3 text-sm">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          Report generated — <span className="font-mono">{lastReport.pdfFilename}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-2">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel-interactive p-8 flex flex-col items-center justify-center text-center gap-4 relative overflow-hidden"
        >
          <div className="w-20 h-20 rounded-2xl bg-red-500/10 flex items-center justify-center">
            <FileText className="w-10 h-10 text-red-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">
              {isFolderMode ? 'Overall Project PDF Report' : 'PDF Compliance Report'}
            </h3>
            <p className="text-slate-400 text-sm mt-2">
              {isFolderMode
                ? `Comprehensive project report for folder ${folderName} summarizing all ${fileList.length} analyzed C files.`
                : 'Comprehensive human-readable report including scores, violations, and applied patches.'}
            </p>
          </div>
          <button
            onClick={isFolderMode ? downloadProjectPDF : downloadPDF}
            disabled={loading || !analysisResult}
            className="mt-4 flex items-center gap-2 px-6 py-3 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30 transition-colors font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            {isFolderMode ? 'Download Project PDF' : 'Download PDF'}
          </button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-panel-interactive p-8 flex flex-col items-center justify-center text-center gap-4 relative overflow-hidden"
        >
          <div className="w-20 h-20 rounded-2xl bg-amber-500/10 flex items-center justify-center">
            <FileJson className="w-10 h-10 text-amber-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">JSON Audit Log</h3>
            <p className="text-slate-400 text-sm mt-2">Machine-readable verification output for CI/CD pipelines and auditing tools.</p>
          </div>
          <button
            onClick={downloadJSON}
            disabled={loading || !analysisResult}
            className="mt-4 flex items-center gap-2 px-6 py-3 bg-amber-500/20 text-amber-300 rounded-lg hover:bg-amber-500/30 transition-colors font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Download JSON
          </button>
        </motion.div>
      </div>
    </div>
  );
};

export default Reports;
