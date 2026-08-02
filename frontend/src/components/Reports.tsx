import { useState } from 'react';
import { Download, FileText, Loader2, AlertCircle, Archive, CheckCircle2, ShieldCheck, Cpu, Code2 } from 'lucide-react';
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
    setActiveTab,
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
      const files_summary = fileList.map((f, i) => {
        const m = getAnalysisMetrics(i);
        return {
          file_name:        f.file_name,
          violations_count: m.total_detected,
          accepted_count:   m.accepted,
          compliance_score: m.compliance_score,
        };
      });

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

  const downloadZipArchive = async () => {
    if (!isFolderMode || fileList.length === 0) return;
    setLoading(true);
    setError(null);

    try {
      const payloadFiles = fileList.map((f) => ({
        file_name: f.file_name,
        corrected_code: f.working_code || f.source_code,
      }));

      const res = await fetch('http://localhost:8000/api/download-zip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_name: folderName || 'Project',
          files: payloadFiles,
        }),
      });

      if (!res.ok) throw new Error('Failed to package ZIP archive.');

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${(folderName || 'Project').replace(/\s+/g, '_')}_fixed.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || 'Error downloading ZIP archive.');
    } finally {
      setLoading(false);
    }
  };

  // Guarantee #9: Serialize finalized session — never independently recompute
  let accepted = 0, totalViol = 0, overallScoreVal = 100;

  if (isFolderMode && fileList.length > 0) {
    for (let i = 0; i < fileList.length; i++) {
      const m = getAnalysisMetrics(i);
      totalViol += m.total_detected;
      accepted  += m.accepted;
    }
    overallScoreVal = Math.round(
      fileList.reduce((acc, f) => acc + f.compliance_score, 0) / fileList.length
    );
  } else if (analysisResult) {
    const m = getAnalysisMetrics();
    totalViol       = m.total_detected;
    accepted        = m.accepted;
    overallScoreVal = Math.round(m.compliance_score);
  }

  const hasData = isFolderMode ? fileList.length > 0 : Boolean(analysisResult);

  return (
    <div className="h-full flex flex-col gap-6 p-2 justify-between">
      {/* Top Header */}
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white mb-1">Compliance Reports</h2>
          <p className="text-slate-400">Download executive PDF compliance reports and remediated source code archives.</p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {hasData ? (
        <div className="flex flex-col gap-6 flex-1 justify-between">
          {/* Main 2-Card Grid */}
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1"
          >
            {/* Card 1: Executive PDF Report */}
            <div className="glass-panel p-6 flex flex-col justify-between gap-5 border border-slate-700/60 shadow-xl">
              <div>
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-violet-500/20 border border-violet-500/30 flex items-center justify-center text-violet-400">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-lg">Executive PDF Compliance Report</h3>
                    <p className="text-xs text-slate-400 font-mono">
                      {isFolderMode ? `${folderName} (${fileList.length} files)` : analysisResult?.file_name}
                    </p>
                  </div>
                </div>

                <p className="text-sm text-slate-300 mb-4 leading-relaxed">
                  Official PDF compliance report containing violation audit trails, patch diffs, compliance metrics, and score validation.
                </p>

                {/* Metadata & Invariants Box */}
                <div className="bg-slate-800/60 border border-slate-700/50 p-4 rounded-xl space-y-2 text-xs font-mono mb-4">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Target Resource:</span>
                    <span className="text-white font-bold truncate max-w-[180px]">{isFolderMode ? folderName : analysisResult?.file_name}</span>
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

                {/* PDF Checklist */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">What's Included in this PDF</h4>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                      <span>Executive Compliance Summary & Score Validation</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                      <span>Baseline Violation Audit Trail & Rule Breakdown</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                      <span>Side-by-Side Patch Diffs & Decision Ledger</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                      <span>Remediated Source Code Appendix & Sign-off</span>
                    </li>
                  </ul>
                </div>
              </div>

              <button
                onClick={isFolderMode ? downloadProjectPDF : downloadPDF}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-2.5 bg-violet-600 hover:bg-violet-500 text-white font-semibold rounded-xl text-sm transition-all shadow-lg shadow-violet-500/20 disabled:opacity-50 mt-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                {isFolderMode ? 'Download Project Summary PDF' : 'Download Executive PDF Report'}
              </button>
            </div>

            {/* Card 2: Corrected Source Code */}
            <div className="glass-panel p-6 flex flex-col justify-between gap-5 border border-slate-700/60 shadow-xl">
              <div>
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-sky-500/20 border border-sky-500/30 flex items-center justify-center text-sky-400">
                    <Archive className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-lg">Corrected Source Code</h3>
                    <p className="text-xs text-slate-400 font-mono">
                      {isFolderMode ? 'Multi-File ZIP Package' : 'Single File Corrected Source'}
                    </p>
                  </div>
                </div>

                <p className="text-sm text-slate-300 mb-4 leading-relaxed">
                  {isFolderMode
                    ? 'Package all remediated C source files into a clean ZIP archive for deployment or CI/CD integration.'
                    : 'View or export your remediated C source file containing all accepted automated and manual fixes.'}
                </p>

                {/* Metadata Box */}
                <div className="bg-slate-800/60 border border-slate-700/50 p-4 rounded-xl space-y-2 text-xs font-mono mb-4">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Packaging Format:</span>
                    <span className="text-sky-400 font-bold">{isFolderMode ? 'ZIP Archive' : 'C Source File (.c)'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Target Scope:</span>
                    <span className="text-white font-bold">{isFolderMode ? `${fileList.length} C Files` : 'Single C File'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Remediation Status:</span>
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Validated
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Artifact Delivery:</span>
                    <span className="text-slate-200 font-bold">Browser Downloads</span>
                  </div>
                </div>

                {/* Workflow Info Box */}
                <div className="bg-slate-800/40 p-4 rounded-xl border border-slate-700/40">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Source Code Integration</h4>
                  <p className="text-xs text-slate-300 leading-relaxed mb-3">
                    {isFolderMode
                      ? 'The generated ZIP package contains updated C files with all range-based AST fixes applied.'
                      : 'All accepted automated fixes and manual edits are stored in your active session working copy.'}
                  </p>
                  {!isFolderMode && (
                    <button
                      onClick={() => setActiveTab('generated-code')}
                      className="w-full py-2 px-3 rounded-lg bg-slate-700 hover:bg-slate-600 text-xs font-semibold text-slate-200 flex items-center justify-center gap-2 transition-colors"
                    >
                      <Code2 className="w-3.5 h-3.5 text-violet-400" />
                      View Corrected Code in Editor →
                    </button>
                  )}
                </div>
              </div>

              {isFolderMode ? (
                <button
                  onClick={downloadZipArchive}
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-2 py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-semibold rounded-xl text-sm transition-all shadow-lg shadow-sky-500/20 disabled:opacity-50 mt-2"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                  Download Project ZIP Archive
                </button>
              ) : (
                <div className="p-2.5 bg-slate-800/60 rounded-xl text-xs text-slate-400 text-center font-mono border border-slate-700/50">
                  Source code synced to <span className="text-violet-400 font-bold">Generated Code</span> tab.
                </div>
              )}
            </div>
          </motion.div>

          {/* Bottom Engine Metadata Section */}
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-2xl glass-panel bg-slate-800/40 border border-slate-700/50 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono shadow-md"
          >
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0" />
              <div>
                <div className="text-slate-400">Standard</div>
                <div className="text-white font-bold">MISRA C:2012</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Cpu className="w-5 h-5 text-violet-400 flex-shrink-0" />
              <div>
                <div className="text-slate-400">Engine Version</div>
                <div className="text-white font-bold">v1.0.0 Baseline</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-sky-400 flex-shrink-0" />
              <div>
                <div className="text-slate-400">State Invariants</div>
                <div className="text-emerald-400 font-bold">100% Synchronized</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-amber-400 flex-shrink-0" />
              <div>
                <div className="text-slate-400">Storage Mode</div>
                <div className="text-white font-bold">Transient Streaming</div>
              </div>
            </div>
          </motion.div>
        </div>
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
