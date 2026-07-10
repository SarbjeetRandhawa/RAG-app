import React, { useState, useEffect } from 'react';
import { fetchEvaluation } from '../services/api';
import { 
  ChevronDown, ChevronRight, CheckCircle2, XCircle, AlertTriangle, 
  Clock, Activity, Loader2, BarChart2, Code, Database, FileText
} from 'lucide-react';

export default function EvaluationCard({ messageId }) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('metrics');
  const [evalData, setEvalData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!messageId || !isOpen) return;
    
    let interval;
    const poll = async () => {
      try {
        const data = await fetchEvaluation(messageId);
        setEvalData(data);
        if (data.status === 'completed' || data.status === 'error') {
          clearInterval(interval);
        }
      } catch (err) {
        setError(err.message);
        clearInterval(interval);
      }
    };

    if(!evalData || evalData.status === 'pending') {
      poll();
      interval = setInterval(poll, 2000);
    }
    
    return () => clearInterval(interval);
  }, [messageId, isOpen]);

  if (!messageId) return null;

  return (
    <div className="mt-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden shadow-sm transition-all duration-200">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-3 flex items-center justify-between bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/80 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-brand-500" />
          <span className="text-[12px] font-bold text-slate-700 dark:text-slate-200">AI Evaluation & Observability</span>
          {evalData?.status === 'pending' && <Loader2 className="w-3.5 h-3.5 text-brand-500 animate-spin ml-2" />}
          {evalData?.status === 'completed' && (
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ml-2 ${
              evalData.overall_score >= 0.8 ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
            }`}>
              Score: {Math.round(evalData.overall_score * 100)}%
            </span>
          )}
        </div>
        {isOpen ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
      </button>

      {isOpen && (
        <div className="p-4 border-t border-slate-200 dark:border-slate-700">
          {!evalData && !error && (
            <div className="flex items-center space-x-2 text-slate-500 text-[12px]">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Fetching evaluation data...</span>
            </div>
          )}
          
          {error && (
            <div className="text-rose-500 text-[12px] flex items-center">
              <AlertTriangle className="w-4 h-4 mr-2" />
              {error}
            </div>
          )}

          {evalData?.status === 'pending' && (
            <div className="text-slate-500 text-[12px] flex flex-col items-center justify-center py-6 space-y-3">
              <Loader2 className="w-6 h-6 animate-spin text-brand-500" />
              <span>Running DeepEval metrics in the background...</span>
            </div>
          )}

          {evalData?.status === 'error' && (
            <div className="text-rose-500 text-[12px] flex items-center">
              <XCircle className="w-4 h-4 mr-2" />
              Evaluation failed: {evalData.error}
            </div>
          )}

          {evalData?.status === 'completed' && (
            <div>
              {/* Tabs */}
              <div className="flex space-x-4 border-b border-slate-200 dark:border-slate-700 mb-4 overflow-x-auto no-scrollbar">
                {[
                  { id: 'metrics', label: 'Metrics', icon: BarChart2 },
                  { id: 'timing', label: 'Timing', icon: Clock },
                  { id: 'json', label: 'Raw JSON', icon: Code }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-1.5 pb-2 text-[11px] font-bold whitespace-nowrap border-b-2 transition-colors ${
                      activeTab === tab.id 
                        ? 'border-brand-500 text-brand-600 dark:text-brand-400' 
                        : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                    }`}
                  >
                    <tab.icon className="w-3.5 h-3.5" />
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="text-[12px]">
                {activeTab === 'metrics' && (
                  <div className="space-y-4">
                    {Object.entries(evalData.metrics || {}).map(([key, metric]) => {
                      const colorClass = metric.passed 
                        ? 'text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200' 
                        : 'text-rose-600 bg-rose-50 dark:bg-rose-900/20 border-rose-200';
                      
                      return (
                        <div key={key} className={`p-3 rounded-lg border ${colorClass}`}>
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-bold capitalize">{key.replace('_', ' ')}</span>
                            <div className="flex items-center space-x-2">
                              <span className="font-mono text-[10px] font-bold">{(metric.score * 100).toFixed(0)}%</span>
                              {metric.passed ? <CheckCircle2 className="w-4 h-4 text-emerald-500" /> : <XCircle className="w-4 h-4 text-rose-500" />}
                            </div>
                          </div>
                          {/* Progress bar */}
                          <div className="w-full bg-slate-200/50 dark:bg-slate-700/50 h-1.5 rounded-full mb-2 overflow-hidden">
                            <div 
                              className={`h-full ${metric.passed ? 'bg-emerald-500' : 'bg-rose-500'}`} 
                              style={{ width: `${metric.score * 100}%` }}
                            />
                          </div>
                          <p className="text-[11px] text-slate-600 dark:text-slate-300 italic opacity-90">{metric.reason}</p>
                        </div>
                      )
                    })}
                  </div>
                )}

                {activeTab === 'timing' && (
                  <div className="space-y-2 font-mono text-[11px]">
                    {Object.entries(evalData.eval_payload?.metadata || {}).map(([k, v]) => (
                      <div key={k} className="flex justify-between p-2 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded">
                        <span className="text-slate-500">{k}</span>
                        <span className="font-bold text-slate-700 dark:text-slate-300">
                          {k.includes('time') ? `${Number(v).toFixed(1)} ms` : v}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === 'json' && (
                  <pre className="p-3 bg-slate-900 text-emerald-400 rounded-lg font-mono text-[10px] overflow-x-auto overflow-y-auto max-h-96">
                    {JSON.stringify(evalData, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
