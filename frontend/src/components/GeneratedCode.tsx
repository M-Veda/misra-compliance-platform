import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Editor } from '@monaco-editor/react';
import { Copy, Download, FileCode2, Hash, CheckCircle2, Terminal, Folder, Archive } from 'lucide-react';
import { useAppContext } from '../context/AppContext';

const GeneratedCode = () => {
  const {
    workingCode,
    analysisResult,
    settings,
    isFolderMode,
    folderName,
    fileList,
    activeFileIndex,
    setActiveFileIndex,
  } = useAppContext();

  // Guarantee #8: Generated Code ALWAYS derives from the authoritative working copy
  const correctedCode = isFolderMode
    ? (fileList[activeFileIndex]?.working_code ?? fileList[activeFileIndex]?.corrected_code ?? '')
    : workingCode;


  const [showLineNumbers, setShowLineNumbers] = useState(true);
  const [copied, setCopied] = useState(false);
  const [downloadingZip, setDownloadingZip] = useState(false);

  const suffix = settings.filenameSuffix ?? '_fixed';

  // Derive output filename for individual download
  const fixedFilename = (() => {
    if (!analysisResult?.file_name) return `output${suffix}.c`;
    const name = analysisResult.file_name.replace(/\\/g, '/').split('/').pop() ?? analysisResult.file_name;
    const dot = name.lastIndexOf('.');
    return dot !== -1
      ? `${name.slice(0, dot)}${suffix}${name.slice(dot)}`
      : `${name}${suffix}.c`;
  })();

  const handleCopy = useCallback(async () => {
    if (!correctedCode) return;
    try {
      await navigator.clipboard.writeText(correctedCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = correctedCode;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [correctedCode]);

  const handleDownloadSingle = useCallback(() => {
    if (!correctedCode) return;
    const blob = new Blob([correctedCode], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fixedFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [correctedCode, fixedFilename]);

  const handleDownloadZip = useCallback(async () => {
    if (!isFolderMode || fileList.length === 0) return;
    setDownloadingZip(true);
    try {
      const payload = {
        folder_name: folderName || 'MISRA_Project',
        files: fileList.map(f => ({
          file_name: f.file_name,
          corrected_code: f.corrected_code || f.source_code,
        })),
      };

      const resp = await fetch('http://localhost:8000/api/download-zip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) throw new Error('ZIP download failed');
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${folderName || 'Project'}_fixed.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download ZIP archive:', err);
    } finally {
      setDownloadingZip(false);
    }
  }, [isFolderMode, fileList, folderName]);

  if (!analysisResult) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500 flex-col gap-4">
        <Terminal className="w-12 h-12 text-slate-700" />
        <p>No analysis result found. Please upload and analyze a file or folder first.</p>
      </div>
    );
  }

  const lineCount = correctedCode ? correctedCode.split('\n').length : 0;
  const charCount = correctedCode ? correctedCode.length : 0;

  return (
    <div className="h-full flex flex-col gap-6 p-2">
      {/* File selector for folder mode */}
      {isFolderMode && (
        <div className="flex items-center gap-3 bg-slate-800/90 px-4 py-3 rounded-xl border border-slate-700/80 shadow-md">
          <Folder className="w-5 h-5 text-sky-400 flex-shrink-0" />
          <span className="text-sm font-bold text-white">Select File ({folderName}):</span>
          <select
            value={activeFileIndex}
            onChange={(e) => setActiveFileIndex(Number(e.target.value))}
            className="bg-slate-900 text-sm font-mono font-semibold text-white px-3 py-1.5 rounded-lg border border-slate-700 focus:outline-none focus:border-violet-500 cursor-pointer"
          >
            {fileList.map((file, idx) => (
              <option key={idx} value={idx}>
                {file.file_name} ({file.violations.length} violations)
              </option>
            ))}
          </select>
          <span className="text-xs text-slate-400 ml-auto font-mono">
            {fileList.length} total files analyzed
          </span>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white mb-1">Generated Code</h2>
          <p className="text-slate-400">
            Current corrected source code after all accepted and manual fixes.
          </p>
        </div>

        {/* Action toolbar */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Toggle line numbers */}
          <button
            onClick={() => setShowLineNumbers(prev => !prev)}
            title="Toggle line numbers"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors text-sm font-medium ${
              showLineNumbers && settings.showLineNumbers
                ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700/50'
            }`}
          >
            <Hash className="w-4 h-4" />
            Line Numbers
          </button>

          {/* Copy */}
          <button
            onClick={handleCopy}
            disabled={!correctedCode}
            className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/50 rounded-lg transition-colors text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {copied ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="text-emerald-400">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy Code
              </>
            )}
          </button>

          {/* Download Individual File */}
          <button
            onClick={handleDownloadSingle}
            disabled={!correctedCode}
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-violet-500/20"
          >
            <Download className="w-4 h-4" />
            Download .c File
          </button>

          {/* Download ZIP for Folder */}
          {isFolderMode && (
            <button
              onClick={handleDownloadZip}
              disabled={downloadingZip || fileList.length === 0}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-sky-600 to-cyan-600 hover:from-sky-500 hover:to-cyan-500 text-white rounded-lg transition-colors text-sm font-semibold disabled:opacity-40 shadow-lg shadow-sky-500/20"
            >
              <Archive className="w-4 h-4" />
              {downloadingZip ? 'Packaging ZIP...' : 'Download All Fixed Files (ZIP)'}
            </button>
          )}
        </div>
      </div>

      {/* File info bar */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel px-5 py-3 flex items-center gap-6 text-sm"
      >
        <div className="flex items-center gap-2 text-violet-300 font-medium">
          <FileCode2 className="w-4 h-4" />
          <span className="font-mono">{fixedFilename}</span>
        </div>
        <div className="h-4 w-px bg-slate-700" />
        <span className="text-slate-400">
          <span className="text-slate-200 font-semibold">{lineCount}</span> lines
        </span>
        <div className="h-4 w-px bg-slate-700" />
        <span className="text-slate-400">
          <span className="text-slate-200 font-semibold">{charCount.toLocaleString()}</span> chars
        </span>
        <div className="h-4 w-px bg-slate-700" />
        <span className="text-slate-400">
          Source: <span className="font-mono text-slate-300">{analysisResult.file_name}</span>
        </span>
      </motion.div>

      {/* Monaco Editor */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex-1 glass-panel overflow-hidden flex flex-col min-h-0"
      >
        {/* Editor title bar */}
        <div className="px-4 py-3 border-b border-slate-700/50 bg-slate-800/80 flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/70" />
            <div className="w-3 h-3 rounded-full bg-amber-500/70" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/70" />
          </div>
          <span className="font-mono text-sm text-violet-300 ml-2">{fixedFilename}</span>
          <span className="ml-auto text-xs text-slate-500 font-medium">read-only • C source</span>
        </div>

        {/* Editor body */}
        <div className="flex-1 min-h-0 bg-[#1e1e1e]">
          {correctedCode ? (
            <Editor
              height="100%"
              language="c"
              theme={settings.theme === 'light' ? 'vs' : 'vs-dark'}
              value={correctedCode}
              options={{
                readOnly: true,
                minimap: { enabled: true },
                fontSize: settings.fontSize,
                fontFamily: 'Consolas, "Courier New", monospace',
                lineNumbers: (showLineNumbers && settings.showLineNumbers) ? 'on' : 'off',
                scrollBeyondLastLine: false,
                wordWrap: settings.wordWrap ? 'on' : 'off',
                renderLineHighlight: 'line',
                smoothScrolling: true,
                cursorBlinking: 'solid',
                folding: true,
                foldingHighlight: true,
                renderWhitespace: 'none',
                occurrencesHighlight: 'off',
                selectionHighlight: false,
                domReadOnly: true,
              }}
            />
          ) : (
            <div className="h-full flex items-center justify-center flex-col gap-4 text-slate-500">
              <FileCode2 className="w-16 h-16 text-slate-700" />
              <div className="text-center">
                <p className="font-semibold text-slate-400 mb-1">No patches applied yet</p>
                <p className="text-sm">
                  Accept violations in the Violations Review page to see corrected code here.
                </p>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default GeneratedCode;
