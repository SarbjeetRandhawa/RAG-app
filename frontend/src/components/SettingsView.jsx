import React from 'react';
import { 
  Sliders, 
  BrainCircuit, 
  Database, 
  ShieldCheck, 
  HelpCircle,
  Save,
  RotateCcw,
  AlertCircle
} from 'lucide-react';

export default function SettingsView({
  embeddingModels,
  selectedEmbeddingModel,
  setSelectedEmbeddingModel,
  llmModels,
  selectedLlmModel,
  setSelectedLlmModel,
  rerankerModel,
  setRerankerModel,
  reflectionModel,
  setReflectionModel,
  guardrailModel,
  setGuardrailModel,
  chunkSize,
  setChunkSize,
  chunkOverlap,
  setChunkOverlap,
  topK,
  setTopK,
  temperature,
  setTemperature,
  onSaveSettings
}) {

  const rerankers = [
    { id: 'cohere-rerank-english-v3.0', name: 'Cohere Rerank v3.0' },
    { id: 'none', name: 'No Reranker (Standard Retrieve)' }
  ];

  const reflectionModels = [
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini (Fast Verify)' },
    { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash' },
    { id: 'llama-3.1-8b', name: 'Llama 3.1 8B Instruct' },
    { id: 'none', name: 'Disabled (No critique phase)' }
  ];

  const guardrails = [
    { id: 'llama-guard-3', name: 'Llama Guard 3' },
    { id: 'nemo-guardrails', name: 'NeMo Guardrails (Custom Policy)' },
    { id: 'none', name: 'Disabled' }
  ];

  const handleReset = () => {
    setSelectedEmbeddingModel(embeddingModels[0]?.id || '');
    setSelectedLlmModel(llmModels[0]?.id || '');
    setRerankerModel('cohere-rerank-english-v3.0');
    setReflectionModel('gpt-4o-mini');
    setGuardrailModel('none');
    setChunkSize(1000);
    setChunkOverlap(200);
    setTopK(5);
    setTemperature(0.2);
    alert('Settings reverted to enterprise defaults');
  };

  return (
    <div className="flex-1 p-8 bg-slate-50 space-y-8 select-none">
      
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col space-y-1">
          <h2 className="text-xl font-bold text-slate-800">Advanced Pipeline Config</h2>
          <p className="text-[13px] text-slate-500">
            Tune embedding indices, reranking networks, generator behaviors, and reflection guardrails.
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={handleReset}
            className="px-3.5 py-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 rounded-xl text-[12px] font-semibold flex items-center space-x-1.5 transition-all active:scale-[0.98]"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Defaults</span>
          </button>

          <button
            onClick={onSaveSettings}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-[12px] font-semibold flex items-center space-x-1.5 shadow-premium transition-all active:scale-[0.98]"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Configuration</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* CARD 1: MODEL ROUTING */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-subtle space-y-6">
          <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
            <BrainCircuit className="w-5 h-5 text-brand-600" />
            <h3 className="text-[13px] font-extrabold text-slate-800 uppercase tracking-wider">
              AI Model Orchestrator
            </h3>
          </div>

          <div className="space-y-4">
            {/* Embedding Model */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-slate-500 uppercase flex items-center">
                Embedding Model
                <HelpCircle className="w-3 h-3 text-slate-300 ml-1 cursor-pointer" title="Used to generate dense vectors for documents and query matching." />
              </label>
              <select
                value={selectedEmbeddingModel}
                onChange={(e) => setSelectedEmbeddingModel(e.target.value)}
                className="w-full text-[12px] bg-slate-50 border border-slate-200 p-2.5 rounded-lg outline-none cursor-pointer focus:border-brand-400"
              >
                {embeddingModels.map((m) => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </div>

            {/* Reranker Model */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-slate-500 uppercase flex items-center">
                Reranker Model
                <HelpCircle className="w-3 h-3 text-slate-300 ml-1 cursor-pointer" title="Refines retrieval scores to order matching passages by semantic accuracy." />
              </label>
              <select
                value={rerankerModel}
                onChange={(e) => setRerankerModel(e.target.value)}
                className="w-full text-[12px] bg-slate-50 border border-slate-200 p-2.5 rounded-lg outline-none cursor-pointer focus:border-brand-400"
              >
                {rerankers.map((m) => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </div>

            {/* LLM Model */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-slate-500 uppercase flex items-center">
                LLM Generator
                <HelpCircle className="w-3 h-3 text-slate-300 ml-1 cursor-pointer" title="Underlying foundational model rendering the final natural response." />
              </label>
              <select
                value={selectedLlmModel}
                onChange={(e) => setSelectedLlmModel(e.target.value)}
                className="w-full text-[12px] bg-slate-50 border border-slate-200 p-2.5 rounded-lg outline-none cursor-pointer focus:border-brand-400"
              >
                {llmModels.map((m) => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </div>

            {/* Reflection Model */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-slate-500 uppercase flex items-center">
                Critique & Reflection Model
                <HelpCircle className="w-3 h-3 text-slate-300 ml-1 cursor-pointer" title="Self-reflection LLM checking references to avoid hallucinations." />
              </label>
              <select
                value={reflectionModel}
                onChange={(e) => setReflectionModel(e.target.value)}
                className="w-full text-[12px] bg-slate-50 border border-slate-200 p-2.5 rounded-lg outline-none cursor-pointer focus:border-brand-400"
              >
                {reflectionModels.map((m) => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </div>

            {/* Guardrail Policy */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-slate-500 uppercase flex items-center">
                Safety Guardrail Model
                <HelpCircle className="w-3 h-3 text-slate-300 ml-1 cursor-pointer" title="Validates prompt safety and output alignment rules." />
              </label>
              <select
                value={guardrailModel}
                onChange={(e) => setTerminalStateGuardrail(e)}
                className="w-full text-[12px] bg-slate-50 border border-slate-200 p-2.5 rounded-lg outline-none cursor-pointer focus:border-brand-400"
              >
                {guardrails.map((m) => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* CARD 2: INDEX PARAMETERS */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-subtle space-y-6">
          <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
            <Sliders className="w-5 h-5 text-indigo-500" />
            <h3 className="text-[13px] font-extrabold text-slate-800 uppercase tracking-wider">
              Retrieval & Indexing Parameters
            </h3>
          </div>

          <div className="space-y-6">
            
            {/* Chunk Size */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[11px] font-bold">
                <span className="text-slate-500">CHUNK SIZE (Tokens)</span>
                <span className="text-brand-600 bg-brand-50 px-2 py-0.5 rounded font-mono">{chunkSize} tokens</span>
              </div>
              <input
                type="range"
                min="200"
                max="2000"
                step="50"
                value={chunkSize}
                onChange={(e) => setChunkSize(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-brand-600"
              />
              <p className="text-[10px] text-slate-400">Controls size of text blocks parsed. Larger chunks provide broader context; smaller chunks target details.</p>
            </div>

            {/* Chunk Overlap */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[11px] font-bold">
                <span className="text-slate-500">CHUNK OVERLAP</span>
                <span className="text-brand-600 bg-brand-50 px-2 py-0.5 rounded font-mono">{chunkOverlap} tokens</span>
              </div>
              <input
                type="range"
                min="0"
                max="500"
                step="10"
                value={chunkOverlap}
                onChange={(e) => setChunkOverlap(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-brand-600"
              />
              <p className="text-[10px] text-slate-400">Maintains textual continuity across neighboring chunk boundaries.</p>
            </div>

            {/* Top-K retrieved chunks */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[11px] font-bold">
                <span className="text-slate-500">TOP-K (Matches retrieved)</span>
                <span className="text-brand-600 bg-brand-50 px-2 py-0.5 rounded font-mono">{topK} chunks</span>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                step="1"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-brand-600"
              />
              <p className="text-[10px] text-slate-400">Maximum number of relevant paragraphs sent to context builder.</p>
            </div>

            {/* Temperature */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[11px] font-bold">
                <span className="text-slate-500">TEMPERATURE (Generation entropy)</span>
                <span className="text-brand-600 bg-brand-50 px-2 py-0.5 rounded font-mono">{temperature}</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.2"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-brand-600"
              />
              <p className="text-[10px] text-slate-400">Lower temperatures yield strict factual replication. Higher temperatures permit creative variance.</p>
            </div>

          </div>
        </div>

      </div>

      {/* Safety Policy Alert banner */}
      <div className="bg-amber-50/50 border border-amber-200 rounded-2xl p-4 flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
        <div className="text-[12px] text-amber-800 leading-relaxed">
          <p className="font-bold mb-0.5">Enterprise Content Moderation Enabled</p>
          Settings modified here apply globally to active search nodes. Any policy changes are logged in compliance audits under ISO/IEC 42001 regulations.
        </div>
      </div>

    </div>
  );

  function setTerminalStateGuardrail(e) {
    setGuardrailModel(e.target.value);
  }
}
