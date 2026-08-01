import { useRef, useState } from 'react';
import { UploadCloud, Folder, FileCode, Check, Loader2, AlertCircle, Play } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAppContext } from '../context/AppContext';
import type { FileAnalysisItem } from '../types';

interface FolderSelectionInfo {
  folderName: string;
  totalFiles: number;
  cFiles: File[];
  ignoredCount: number;
}

const Analysis = () => {
  const {
    setAnalysisResult,
    setOriginalCode,
    setAllViolations,
    setWorkingCode,
    addRecentScan,
    setActiveTab,
    resetSession,
    setFolderName,
    setFileList,
  } = useAppContext();

  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [folderInfo, setFolderInfo] = useState<FolderSelectionInfo | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const handleSingleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.c')) {
      setError('Only .c source files are supported.');
      return;
    }

    setIsUploading(true);
    setError(null);
    setFolderInfo(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Analysis failed.');
      }

      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Unknown analysis error.');
      }

      resetSession();
      setOriginalCode(data.source_code);
      // Set immutable baseline violations — called once after initial analysis
      setAllViolations(data.violations);
      // Initialize authoritative working copy to original source
      setWorkingCode(data.source_code);
      setAnalysisResult(data);

      addRecentScan({
        id: Date.now(),
        file: file.name,
        score: data.compliance_score,
        time: 'Just now',
        status: data.violations.length === 0 ? 'Perfect' : 'Failed'
      });

      setActiveTab('violations');
    } catch (err: any) {
      setError(err.message || 'Error uploading file.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleFolderSelection = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setError(null);
    const fileArray = Array.from(files);
    const totalFiles = fileArray.length;

    let detectedFolderName = 'Uploaded_Folder';
    const firstRel = fileArray[0]?.webkitRelativePath;
    if (firstRel && firstRel.includes('/')) {
      detectedFolderName = firstRel.split('/')[0];
    }

    const cFiles = fileArray.filter(f => f.name.toLowerCase().endsWith('.c'));
    const ignoredCount = totalFiles - cFiles.length;

    if (cFiles.length === 0) {
      setFolderInfo(null);
      setError('No C source files found in the selected folder.');
      return;
    }

    setFolderInfo({
      folderName: detectedFolderName,
      totalFiles,
      cFiles,
      ignoredCount,
    });
  };

  const handleStartFolderAnalysis = async () => {
    if (!folderInfo || folderInfo.cFiles.length === 0) return;

    setIsUploading(true);
    setError(null);
    resetSession();
    setFolderName(folderInfo.folderName);

    const analyzedItems: FileAnalysisItem[] = [];

    try {
      for (const file of folderInfo.cFiles) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('http://localhost:8000/api/upload', {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            const relPath = file.webkitRelativePath
              ? file.webkitRelativePath.replace(`${folderInfo.folderName}/`, '')
              : file.name;

            analyzedItems.push({
              file_name: relPath,
              original_code: data.source_code,
              // Single authoritative working copy — initially equals original
              working_code: data.source_code,
              source_code: data.source_code,
              corrected_code: data.source_code,
              violations: data.violations || [],
              // Immutable baseline — never replaced after this point
              all_violations: data.violations || [],
              decisions: {},
              manual_codes: {},
              compliance_score: data.compliance_score || 0,
            });
          }
        }
      }

      if (analyzedItems.length === 0) {
        throw new Error('Failed to analyze C source files in the folder.');
      }

      setFileList(analyzedItems);

      const totalScore = Math.round(
        analyzedItems.reduce((acc, f) => acc + f.compliance_score, 0) / analyzedItems.length
      );

      addRecentScan({
        id: Date.now(),
        file: `${folderInfo.folderName} (${analyzedItems.length} C files)`,
        score: totalScore,
        time: 'Just now',
        status: analyzedItems.every(f => f.violations.length === 0) ? 'Perfect' : 'Failed'
      });

      setActiveTab('violations');
    } catch (err: any) {
      setError(err.message || 'Error analyzing folder files.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="h-full flex flex-col gap-6 p-2">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-white mb-1">Source Code Analysis</h2>
        <p className="text-slate-400">Upload single C files or an entire folder to verify MISRA C:2012 compliance.</p>
      </div>

      <div className="flex-1 glass-panel flex flex-col items-center justify-center p-8 border-dashed border-2 border-slate-600/50 hover:border-violet-500/50 transition-colors relative">
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring" }}
          className="w-20 h-20 rounded-full bg-violet-500/10 flex items-center justify-center mb-4"
        >
          <UploadCloud className="w-10 h-10 text-violet-400" />
        </motion.div>
        
        <h3 className="text-2xl font-bold text-white mb-2">Upload Source</h3>
        <p className="text-slate-400 mb-6 max-w-md text-center text-sm">
          Select a single C file or a folder containing multiple C source files for automated MISRA C analysis.
        </p>

        {/* Supported badges */}
        <div className="flex gap-4 mb-8 text-xs font-semibold text-slate-300 bg-slate-800/60 px-4 py-2 rounded-xl border border-slate-700/50">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <Check className="w-4 h-4" /> Single C file
          </span>
          <span className="h-4 w-px bg-slate-700" />
          <span className="flex items-center gap-1.5 text-emerald-400">
            <Check className="w-4 h-4" /> Folder containing multiple C files
          </span>
        </div>

        {/* Upload Buttons */}
        <div className="flex items-center gap-4 flex-wrap justify-center mb-4">
          <input
            type="file"
            accept=".c"
            className="hidden"
            ref={fileInputRef}
            onChange={handleSingleFileUpload}
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="px-6 py-3.5 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl font-bold text-base hover:from-violet-500 hover:to-indigo-500 shadow-lg shadow-violet-500/25 transition-all transform hover:-translate-y-0.5 disabled:opacity-50 flex items-center gap-2"
          >
            <FileCode className="w-5 h-5" />
            Select C File
          </button>

          <input
            type="file"
            className="hidden"
            ref={folderInputRef}
            onChange={handleFolderSelection}
            {...({ webkitdirectory: '', directory: '', multiple: true } as any)}
          />
          <button 
            onClick={() => folderInputRef.current?.click()}
            disabled={isUploading}
            className="px-6 py-3.5 bg-gradient-to-r from-sky-600 to-cyan-600 text-white rounded-xl font-bold text-base hover:from-sky-500 hover:to-cyan-500 shadow-lg shadow-sky-500/25 transition-all transform hover:-translate-y-0.5 disabled:opacity-50 flex items-center gap-2"
          >
            <Folder className="w-5 h-5" />
            Select Folder
          </button>
        </div>

        {/* Selected Folder summary card */}
        {folderInfo && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-5 rounded-2xl bg-slate-800/80 border border-slate-700/80 max-w-md w-full text-center flex flex-col items-center gap-3 shadow-xl"
          >
            <div className="text-lg font-bold text-white flex items-center gap-2">
              <Folder className="w-5 h-5 text-sky-400" />
              Folder: <span className="font-mono text-sky-300">{folderInfo.folderName}</span>
            </div>
            <div className="grid grid-cols-3 gap-2 w-full text-xs font-semibold">
              <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-700/50">
                <div className="text-slate-400">Detected</div>
                <div className="text-sm text-white font-bold">{folderInfo.totalFiles} files</div>
              </div>
              <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-700/50">
                <div className="text-slate-400">C Source</div>
                <div className="text-sm text-emerald-400 font-bold">{folderInfo.cFiles.length} files</div>
              </div>
              <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-700/50">
                <div className="text-slate-400">Ignored</div>
                <div className="text-sm text-amber-400 font-bold">{folderInfo.ignoredCount} files</div>
              </div>
            </div>
            <div className="text-xs text-emerald-400 font-medium">Ready for analysis</div>
            <button
              onClick={handleStartFolderAnalysis}
              disabled={isUploading}
              className="mt-2 w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 text-sm disabled:opacity-50"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing C Files...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  Analyze Folder ({folderInfo.cFiles.length} C files)
                </>
              )}
            </button>
          </motion.div>
        )}

        {error && (
          <div className="mt-6 px-4 py-3 bg-red-500/20 border border-red-500/50 rounded-xl text-red-400 font-semibold text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default Analysis;
