import React, { useState, useEffect, useRef } from 'react';
import MarkdownRenderer from './MarkdownRenderer';
import EvaluationCard from './EvaluationCard';
import { 
  Send, 
  Paperclip, 
  Mic, 
  MicOff, 
  Copy, 
  Check, 
  RotateCw, 
  ThumbsUp, 
  ThumbsDown, 
  TrendingUp, 
  Clock, 
  ChevronRight, 
  ChevronLeft, 
  Eye, 
  CheckCircle2, 
  FileText, 
  AlertTriangle,
  HelpCircle,
  Code,
  BookOpen,
  ArrowRight,
  RefreshCcw,
  Volume2,
  BrainCircuit
} from 'lucide-react';

export default function ChatView({ 
  messages, 
  onSendMessage, 
  isStreaming, 
  activePipelineData,
  selectedLlmModel
}) {
  const [inputText, setInputText] = useState('');
  const [isInspectorOpen, setIsInspectorOpen] = useState(true);
  const [activeInspectorStage, setActiveInspectorStage] = useState('LLM');
  const [isVoiceRecording, setIsVoiceRecording] = useState(false);
  const [copiedMessageId, setCopiedMessageId] = useState(null);
  const [selectedCitation, setSelectedCitation] = useState(null);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() || isStreaming) return;
    onSendMessage(inputText);
    setInputText('');
  };

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedMessageId(id);
    setTimeout(() => setCopiedMessageId(null), 2000);
  };

  // Mock Voice Recording Toggle
  const toggleVoice = () => {
    setIsVoiceRecording(!isVoiceRecording);
    if (!isVoiceRecording) {
      // Simulate input writing after listening
      setTimeout(() => {
        setInputText("What are the quarterly growth rates and vector retrieval parameters outlined in the architecture doc?");
        setIsVoiceRecording(false);
      }, 3000);
    }
  };

  // Pipeline Stages list
  const pipelineStages = [
    { id: 'Query', name: 'Query Input', desc: 'Processes raw query text, removes noise, detects language, and runs initial intent analysis.', key: 'query' },
    { id: 'Query Rewrite', name: 'Query Rewrite', desc: 'Uses light LLM to expand query into multiple search terms and resolve pronouns.', key: 'rewrite' },
    { id: 'Embedding', name: 'Embedding Generation', desc: 'Converts rewritten query into a dense vector embedding using Selected Embedding Model.', key: 'embedding' },
    { id: 'Vector Search', name: 'Vector Database Search', desc: 'Executes Cosine Similarity match against index. Retrieves top 30 candidate chunks.', key: 'vector' },
    { id: 'BM25 Search', name: 'BM25 Keyword Search', desc: 'Executes exact keyword match against BM25 index. Retrieves top 30 candidate chunks.', key: 'bm25' },
    { id: 'Reranker', name: 'Cross-Encoder Reranker', desc: 'Applies deep Reranking model (and RRF fusion) to score semantic relevance, filtering top 10.', key: 'rerank' },
    { id: 'Prompt Builder', name: 'Prompt Builder', desc: 'Injects system rules, chat history context, and reranked context chunks into LLM prompt template.', key: 'prompt' },
    { id: 'LLM', name: 'LLM Generator', desc: 'Streams responses token-by-token based on the built prompt.', key: 'llm' },
    { id: 'Reflection', name: 'Self-Correction / Critique', desc: 'Checks response against source chunks to guarantee zero hallucinations or policy violations.', key: 'reflection' },
    { id: 'Final Answer', name: 'Formatted Answer', desc: 'Attaches citations, checks metadata, and exposes UI interaction points.', key: 'final' }
  ];

  // Helper to get active pipeline stage data
  const getStageData = (stageKey) => {
    if (!activePipelineData) return null;
    return activePipelineData[stageKey] || null;
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-slate-50 dark:bg-slate-900 relative h-full transition-colors duration-200">
      {/* LEFT: MAIN CHAT PANEL */}
      <div className="flex-1 flex flex-col min-w-0 bg-white dark:bg-slate-950 shadow-subtle border-r border-slate-100 dark:border-slate-800 h-full relative transition-colors duration-200">
        {/* Messages List Area */}
        <div className="flex-grow overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center max-w-lg mx-auto text-center space-y-6 select-none">
              <div className="w-16 h-16 rounded-2xl bg-brand-50 flex items-center justify-center text-brand-600 shadow-premium">
                <BrainCircuit className="w-8 h-8 animate-pulse" />
              </div>
              <div className="space-y-2">
                <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">Enterprise Intelligent Search</h2>
                <p className="text-[13px] text-slate-500 dark:text-slate-400 leading-relaxed">
                  Query across uploaded documents, PDF research papers, technical specs, and enterprise wikis. Inspect the vector pipeline in real-time.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 w-full pt-4">
                {[
                  "Calculate the Q4 quarterly growth rates.",
                  "Summarize the vector store parameters.",
                  "What chunking size is configured?",
                  "Inspect the pipeline stages execution."
                ].map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => onSendMessage(q)}
                    className="p-3 text-left bg-slate-50 dark:bg-slate-900 hover:bg-slate-100/80 dark:hover:bg-slate-800 border border-slate-100 dark:border-slate-800 hover:border-slate-200 dark:hover:border-slate-700 rounded-xl text-[12px] text-slate-600 dark:text-slate-300 font-medium transition-all"
                  >
                    {q} &rarr;
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m) => {
              if (m.role === 'assistant' && !m.content) return null;
              return (
              <div key={m.id} className="space-y-3">
                {/* User / AI Message Row */}
                <div className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`flex gap-3 max-w-[85%] ${m.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    
                    {/* Avatar */}
                    <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold shadow-subtle border ${
                      m.role === 'user' 
                        ? 'bg-slate-800 text-white border-slate-700' 
                        : 'bg-brand-50 dark:bg-brand-900/50 text-brand-700 dark:text-brand-400 border-brand-200 dark:border-brand-800'
                    }`}>
                      {m.role === 'user' ? 'US' : 'AI'}
                    </div>

                    {/* Chat Bubble Content */}
                    <div className={`p-4 rounded-2xl message-bubble ${
                      m.role === 'user'
                        ? 'bg-slate-800 text-slate-50'
                        : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 border border-slate-200 dark:border-slate-700 shadow-sm'
                    }`}>
                      {/* Markdown Text Body */}
                      <MarkdownRenderer content={m.content} />

                      {/* AI citations & metadata */}
                      {m.role === 'assistant' && (
                        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700 space-y-3">
                          {/* Response Stats */}
                          <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-[11px] text-slate-400 font-medium">
                            <span className="flex items-center">
                              <Clock className="w-3.5 h-3.5 mr-1 text-slate-300" />
                              Latency: <b className="text-slate-600 ml-0.5">{m.stats?.latency || '0.92s'}</b>
                            </span>
                            <span className="flex items-center">
                              <TrendingUp className="w-3.5 h-3.5 mr-1 text-slate-300" />
                              Confidence: 
                              <span className={`ml-1 font-bold ${
                                (m.stats?.confidence || 90) >= 85 ? 'text-emerald-600' : 'text-amber-600'
                              }`}>{(m.stats?.confidence || 90)}%</span>
                            </span>
                            <span className="flex items-center">
                              <BookOpen className="w-3.5 h-3.5 mr-1 text-slate-300" />
                              Model: <b className="text-slate-600 ml-0.5">{m.stats?.model || selectedLlmModel}</b>
                            </span>
                          </div>

                          {/* Source Citations */}
                          {m.citations && m.citations.length > 0 && (
                            <div className="space-y-1.5">
                              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Sources:</span>
                              <div className="flex flex-wrap gap-2">
                                {m.citations.map((c, i) => (
                                  <button
                                    key={i}
                                    onClick={() => setSelectedCitation(c)}
                                    className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-slate-900 hover:bg-brand-50 dark:hover:bg-brand-900/30 border border-slate-200 dark:border-slate-700 hover:border-brand-200 dark:hover:border-brand-700 text-[11px] text-slate-600 dark:text-slate-400 hover:text-brand-700 dark:hover:text-brand-400 transition-all font-medium"
                                  >
                                    <FileText className="w-3 h-3 text-slate-400 group-hover:text-brand-500" />
                                    <span>{c.fileName} (P.{c.page})</span>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Action toolbar */}
                          <div className="flex items-center justify-between pt-1 text-slate-400">
                            <div className="flex items-center space-x-1">
                              <button
                                onClick={() => handleCopy(m.content, m.id)}
                                className="p-1.5 rounded-lg hover:bg-slate-100 hover:text-slate-600 transition-all"
                                title="Copy response"
                              >
                                {copiedMessageId === m.id ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                              </button>
                              <button
                                onClick={() => onSendMessage(messages[messages.length - 2]?.content || m.content)}
                                className="p-1.5 rounded-lg hover:bg-slate-100 hover:text-slate-600 transition-all"
                                title="Regenerate response"
                              >
                                <RotateCw className="w-3.5 h-3.5" />
                              </button>
                            </div>
                            <div className="flex items-center space-x-1">
                              <button className="p-1.5 rounded-lg hover:bg-slate-100 hover:text-emerald-600 transition-all" title="Like response">
                                <ThumbsUp className="w-3.5 h-3.5" />
                              </button>
                              <button className="p-1.5 rounded-lg hover:bg-slate-100 hover:text-rose-600 transition-all" title="Dislike response">
                                <ThumbsDown className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>

                          {m.messageId && <EvaluationCard messageId={m.messageId} />}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              );
            })
          )}

          {isStreaming && (!messages.length || (messages[messages.length - 1].role === 'assistant' && !messages[messages.length - 1].content)) && (
            <div className="flex justify-start">
              <div className="flex gap-3 max-w-[85%]">
                <div className="w-8 h-8 rounded-full bg-brand-50 text-brand-700 flex-shrink-0 flex items-center justify-center text-[10px] font-bold border border-brand-200 animate-pulse">
                  AI
                </div>
                <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm space-y-2">
                  <div className="flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-brand-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 rounded-full bg-brand-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 rounded-full bg-brand-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <p className="text-[11px] text-slate-400 font-medium italic animate-pulse">
                    Computing multi-stage RAG steps...
                  </p>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Floating Citation Reader overlay */}
        {selectedCitation && (
          <div className="absolute inset-x-0 bottom-24 mx-6 p-4 rounded-2xl bg-white border border-brand-200 shadow-premium z-20 animate-in fade-in slide-in-from-bottom-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2">
                <BookOpen className="w-4 h-4 text-brand-600" />
                <h4 className="text-[12px] font-semibold text-slate-800">
                  Citation Reference: {selectedCitation.fileName} (Page {selectedCitation.page}, Sec. {selectedCitation.section})
                </h4>
              </div>
              <button 
                onClick={() => setSelectedCitation(null)}
                className="text-slate-400 hover:text-slate-600 text-xs font-semibold px-2 py-0.5 rounded hover:bg-slate-100"
              >
                Close
              </button>
            </div>
            <div className="mt-2 text-[12px] text-slate-600 bg-slate-50 border border-slate-100 rounded-lg p-3 max-h-32 overflow-y-auto italic font-mono leading-relaxed">
              "...{selectedCitation.snippet}..."
            </div>
            <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400">
              <span>Similarity Match: <b>{(selectedCitation.score * 100).toFixed(1)}%</b></span>
              <span>Chunk Index: #{selectedCitation.chunkId}</span>
            </div>
          </div>
        )}

        {/* Input Bar Form */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
          <form onSubmit={handleSubmit} className="relative bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 focus-within:border-brand-400 dark:focus-within:border-brand-500 focus-within:ring-1 focus-within:ring-brand-100 dark:focus-within:ring-brand-900/30 rounded-xl p-2 transition-all flex flex-col shadow-subtle">
            
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Ask anything about index, vectors, or documents..."
              rows={2}
              className="w-full resize-none outline-none border-none text-[13px] text-slate-800 dark:text-slate-100 p-2 placeholder-slate-400 bg-transparent"
            />

            <div className="flex items-center justify-between pt-2 border-t border-slate-50 dark:border-slate-800 mt-1 select-none">
              <div className="flex items-center space-x-1">
                
                {/* Attach File Button */}
                <button
                  type="button"
                  title="Attach Documents"
                  className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-all"
                  onClick={() => alert("Upload new files via the dedicated 'Documents' page on the sidebar.")}
                >
                  <Paperclip className="w-4 h-4" />
                </button>

                {/* Voice Button */}
                <button
                  type="button"
                  onClick={toggleVoice}
                  title={isVoiceRecording ? "Listening..." : "Voice input"}
                  className={`p-2 rounded-lg transition-all ${
                    isVoiceRecording 
                      ? 'bg-rose-50 text-rose-600 hover:bg-rose-100 animate-pulse' 
                      : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {isVoiceRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>

                {isVoiceRecording && (
                  <span className="text-[10px] text-rose-500 font-semibold animate-pulse">
                    Recording... Click again to stop
                  </span>
                )}
              </div>

              {/* Send Button */}
              <button
                type="submit"
                disabled={!inputText.trim() || isStreaming}
                className={`flex items-center justify-center p-2 rounded-lg text-white transition-all ${
                  inputText.trim() && !isStreaming
                    ? 'bg-brand-600 dark:text-white hover:bg-brand-700 shadow-premium active:scale-95'
                    : 'bg-slate-100 bg-black dark:text-black text-slate-300 cursor-not-allowed'
                }`}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
          
          <div className="flex items-center justify-center space-x-1.5 mt-2 text-[10px] text-slate-400 font-medium">
            <span>Powered by RAG Ingestion Pipeline</span>
            <span>&bull;</span>
            <button 
              type="button"
              onClick={() => setIsInspectorOpen(!isInspectorOpen)} 
              className="text-brand-600 hover:underline flex items-center"
            >
              {isInspectorOpen ? 'Hide Pipeline Inspector' : 'Show Pipeline Inspector'}
              <ChevronRight className={`w-3 h-3 ml-0.5 transform transition-transform ${isInspectorOpen ? 'rotate-90' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Toggle tab floating when collapsed */}
      {!isInspectorOpen && (
        <button
          onClick={() => setIsInspectorOpen(true)}
          className="absolute right-0 top-1/2 transform -translate-y-1/2 bg-white border border-slate-200 border-r-0 hover:bg-slate-50 text-slate-500 hover:text-slate-800 p-1.5 rounded-l-lg shadow-sm focus:outline-none hidden md:block z-20"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      )}

      {/* RIGHT: COLLAPSIBLE PIPELINE INSPECTOR */}
      <div className={`transition-all duration-300 ease-in-out border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 flex flex-col h-full shadow-premium select-none relative z-10 ${
        isInspectorOpen ? 'w-80' : 'w-0 overflow-hidden border-l-0'
      }`}>
        {/* Toggle tab floating */}
        <button
          onClick={() => setIsInspectorOpen(!isInspectorOpen)}
          className="absolute -left-7 top-1/2 transform -translate-y-1/2 bg-white border border-slate-200 border-r-0 hover:bg-slate-50 text-slate-500 hover:text-slate-800 p-1.5 rounded-l-lg shadow-sm focus:outline-none hidden md:block"
        >
          {isInspectorOpen ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>

        {/* Inspector Header */}
        <div className="p-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-brand-600 dark:text-brand-400" />
            <h3 className="text-[13px] font-bold text-slate-800 dark:text-slate-100">Pipeline Inspector</h3>
          </div>
          <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full">
            Active Trace
          </span>
        </div>

        {/* Stages Timeline Scroll */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
          {pipelineStages.map((stage) => {
            const data = getStageData(stage.key);
            const isSelected = activeInspectorStage === stage.id;
            
            // Derive color status
            let statusBadge = "bg-slate-100 text-slate-500";
            let borderStyle = "border-slate-100";
            if (data?.status === 'success') {
              statusBadge = "bg-emerald-50 text-emerald-700 border border-emerald-100";
              borderStyle = isSelected ? "border-brand-500 ring-2 ring-brand-100" : "border-emerald-200 hover:border-emerald-300";
            } else if (data?.status === 'warning') {
              statusBadge = "bg-amber-50 text-amber-700 border border-amber-100";
              borderStyle = isSelected ? "border-brand-500 ring-2 ring-brand-100" : "border-amber-200 hover:border-amber-300";
            }

            return (
              <div
                key={stage.id}
                onClick={() => setActiveInspectorStage(stage.id)}
                className={`p-3 rounded-xl border text-left cursor-pointer transition-all duration-150 relative ${borderStyle} ${
                  isSelected ? 'bg-brand-50/50' : 'bg-white hover:bg-slate-50'
                }`}
              >
                {/* Node details */}
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[12px] font-bold text-slate-700 flex items-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-300 mr-2" />
                    {stage.name}
                  </span>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${statusBadge}`}>
                    {data?.latency ? `${data.latency}` : 'pending'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 truncate line-clamp-1">
                  {stage.desc}
                </p>

                {isSelected && (
                  <div className="absolute right-2 bottom-2 text-brand-600">
                    <CheckCircle2 className="w-3.5 h-3.5 fill-brand-100" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Selected Stage Detail Panel */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 max-h-80 overflow-y-auto">
          {(() => {
            const selectedStageInfo = pipelineStages.find(s => s.id === activeInspectorStage);
            const data = getStageData(selectedStageInfo?.key);
            
            return (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-[12px] font-extrabold text-slate-800 uppercase tracking-wide">
                    {activeInspectorStage} Details
                  </h4>
                  <span className="text-[10px] text-slate-400 font-bold font-mono">
                    {data?.latency || 'N/A'}
                  </span>
                </div>

                <p className="text-[11px] text-slate-600 leading-relaxed">
                  {selectedStageInfo?.desc}
                </p>

                {/* Sub details attributes */}
                {data?.details && (
                  <div className="space-y-2 mt-2 bg-white dark:bg-slate-950 rounded-lg p-2.5 border border-slate-200 dark:border-slate-800">
                    {Object.entries(data.details).map(([key, val]) => (
                      <div key={key} className="text-[11px] space-y-0.5">
                        <span className="font-bold text-slate-400 capitalize text-[9px]">{key}:</span>
                        <div className="bg-slate-50 dark:bg-slate-900 rounded p-1.5 font-mono text-[10px] text-slate-700 dark:text-slate-300 break-words max-h-24 overflow-y-auto">
                          {typeof val === 'object' ? JSON.stringify(val, null, 2) : String(val)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      </div>
    </div>
  );
}
