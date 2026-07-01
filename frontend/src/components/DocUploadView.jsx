import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  Trash2, 
  CheckCircle2, 
  RefreshCw, 
  Loader2, 
  Sliders, 
  Check, 
  Plus, 
  FileDown,
  ChevronRight,
  Database
} from 'lucide-react';
import { uploadDocument } from '../services/api';


export default function DocUploadView({ 
  documents, 
  onUploadDocument, 
  onDeleteDocument, 
  collections 
}) {
  const [dragActive, setDragActive] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [ingestStage, setIngestStage] = useState(''); // 'ocr', 'chunking', 'embedding', 'done', ''
  const [metaTags, setMetaTags] = useState('Research, Architecture, VectorStore');
  const [metaAuthor, setMetaAuthor] = useState('Sarbjeet Randhawa');
  const [targetCollection, setTargetCollection] = useState('col1');

  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = async (file) => {
    setUploadingFile(file);
    setUploadProgress(20);
    setIngestStage('ocr');

    try {
      setUploadProgress(50);
      setIngestStage('embedding');
      
      const uploadedDoc = await uploadDocument(file, metaTags, metaAuthor, targetCollection);
      
      setUploadProgress(100);
      setIngestStage('done');
      
      setTimeout(() => {
        onUploadDocument(uploadedDoc);
        setUploadingFile(null);
        setIngestStage('');
        setUploadProgress(0);
      }, 1000);
      
    } catch (err) {
      console.error(err);
      alert('Failed to upload document.');
      setUploadingFile(null);
      setIngestStage('');
      setUploadProgress(0);
    }
  };


  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  return (
    <div className="flex-1 p-8 bg-slate-50 dark:bg-slate-900 space-y-8 select-none transition-colors duration-200">
      
      {/* View Title */}
      <div className="flex flex-col space-y-1">
        <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">Knowledge Ingestion Center</h2>
        <p className="text-[13px] text-slate-500 dark:text-slate-400">
          Upload PDF reports, Markdown articles, or text documents to parse, split, and index them into Qdrant.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* LEFT/MIDDLE: DRAG ZONE & UPLOADER METADATA */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Drag & Drop Area */}
          <div 
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            onClick={triggerFileInput}
            className={`border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all duration-250 bg-white dark:bg-slate-800 ${
              dragActive 
                ? 'border-brand-500 bg-brand-50/30 dark:bg-brand-900/20 scale-[0.99]' 
                : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 shadow-sm'
            }`}
          >
            <input 
              ref={fileInputRef}
              type="file" 
              className="hidden" 
              accept=".pdf,.txt,.md,.docx" 
              onChange={handleFileChange}
            />

            <div className="w-12 h-12 rounded-xl bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 flex items-center justify-center mb-4 shadow-subtle">
              <UploadCloud className="w-6 h-6" />
            </div>
            
            <h3 className="font-bold text-[14px] text-slate-700 dark:text-slate-200">Drag & drop files here</h3>
            <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
              Supports PDF, TXT, MD, DOCX up to 25MB
            </p>
            <button 
              type="button" 
              className="mt-4 px-4 py-1.5 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-semibold rounded-lg text-[12px] transition-all"
            >
              Browse Files
            </button>
          </div>

          {/* Ingestion Pipeline Progress Tracker */}
          {uploadingFile && (
            <div className="bg-white border border-brand-100 rounded-2xl p-6 shadow-premium space-y-4 animate-in fade-in zoom-in-95">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center space-x-3">
                  <FileText className="w-5 h-5 text-brand-500" />
                  <div>
                    <h4 className="text-[13px] font-bold text-slate-800 truncate max-w-xs">
                      {uploadingFile.name}
                    </h4>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {(uploadingFile.size / 1024).toFixed(1)} KB
                    </span>
                  </div>
                </div>
                <span className="text-[11px] font-extrabold text-brand-600">
                  {uploadProgress}%
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div 
                  className="bg-brand-600 h-full rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>

              {/* Multi-stage state checklist */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pt-2 select-none text-center">
                {[
                  { stage: 'ocr', label: 'OCR & Parsing', desc: 'Layout analysis' },
                  { stage: 'chunking', label: 'Chunk Splitting', desc: 'Recursive tokens' },
                  { stage: 'embedding', label: 'Vector Encoding', desc: 'Batch inference' },
                  { stage: 'done', label: 'Qdrant Ingest', desc: 'Indexed' }
                ].map((s, idx) => {
                  const stagesOrder = ['ocr', 'chunking', 'embedding', 'done'];
                  const currentIdx = stagesOrder.indexOf(ingestStage);
                  const stepIdx = stagesOrder.indexOf(s.stage);
                  
                  let stateColor = 'text-slate-400 border-slate-100';
                  let icon = <div className="w-4 h-4 rounded-full border border-slate-200 mx-auto flex items-center justify-center text-[9px] font-bold">{idx+1}</div>;

                  if (stepIdx < currentIdx || ingestStage === 'done') {
                    stateColor = 'text-emerald-600 border-emerald-100 bg-emerald-50';
                    icon = <CheckCircle2 className="w-4 h-4 text-emerald-500 mx-auto" />;
                  } else if (stepIdx === currentIdx) {
                    stateColor = 'text-brand-600 border-brand-200 bg-brand-50 font-bold';
                    icon = <Loader2 className="w-4 h-4 text-brand-500 mx-auto animate-spin" />;
                  }

                  return (
                    <div key={s.stage} className={`p-2.5 rounded-xl border text-[11px] ${stateColor}`}>
                      {icon}
                      <p className="mt-1.5 font-semibold text-[11px]">{s.label}</p>
                      <span className="text-[9px] opacity-75 hidden sm:inline">{s.desc}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Ingested Documents List */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-subtle space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700 pb-3">
              <h3 className="font-extrabold text-[13px] text-slate-800 dark:text-slate-100 uppercase tracking-wider">
                Ingested Documents Index
              </h3>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 font-bold bg-slate-50 dark:bg-slate-900 px-2 py-0.5 rounded border dark:border-slate-700">
                {documents.length} Files
              </span>
            </div>

            <div className="divide-y divide-slate-100 dark:divide-slate-700 overflow-x-auto">
              <table className="w-full text-left text-[12px]">
                <thead>
                  <tr className="text-slate-400 dark:text-slate-500 font-bold">
                    <th className="py-2.5 pr-4">File Name</th>
                    <th className="py-2.5 px-3">Size</th>
                    <th className="py-2.5 px-3">Chunks</th>
                    <th className="py-2.5 px-3">Collection</th>
                    <th className="py-2.5 px-3">Metadata Tags</th>
                    <th className="py-2.5 pl-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-700/50 transition-all">
                      <td className="py-3 pr-4 font-medium text-slate-800 dark:text-slate-200 max-w-xs truncate flex items-center space-x-2">
                        <FileText className="w-4 h-4 text-slate-400 dark:text-slate-500 flex-shrink-0" />
                        <span className="truncate">{doc.name}</span>
                      </td>
                      <td className="py-3 px-3 text-slate-500 dark:text-slate-400 font-mono text-[11px]">{doc.size}</td>
                      <td className="py-3 px-3 font-semibold text-slate-600 dark:text-slate-300">{doc.chunks}</td>
                      <td className="py-3 px-3">
                        <span className="text-[10px] bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 px-1.5 py-0.5 rounded font-medium">
                          {collections.find(c => c.id === doc.collectionId)?.name || 'Default'}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <div className="flex flex-wrap gap-1">
                          {doc.tags.map((t, idx) => (
                            <span key={idx} className="text-[9px] bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-400 px-1.5 py-0.2 rounded">
                              {t}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-3 pl-4 text-right">
                        <button
                          onClick={() => onDeleteDocument(doc.id)}
                          className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-all"
                          title="Delete document"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {documents.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-400 italic">
                        No documents loaded yet. Use the upload panel above.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: METADATA & PARSING SETTINGS CARD */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-subtle space-y-4">
            <div className="flex items-center space-x-2 border-b border-slate-100 dark:border-slate-700 pb-3">
              <Sliders className="w-4 h-4 text-brand-500 dark:text-brand-400" />
              <h3 className="font-extrabold text-[13px] text-slate-800 dark:text-slate-100 uppercase tracking-wider">
                Ingestion Config
              </h3>
            </div>

            {/* Target Collection */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-slate-500 dark:text-slate-400">Destination Collection</label>
              <select
                value={targetCollection}
                onChange={(e) => setTargetCollection(e.target.value)}
                className="w-full text-[12px] bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 p-2 rounded-lg outline-none cursor-pointer text-slate-800 dark:text-slate-200 focus:border-brand-400 dark:focus:border-brand-500"
              >
                {collections.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            {/* Author */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-slate-500 dark:text-slate-400">Document Owner</label>
              <input
                type="text"
                value={metaAuthor}
                onChange={(e) => setMetaAuthor(e.target.value)}
                className="w-full text-[12px] bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 p-2 rounded-lg outline-none text-slate-800 dark:text-slate-200 focus:border-brand-400 dark:focus:border-brand-500"
              />
            </div>

            {/* Metadata Tags */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-slate-500 dark:text-slate-400">Metadata Tags (Comma-separated)</label>
              <input
                type="text"
                value={metaTags}
                onChange={(e) => setMetaTags(e.target.value)}
                className="w-full text-[12px] bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 p-2 rounded-lg outline-none font-mono text-slate-800 dark:text-slate-200 focus:border-brand-400 dark:focus:border-brand-500"
              />
            </div>

            <div className="border-t border-slate-100 dark:border-slate-700 pt-3 text-[11px] text-slate-400 dark:text-slate-500 leading-relaxed bg-slate-50 dark:bg-slate-900 -mx-5 -mb-5 p-4 rounded-b-2xl">
              <p className="font-semibold text-slate-700 dark:text-slate-300 mb-1 flex items-center">
                <Database className="w-3.5 h-3.5 text-brand-600 mr-1.5" />
                OCR & Parsing Pipeline
              </p>
              By default, document contents are extracted via PyPDF, formatted, split using recursive token chunkers, embedded, and cataloged.
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
