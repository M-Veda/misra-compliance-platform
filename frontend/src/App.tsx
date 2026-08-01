
import { FileSearch, ShieldAlert, FileText, LayoutDashboard, Cpu, FileCode2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Components
import Dashboard from './components/Dashboard';
import Analysis from './components/Analysis';
import Violations from './components/Violations';
import Reports from './components/Reports';
import GeneratedCode from './components/GeneratedCode';

import { useAppContext } from './context/AppContext';

const App = () => {
  const { activeTab, setActiveTab } = useAppContext();

  const navItems = [
    { id: 'dashboard',      label: 'Dashboard',          icon: LayoutDashboard },
    { id: 'analysis',       label: 'Analysis Engine',    icon: FileSearch },
    { id: 'violations',     label: 'Violations Review',  icon: ShieldAlert },
    { id: 'generated-code', label: 'Generated Code',     icon: FileCode2 },
    { id: 'reports',        label: 'Compliance Reports', icon: FileText },
  ];

  return (
    <div className="flex h-screen overflow-hidden font-sans transition-colors duration-300 bg-slate-900 text-slate-50">
      {/* Sidebar */}
      <motion.div 
        initial={{ x: -280 }}
        animate={{ x: 0 }}
        className="w-72 glass-panel m-4 flex flex-col z-10"
      >
        <div className="p-6 flex items-center gap-3 border-b border-slate-700/50">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-sky-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-gradient">MISRA AI</h1>
            <p className="text-xs text-slate-400 font-medium">Compliance Agent</p>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 relative group overflow-hidden ${
                  isActive 
                    ? 'text-white' 
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                {isActive && (
                  <motion.div 
                    layoutId="activeTab"
                    className="absolute inset-0 bg-violet-500/10 border border-violet-500/20 rounded-xl z-0"
                    transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <Icon className={`w-5 h-5 relative z-10 transition-colors duration-300 ${isActive ? 'text-violet-400' : 'group-hover:text-violet-400'}`} />
                <span className="font-medium relative z-10">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden relative">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-violet-900/20 via-slate-900/0 to-slate-900/0 z-0 pointer-events-none" />
        
        <main className="h-full w-full p-4 pl-0 overflow-y-auto relative z-10">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="h-full"
            >
              {activeTab === 'dashboard'      && <Dashboard />}
              {activeTab === 'analysis'       && <Analysis />}
              {activeTab === 'violations'     && <Violations />}
              {activeTab === 'generated-code' && <GeneratedCode />}
              {activeTab === 'reports'        && <Reports />}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};

export default App;
