import React from 'react';
import { Database, Cpu, BrainCircuit, RefreshCw } from 'lucide-react';

export default function Header({ 
  collections, 
  selectedCollection, 
  setSelectedCollection,
  embeddingModels,
  selectedEmbeddingModel,
  setSelectedEmbeddingModel,
  llmModels,
  selectedLlmModel,
  setSelectedLlmModel,
  backendConnected
}) {
  return (
    <header className="h-14 border-b border-slate-200 bg-white flex items-center justify-between px-6 select-none z-10">
      
      {/* Page Context Details */}
      <div className="flex items-center space-x-4">
        {/* Collection Selector */}
        <div className="flex items-center space-x-2">
          <Database className="w-4 h-4 text-slate-400" />
          <select
            value={selectedCollection}
            onChange={(e) => setSelectedCollection(e.target.value)}
            className="text-[12px] font-semibold text-slate-700 bg-slate-50 border border-slate-200 focus:border-brand-400 focus:bg-white px-2.5 py-1.5 rounded-lg outline-none cursor-pointer transition-all"
          >
            {collections.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.docCount} docs)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* RAG Configuration Selectors */}
      <div className="flex items-center space-x-3">
        {/* Embedding model */}
        <div className="flex items-center space-x-1.5 bg-slate-50 border border-slate-100 rounded-lg px-2 py-1">
          <Cpu className="w-3.5 h-3.5 text-brand-500" />
          <span className="text-[10px] text-slate-400 font-bold uppercase">Embed:</span>
          <select
            value={selectedEmbeddingModel}
            onChange={(e) => setSelectedEmbeddingModel(e.target.value)}
            className="text-[11px] font-medium text-slate-700 bg-transparent border-none outline-none cursor-pointer"
          >
            {embeddingModels.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </div>

        {/* LLM model */}
        <div className="flex items-center space-x-1.5 bg-slate-50 border border-slate-100 rounded-lg px-2 py-1">
          <BrainCircuit className="w-3.5 h-3.5 text-indigo-500" />
          <span className="text-[10px] text-slate-400 font-bold uppercase">LLM:</span>
          <select
            value={selectedLlmModel}
            onChange={(e) => setSelectedLlmModel(e.target.value)}
            className="text-[11px] font-medium text-slate-700 bg-transparent border-none outline-none cursor-pointer"
          >
            {llmModels.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </div>

        {/* Connection status indicator */}
        <div className="flex items-center space-x-1.5 pl-2 border-l border-slate-200">
          <span className={`w-2.5 h-2.5 rounded-full ${backendConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
          <span className="text-[10px] text-slate-500 font-medium hidden sm:inline">
            {backendConnected ? 'Ready' : 'Offline'}
          </span>
        </div>
      </div>
    </header>
  );
}
