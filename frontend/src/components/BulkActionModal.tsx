import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, X, AlertTriangle, Loader2, SkipForward, ShieldOff, AlertCircle } from 'lucide-react';

export type BulkDecision = 'Accept' | 'Reject' | 'Skip';
export type BulkSeverityFilter = 'All' | 'Mandatory' | 'Required' | 'Advisory';

export interface BulkSummary {
  /** Number of violations processed / automatically patched in this bulk operation */
  count: number;
  /** Total remaining violations before operation */
  totalBefore?: number;
  /** Violations requiring manual fixes (e.g. Rule 10.3) */
  manualReviewRequired?: number;
  /** Final remaining violations after operation */
  finalRemaining?: number;
  skipped: number;
  failed: number;
  complianceScore: number;
  reason?: string;
  error?: string;
}

export type BulkPhase = 'confirm' | 'progress' | 'summary' | 'idle';

interface Props {
  phase: BulkPhase;
  decision: BulkDecision;
  severityFilter: BulkSeverityFilter;
  totalCount: number;
  currentIndex: number;
  summary: BulkSummary | null;
  onConfirm: () => void;
  onCancel: () => void;
  onClose: () => void;
}

const DECISION_COLOR: Record<BulkDecision, string> = {
  Accept: 'text-emerald-400',
  Reject: 'text-red-400',
  Skip:   'text-slate-400',
};

const DECISION_ICON: Record<BulkDecision, React.FC<{ className?: string }>> = {
  Accept: CheckCircle2,
  Reject: ShieldOff,
  Skip:   SkipForward,
};

const DECISION_BG: Record<BulkDecision, string> = {
  Accept: 'bg-emerald-500/10 border-emerald-500/30',
  Reject: 'bg-red-500/10 border-red-500/30',
  Skip:   'bg-slate-700/40 border-slate-600/30',
};

const PROGRESS_BAR: Record<BulkDecision, string> = {
  Accept: 'bg-emerald-500',
  Reject: 'bg-red-500',
  Skip:   'bg-slate-400',
};

const BulkActionModal = ({
  phase,
  decision,
  severityFilter,
  totalCount,
  currentIndex,
  summary,
  onConfirm,
  onCancel,
  onClose,
}: Props) => {
  const overlayRef = useRef<HTMLDivElement>(null);
  const DecisionIcon = DECISION_ICON[decision];
  const progressPct = totalCount > 0 ? Math.round((currentIndex / totalCount) * 100) : 0;

  // Close on Escape during confirm phase only
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && phase === 'confirm') onCancel();
      if (e.key === 'Escape' && phase === 'summary') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [phase, onCancel, onClose]);

  if (phase === 'idle') return null;

  const severityLabel = severityFilter === 'All' ? 'All' : severityFilter;
  const actionLabel = `${decision} all ${severityLabel} violations`;

  return (
    <AnimatePresence>
      <motion.div
        ref={overlayRef}
        key="bulk-modal-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
        onClick={(e) => {
          if (e.target === overlayRef.current && phase === 'confirm') onCancel();
          if (e.target === overlayRef.current && phase === 'summary') onClose();
        }}
      >
        <motion.div
          key="bulk-modal-card"
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="glass-panel w-full max-w-lg bg-slate-900 border border-slate-700/60 rounded-2xl shadow-2xl overflow-hidden relative"
        >
          {/* ── CONFIRMATION PHASE ── */}
          {phase === 'confirm' && (
            <>
              <div className="p-6 border-b border-slate-700/50 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl border ${DECISION_BG[decision]}`}>
                    <DecisionIcon className={`w-6 h-6 ${DECISION_COLOR[decision]}`} />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white capitalize">Bulk {decision} Action</h3>
                    <p className="text-xs text-slate-400">Targeting {totalCount} violation{totalCount !== 1 ? 's' : ''}</p>
                  </div>
                </div>
                <button
                  onClick={onCancel}
                  className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="p-6 space-y-4">
                <p className="text-sm text-slate-300 leading-relaxed">
                  Are you sure you want to <strong className={DECISION_COLOR[decision]}>{decision.toLowerCase()}</strong> all{' '}
                  <span className="font-semibold text-white">{totalCount}</span> remaining {severityLabel !== 'All' ? severityLabel : ''} violation{totalCount !== 1 ? 's' : ''}?
                </p>

                {decision === 'Accept' && (
                  <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs text-emerald-300 flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                    <span>
                      Automated patches will be applied sequentially from bottom-to-top. Any violations requiring manual review (e.g. Rule 10.3) will be flagged in the final summary.
                    </span>
                  </div>
                )}

                <div className="flex gap-3 pt-2">
                  <button
                    onClick={onCancel}
                    className="flex-1 py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-medium text-sm transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={onConfirm}
                    className={`flex-1 py-2.5 px-4 font-semibold text-sm text-white rounded-xl transition-all shadow-lg ${
                      decision === 'Accept'
                        ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/20'
                        : decision === 'Reject'
                        ? 'bg-red-600 hover:bg-red-500 shadow-red-600/20'
                        : 'bg-slate-600 hover:bg-slate-500'
                    }`}
                  >
                    Confirm {decision} All
                  </button>
                </div>
              </div>
            </>
          )}

          {/* ── PROGRESS PHASE ── */}
          {phase === 'progress' && (
            <div className="p-8 flex flex-col items-center justify-center text-center space-y-6">
              <div className="relative">
                <Loader2 className={`w-12 h-12 animate-spin ${DECISION_COLOR[decision]}`} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white mb-1">Applying Bulk {decision}</h3>
                <p className="text-xs font-mono text-slate-400">
                  Processing violation {currentIndex} of {totalCount}...
                </p>
              </div>

              {/* Progress bar */}
              <div className="w-full">
                <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden border border-slate-700">
                  <motion.div
                    className={`h-full rounded-full ${PROGRESS_BAR[decision]}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${progressPct}%` }}
                    transition={{ duration: 0.2 }}
                  />
                </div>
                <p className="text-xs text-slate-500 text-center mt-2 font-mono">{progressPct}% complete</p>
              </div>
            </div>
          )}

          {/* ── SUMMARY PHASE ── */}
          {phase === 'summary' && summary && (
            <>
              <div className="p-6 border-b border-slate-700/50 bg-slate-800/40 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">Bulk Action Summary</h3>
                    <p className="text-xs text-slate-400 capitalize">{actionLabel} completed</p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="p-6 space-y-4">
                {summary.error && (
                  <div className="flex items-start gap-3 p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-xs">
                    <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-red-300">Operation Error</p>
                      <p className="text-red-200/80 mt-0.5 font-mono">{summary.error}</p>
                    </div>
                  </div>
                )}

                {decision === 'Accept' ? (
                  <div className="space-y-3">
                    {/* Summary Metrics Grid */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/50 text-center font-mono">
                        <p className="text-xs text-slate-400 mb-0.5">Total Initial Remaining</p>
                        <p className="text-xl font-bold text-white">{summary.totalBefore ?? (summary.count + summary.failed)}</p>
                      </div>
                      <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center font-mono">
                        <p className="text-xs text-slate-400 mb-0.5">Automatically Patched</p>
                        <p className="text-xl font-bold text-emerald-400">{summary.count}</p>
                      </div>
                      <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-center font-mono">
                        <p className="text-xs text-slate-400 mb-0.5">Manual Review Required</p>
                        <p className="text-xl font-bold text-amber-400">{summary.manualReviewRequired ?? 0}</p>
                      </div>
                      <div className="p-3.5 rounded-xl bg-sky-500/10 border border-sky-500/20 text-center font-mono">
                        <p className="text-xs text-slate-400 mb-0.5">Final Remaining</p>
                        <p className="text-xl font-bold text-sky-300">{summary.finalRemaining ?? 0}</p>
                      </div>
                    </div>

                    {/* Compliance Score Indicator */}
                    <div className="p-3 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-between text-xs font-mono">
                      <span className="text-slate-300">Updated Compliance Score:</span>
                      <span className="text-base font-bold text-violet-400">{summary.complianceScore.toFixed(1)}%</span>
                    </div>

                    {/* Explanation Box if Manual Review Required */}
                    {Boolean(summary.manualReviewRequired && summary.manualReviewRequired > 0) && (
                      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300 space-y-2">
                        <div className="font-bold text-sm text-amber-400 flex items-center gap-1.5">
                          <AlertCircle className="w-4 h-4 flex-shrink-0" />
                          <span>Why are {summary.manualReviewRequired} violation{summary.manualReviewRequired !== 1 ? 's' : ''} still remaining?</span>
                        </div>
                        <p className="leading-relaxed text-amber-200/90">
                          These violations require developer intent. MISRA Rule 10.3 cannot be safely auto-fixed without developer input because inserting an explicit cast may alter program runtime behaviour. Manual review is required.
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-3 font-mono">
                    <div className="col-span-2 p-4 rounded-xl bg-slate-800/60 border border-slate-700/50 text-center">
                      <p className="text-xs text-slate-400 mb-1">{decision}ed Count</p>
                      <p className={`text-3xl font-bold ${DECISION_COLOR[decision]}`}>{summary.count}</p>
                    </div>
                    <div className="p-3.5 rounded-xl bg-violet-500/10 border border-violet-500/20 text-center">
                      <p className="text-xs text-slate-400 mb-1">Compliance Score</p>
                      <p className="text-xl font-bold text-violet-400">{summary.complianceScore.toFixed(1)}%</p>
                    </div>
                    <div className="p-3.5 rounded-xl bg-sky-500/10 border border-sky-500/20 text-center">
                      <p className="text-xs text-slate-400 mb-1">Remaining</p>
                      <p className="text-xl font-bold text-sky-300">{summary.finalRemaining ?? summary.skipped}</p>
                    </div>
                  </div>
                )}

                <button
                  onClick={onClose}
                  className="w-full py-3 bg-violet-600 hover:bg-violet-500 text-white rounded-xl font-semibold text-sm transition-colors shadow-lg shadow-violet-500/20 flex items-center justify-center gap-2"
                >
                  {decision === 'Accept' && summary.manualReviewRequired && summary.manualReviewRequired > 0
                    ? 'Review Manual Violations →'
                    : 'Done'}
                </button>
              </div>
            </>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default BulkActionModal;
