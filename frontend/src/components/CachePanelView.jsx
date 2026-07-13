import React, { useState, useEffect } from 'react';
import { fetchCacheStats, clearCacheNamespace } from '../services/api';
import { Database, Trash2, RefreshCw, Activity, Layers, CheckCircle2, AlertCircle } from 'lucide-react';

export default function CachePanelView() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const loadStats = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const data = await fetchCacheStats();
      setStats(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const handleClear = async (namespace) => {
    if (confirm(`Are you sure you want to clear the ${namespace} cache?`)) {
      try {
        await clearCacheNamespace(namespace);
        await loadStats(true);
      } catch (err) {
        alert(err.message);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <RefreshCw className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-red-500 space-y-4">
        <AlertCircle className="w-12 h-12" />
        <p>{error}</p>
        <button onClick={() => loadStats(true)} className="px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-600 rounded-lg font-medium">Retry</button>
      </div>
    );
  }

  const isConnected = stats?.status === 'connected';

  return (
    <div className="h-full p-6 lg:p-8 bg-slate-50 dark:bg-slate-900 overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 ease-out">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-950 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center space-x-3">
              <Database className="w-6 h-6 text-brand-600" />
              <span>Redis Cache Developer Panel</span>
            </h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1 flex items-center space-x-2">
              <span>Status:</span>
              {isConnected ? (
                <span className="text-emerald-600 dark:text-emerald-400 font-medium flex items-center space-x-1">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Connected</span>
                </span>
              ) : (
                <span className="text-red-500 dark:text-red-400 font-medium flex items-center space-x-1">
                  <AlertCircle className="w-4 h-4" />
                  <span>Disconnected (Fallback Mode)</span>
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button 
              onClick={() => loadStats(true)}
              className="flex items-center justify-center space-x-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl font-medium transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            <button 
              onClick={() => handleClear('all')}
              disabled={!isConnected}
              className="flex items-center justify-center space-x-2 px-4 py-2 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 text-red-600 dark:text-red-400 rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Trash2 className="w-4 h-4" />
              <span>Clear All</span>
            </button>
          </div>
        </div>

        {/* Grid of Namespaces */}
        {isConnected && stats.namespaces && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(stats.namespaces).map(([namespace, nsStats]) => (
              <div key={namespace} className="bg-white dark:bg-slate-950 rounded-2xl border border-slate-100 dark:border-slate-800 p-5 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200 capitalize flex items-center space-x-2">
                      <Layers className="w-4 h-4 text-brand-500" />
                      <span>{namespace}</span>
                    </h3>
                    <div className="mt-1 flex items-center space-x-2 text-xs">
                      <span className={`px-2 py-0.5 rounded-full font-medium ${nsStats.enabled ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}`}>
                        {nsStats.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                  </div>
                  <button 
                    onClick={() => handleClear(namespace)}
                    className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                    title="Clear Namespace"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4 mt-6">
                  <div className="bg-slate-50 dark:bg-slate-900/50 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                    <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Hits</p>
                    <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{nsStats.hits}</p>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-900/50 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                    <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Misses</p>
                    <p className="text-xl font-bold text-slate-700 dark:text-slate-300 mt-1">{nsStats.misses}</p>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                  <div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Hit Rate</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Activity className="w-3.5 h-3.5 text-brand-500" />
                      <span className="text-sm font-bold text-slate-800 dark:text-slate-200">{nsStats.hit_rate}%</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Keys stored</p>
                    <p className="text-sm font-bold text-slate-800 dark:text-slate-200 mt-1">{nsStats.keys_count}</p>
                  </div>
                </div>

                {/* Optional mini progress bar for hit rate */}
                <div className="w-full h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full mt-4 overflow-hidden">
                  <div 
                    className="h-full bg-brand-500 rounded-full transition-all duration-1000"
                    style={{ width: `${nsStats.hit_rate}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
