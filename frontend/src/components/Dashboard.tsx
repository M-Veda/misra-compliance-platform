import { useEffect, useState } from 'react';
import { ShieldCheck, AlertTriangle, FileCode, CheckCircle, Clock, ShieldAlert, Folder } from 'lucide-react';
import { motion } from 'framer-motion';
import type { Variants } from 'framer-motion';
import { 
  Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { useAppContext } from '../context/AppContext';
import { ALL_10_MISRA_RULES } from '../types';

interface Rule {
  rule_number: string;
  rule_name: string;
  severity: string;
  category: string;
  description: string;
}

const Dashboard = () => {
  const [rules, setRules] = useState<Rule[]>(ALL_10_MISRA_RULES);
  const [loading, setLoading] = useState(false);
  const { recentScans, isFolderMode, folderName, fileList, analysisResult, getAnalysisMetrics } = useAppContext();

  // Compute severity distribution from actual rules
  const severityData = [
    { name: 'Mandatory', value: rules.filter(r => r.severity === 'Mandatory').length },
    { name: 'Required', value: rules.filter(r => r.severity === 'Required').length },
    { name: 'Advisory', value: rules.filter(r => r.severity === 'Advisory').length },
  ].filter(d => d.value > 0);

  const COLORS = ['#ef4444', '#f59e0b', '#3b82f6'];

  useEffect(() => {
    const fetchRules = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/rules');
        if (res.ok) {
          const data = await res.json();
          if (data.rules && data.rules.length > 0) {
            setRules(data.rules);
          }
        }
      } catch (err) {
        console.warn("Backend API rules fetch note (using canonical 10-rule set):", err);
      } finally {
        setLoading(false);
      }
    };
    fetchRules();
  }, []);

  // ── Metrics: always from single source of truth ──────────────────────────
  const totalFoldersAnalyzed = folderName ? 1 : 0;
  const totalCFilesAnalyzed  = isFolderMode ? fileList.length : (analysisResult ? 1 : 0);

  let totalViolationsAcrossAll = 0;
  let totalAcceptedAcrossAll   = 0;
  let overallScore             = 100;

  if (isFolderMode && fileList.length > 0) {
    for (let i = 0; i < fileList.length; i++) {
      const m = getAnalysisMetrics(i);
      totalViolationsAcrossAll += m.total_detected;
      totalAcceptedAcrossAll   += m.accepted;
    }
    overallScore = Math.round(fileList.reduce((acc, f) => acc + f.compliance_score, 0) / fileList.length);
  } else {
    const m = getAnalysisMetrics();
    totalViolationsAcrossAll = m.total_detected;
    totalAcceptedAcrossAll   = m.accepted;
    overallScore             = Math.round(m.compliance_score);
  }


  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <div className="h-full flex flex-col gap-6 p-2">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white mb-1">System Overview</h2>
          <p className="text-slate-400">Monitoring 10 critical MISRA C:2012 rules.</p>
        </div>
        <div className="flex gap-3">
          <div className="px-4 py-2 glass-panel flex items-center gap-2 text-sm font-medium text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Agent Active
          </div>
        </div>
      </div>

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4"
      >
        {/* Stats Cards */}
        {[
          { label: 'Overall Compliance', value: `${overallScore}%`, icon: ShieldCheck, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
          { label: 'Folders Analyzed', value: totalFoldersAnalyzed.toString(), icon: Folder, color: 'text-sky-400', bg: 'bg-sky-400/10' },
          { label: 'C Files Analyzed', value: totalCFilesAnalyzed.toString(), icon: CheckCircle, color: 'text-indigo-400', bg: 'bg-indigo-400/10' },
          { label: 'Total Violations', value: totalViolationsAcrossAll.toString(), icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-400/10' },
          { label: 'Active Rules', value: rules.length.toString(), icon: FileCode, color: 'text-violet-400', bg: 'bg-violet-400/10' },
        ].map((stat, i) => (
          <motion.div key={i} variants={itemVariants} className="glass-panel-interactive p-5 flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl ${stat.bg} flex items-center justify-center flex-shrink-0`}>
              <stat.icon className={`w-6 h-6 ${stat.color}`} />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{stat.value}</div>
              <div className="text-xs text-slate-400 font-medium">{stat.label}</div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Multi-file folder breakdown section if folder mode is active */}
      {isFolderMode && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-5"
        >
          <div className="flex justify-between items-center mb-4 border-b border-slate-700/50 pb-3">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Folder className="w-5 h-5 text-sky-400" />
              Violations Grouped by File ({fileList.length} Files in {folderName})
            </h3>
            <span className="text-xs font-semibold px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300">
              Overall Score: {overallScore}%
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-56 overflow-y-auto custom-scrollbar">
            {fileList.map((f, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 flex justify-between items-center">
                <div className="overflow-hidden pr-2">
                  <div className="text-sm font-bold text-slate-200 font-mono truncate">{f.file_name}</div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    {f.violations.length} {f.violations.length === 1 ? 'violation' : 'violations'}
                  </div>
                </div>
                <div className={`text-sm font-extrabold px-2.5 py-1 rounded-lg ${
                  f.compliance_score === 100 ? 'bg-emerald-500/20 text-emerald-400' :
                  f.compliance_score >= 80 ? 'bg-amber-500/20 text-amber-400' : 'bg-red-500/20 text-red-400'
                }`}>
                  {f.compliance_score}%
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-[350px]">
        {/* Supported Rules Panel */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2 glass-panel flex flex-col overflow-hidden"
        >
          <div className="p-6 border-b border-slate-700/50 flex justify-between items-center bg-slate-800/40">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-violet-400" />
              Supported Rules Dashboard
            </h3>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-violet-500/20 text-violet-300">
              {rules.length} / 10 Implemented
            </span>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500"></div>
              </div>
            ) : (
              <div className="space-y-3">
                {rules.map((rule, idx) => (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 + (idx * 0.05) }}
                    key={rule.rule_number} 
                    className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 hover:bg-slate-700/40 transition-colors group"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-3">
                        <span className="text-lg font-mono font-bold text-violet-300">Rule {rule.rule_number}</span>
                        <span className="text-base font-semibold text-slate-200">{rule.rule_name}</span>
                      </div>
                      <div className="flex gap-2 text-xs font-bold uppercase tracking-wider">
                        <span className={`px-2 py-1 rounded-md ${
                          rule.severity === 'Mandatory' ? 'bg-red-500/20 text-red-400' :
                          rule.severity === 'Required' ? 'bg-amber-500/20 text-amber-400' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          {rule.severity}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-slate-400 leading-relaxed pl-1">{rule.description}</p>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </motion.div>

        {/* Right Sidebar Charts */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-panel p-6 flex flex-col gap-6"
        >
          <div>
            <h3 className="text-lg font-bold text-white mb-4">Rule Severity Distribution</h3>
            <div className="h-44">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={75}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {severityData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.5rem' }}
                    itemStyle={{ color: '#f8fafc' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-4 mt-2 text-xs font-medium">
              {severityData.map((item, i) => (
                <div key={item.name} className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i] }} />
                  <span className="text-slate-300">{item.name}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t border-slate-700/50 pt-6">
            <h3 className="text-lg font-bold text-white mb-4">Recent Scans</h3>
            <div className="space-y-4">
              {recentScans.length === 0 ? (
                <div className="text-slate-500 text-sm">No recent scans.</div>
              ) : (
                recentScans.slice(0, 5).map((scan) => (
                  <div key={scan.id} className="flex items-center justify-between group">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center">
                        <FileCode className="w-4 h-4 text-slate-400 group-hover:text-violet-400 transition-colors" />
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-slate-200 truncate max-w-[140px]">{scan.file}</div>
                        <div className="text-xs text-slate-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {scan.time}
                        </div>
                      </div>
                    </div>
                    <div className={`text-sm font-bold ${
                      scan.score === 100 ? 'text-emerald-400' :
                      scan.score >= 80 ? 'text-amber-400' : 'text-red-400'
                    }`}>
                      {scan.score}%
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
