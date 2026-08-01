import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import type {
  AnalysisResult,
  RuleViolation,
  AppSettings,
  FileAnalysisItem,
  AnalysisMetrics,
  DecisionType,
} from '../types';
import { DEFAULT_SETTINGS } from '../types';

export type DecisionMap = Record<string, DecisionType>;
export type ManualCodeMap = Record<string, string>;

interface ScanHistory {
  id: number;
  file: string;
  score: number;
  time: string;
  status: string;
}

interface AppContextType {
  // ── Single-file compat ─────────────────────────────────────────────────────
  originalCode: string;
  setOriginalCode: (code: string) => void;

  analysisResult: AnalysisResult | null;
  setAnalysisResult: (result: AnalysisResult | null) => void;

  /** Immutable baseline violations — NEVER replaced after first set */
  allViolations: RuleViolation[];
  /** Sets the immutable baseline ONCE. Call only on initial analysis. */
  setAllViolations: (violations: RuleViolation[]) => void;

  decisions: DecisionMap;
  setDecision: (key: string, decision: DecisionType) => void;
  updateDecisions: (batch: DecisionMap) => void;

  manualCodes: ManualCodeMap;
  setManualCode: (key: string, code: string) => void;

  /**
   * The authoritative working copy.
   * All Accept/Manual patch applications update this.
   * Generated Code and Reports always read from this.
   */
  workingCode: string;
  setWorkingCode: (code: string) => void;

  /** Alias kept for legacy usage — delegates to workingCode */
  correctedCode: string;
  setCorrectedCode: (code: string) => void;

  selectedViolation: RuleViolation | null;
  setSelectedViolation: (violation: RuleViolation | null) => void;

  recentScans: ScanHistory[];
  addRecentScan: (scan: ScanHistory) => void;

  activeTab: string;
  setActiveTab: (tab: string) => void;

  settings: AppSettings;
  updateSettings: (newSettings: Partial<AppSettings>) => void;
  resetSettings: () => void;

  resetSession: () => void;

  // ── Folder & Multi-file ────────────────────────────────────────────────────
  folderName: string | null;
  setFolderName: (name: string | null) => void;
  fileList: FileAnalysisItem[];
  setFileList: (files: FileAnalysisItem[]) => void;
  activeFileIndex: number;
  setActiveFileIndex: (index: number) => void;
  updateActiveFileItem: (updates: Partial<FileAnalysisItem>) => void;
  isFolderMode: boolean;

  // ── Single source of truth metrics ────────────────────────────────────────
  /** Returns fully synchronized metrics. Never independently recompute in pages. */
  getAnalysisMetrics: (fileIdx?: number) => AnalysisMetrics;
}

const AppContext = createContext<AppContextType | undefined>(undefined);
const STORAGE_KEY = 'misra_ai_settings';

// ── Metrics computation — the ONLY place statistics are calculated ──────────
function computeMetrics(
  allViolations: RuleViolation[],
  decisions: DecisionMap,
  currentViolations: RuleViolation[],
): AnalysisMetrics {
  const total_detected = allViolations.length;
  const accepted  = Object.values(decisions).filter(d => d === 'Accept').length;
  const rejected  = Object.values(decisions).filter(d => d === 'Reject').length;
  const skipped   = Object.values(decisions).filter(d => d === 'Skip').length;
  const manual    = Object.values(decisions).filter(d => d === 'Manual').length;
  // Remaining = violations still in the active list (not yet reviewed)
  const remaining = currentViolations.length;

  // Compliance: 100% if no violations remain, otherwise per-rule deduction
  const violated_rules = new Set(currentViolations.map(v => v.rule_number));
  const compliance_score = total_detected === 0
    ? 100.0
    : currentViolations.length === 0
      ? 100.0
      : Math.max(0, 100.0 - violated_rules.size * 10.0);

  return { total_detected, accepted, rejected, skipped, manual, remaining, compliance_score };
}

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [folderName, setFolderName] = useState<string | null>(null);
  const [fileList, setFileListState] = useState<FileAnalysisItem[]>([]);
  const [activeFileIndex, setActiveFileIndex] = useState<number>(0);

  // Single-file fallback states
  const [singleOriginalCode, setSingleOriginalCode]     = useState<string>('');
  const [singleWorkingCode,  setSingleWorkingCode]       = useState<string>('');
  const [singleAnalysisResult, setSingleAnalysisResult] = useState<AnalysisResult | null>(null);
  /** Immutable baseline — only set once per session */
  const [singleAllViolations, setSingleAllViolations]   = useState<RuleViolation[]>([]);
  const [singleDecisions,     setSingleDecisionsMap]    = useState<DecisionMap>({});
  const [singleManualCodes,   setSingleManualCodesMap]  = useState<ManualCodeMap>({});

  const [selectedViolation, setSelectedViolation] = useState<RuleViolation | null>(null);
  const [recentScans,       setRecentScans]        = useState<ScanHistory[]>([]);
  const [activeTab,         setActiveTab]          = useState('dashboard');

  const [settings, setSettingsState] = useState<AppSettings>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return { ...DEFAULT_SETTINGS, ...JSON.parse(saved) };
    } catch (e) {
      console.error('Failed to load settings from localStorage:', e);
    }
    return DEFAULT_SETTINGS;
  });

  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(settings)); }
    catch (e) { console.error('Failed to save settings:', e); }
  }, [settings]);

  const updateSettings = (newSettings: Partial<AppSettings>) =>
    setSettingsState(prev => ({ ...prev, ...newSettings }));

  const resetSettings = () => setSettingsState(DEFAULT_SETTINGS);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).__appContext = {
        setAnalysisResult: setSingleAnalysisResult,
        setOriginalCode: setSingleOriginalCode,
        setAllViolations: setSingleAllViolations,
        setWorkingCode: setSingleWorkingCode,
        setSelectedViolation,
        setActiveTab,
      };
    }
  }, []);

  const isFolderMode = fileList.length > 0;
  const activeFile   = isFolderMode ? (fileList[activeFileIndex] ?? fileList[0]) : null;

  // ── Computed values — always read from active file in folder mode ──────────
  const originalCode  = activeFile ? activeFile.original_code  : singleOriginalCode;
  const workingCode   = activeFile ? activeFile.working_code   : singleWorkingCode;
  const correctedCode = workingCode;  // alias — always the same
  const allViolations = activeFile ? activeFile.all_violations : singleAllViolations;
  const decisions     = activeFile ? activeFile.decisions       : singleDecisions;
  const manualCodes   = activeFile ? activeFile.manual_codes    : singleManualCodes;

  const analysisResult: AnalysisResult | null = activeFile ? {
    success: true,
    file_name: activeFile.file_name,
    source_code: activeFile.working_code,
    violations: activeFile.violations,
    compliance_score: activeFile.compliance_score,
  } : singleAnalysisResult;

  // ── Folder file list management ────────────────────────────────────────────
  const setFileList = (files: FileAnalysisItem[]) => {
    setFileListState(files);
    setActiveFileIndex(0);
    setSelectedViolation(null);
  };

  const updateActiveFileItem = (updates: Partial<FileAnalysisItem>) => {
    if (!isFolderMode) return;
    setFileListState(prev => prev.map((f, idx) => {
      if (idx !== activeFileIndex) return f;
      const merged = { ...f, ...updates };
      // Keep working_code and source_code/corrected_code in sync
      if (updates.working_code) {
        merged.source_code   = updates.working_code;
        merged.corrected_code = updates.working_code;
      }
      return merged;
    }));
  };

  // ── Setters ────────────────────────────────────────────────────────────────
  const setOriginalCode = (code: string) => {
    if (isFolderMode) updateActiveFileItem({ original_code: code });
    else setSingleOriginalCode(code);
  };

  /**
   * Update the authoritative working copy.
   * All patch applications (Accept/Manual) MUST call this.
   */
  const setWorkingCode = (code: string) => {
    if (isFolderMode) {
      updateActiveFileItem({
        working_code:  code,
        source_code:   code,
        corrected_code: code,
      });
    } else {
      setSingleWorkingCode(code);
    }
  };

  // Legacy alias — always delegates to setWorkingCode
  const setCorrectedCode = setWorkingCode;

  /**
   * Sets the immutable baseline violations.
   * In folder mode, only sets all_violations once (never overwrites existing baseline).
   */
  const setAllViolations = (violations: RuleViolation[]) => {
    if (isFolderMode) {
      // Only set baseline if not already set
      setFileListState(prev => prev.map((f, idx) => {
        if (idx !== activeFileIndex) return f;
        if (f.all_violations.length > 0) return f; // Guard: never replace existing baseline
        return { ...f, all_violations: violations };
      }));
    } else {
      // Only set if not already set — guard immutability
      setSingleAllViolations(prev => prev.length > 0 ? prev : violations);
    }
  };

  const setAnalysisResult = (result: AnalysisResult | null) => {
    if (isFolderMode) {
      if (result) {
        updateActiveFileItem({
          working_code:   result.source_code,
          source_code:    result.source_code,
          corrected_code: result.source_code,
          violations:     result.violations,
          compliance_score: result.compliance_score,
        });
      }
    } else {
      setSingleAnalysisResult(result);
    }
  };

  const setDecision = (key: string, decision: DecisionType) => {
    if (isFolderMode) {
      setFileListState(prev => prev.map((f, idx) => {
        if (idx !== activeFileIndex) return f;
        return { ...f, decisions: { ...f.decisions, [key]: decision } };
      }));
    } else {
      setSingleDecisionsMap(prev => ({ ...prev, [key]: decision }));
    }
  };

  const updateDecisions = (batch: DecisionMap) => {
    if (isFolderMode) {
      setFileListState(prev => prev.map((f, idx) => {
        if (idx !== activeFileIndex) return f;
        return { ...f, decisions: { ...f.decisions, ...batch } };
      }));
    } else {
      setSingleDecisionsMap(prev => ({ ...prev, ...batch }));
    }
  };

  const setManualCode = (key: string, code: string) => {
    if (isFolderMode) {
      setFileListState(prev => prev.map((f, idx) => {
        if (idx !== activeFileIndex) return f;
        return { ...f, manual_codes: { ...f.manual_codes, [key]: code } };
      }));
    } else {
      setSingleManualCodesMap(prev => ({ ...prev, [key]: code }));
    }
  };

  const addRecentScan = (scan: ScanHistory) =>
    setRecentScans(prev => [scan, ...prev]);

  const resetSession = () => {
    setFolderName(null);
    setFileListState([]);
    setActiveFileIndex(0);
    setSingleOriginalCode('');
    setSingleWorkingCode('');
    setSingleAnalysisResult(null);
    setSingleAllViolations([]);
    setSingleDecisionsMap({});
    setSingleManualCodesMap({});
    setSelectedViolation(null);
  };

  // ── Single source of truth metrics ────────────────────────────────────────
  const getAnalysisMetrics = useCallback((fileIdx?: number): AnalysisMetrics => {
    if (isFolderMode) {
      const idx = fileIdx ?? activeFileIndex;
      const file = fileList[idx];
      if (!file) return { total_detected: 0, accepted: 0, rejected: 0, skipped: 0, manual: 0, remaining: 0, compliance_score: 100 };
      return computeMetrics(file.all_violations, file.decisions, file.violations);
    }
    return computeMetrics(
      singleAllViolations,
      singleDecisions,
      singleAnalysisResult?.violations ?? [],
    );
  }, [isFolderMode, fileList, activeFileIndex, singleAllViolations, singleDecisions, singleAnalysisResult]);

  const ctxValue = {
    originalCode,
    setOriginalCode,
    analysisResult,
    setAnalysisResult,
    allViolations,
    setAllViolations,
    decisions,
    setDecision,
    updateDecisions,
    manualCodes,
    setManualCode,
    workingCode,
    setWorkingCode,
    correctedCode,
    setCorrectedCode,
    selectedViolation,
    setSelectedViolation,
    recentScans,
    addRecentScan,
    activeTab,
    setActiveTab,
    settings,
    updateSettings,
    resetSettings,
    resetSession,
    folderName,
    setFolderName,
    fileList,
    setFileList,
    activeFileIndex,
    setActiveFileIndex,
    updateActiveFileItem,
    isFolderMode,
    getAnalysisMetrics,
  };

  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).__appContext = ctxValue;
    }
  }, [ctxValue]);

  return (
    <AppContext.Provider value={ctxValue}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
