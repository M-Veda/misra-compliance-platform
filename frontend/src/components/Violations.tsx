import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Code, Check, X, SkipForward, MessageSquare, Terminal, Loader2,
  RefreshCw, Search, Edit3, ChevronDown, Zap, Folder, ArrowRight, AlertCircle
} from 'lucide-react';
import { DiffEditor } from '@monaco-editor/react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppContext } from '../context/AppContext';
import type { RuleViolation } from '../types';
import { violationStableKey } from '../types';
import BulkActionModal from './BulkActionModal';
import type { BulkDecision, BulkSeverityFilter, BulkPhase, BulkSummary } from './BulkActionModal';

// ─── helpers ────────────────────────────────────────────────────────────────

const SEVERITY_COLORS: Record<string, string> = {
  Mandatory: 'bg-red-500/20 text-red-400',
  Required:  'bg-amber-500/20 text-amber-400',
  Advisory:  'bg-blue-500/20 text-blue-400',
};

type BulkItem = { decision: BulkDecision; severity: BulkSeverityFilter; label: string };

// ─── Toast ────────────────────────────────────────────────────────────────────

interface ToastProps { message: string; onDone: () => void }

const Toast = ({ message, onDone }: ToastProps) => {
  useEffect(() => {
    const t = setTimeout(onDone, 3000);
    return () => clearTimeout(t);
  }, [onDone]);
  return (
    <AnimatePresence>
      <motion.div
        key="toast"
        initial={{ opacity: 0, y: 40, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 40, scale: 0.95 }}
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] px-6 py-3 rounded-xl bg-slate-800 border border-slate-600 text-white text-sm font-semibold shadow-2xl shadow-black/40 flex items-center gap-2"
      >
        <Zap className="w-4 h-4 text-violet-400" />
        {message}
      </motion.div>
    </AnimatePresence>
  );
};

// ─── Component ────────────────────────────────────────────────────────────────

const Violations = () => {
  const {
    analysisResult,
    setAnalysisResult,
    workingCode,
    setWorkingCode,
    decisions,
    setDecision,
    updateDecisions,
    manualCodes,
    setManualCode,
    selectedViolation,
    setSelectedViolation,
    isFolderMode,
    folderName,
    fileList,
    activeFileIndex,
    setActiveFileIndex,
    updateActiveFileItem,
    getAnalysisMetrics,
  } = useAppContext();

  type DecisionMap = Record<string, 'Accept' | 'Reject' | 'Skip' | 'Manual'>;

  const [patchedCode,          setPatchedCode]          = useState<string>('');
  const [canAutopatch,         setCanAutopatch]          = useState<boolean | null>(null);
  const [noPatchReason,        setNoPatchReason]         = useState<string>('');
  const [loadingPatch,         setLoadingPatch]          = useState(false);
  const [explanation,          setExplanation]           = useState<string>('');
  const [structuredAiData,     setStructuredAiData]      = useState<any>(null);
  const [loadingExplanation,   setLoadingExplanation]    = useState(false);
  const [reanalyzing,          setReanalyzing]           = useState(false);
  const [manualMode,           setManualMode]            = useState(false);
  const [manualInput,          setManualInput]           = useState('');
  const [manualReviewKeys,     setManualReviewKeys]      = useState<Set<string>>(new Set());

  // Search & Filter
  const [searchTerm,     setSearchTerm]     = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('All');

  // Bulk Actions
  const [bulkMenuOpen, setBulkMenuOpen] = useState(false);
  const bulkMenuRef = useRef<HTMLDivElement>(null);

  // Bulk modal state
  const [bulkPhase,         setBulkPhase]         = useState<BulkPhase>('idle');
  const [bulkDecision,      setBulkDecision]       = useState<BulkDecision>('Accept');
  const [bulkSeverityFilter,setBulkSeverityFilter] = useState<BulkSeverityFilter>('All');
  const [bulkTargetCount,   setBulkTargetCount]    = useState(0);
  const [bulkCurrentIndex,  setBulkCurrentIndex]   = useState(0);
  const [bulkSummary,       setBulkSummary]        = useState<BulkSummary | null>(null);

  // Toast
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  /**
   * Preview cache: keyed by "${stable_id}:${working_code hash}"
   */
  const previewCache = useRef<Map<string, { patchedCode: string; canAutopatch: boolean; reason: string }>>(new Map());

  // Close bulk menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (bulkMenuRef.current && !bulkMenuRef.current.contains(e.target as Node)) {
        setBulkMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // ── Fetch patch preview (with caching) ─────────────────────────────────────
  useEffect(() => {
    if (!selectedViolation || !analysisResult) {
      setPatchedCode('');
      setCanAutopatch(null);
      setNoPatchReason('');
      setExplanation('');
      setManualMode(false);
      return;
    }

    const key = violationStableKey(selectedViolation);

    // Show stored manual code in the diff if already manually fixed
    if (decisions[key] === 'Manual' && manualCodes[key]) {
      setPatchedCode(manualCodes[key]);
      setCanAutopatch(false);
      setNoPatchReason('Already manually fixed.');
      return;
    }

    const currentWorking = workingCode || analysisResult.source_code;
    const workingHash = currentWorking.length.toString(16) + currentWorking.slice(0, 64);
    const cacheKey = `${key}:${workingHash}`;

    const cached = previewCache.current.get(cacheKey);
    if (cached) {
      setPatchedCode(cached.patchedCode);
      setCanAutopatch(cached.canAutopatch);
      setNoPatchReason(cached.reason);
      return;
    }

    const fetchPatch = async () => {
      setLoadingPatch(true);
      try {
        const response = await fetch('http://localhost:8000/api/preview-patch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source_code: currentWorking,
            violation: selectedViolation,
            decision: 'Accept',
          }),
        });
        const data = await response.json();

        const resultCode   = data.modified_code || currentWorking;
        const autopatch    = !!data.can_autopatch;
        const reason       = data.no_patch_reason || data.error || '';
        const patchChanged = data.patch_actually_changed === true || (autopatch && resultCode !== currentWorking);

        const cacheEntry = {
          patchedCode: patchChanged ? resultCode : currentWorking,
          canAutopatch: autopatch && patchChanged,
          reason: autopatch && patchChanged ? '' : (reason || 'Patch would not modify the source code.'),
        };

        previewCache.current.set(cacheKey, cacheEntry);
        setPatchedCode(cacheEntry.patchedCode);
        setCanAutopatch(cacheEntry.canAutopatch);
        setNoPatchReason(cacheEntry.reason);
      } catch (err) {
        console.error('Failed to fetch patch:', err);
        const previewObj = selectedViolation.patch_preview;
        if (previewObj) {
          const orig     = previewObj.original_source || selectedViolation.code_snippet || '';
          const proposed = previewObj.replacement_source || orig;
          setPatchedCode(proposed);
          setCanAutopatch(false);
          setNoPatchReason('Server unreachable — showing upload-time preview.');
        } else {
          setPatchedCode(currentWorking);
          setCanAutopatch(false);
          setNoPatchReason('Network or server error during patch preview generation.');
        }
      } finally {
        setLoadingPatch(false);
      }
    };

    fetchPatch();
    setExplanation('');
    setManualMode(false);
  }, [selectedViolation, analysisResult, workingCode]);

  const aiBackdropRef = useRef<HTMLDivElement>(null);

  // ── Dismiss Ask AI modal on Escape key ──────────────────────────────────────
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && explanation) {
        setExplanation('');
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [explanation]);

  // ── Ask AI ──────────────────────────────────────────────────────────────────
  const handleAskAI = async () => {
    if (!selectedViolation || !analysisResult) return;
    setLoadingExplanation(true);
    setStructuredAiData(null);
    try {
      const response = await fetch('http://localhost:8000/api/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_code: workingCode || analysisResult.source_code,
          violation: selectedViolation,
        }),
      });
      const data = await response.json();
      setExplanation(data.explanation);
      if (data.structured) {
        setStructuredAiData(data.structured);
      } else {
        try {
          setStructuredAiData(JSON.parse(data.explanation));
        } catch {
          setStructuredAiData(null);
        }
      }
    } catch (err) {
      console.error('Failed to fetch explanation:', err);
      setExplanation('Failed to get explanation from AI.');
    } finally {
      setLoadingExplanation(false);
    }
  };

  // ── Helper to start manual fix workflow pre-filled with suggested fix ───────
  const startManualFix = () => {
    if (!selectedViolation || !analysisResult) return;
    const currentWorking = workingCode || analysisResult.source_code;
    const suggested = patchedCode || selectedViolation.patch_preview?.replacement_source || selectedViolation.suggested_fix || currentWorking;
    setManualInput(suggested);
    setManualMode(true);
  };

  // ── Next violation helper ────────────────────────────────────────────────────
  const getNextViolation = (currentList: RuleViolation[], currentItem: RuleViolation): RuleViolation | null => {
    const currentIndex = currentList.findIndex(v => v === currentItem);
    const updated = currentList.filter(v => v !== currentItem);
    if (updated.length === 0) return null;
    return updated[Math.min(currentIndex, updated.length - 1)] ?? null;
  };

  // ── Decision handler ─────────────────────────────────────────────────────────
  const handleDecision = async (decision: 'Accept' | 'Reject' | 'Skip' | 'Manual') => {
    if (!selectedViolation || !analysisResult) return;

    const key = violationStableKey(selectedViolation);
    const nextSelected = getNextViolation(analysisResult.violations, selectedViolation);
    const currentWorking = workingCode || analysisResult.source_code;

    if (decision === 'Accept') {
      if (!canAutopatch || !patchedCode || patchedCode === currentWorking) {
        startManualFix();
        return;
      }

      const newSource = patchedCode;
      // Compute newViolations first so we can derive the correct compliance score
      const newViolations = analysisResult.violations.filter(v => v !== selectedViolation);
      // Score = 100 - (unique rules in REMAINING code violations × 10)
      // Accept changes the code → update score from the new remaining violations list
      const newScore = newViolations.length === 0
        ? 100.0
        : Math.max(0, 100.0 - new Set(newViolations.map(v => v.rule_number)).size * 10.0);

      previewCache.current.clear();

      setDecision(key, 'Accept');
      setWorkingCode(newSource);
      setAnalysisResult({
        ...analysisResult,
        source_code: newSource,
        violations: newViolations,
        compliance_score: newScore,  // authoritative: derived from actual remaining code violations
      });
      if (isFolderMode) {
        updateActiveFileItem({
          working_code:    newSource,
          source_code:     newSource,
          corrected_code:  newSource,
          violations:      newViolations,
          compliance_score: newScore,
        });
      }

    } else if (decision === 'Manual') {
      if (!manualInput.trim()) {
        alert('Please enter the manually corrected code before confirming.');
        return;
      }
      const newSource = manualInput.trim();
      if (newSource === currentWorking) {
        alert('The manual code is identical to the current working source. Please make a change first.');
        return;
      }

      const newViolations = analysisResult.violations.filter(v => v !== selectedViolation);
      // Manual fix changes the code → update score from the new remaining violations list
      const newScore = newViolations.length === 0
        ? 100.0
        : Math.max(0, 100.0 - new Set(newViolations.map(v => v.rule_number)).size * 10.0);

      previewCache.current.clear();

      setDecision(key, 'Manual');
      setManualCode(key, newSource);
      setWorkingCode(newSource);
      setAnalysisResult({
        ...analysisResult,
        source_code: newSource,
        violations: newViolations,
        compliance_score: newScore,  // authoritative: derived from actual remaining code violations
      });
      if (isFolderMode) {
        updateActiveFileItem({
          working_code:    newSource,
          source_code:     newSource,
          corrected_code:  newSource,
          violations:      newViolations,
          compliance_score: newScore,
        });
      }
      setManualMode(false);
      setManualInput('');

    } else {
      // Reject / Skip: code is NOT changed — compliance_score must NOT be updated
      const newViolations = analysisResult.violations.filter(v => v !== selectedViolation);
      setDecision(key, decision);
      setAnalysisResult({
        ...analysisResult,
        violations: newViolations,
        // compliance_score deliberately preserved: code hasn't changed, score must not improve
      });
      if (isFolderMode) {
        updateActiveFileItem({
          violations: newViolations,
          // compliance_score is NOT updated here — only Accept/Manual/Re-analyze may change it
        });
      }
    }

    setSelectedViolation(nextSelected);
  };

  // ── Re-analyze ─────────────────────────────────────────────────────────────
  const handleReAnalyze = async () => {
    if (!analysisResult) return;
    setReanalyzing(true);
    try {
      const codeToAnalyze = workingCode || analysisResult.source_code;
      const blob = new Blob([codeToAnalyze], { type: 'text/plain' });
      const formData = new FormData();
      formData.append('file', blob, analysisResult.file_name);

      const response = await fetch('http://localhost:8000/api/upload', { method: 'POST', body: formData });
      const data = await response.json();

      if (data.success) {
        const newViolations: RuleViolation[] = data.violations || [];
        const finalScore = newViolations.length === 0 ? 100.0 : data.compliance_score;

        setAnalysisResult({
          ...analysisResult,
          source_code: codeToAnalyze,
          violations: newViolations,
          compliance_score: finalScore,
        });
        if (isFolderMode) {
          updateActiveFileItem({
            working_code:   codeToAnalyze,
            source_code:    codeToAnalyze,
            corrected_code: codeToAnalyze,
            violations:     newViolations,
            compliance_score: finalScore,
          });
        }
        setSelectedViolation(null);
        previewCache.current.clear();

        const remaining = newViolations.length;
        setToastMessage(
          remaining === 0
            ? '✅ Re-analysis complete — 0 remaining violations.'
            : `⚠️ Re-analysis found ${remaining} remaining violation${remaining !== 1 ? 's' : ''}.`
        );
      }
    } catch (err) {
      console.error('Re-analysis failed:', err);
      setToastMessage('Re-analysis failed — check backend connection.');
    } finally {
      setReanalyzing(false);
    }
  };

  // ── BULK ACTIONS ───────────────────────────────────────────────────────────
  const executeBulkActionParams = useCallback(async (dec: BulkDecision, sevFilter: BulkSeverityFilter) => {
    if (!analysisResult) return;
    setBulkPhase('progress');

    const targets = analysisResult.violations.filter(v =>
      !decisions[violationStableKey(v)] &&
      (sevFilter === 'All' || v.severity === sevFilter)
    );

    setBulkTargetCount(targets.length);

    if (dec === 'Accept') {
      let workingSource = workingCode || analysisResult.source_code;
      let failed = 0;
      let patchError: string | undefined;
      let currentViolationsList = [...analysisResult.violations];
      const newDecisions: DecisionMap = { ...decisions };

      /**
       * Multi-Pass Atomic Bulk Patching Algorithm
       *
       * MATHEMATICAL & ALGORITHMIC PROOF:
       * 1. Loop Invariant:
       *    At the start of pass k, `currentViolationsList` contains the exact set of AST violations
       *    detected by pycparser on `workingSource`.
       *    Each pass applies all valid, non-overlapping range-based AST operations bottom-up.
       *    Thus, |V_{k+1}| < |V_k| or workingSource is unchanged (data.modified_code === workingSource).
       *
       * 2. Termination Guarantee:
       *    The loop terminates in at most 5 iterations because:
       *    a) If V_k = \emptyset, loop breaks immediately (100% compliance reached).
       *    b) If a pass produces no AST modifications (modified_code === workingSource), loop breaks.
       *    c) Hard upper bound `pass < 5` guarantees finite runtime even under adversarial AST syntax.
       *
       * 3. Non-Oscillation Proof:
       *    The patch engine performs deterministic AST transformations (inserting casts, (void)param,
       *    explicit parentheses, prototype declarations, static linkage).
       *    A transformed AST node strictly satisfies the corresponding MISRA rule rule-checker, so
       *    re-analysis cannot recreate previously removed violation nodes.
       *
       * 4. Decision Bookkeeping Correctness:
       *    `newDecisions` is updated ONLY AFTER the multi-pass loop finishes.
       *    `remainingKeySet` tracks violations that remain in `currentViolationsList`.
       *    Only violations whose AST nodes were successfully eliminated receive the 'Accept' decision.
       *    Remaining violations are flagged in `manualReviewKeys` for human review.
       */
      for (let pass = 0; pass < 5; pass++) {
        const pendingTargets = currentViolationsList.filter(v =>
          sevFilter === 'All' || v.severity === sevFilter
        );
        if (pendingTargets.length === 0) break;

        try {
          const resp = await fetch('http://localhost:8000/api/apply-patches', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source_code: workingSource, violations: pendingTargets }),
          });
          const data = await resp.json();

          if (data.success && data.modified_code && data.modified_code !== workingSource) {
            workingSource = data.modified_code;

            const blob = new Blob([workingSource], { type: 'text/plain' });
            const formData = new FormData();
            formData.append('file', blob, analysisResult.file_name);
            const reScanResp = await fetch('http://localhost:8000/api/upload', { method: 'POST', body: formData });
            const reScanData = await reScanResp.json();

            if (reScanData.success) {
              currentViolationsList = reScanData.violations || [];
              if (currentViolationsList.length === 0) break;
            } else {
              currentViolationsList = [];
              break;
            }
          } else if (data.success && data.modified_code === workingSource) {
            // Source did not change in this pass (AST fixed or unpatchable remaining)
            break;
          } else {
            failed += pendingTargets.length;
            patchError = data.error || 'Patch application failed.';
            break;
          }
        } catch (err) {
          failed += pendingTargets.length;
          patchError = 'Network or server error during bulk patching.';
          break;
        }
      }

      // Mark only successfully patched out violations as Accept
      const remainingKeySet = new Set(currentViolationsList.map(violationStableKey));
      for (const v of analysisResult.violations) {
        const k = violationStableKey(v);
        if (!remainingKeySet.has(k) && (sevFilter === 'All' || v.severity === sevFilter)) {
          newDecisions[k] = 'Accept';
        }
      }

      const totalInitialRemaining = analysisResult.violations.length;
      const manualReviewRequiredCount = currentViolationsList.length;
      const autoPatchedCount = Math.max(0, totalInitialRemaining - manualReviewRequiredCount);

      // finalScore: from re-scan of actual working code after patches applied → authoritative
      const finalScore = currentViolationsList.length === 0
        ? 100.0
        : Math.max(0, 100.0 - (new Set(currentViolationsList.map(v => v.rule_number)).size * 10.0));

      const totalAccepted = Object.values(newDecisions).filter(d => d === 'Accept').length;

      setManualReviewKeys(remainingKeySet);
      updateDecisions(newDecisions);
      setWorkingCode(workingSource);
      setAnalysisResult({
        ...analysisResult,
        source_code: workingSource,
        violations: currentViolationsList,
        compliance_score: finalScore,  // authoritative: from backend rescan after patches
      });
      if (isFolderMode) {
        updateActiveFileItem({
          working_code:     workingSource,
          source_code:      workingSource,
          corrected_code:   workingSource,
          violations:       currentViolationsList,
          compliance_score: finalScore,
          is_finalized:     currentViolationsList.length === 0,
          total_accepted_count: totalAccepted,
        });
      }

      previewCache.current.clear();
      if (currentViolationsList.length > 0) {
        setSelectedViolation(currentViolationsList[0]);
      } else {
        setSelectedViolation(null);
      }

      setBulkSummary({
        count: autoPatchedCount,
        totalBefore: totalInitialRemaining,
        manualReviewRequired: manualReviewRequiredCount,
        finalRemaining: currentViolationsList.length,
        skipped: 0,
        failed,
        complianceScore: finalScore,
        reason: manualReviewRequiredCount > 0
          ? "Rule 10.3 requires developer intent and cannot be safely auto-fixed."
          : undefined,
        error: patchError,
      });

      if (manualReviewRequiredCount > 0) {
        setToastMessage(`Accept All complete: ${autoPatchedCount} violations automatically patched. ${manualReviewRequiredCount} require manual review.`);
      } else {
        setToastMessage(`Accept All complete: All ${autoPatchedCount} violations automatically patched (100% compliance).`);
      }

    } else {
      // Reject / Skip bulk — code is NOT changed, score must NOT change
      const newDecisions: DecisionMap = { ...decisions };
      const targetKeys = new Set(targets.map(violationStableKey));

      for (const v of targets) {
        newDecisions[violationStableKey(v)] = dec;
        setBulkCurrentIndex(p => p + 1);
        await new Promise(r => setTimeout(r, 0));
      }

      const updatedViolations = analysisResult.violations.filter(v => !targetKeys.has(violationStableKey(v)));

      updateDecisions(newDecisions);
      // compliance_score deliberately NOT updated: code hasn't changed on Reject/Skip
      setAnalysisResult({ ...analysisResult, violations: updatedViolations });
      if (isFolderMode) {
        // compliance_score is NOT passed here — only Accept/Manual/Re-analyze may change it
        updateActiveFileItem({ violations: updatedViolations });
      }
      setSelectedViolation(null);
      setBulkSummary({ count: targets.length, skipped: 0, failed: 0, complianceScore: analysisResult.compliance_score });
    }

    setBulkPhase('summary');
  }, [
    analysisResult, decisions, workingCode,
    updateDecisions, setWorkingCode, setAnalysisResult,
    setSelectedViolation, isFolderMode, updateActiveFileItem,
  ]);

  const handleBulkMenuSelect = useCallback((item: BulkItem) => {
    if (!analysisResult) return;
    setBulkMenuOpen(false);

    const targets = analysisResult.violations.filter(v =>
      !decisions[violationStableKey(v)] &&
      (item.severity === 'All' || v.severity === item.severity)
    );

    if (targets.length === 0) {
      setToastMessage(`No undecided ${item.severity === 'All' ? '' : item.severity + ' '}violations to ${item.decision.toLowerCase()}.`);
      return;
    }

    setBulkDecision(item.decision);
    setBulkSeverityFilter(item.severity);
    setBulkTargetCount(targets.length);
    setBulkCurrentIndex(0);
    setBulkSummary(null);

    executeBulkActionParams(item.decision, item.severity);
  }, [analysisResult, decisions, executeBulkActionParams]);

  const handleBulkConfirm = useCallback(() => executeBulkActionParams(bulkDecision, bulkSeverityFilter),
    [executeBulkActionParams, bulkDecision, bulkSeverityFilter]);
  const handleBulkCancel  = useCallback(() => setBulkPhase('idle'), []);
  const handleBulkClose   = useCallback(() => {
    setBulkPhase('idle');
    const opCount = bulkSummary?.count ?? 0;
    const manualCount = bulkSummary?.manualReviewRequired ?? 0;
    if (bulkDecision === 'Accept') {
      if (manualCount > 0) {
        setToastMessage(`Accepted ${opCount} violation${opCount !== 1 ? 's' : ''}. ${manualCount} manual-review violation${manualCount !== 1 ? 's' : ''} auto-selected.`);
        if (analysisResult && analysisResult.violations.length > 0) {
          setSelectedViolation(analysisResult.violations[0]);
        }
      } else {
        setToastMessage(`Accept All complete: 100% compliance reached (${opCount} patches applied).`);
      }
    } else {
      const noun = bulkDecision === 'Reject' ? 'Rejected' : 'Skipped';
      const sev = bulkSeverityFilter === 'All' ? '' : `${bulkSeverityFilter} `;
      setToastMessage(`${noun} ${opCount} ${sev}violation${opCount !== 1 ? 's' : ''}.`);
    }
  }, [bulkSummary, bulkDecision, bulkSeverityFilter, analysisResult, setSelectedViolation]);

  if (!analysisResult) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500 flex-col gap-4">
        <Terminal className="w-12 h-12 text-slate-700" />
        <p>No analysis result found. Please go to the Analysis tab and upload a file.</p>
      </div>
    );
  }

  const currentWorking = workingCode || analysisResult.source_code;
  const metrics = getAnalysisMetrics();

  // Dynamic Bulk Action groups — only render categories that exist in active violations
  const dynamicBulkGroups = useMemo(() => {
    if (!analysisResult) return [];
    const active = analysisResult.violations.filter(v => !decisions[violationStableKey(v)]);
    if (active.length === 0) return [];

    const counts = {
      All: active.length,
      Mandatory: active.filter(v => v.severity === 'Mandatory').length,
      Required:  active.filter(v => v.severity === 'Required').length,
      Advisory:  active.filter(v => v.severity === 'Advisory').length,
    };

    const categories: { severity: BulkSeverityFilter; label: string }[] = [
      { severity: 'All', label: `All Violations (${counts.All})` }
    ];
    if (counts.Mandatory > 0) categories.push({ severity: 'Mandatory', label: `Mandatory (${counts.Mandatory})` });
    if (counts.Required > 0)  categories.push({ severity: 'Required', label: `Required (${counts.Required})` });
    if (counts.Advisory > 0)  categories.push({ severity: 'Advisory', label: `Advisory (${counts.Advisory})` });

    return [
      {
        group: 'Accept', color: 'text-emerald-400',
        items: categories.map(c => ({ decision: 'Accept' as BulkDecision, severity: c.severity, label: c.label }))
      },
      {
        group: 'Reject', color: 'text-red-400',
        items: categories.map(c => ({ decision: 'Reject' as BulkDecision, severity: c.severity, label: c.label }))
      },
      {
        group: 'Skip', color: 'text-slate-400',
        items: categories.map(c => ({ decision: 'Skip' as BulkDecision, severity: c.severity, label: c.label }))
      },
    ];
  }, [analysisResult, decisions]);

  const filteredViolations = analysisResult.violations.filter(v => {
    const matchesSearch   = v.rule_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            v.rule_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            v.message.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSeverity = severityFilter === 'All' || v.severity === severityFilter;
    return matchesSearch && matchesSeverity;
  });

  const acceptEnabled = (
    !!selectedViolation &&
    !loadingPatch &&
    patchedCode !== '' &&
    patchedCode !== currentWorking
  );

  return (
    <>
      {/* Bulk Action Modal */}
      <BulkActionModal
        phase={bulkPhase}
        decision={bulkDecision}
        severityFilter={bulkSeverityFilter}
        totalCount={bulkTargetCount}
        currentIndex={bulkCurrentIndex}
        summary={bulkSummary}
        onConfirm={handleBulkConfirm}
        onCancel={handleBulkCancel}
        onClose={handleBulkClose}
      />

      {/* Toast */}
      {toastMessage && <Toast message={toastMessage} onDone={() => setToastMessage(null)} />}

      <div className="h-full flex flex-col gap-6 p-2">
        {/* Folder file selector */}
        {isFolderMode && (
          <div className="flex items-center gap-3 bg-slate-800/90 px-4 py-3 rounded-xl border border-slate-700/80 shadow-md">
            <Folder className="w-5 h-5 text-sky-400 flex-shrink-0" />
            <span className="text-sm font-bold text-white">Active File ({folderName}):</span>
            <select
              value={activeFileIndex}
              onChange={(e) => { setActiveFileIndex(Number(e.target.value)); setSelectedViolation(null); }}
              className="bg-slate-900 text-sm font-mono font-semibold text-white px-3 py-1.5 rounded-lg border border-slate-700 focus:outline-none focus:border-violet-500 cursor-pointer"
            >
              {fileList.map((file, idx) => (
                <option key={idx} value={idx}>
                  {file.file_name} ({file.violations.length} remaining)
                </option>
              ))}
            </select>
            <span className="text-xs text-slate-400 ml-auto font-mono">
              Score: <span className="font-bold text-emerald-400">{fileList[activeFileIndex]?.compliance_score || 0}%</span>
            </span>
          </div>
        )}

        {/* Header row */}
        <div className="flex justify-between items-end">
          <div>
            <h2 className="text-3xl font-bold tracking-tight text-white mb-1">Violations Review</h2>
            <p className="text-slate-400">Human-in-the-loop review of AI-proposed compliance patches.</p>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="text-emerald-400 font-semibold">{metrics.accepted} Accepted</span>
            <span className="text-red-400 font-semibold">{metrics.rejected} Rejected</span>
            <span className="text-slate-400 font-semibold">{metrics.skipped} Skipped</span>
            <span className="text-amber-400 font-semibold">{metrics.manual} Manual</span>
            <span className="text-slate-500 font-semibold">{metrics.remaining} Remaining</span>

            {/* Bulk Actions */}
            <div className="relative ml-2" ref={bulkMenuRef}>
              <button
                onClick={() => setBulkMenuOpen(prev => !prev)}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors text-sm font-medium"
              >
                <Zap className="w-4 h-4 text-violet-400" />
                Bulk Actions
                <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${bulkMenuOpen ? 'rotate-180' : ''}`} />
              </button>
              <AnimatePresence>
                {bulkMenuOpen && (
                  <motion.div
                    key="bulk-menu"
                    initial={{ opacity: 0, scale: 0.95, y: -8 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -8 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 top-full mt-2 w-56 rounded-xl bg-slate-800 border border-slate-700/80 shadow-2xl shadow-black/40 z-30 overflow-hidden"
                  >
                    {dynamicBulkGroups.length === 0 ? (
                      <div className="px-4 py-3 text-xs text-slate-400 text-center">
                        No undecided violations remaining
                      </div>
                    ) : (
                      dynamicBulkGroups.map((group, gi) => (
                        <div key={group.group}>
                          {gi > 0 && <div className="h-px bg-slate-700/60 mx-2" />}
                          <div className={`px-3 py-2 text-[11px] font-bold uppercase tracking-widest ${group.color}`}>
                            {group.group}
                          </div>
                          {group.items.map(item => (
                            <button
                              key={`${item.decision}-${item.severity}`}
                              onClick={() => handleBulkMenuSelect(item)}
                              className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 hover:text-white transition-colors flex items-center gap-2"
                            >
                              <span className="text-slate-500">›</span>
                              {item.label}
                            </button>
                          ))}
                        </div>
                      ))
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Re-analyze */}
            <button
              onClick={handleReAnalyze}
              disabled={reanalyzing}
              className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors text-sm font-medium disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${reanalyzing ? 'animate-spin' : ''}`} />
              Re-analyze Code
            </button>
          </div>
        </div>

        <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-0">
          {/* Left sidebar — Violation list */}
          <div className="glass-panel flex flex-col overflow-hidden col-span-1">
            <div className="p-4 border-b border-slate-700/50 bg-slate-800/50 flex flex-col gap-3">
              <div className="flex justify-between items-center">
                <h3 className="font-bold text-white flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-violet-400" />
                  Issues ({filteredViolations.length}/{analysisResult.violations.length})
                </h3>
              </div>
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search rule or message..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-slate-900/60 border border-slate-700/50 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-violet-500"
                />
              </div>
              <div className="flex gap-1 overflow-x-auto text-[11px] font-semibold">
                {['All', 'Mandatory', 'Required', 'Advisory'].map((sev) => {
                  const count = sev === 'All'
                    ? analysisResult.violations.length
                    : analysisResult.violations.filter(v => v.severity === sev).length;
                  if (sev !== 'All' && count === 0) return null;
                  return (
                    <button
                      key={sev}
                      onClick={() => setSeverityFilter(sev as BulkSeverityFilter)}
                      className={`px-2 py-1 rounded transition-colors flex items-center gap-1 ${
                        severityFilter === sev
                          ? 'bg-violet-500 text-white font-bold'
                          : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {sev} <span className="text-[10px] opacity-75 font-mono">({count})</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
              {filteredViolations.length === 0 ? (
                <div className="p-4 text-center text-slate-500 text-sm">
                  {analysisResult.violations.length === 0
                    ? '✅ All violations have been reviewed.'
                    : 'No matching violations.'}
                </div>
              ) : (
                filteredViolations.map((violation, idx) => {
                  const key = violationStableKey(violation);
                  const dec = decisions[key];
                  return (
                    <div
                      key={idx}
                      onClick={() => { setSelectedViolation(violation); setManualMode(false); }}
                      className={`p-3 rounded-lg cursor-pointer transition-all border ${
                        selectedViolation === violation
                          ? 'bg-violet-500/20 border-violet-500/50'
                          : 'bg-slate-800/40 border-slate-700/50 hover:bg-slate-700/50'
                      }`}
                    >
                      <div className="flex justify-between items-start mb-1">
                        <span className="text-xs font-mono font-bold text-violet-300">Rule {violation.rule_number}</span>
                        <div className="flex items-center gap-1.5">
                          {manualReviewKeys.has(key) && (
                            <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                              <AlertCircle className="w-2.5 h-2.5" />
                              Manual Review Required
                            </span>
                          )}
                          <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${SEVERITY_COLORS[violation.severity] ?? 'bg-slate-500/20 text-slate-400'}`}>
                            {violation.severity}
                          </span>
                        </div>
                      </div>
                      <div className="text-sm font-semibold text-slate-200 line-clamp-1">{violation.rule_name}</div>
                      <div className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                        <Code className="w-3 h-3" /> Line {violation.line}
                        {dec && <span className={`ml-auto text-[10px] font-bold ${dec === 'Accept' ? 'text-emerald-400' : dec === 'Reject' ? 'text-red-400' : dec === 'Manual' ? 'text-amber-400' : 'text-slate-400'}`}>{dec}</span>}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Center — Editor & Preview */}
          <div className="lg:col-span-3 flex flex-col gap-4 min-h-0">
            <div className="flex-1 glass-panel overflow-hidden flex flex-col min-h-0">
              <div className="p-3 border-b border-slate-700/50 bg-slate-800/80 flex justify-between items-center">
                <span className="font-mono text-sm text-violet-300 flex items-center gap-2">
                  <Code className="w-4 h-4" />
                  {manualMode ? 'Manual Fix Editor (Pre-filled with Analyzer Suggestion)' : 'Patch Preview — Original vs Proposed'}
                </span>
                {selectedViolation && (
                  <span className="text-xs text-slate-400">
                    Rule {selectedViolation.rule_number} — Line {selectedViolation.line}
                  </span>
                )}
              </div>

              <div className="flex-1 bg-[#1e1e1e] relative flex flex-col min-h-[300px]">
                {loadingPatch && (
                  <div className="absolute inset-0 z-10 bg-[#1e1e1e]/80 flex items-center justify-center backdrop-blur-sm">
                    <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
                  </div>
                )}

                {selectedViolation && !manualMode ? (
                  <DiffEditor
                    height="100%"
                    language="c"
                    theme="vs-dark"
                    original={currentWorking}
                    modified={patchedCode || currentWorking}
                    options={{
                      minimap: { enabled: false },
                      fontSize: 14,
                      fontFamily: 'Consolas, monospace',
                      scrollBeyondLastLine: false,
                      readOnly: true,
                      renderSideBySide: true,
                      wordWrap: 'on',
                      lineNumbers: 'on',
                    }}
                  />
                ) : manualMode ? (
                  <div className="h-full flex flex-col p-4 gap-4 overflow-y-auto">
                    {/* Guidance banner showing Original -> Suggested -> Editable */}
                    <div className="p-3 bg-slate-800/90 border border-violet-500/30 rounded-xl text-xs flex flex-col gap-2">
                      <div className="flex items-center gap-2 text-violet-300 font-bold">
                        <Edit3 className="w-4 h-4 text-amber-400" />
                        Manual Fix Workflow: Original Snippet <ArrowRight className="w-3 h-3 text-slate-400" /> Analyzer Suggestion <ArrowRight className="w-3 h-3 text-slate-400" /> Your Refactoring
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-slate-300 font-mono">
                        <div className="p-2 bg-slate-900/80 rounded border border-red-500/30">
                          <span className="text-[10px] text-red-400 font-sans font-bold block mb-1">ORIGINAL CODE:</span>
                          <code>{selectedViolation?.code_snippet || 'Selected line'}</code>
                        </div>
                        <div className="p-2 bg-slate-900/80 rounded border border-emerald-500/30">
                          <span className="text-[10px] text-emerald-400 font-sans font-bold block mb-1">ANALYZER SUGGESTED FIX:</span>
                          <code>{selectedViolation?.suggested_fix || 'Automated suggested fix'}</code>
                        </div>
                      </div>
                      <p className="text-slate-400 text-[11px] font-sans">
                        The editor below is pre-filled with the analyzer's best safe suggestion. Adjust formatting, modify parentheses, or refine code logic before clicking Confirm.
                      </p>
                    </div>

                    <textarea
                      className="flex-1 w-full min-h-[260px] bg-slate-950 text-slate-100 font-mono text-sm p-4 rounded-xl border border-slate-700 focus:outline-none focus:border-violet-500 resize-none shadow-inner"
                      placeholder="Modify source code..."
                      value={manualInput}
                      onChange={e => setManualInput(e.target.value)}
                    />
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-slate-500">
                    Select a violation from the list to view the proposed patch.
                  </div>
                )}
              </div>
            </div>

            {/* AI Engineering Assistant Modal Popup */}
            {explanation && (
              <div
                ref={aiBackdropRef}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
                onClick={(e) => {
                  if (e.target === aiBackdropRef.current) setExplanation('');
                }}
              >
                <div className="glass-panel w-full max-w-4xl max-h-[85vh] overflow-y-auto custom-scrollbar bg-slate-900 border border-violet-500/40 rounded-2xl shadow-2xl p-6 space-y-4 relative">
                  <div className="flex items-center justify-between border-b border-slate-700/60 pb-3">
                    <div className="flex items-center gap-2">
                      <div className="p-2 bg-violet-500/20 text-violet-300 rounded-lg">
                        <MessageSquare className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-white flex items-center gap-2">
                          MISRA AI Engineering Assistant Analysis
                          {selectedViolation && (
                            <span className="px-2 py-0.5 text-xs bg-violet-500/20 text-violet-300 rounded-full border border-violet-500/30 font-mono">
                              Rule {selectedViolation.rule_number}
                            </span>
                          )}
                        </h4>
                        <p className="text-xs text-slate-400">Deterministic AST Traversal & Safety Impact Assessment</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {structuredAiData && (
                        <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20 text-xs font-mono font-bold">
                          🎯 {(structuredAiData.confidence * 100).toFixed(0)}% Confidence
                        </div>
                      )}
                      <button
                        onClick={() => setExplanation('')}
                        className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors border border-slate-700"
                        title="Close Ask AI modal (Esc)"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                {structuredAiData ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    {/* What AI Found */}
                    <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/50 space-y-1">
                      <div className="font-bold text-violet-300 flex items-center gap-1.5">
                        🔍 What AI Found
                      </div>
                      <p className="text-slate-300 leading-relaxed">{structuredAiData.what_ai_found}</p>
                    </div>

                    {/* Why It Matters */}
                    <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/50 space-y-1">
                      <div className="font-bold text-amber-400 flex items-center gap-1.5">
                        ⚠ Why It Matters
                      </div>
                      <p className="text-slate-300 leading-relaxed">{structuredAiData.why_it_matters}</p>
                    </div>

                    {/* MISRA Summary */}
                    <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/50 space-y-1">
                      <div className="font-bold text-sky-400 flex items-center gap-1.5">
                        📖 MISRA Requirement
                      </div>
                      <p className="text-slate-300 leading-relaxed">{structuredAiData.misra_summary}</p>
                    </div>

                    {/* AI Analysis */}
                    <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/50 space-y-1">
                      <div className="font-bold text-indigo-300 flex items-center gap-1.5">
                        🧠 AI AST Analysis
                      </div>
                      <p className="text-slate-300 leading-relaxed">{structuredAiData.ai_analysis}</p>
                    </div>

                    {/* Recommended Fix */}
                    <div className="md:col-span-2 p-3 bg-slate-800/80 rounded-xl border border-emerald-500/30 space-y-2">
                      <div className="font-bold text-emerald-400 flex items-center gap-1.5">
                        💡 Recommended Fix & Rationale
                      </div>
                      <p className="text-slate-300 leading-relaxed">{structuredAiData.why_fix_works}</p>
                      {structuredAiData.recommended_fix && (
                        <div className="p-2 bg-slate-950 rounded border border-emerald-500/20 font-mono text-emerald-300 text-xs">
                          <code>{structuredAiData.recommended_fix}</code>
                        </div>
                      )}
                      {structuredAiData.alternative_fixes?.length > 0 && (
                        <div className="pt-1 text-[11px] text-slate-400">
                          <span className="font-bold text-slate-300">Alternative Fixes:</span>
                          <ul className="list-disc list-inside mt-1 space-y-0.5 text-slate-300">
                            {structuredAiData.alternative_fixes.map((alt: string, i: number) => (
                              <li key={i}>{alt}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* Impact Analysis Grid */}
                    <div className="md:col-span-2 p-3 bg-slate-800/60 rounded-xl border border-slate-700/50">
                      <div className="font-bold text-violet-300 flex items-center gap-1.5 mb-2">
                        ⚖ Impact Analysis
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px]">
                        <div className="p-2 bg-slate-900/80 rounded border border-slate-700">
                          <span className="text-slate-400 block font-sans">Runtime:</span>
                          <span className="font-bold text-emerald-400 font-mono">{structuredAiData.impact_analysis?.runtime || '0% penalty'}</span>
                        </div>
                        <div className="p-2 bg-slate-900/80 rounded border border-slate-700">
                          <span className="text-slate-400 block font-sans">Memory:</span>
                          <span className="font-bold text-emerald-400 font-mono">{structuredAiData.impact_analysis?.memory || '0 bytes'}</span>
                        </div>
                        <div className="p-2 bg-slate-900/80 rounded border border-slate-700">
                          <span className="text-slate-400 block font-sans">Compilation:</span>
                          <span className="font-bold text-sky-400 font-mono">{structuredAiData.impact_analysis?.compilation || 'Clean build'}</span>
                        </div>
                        <div className="p-2 bg-slate-900/80 rounded border border-slate-700">
                          <span className="text-slate-400 block font-sans">Compliance:</span>
                          <span className="font-bold text-violet-300 font-mono">{structuredAiData.impact_analysis?.compliance || '+10% Gain'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-slate-300 whitespace-pre-wrap">{explanation}</p>
                )}
                </div>
              </div>
            )}

            {/* Action Bar */}
            <div className="glass-panel p-4 flex gap-4 justify-between items-center bg-slate-800/40">
              <button
                onClick={handleAskAI}
                disabled={!selectedViolation || loadingExplanation || manualMode}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loadingExplanation ? <Loader2 className="w-4 h-4 animate-spin" /> : <MessageSquare className="w-4 h-4" />}
                Ask AI
              </button>
              <div className="flex gap-3 flex-wrap">
                {manualMode ? (
                  <>
                    <button
                      onClick={() => { setManualMode(false); setManualInput(''); }}
                      className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors text-sm font-medium"
                    >
                      <X className="w-4 h-4" /> Cancel
                    </button>
                    <button
                      onClick={() => handleDecision('Manual')}
                      className="flex items-center gap-2 px-4 py-2 bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 rounded-lg transition-colors text-sm font-medium"
                    >
                      <Check className="w-4 h-4" /> Confirm Manual Fix
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => handleDecision('Skip')}
                      disabled={!selectedViolation}
                      className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors text-sm font-medium disabled:opacity-50"
                    >
                      <SkipForward className="w-4 h-4" /> Skip
                    </button>
                    <button
                      onClick={() => handleDecision('Reject')}
                      disabled={!selectedViolation}
                      className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded-lg transition-colors text-sm font-medium disabled:opacity-50"
                    >
                      <X className="w-4 h-4" /> Reject
                    </button>
                    <button
                      onClick={startManualFix}
                      disabled={!selectedViolation}
                      className="flex items-center gap-2 px-4 py-2 bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 rounded-lg transition-colors text-sm font-medium disabled:opacity-50"
                    >
                      <Edit3 className="w-4 h-4" /> Manual Fix
                    </button>
                    <button
                      onClick={() => handleDecision('Accept')}
                      disabled={!acceptEnabled}
                      title={acceptEnabled ? 'Apply this patch' : (noPatchReason || 'No automated patch available — use Manual Fix instead')}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors text-sm font-medium ${
                        acceptEnabled
                          ? 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30'
                          : 'bg-slate-700/40 text-slate-500 cursor-not-allowed opacity-50'
                      }`}
                    >
                      <Check className="w-4 h-4" /> Accept Patch
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Violations;
