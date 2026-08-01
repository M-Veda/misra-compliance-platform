import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Palette, 
  Sliders, 
  Bot, 
  FileCode, 
  FileText, 
  RotateCcw, 
  Check, 
  AlertTriangle,
  Moon,
  Sun
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';

const Settings = () => {
  const { settings, updateSettings, resetSettings } = useAppContext();
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);

  const handleReset = () => {
    resetSettings();
    setShowResetModal(false);
    setResetSuccess(true);
    setTimeout(() => setResetSuccess(false), 3000);
  };

  return (
    <div className="h-full flex flex-col gap-6 p-2 max-w-5xl mx-auto custom-scrollbar">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-white mb-1">Settings</h2>
        <p className="text-slate-400">Configure editor, review workflow, AI, and report preferences.</p>
      </div>

      {resetSuccess && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-emerald-500/20 border border-emerald-500/50 rounded-xl text-emerald-400 flex items-center gap-3"
        >
          <Check className="w-5 h-5 flex-shrink-0" />
          Settings restored to default values.
        </motion.div>
      )}

      <div className="space-y-6 pb-12">
        {/* ── SECTION 1: APPEARANCE ── */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-6"
        >
          <div className="flex items-center gap-3 border-b border-slate-700/50 pb-4 mb-6">
            <Palette className="w-5 h-5 text-violet-400" />
            <h3 className="text-lg font-bold text-white">Appearance & Editor</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Theme */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-semibold text-slate-200">Theme</label>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => updateSettings({ theme: 'dark' })}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl border transition-all ${
                    settings.theme === 'dark'
                      ? 'bg-violet-600/30 border-violet-500 text-white font-bold shadow-lg shadow-violet-500/10'
                      : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:text-white'
                  }`}
                >
                  <Moon className="w-4 h-4" /> Dark (Default)
                </button>
                <button
                  type="button"
                  onClick={() => updateSettings({ theme: 'light' })}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl border transition-all ${
                    settings.theme === 'light'
                      ? 'bg-violet-600/30 border-violet-500 text-white font-bold shadow-lg shadow-violet-500/10'
                      : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:text-white'
                  }`}
                >
                  <Sun className="w-4 h-4" /> Light
                </button>
              </div>
            </div>

            {/* Font Size Slider */}
            <div className="flex flex-col gap-2">
              <div className="flex justify-between items-center">
                <label className="text-sm font-semibold text-slate-200">Editor Font Size</label>
                <span className="text-xs font-mono font-bold text-violet-300">{settings.fontSize} px</span>
              </div>
              <input
                type="range"
                min={12}
                max={24}
                step={1}
                value={settings.fontSize}
                onChange={(e) => updateSettings({ fontSize: Number(e.target.value) })}
                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-violet-500 mt-2"
              />
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>12px</span>
                <span>18px</span>
                <span>24px</span>
              </div>
            </div>

            {/* Show Line Numbers */}
            <div className="flex justify-between items-center p-3 rounded-xl bg-slate-800/40 border border-slate-700/50">
              <div>
                <div className="text-sm font-semibold text-slate-200">Show Line Numbers</div>
                <div className="text-xs text-slate-400">Display line numbers in all code editors</div>
              </div>
              <button
                type="button"
                onClick={() => updateSettings({ showLineNumbers: !settings.showLineNumbers })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.showLineNumbers ? 'bg-violet-600' : 'bg-slate-700'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.showLineNumbers ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Word Wrap */}
            <div className="flex justify-between items-center p-3 rounded-xl bg-slate-800/40 border border-slate-700/50">
              <div>
                <div className="text-sm font-semibold text-slate-200">Word Wrap</div>
                <div className="text-xs text-slate-400">Wrap long lines in Monaco editors</div>
              </div>
              <button
                type="button"
                onClick={() => updateSettings({ wordWrap: !settings.wordWrap })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.wordWrap ? 'bg-violet-600' : 'bg-slate-700'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.wordWrap ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </motion.div>

        {/* ── SECTION 2: REVIEW PREFERENCES ── */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="glass-panel p-6"
        >
          <div className="flex items-center gap-3 border-b border-slate-700/50 pb-4 mb-6">
            <Sliders className="w-5 h-5 text-violet-400" />
            <h3 className="text-lg font-bold text-white">Review Preferences</h3>
          </div>

          <div className="space-y-4">
            {/* Confirm before Bulk Actions */}
            <div className="flex justify-between items-center p-4 rounded-xl bg-slate-800/40 border border-slate-700/50">
              <div>
                <div className="text-sm font-semibold text-slate-200">Confirm before Bulk Actions</div>
                <div className="text-xs text-slate-400">Show confirmation modal before applying bulk decisions</div>
              </div>
              <button
                type="button"
                onClick={() => updateSettings({ confirmBulkActions: !settings.confirmBulkActions })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.confirmBulkActions ? 'bg-violet-600' : 'bg-slate-700'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.confirmBulkActions ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Confirm before Re-analysis */}
            <div className="flex justify-between items-center p-4 rounded-xl bg-slate-800/40 border border-slate-700/50">
              <div>
                <div className="text-sm font-semibold text-slate-200">Confirm before Re-analysis</div>
                <div className="text-xs text-slate-400">Require explicit confirmation before running code re-analysis</div>
              </div>
              <button
                type="button"
                onClick={() => updateSettings({ confirmReanalysis: !settings.confirmReanalysis })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.confirmReanalysis ? 'bg-violet-600' : 'bg-slate-700'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.confirmReanalysis ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Auto Scroll Next Violation */}
            <div className="flex justify-between items-center p-4 rounded-xl bg-slate-800/40 border border-slate-700/50">
              <div>
                <div className="text-sm font-semibold text-slate-200">Automatically Scroll to Next Violation after Accept</div>
                <div className="text-xs text-slate-400">Advance to next pending violation when a decision is made</div>
              </div>
              <button
                type="button"
                onClick={() => updateSettings({ autoScrollNextViolation: !settings.autoScrollNextViolation })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.autoScrollNextViolation ? 'bg-violet-600' : 'bg-slate-700'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.autoScrollNextViolation ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </motion.div>

        {/* ── SECTION 3: AI ── */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-panel p-6"
        >
          <div className="flex items-center gap-3 border-b border-slate-700/50 pb-4 mb-6">
            <Bot className="w-5 h-5 text-violet-400" />
            <h3 className="text-lg font-bold text-white">AI Assistant</h3>
          </div>

          <div className="flex justify-between items-center p-4 rounded-xl bg-slate-800/40 border border-slate-700/50">
            <div>
              <div className="text-sm font-semibold text-slate-200">Enable AI Explanations</div>
              <div className="text-xs text-slate-400">Allow "Ask AI" requests for detailed rule violation explanations</div>
            </div>
            <button
              type="button"
              onClick={() => updateSettings({ enableAIExplanations: !settings.enableAIExplanations })}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.enableAIExplanations ? 'bg-violet-600' : 'bg-slate-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.enableAIExplanations ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </motion.div>

        {/* ── SECTION 4: GENERATED CODE ── */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="glass-panel p-6"
        >
          <div className="flex items-center gap-3 border-b border-slate-700/50 pb-4 mb-6">
            <FileCode className="w-5 h-5 text-violet-400" />
            <h3 className="text-lg font-bold text-white">Generated Code Settings</h3>
          </div>

          <div className="flex flex-col gap-3">
            <label className="text-sm font-semibold text-slate-200">
              Default Download Filename Suffix
            </label>
            <p className="text-xs text-slate-400">
              Appended to original filename when downloading corrected C files (e.g. <span className="font-mono text-violet-300">sample{settings.filenameSuffix || '_fixed'}.c</span>)
            </p>
            <div className="flex gap-3 max-w-md">
              <input
                type="text"
                value={settings.filenameSuffix}
                onChange={(e) => updateSettings({ filenameSuffix: e.target.value })}
                placeholder="_fixed"
                className="flex-1 bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 font-mono focus:outline-none focus:border-violet-500"
              />
            </div>
          </div>
        </motion.div>

        {/* ── SECTION 5: REPORTS ── */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-panel p-6"
        >
          <div className="flex items-center gap-3 border-b border-slate-700/50 pb-4 mb-6">
            <FileText className="w-5 h-5 text-violet-400" />
            <h3 className="text-lg font-bold text-white">Compliance Reports</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex flex-col gap-2">
              <label className="text-sm font-semibold text-slate-200">Default Report Format</label>
              <div className="flex gap-2">
                {(['pdf', 'json', 'both'] as const).map((fmt) => (
                  <button
                    key={fmt}
                    type="button"
                    onClick={() => updateSettings({ defaultReportFormat: fmt })}
                    className={`flex-1 py-2 px-3 rounded-xl border text-sm uppercase font-semibold transition-all ${
                      settings.defaultReportFormat === fmt
                        ? 'bg-violet-600/30 border-violet-500 text-white shadow-lg shadow-violet-500/10'
                        : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:text-white'
                    }`}
                  >
                    {fmt}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex justify-between items-center p-3 rounded-xl bg-slate-800/40 border border-slate-700/50">
              <div>
                <div className="text-sm font-semibold text-slate-200">Auto-open Download</div>
                <div className="text-xs text-slate-400">Automatically open download link after generating reports</div>
              </div>
              <button
                type="button"
                onClick={() => updateSettings({ autoOpenReport: !settings.autoOpenReport })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.autoOpenReport ? 'bg-violet-600' : 'bg-slate-700'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.autoOpenReport ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </motion.div>

        {/* ── SECTION 6: DANGER ZONE / RESET ── */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="glass-panel p-6 border-red-500/30 bg-red-500/5"
        >
          <div className="flex items-center gap-3 border-b border-red-500/20 pb-4 mb-6">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h3 className="text-lg font-bold text-white">Danger Zone</h3>
          </div>

          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <div className="text-sm font-semibold text-slate-200">Reset Settings</div>
              <div className="text-xs text-slate-400 mt-0.5">
                Restore all application preferences back to factory defaults.
              </div>
            </div>
            <button
              type="button"
              onClick={() => setShowResetModal(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-red-500/20 border border-red-500/40 text-red-300 hover:bg-red-500/30 rounded-xl transition-colors text-sm font-semibold"
            >
              <RotateCcw className="w-4 h-4" /> Reset Settings
            </button>
          </div>
        </motion.div>
      </div>

      {/* Reset Confirmation Modal */}
      <AnimatePresence>
        {showResetModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={() => setShowResetModal(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-md mx-4 rounded-2xl bg-slate-800 border border-slate-700 p-6 shadow-2xl space-y-6"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400 flex-shrink-0">
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Reset All Settings?</h3>
                  <p className="text-sm text-slate-400 mt-1">
                    This will restore all appearance, review, AI, and report preferences to default values.
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowResetModal(false)}
                  className="flex-1 px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-xl font-semibold transition-colors"
                >
                  Confirm Reset
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Settings;
