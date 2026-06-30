import React, { useState, useEffect } from 'react';
import { fetchDocuments, chatQuery, checkHealth, deleteDocument, fetchAnalytics } from './services/api';

import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatView from './components/ChatView';
import DocUploadView from './components/DocUploadView';
import AnalyticsView from './components/AnalyticsView';
import SettingsView from './components/SettingsView';

export default function App() {
  // Views Routing
  const [activeView, setActiveView] = useState('chat');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // RAG collections state
  const [collections, setCollections] = useState([
    { id: 'col1', name: 'Standard PDF Collection', docCount: 3 },
    { id: 'col2', name: 'Product Engineering Docs', docCount: 1 },
    { id: 'col3', name: 'Finance & Compliance', docCount: 0 }
  ]);
  const [selectedCollection, setSelectedCollection] = useState('col1');

  // AI Models Config
  const [embeddingModels] = useState([
    { id: 'cohere-embed-english-v3.0', name: 'Cohere embed-english-v3.0' }
  ]);
  const [selectedEmbeddingModel, setSelectedEmbeddingModel] = useState('cohere-embed-english-v3.0');

  const [llmModels] = useState([
    { id: 'gpt-4.1', name: 'GPT-4.1 (Azure OpenAI)' }
  ]);
  const [selectedLlmModel, setSelectedLlmModel] = useState('gpt-4.1');

  const [rerankerModel, setRerankerModel] = useState('cohere-rerank-english-v3.0');
  const [reflectionModel, setReflectionModel] = useState('gpt-4o-mini');
  const [guardrailModel, setGuardrailModel] = useState('none');

  // Hyperparameters
  const [chunkSize, setChunkSize] = useState(1000);
  const [chunkOverlap, setChunkOverlap] = useState(200);
  const [topK, setTopK] = useState(5);
  const [temperature, setTemperature] = useState(0.2);

  // Connection State
  const [backendConnected, setBackendConnected] = useState(true);

  // Ingested Documents List
  const [documents, setDocuments] = useState([]);
  const [analyticsData, setAnalyticsData] = useState(null);

  useEffect(() => {
    checkHealth().then(setBackendConnected);
    fetchDocuments().then(setDocuments).catch(console.error);
    fetchAnalytics().then(setAnalyticsData).catch(console.error);
  }, []);

  // Chat Conversations State
  const [chatHistory, setChatHistory] = useState([
    { id: 'chat_1', title: 'Q4 Growth rates analysis' },
    { id: 'chat_2', title: 'System Chunking overlap' }
  ]);
  const [activeChatId, setActiveChatId] = useState('chat_1');

  // Message store (chatId -> array of messages)
  const [conversations, setConversations] = useState({
    chat_1: [
      { 
        id: 'msg_1', 
        role: 'user', 
        content: 'What were the quarterly growth rates mentioned in the Q4 forecast?' 
      },
      { 
        id: 'msg_2', 
        role: 'assistant', 
        content: `Based on the uploaded document **Q4_Growth_Forecasts.pdf** (Section 3.2, Page 12), the growth rates for the fiscal year are broken down as follows:

*   **Q1 Growth**: 4.2% YoY (Year-over-Year), driven by subscription expansions.
*   **Q2 Growth**: 5.8% YoY, boosted by enterprise service activations.
*   **Q3 Growth**: 6.1% YoY, meeting target thresholds.
*   **Q4 Projection**: Expected **7.2% YoY**, representing an accelerated run-rate.

The aggregate compound annual growth rate (CAGR) is estimated at **5.82%** for the full year.`,
        stats: { latency: '1.24s', confidence: 96, model: 'GPT-4.1 (Azure OpenAI)' },
        citations: [
          { 
            fileName: 'Q4_Growth_Forecasts.pdf', 
            page: 12, 
            section: '3.2 Quarterly Growth Metrics', 
            snippet: 'Q4 projection is slated at 7.2% YoY driven by enterprise service activations, outstripping the Q3 growth ceiling of 6.1%. Combined annual CAGR stands at 5.82%.', 
            score: 0.96, 
            chunkId: 104 
          }
        ]
      }
    ],
    chat_2: [
      {
        id: 'msg_1',
        role: 'user',
        content: 'Explain the configured chunk size and overlap parameters.'
      },
      {
        id: 'msg_2',
        role: 'assistant',
        content: `The RAG Ingestion pipeline uses a **Recursive Character Text Splitter** with the following system configuration:

1.  **Chunk Size**: 1000 tokens. This segment length preserves semantic cohesion within paragraphs.
2.  **Chunk Overlap**: 200 tokens. This 20% boundary overlap ensures context continuity between sequential blocks, avoiding cutoffs in cross-chunk facts.

Vector embeddings are generated using the selected Embedding model and uploaded directly to the Qdrant database collection.`,
        stats: { latency: '0.85s', confidence: 91, model: 'GPT-4.1 (Azure OpenAI)' },
        citations: [
          {
            fileName: 'RAG_System_Architecture.md',
            page: 3,
            section: 'Chunk Splitting Scheme',
            snippet: 'Our pipeline leverages a default chunk size of 1000 tokens coupled with an overlap threshold of 200 tokens. This keeps contextual parameters high during vector search matches.',
            score: 0.93,
            chunkId: 12
          }
        ]
      }
    ]
  });

  const [isStreaming, setIsStreaming] = useState(false);
  const [activePipelineData, setActivePipelineData] = useState(null);

  // Initialize pipeline data for active trace
  useEffect(() => {
    // Populate default initial trace details based on active chat
    if (activeChatId === 'chat_1') {
      setActivePipelineData({
        query: { latency: '8ms', status: 'success', details: { rawQuery: 'What were the quarterly growth rates mentioned in the Q4 forecast?' } },
        rewrite: { latency: '140ms', status: 'success', details: { rewritten: 'What are the YoY growth rates for Q1, Q2, Q3, and projected Q4 in the Q4 Forecasts PDF?' } },
        embedding: { latency: '92ms', status: 'success', details: { model: selectedEmbeddingModel, dimensions: 1024 } },
        vector: { latency: '35ms', status: 'success', details: { collection: 'Standard PDF Collection', hitsFound: 12 } },
        rerank: { latency: '105ms', status: 'success', details: { model: rerankerModel, topMatchScore: 0.96 } },
        prompt: { latency: '4ms', status: 'success', details: { contextLength: '2,400 tokens', systemPromptLength: '350 tokens' } },
        llm: { latency: '820ms', status: 'success', details: { tokensPerSec: '54 t/s', model: selectedLlmModel } },
        reflection: { latency: '190ms', status: 'success', details: { model: reflectionModel, selfCritiquePassed: true } },
        final: { latency: '15ms', status: 'success', details: { citationCount: 1, confidenceScore: 0.96 } }
      });
    } else {
      setActivePipelineData({
        query: { latency: '10ms', status: 'success', details: { rawQuery: 'Explain the configured chunk size and overlap parameters.' } },
        rewrite: { latency: '110ms', status: 'success', details: { rewritten: 'What is the token chunk size and chunk overlap parameter settings in the documentation?' } },
        embedding: { latency: '75ms', status: 'success', details: { model: selectedEmbeddingModel, dimensions: 1024 } },
        vector: { latency: '42ms', status: 'success', details: { collection: 'Standard PDF Collection', hitsFound: 6 } },
        rerank: { latency: '80ms', status: 'success', details: { model: rerankerModel, topMatchScore: 0.93 } },
        prompt: { latency: '3ms', status: 'success', details: { contextLength: '1,800 tokens', systemPromptLength: '350 tokens' } },
        llm: { latency: '510ms', status: 'success', details: { tokensPerSec: '62 t/s', model: selectedLlmModel } },
        reflection: { latency: '120ms', status: 'success', details: { model: reflectionModel, selfCritiquePassed: true } },
        final: { latency: '10ms', status: 'success', details: { citationCount: 1, confidenceScore: 0.91 } }
      });
    }
  }, [activeChatId, selectedEmbeddingModel, selectedLlmModel, rerankerModel, reflectionModel]);

  // Create new session
  const handleNewChat = () => {
    const newId = 'chat_' + Date.now();
    const newTitle = 'New Chat Session ' + (chatHistory.length + 1);
    setChatHistory([{ id: newId, title: newTitle }, ...chatHistory]);
    setConversations({
      ...conversations,
      [newId]: []
    });
    setActiveChatId(newId);
    setActiveView('chat');
  };

  // Simulate streaming response and pipeline milestones
  const handleSendMessage = async (text) => {
    // 1. Append user message
    const userMsg = {
      id: 'msg_user_' + Date.now(),
      role: 'user',
      content: text
    };
    const currentChatId = activeChatId;
    const currentMsgs = conversations[currentChatId] || [];
    
    // Update active chat title if it's generic new chat
    const activeChat = chatHistory.find(c => c.id === currentChatId);
    if (activeChat && activeChat.title.startsWith('New Chat Session')) {
      const updatedHistory = chatHistory.map(c => 
        c.id === currentChatId ? { ...c, title: text.length > 28 ? text.slice(0, 28) + '...' : text } : c
      );
      setChatHistory(updatedHistory);
    }

    setConversations(prev => ({
      ...prev,
      [currentChatId]: [...currentMsgs, userMsg]
    }));
    
    setIsStreaming(true);

    // Initial clear / reset pipeline inspector indicators to running/pending
    setActivePipelineData({
      query: { latency: '...', status: 'warning', details: { rawQuery: text } },
      rewrite: { latency: 'pending', status: 'inactive' },
      embedding: { latency: 'pending', status: 'inactive' },
      vector: { latency: 'pending', status: 'inactive' },
      rerank: { latency: 'pending', status: 'inactive' },
      prompt: { latency: 'pending', status: 'inactive' },
      llm: { latency: 'pending', status: 'inactive' },
      reflection: { latency: 'pending', status: 'inactive' },
      final: { latency: 'pending', status: 'inactive' }
    });

    try {
      const response = await chatQuery(text, selectedLlmModel, selectedCollection);
      
      const assistantMsg = {
        id: 'msg_ai_' + Date.now(),
        role: 'assistant',
        content: response.answer,
        stats: response.stats,
        citations: response.citations
      };

      setConversations(prev => ({
        ...prev,
        [currentChatId]: [...(prev[currentChatId] || []), assistantMsg]
      }));

      if (response.pipeline_data) {
        setActivePipelineData(response.pipeline_data);
      }
    } catch (err) {
      console.error(err);
      const errorMsg = {
        id: 'msg_ai_' + Date.now(),
        role: 'assistant',
        content: "Sorry, I encountered an error communicating with the server.",
      };
      setConversations(prev => ({
        ...prev,
        [currentChatId]: [...(prev[currentChatId] || []), errorMsg]
      }));
    } finally {
      setIsStreaming(false);
    }
  };

  // Document management actions
  const handleUploadDocument = (newDoc) => {
    setDocuments([newDoc, ...documents]);
    // update collection count
    setCollections(collections.map(c => 
      c.id === newDoc.collectionId ? { ...c, docCount: c.docCount + 1 } : c
    ));
  };

  const handleDeleteDocument = async (id) => {
    try {
      await deleteDocument(id);
      const docToDelete = documents.find(d => d.id === id);
      if (!docToDelete) return;
      setDocuments(documents.filter(d => d.id !== id));
      setCollections(collections.map(c => 
        c.id === docToDelete.collectionId ? { ...c, docCount: Math.max(0, c.docCount - 1) } : c
      ));
    } catch (err) {
      console.error(err);
      alert("Failed to delete document.");
    }
  };


  const handleSaveSettings = () => {
    alert("Enterprise pipeline configurations updated! Changes will affect subsequent search retrievals.");
    setActiveView('chat');
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      
      {/* Sidebar navigation */}
      <Sidebar 
        activeView={activeView}
        setActiveView={(v) => {
          setActiveView(v);
          setMobileMenuOpen(false);
        }}
        chatHistory={chatHistory}
        activeChatId={activeChatId}
        setActiveChatId={(id) => {
          setActiveChatId(id);
          setMobileMenuOpen(false);
        }}
        onNewChat={() => {
          handleNewChat();
          setMobileMenuOpen(false);
        }}
        mobileMenuOpen={mobileMenuOpen}
        setMobileMenuOpen={setMobileMenuOpen}
      />

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        
        {/* Header bar */}
        <Header 
          collections={collections}
          selectedCollection={selectedCollection}
          setSelectedCollection={setSelectedCollection}
          embeddingModels={embeddingModels}
          selectedEmbeddingModel={selectedEmbeddingModel}
          setSelectedEmbeddingModel={setSelectedEmbeddingModel}
          llmModels={llmModels}
          selectedLlmModel={selectedLlmModel}
          setSelectedLlmModel={setSelectedLlmModel}
          backendConnected={backendConnected}
          setMobileMenuOpen={setMobileMenuOpen}
        />

        {/* View Router */}
        <div className="flex-1 overflow-auto min-h-0">
          {activeView === 'chat' && (
            <ChatView 
              messages={conversations[activeChatId] || []}
              onSendMessage={handleSendMessage}
              isStreaming={isStreaming}
              activePipelineData={activePipelineData}
              selectedLlmModel={selectedLlmModel}
            />
          )}

          {activeView === 'documents' && (
            <DocUploadView 
              documents={documents}
              onUploadDocument={handleUploadDocument}
              onDeleteDocument={handleDeleteDocument}
              collections={collections}
            />
          )}

          {activeView === 'analytics' && (
            <AnalyticsView 
              documents={documents}
              analyticsData={analyticsData}
            />
          )}

          {activeView === 'settings' && (
            <SettingsView 
              embeddingModels={embeddingModels}
              selectedEmbeddingModel={selectedEmbeddingModel}
              setSelectedEmbeddingModel={setSelectedEmbeddingModel}
              llmModels={llmModels}
              selectedLlmModel={selectedLlmModel}
              setSelectedLlmModel={setSelectedLlmModel}
              rerankerModel={rerankerModel}
              setRerankerModel={setRerankerModel}
              reflectionModel={reflectionModel}
              setReflectionModel={setReflectionModel}
              guardrailModel={guardrailModel}
              setGuardrailModel={setGuardrailModel}
              chunkSize={chunkSize}
              setChunkSize={setChunkSize}
              chunkOverlap={chunkOverlap}
              setChunkOverlap={setChunkOverlap}
              topK={topK}
              setTopK={setTopK}
              temperature={temperature}
              setTemperature={setTemperature}
              onSaveSettings={handleSaveSettings}
            />
          )}
        </div>

      </div>
    </div>
  );
}
