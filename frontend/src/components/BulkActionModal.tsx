import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, X, AlertTriangle, Loader2, SkipForward, ShieldOff } from 'lucide-react';

export type BulkDecision = 'Accept' | 'Reject' | 'Skip';
export type BulkSeverityFilter = 'All' | 'Mandatory' | 'Required' | 'Advisory';

export interface BulkSummary {
  accepted: number;
  skipped: number;
  failed: number;
  complianceScore: number;
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
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        onClick={(e) => {
          if (e.target === overlayRef.current && phase === 'confirm') onCancel();
          if (e.target === overlayRef.current && phase === 'summary') onClose();
        }}
      >
        <motion.div
          key="bulk-modal-card"
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          transition={{ type: 'spring', bounce: 0.3, duration: 0.5 }}
          className="w-full max-w-md mx-4 rounded-2xl bg-slate-800 border border-slate-700/80 shadow-2xl shadow-black/40 overflow-hidden"
        >
          {/* ── CONFIRMATION PHASE ── */}
          {phase === 'confirm' && (
            <>
              <div className={`p-6 border-b border-slate-700/50 flex items-center gap-4 ${DECISION_BG[decision]}`}>
                <div className={`w-12 h-12 rounded-xl ${DECISION_BG[decision]} border flex items-center justify-center flex-shrink-0`}>
                  <DecisionIcon className={`w-6 h-6 ${DECISION_COLOR[decision]}`} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white capitalize">{actionLabel}?</h3>
                  <p className="text-sm text-slate-400 mt-0.5">This action will process {totalCount} violation{totalCount !== 1 ? 's' : ''}.</p>
                </div>
              </div>

              <div className="p-6">
                <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 mb-6">
                  <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-amber-200">
                    {decision === 'Accept'
                      ? `${totalCount} patch${totalCount !== 1 ? 'es' : ''} will be applied to the working code. This cannot be undone without re-uploading.`
                      : `Decision will be recorded for ${totalCount} violation${totalCount !== 1 ? 's' : ''}. The source code will not be changed.`}
                  </p>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={onCancel}
                    className="flex-1 px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={onConfirm}
                    className={`flex-1 px-4 py-3 rounded-xl font-semibold transition-colors flex items-center justify-center gap-2 ${
                      decision === 'Accept'
                        ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                        : decision === 'Reject'
                        ? 'bg-red-600 hover:bg-red-500 text-white'
                        : 'bg-slate-600 hover:bg-slate-500 text-white'
                    }`}
                  >
                    <DecisionIcon className="w-4 h-4" />
                    Proceed
                  </button>
                </div>
              </div>
            </>
          )}

          {/* ── PROGRESS PHASE ── */}
          {phase === 'progress' && (
            <div className="p-8 flex flex-col items-center gap-6">
              <div className="w-16 h-16 rounded-2xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
              </div>
              <div className="text-center">
                <h3 className="text-xl font-bold text-white mb-1">
                  {decision === 'Accept' ? 'Applying fixes…' : decision === 'Reject' ? 'Recording rejections…' : 'Marking as skipped…'}
                </h3>
                <p className={`text-3xl font-mono font-bold mt-3 ${DECISION_COLOR[decision]}`}>
                  {currentIndex} <span className="text-slate-500 text-xl">/ {totalCount}</span>
                </p>
              </div>

              {/* Progress bar */}
              <div className="w-full">
                <div className="w-full h-2.5 bg-slate-700 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full ${PROGRESS_BAR[decision]}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${progressPct}%` }}
                    transition={{ duration: 0.2 }}
                  />
                </div>
                <p className="text-xs text-slate-500 text-center mt-2">{progressPct}% complete</p>
              </div>
            </div>
          )}

          {/* ── SUMMARY PHASE ── */}
          {phase === 'summary' && summary && (
            <>
              <div className="p-6 border-b border-slate-700/50 bg-emerald-500/5 flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="w-7 h-7 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Bulk Operation Complete</h3>
                  <p className="text-sm text-slate-400 mt-0.5 capitalize">{actionLabel} — finished</p>
                </div>
              </div>

              <div className="p-6">
                {summary.error && (
                  <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 mb-6">
                    <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-semibold text-red-300">Code generation failed / rejected</p>
                      <p className="text-xs text-red-200/80 mt-1 font-mono">{summary.error}</p>
                    </div>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  {decision === 'Accept' && (
                    <div className="col-span-2 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                      <p className="text-sm text-slate-400 mb-1">Accepted</p>
                      <p className="text-3xl font-bold text-emerald-400">{summary.accepted}</p>
                    </div>
                  )}
                  {decision === 'Reject' && (
                    <div className="col-span-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-center">
                      <p className="text-sm text-slate-400 mb-1">Rejected</p>
                      <p className="text-3xl font-bold text-red-400">{summary.accepted}</p>
                    </div>
                  )}
                  {decision === 'Skip' && (
                    <div className="col-span-2 p-4 rounded-xl bg-slate-700/40 border border-slate-600/40 text-center">
                      <p className="text-sm text-slate-400 mb-1">Skipped</p>
                      <p className="text-3xl font-bold text-slate-300">{summary.accepted}</p>
                    </div>
                  )}

                  <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-center">
                    <p className="text-sm text-slate-400 mb-1">
                      {decision === 'Accept' ? 'Skipped (patch failed)' : 'Already Decided'}
                    </p>
                    <p className="text-2xl font-bold text-amber-400">{summary.failed}</p>
                  </div>

                  <div className="p-4 rounded-xl bg-violet-500/10 border border-violet-500/20 text-center">
                    <p className="text-sm text-slate-400 mb-1">Compliance Score</p>
                    <p className="text-2xl font-bold text-violet-400">{summary.complianceScore.toFixed(1)}%</p>
                  </div>
                </div>

                <button
                  onClick={onClose}
                  className="w-full px-4 py-3 bg-violet-600 hover:bg-violet-500 text-white rounded-xl font-semibold transition-colors"
                >
                  Done
                </button>
              </div>
            </>
          )}

          {/* Close button for summary */}
          {phase === 'summary' && (
            <button
              onClick={onClose}
              className="absolute top-4 right-4 w-8 h-8 rounded-lg bg-slate-700 hover:bg-slate-600 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default BulkActionModal;
