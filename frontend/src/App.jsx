import React, { useState, useEffect } from 'react';
import { fetchDocuments, chatQuery, checkHealth, deleteDocument, fetchAnalytics, fetchSessions, createSession, fetchSession } from './services/api';

import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatView from './components/ChatView';
import DocUploadView from './components/DocUploadView';
import AnalyticsView from './components/AnalyticsView';
import SettingsView from './components/SettingsView';
import CachePanelView from './components/CachePanelView';

export default function App() {
  // Theme State
  const [isDarkMode, setIsDarkMode] = useState(() => {
    return localStorage.getItem('theme') === 'dark';
  });

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDarkMode]);

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

  // Chat Conversations State
  const [chatHistory, setChatHistory] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);

  // Message store (chatId -> array of messages)
  const [conversations, setConversations] = useState({});
  const [conversationMemory, setConversationMemory] = useState({});

  const [isStreaming, setIsStreaming] = useState(false);
  const [activePipelineData, setActivePipelineData] = useState(null);

  useEffect(() => {
    checkHealth().then(setBackendConnected);
    fetchDocuments().then(setDocuments).catch(console.error);
    fetchAnalytics().then(setAnalyticsData).catch(console.error);
    initializeSessions();
  }, []);

  // Initialize pipeline data for active trace
  useEffect(() => {
    setActivePipelineData(null);
  }, [activeChatId, selectedEmbeddingModel, selectedLlmModel, rerankerModel, reflectionModel]);

  // Create new session
  const initializeSessions = async () => {
    try {
      let sessions = await fetchSessions();
      if (sessions.length === 0) {
        const session = await createSession('New Chat Session', selectedCollection);
        sessions = [session];
      }
      setChatHistory(sessions);
      const firstSessionId = sessions[0].id;
      setActiveChatId(firstSessionId);
      await loadSession(firstSessionId);
    } catch (err) {
      console.error(err);
    }
  };

  const loadSession = async (sessionId) => {
    try {
      const data = await fetchSession(sessionId);
      setConversations(prev => ({
        ...prev,
        [sessionId]: data.messages || []
      }));
      setConversationMemory(prev => ({
        ...prev,
        [sessionId]: {
          summary: data.memory?.summary || "",
          recentMessages: data.memory?.recentMessages || []
        }
      }));
    } catch (err) {
      console.error(err);
    }
  };

  const handleSelectChat = async (id) => {
    setActiveChatId(id);
    setMobileMenuOpen(false);
    setActiveView('chat');
    await loadSession(id);
  };

  const handleNewChat = async () => {
    try {
      const session = await createSession('New Chat Session', selectedCollection);
      setChatHistory(prev => [session, ...prev]);
      setConversations(prev => ({
        ...prev,
        [session.id]: []
      }));
      setConversationMemory(prev => ({
        ...prev,
        [session.id]: { summary: "", recentMessages: [] }
      }));
      setActiveChatId(session.id);
      setActiveView('chat');
    } catch (err) {
      console.error(err);
    }
  };

  // Simulate streaming response and pipeline milestones
  const handleSendMessage = async (text) => {
    // 1. Append user message
    const userMsg = {
      id: 'msg_user_' + Date.now(),
      role: 'user',
      content: text
    };
    let currentChatId = activeChatId;
    if (!currentChatId) {
      const session = await createSession('New Chat Session', selectedCollection);
      currentChatId = session.id;
      setChatHistory(prev => [session, ...prev]);
      setActiveChatId(currentChatId);
    }
    const currentMsgs = conversations[currentChatId] || [];
    const storedMemory = conversationMemory[currentChatId] || {};
    const fallbackMessages = currentMsgs
        .filter(m => (m.role === 'user' || m.role === 'assistant') && m.content?.trim())
        .slice(-9)
        .map(m => ({ role: m.role, content: m.content }));
    const memory = {
      summary: storedMemory.summary || "",
      messages: storedMemory.recentMessages?.length ? storedMemory.recentMessages : fallbackMessages
    };
    
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
      let accumulatedContent = "";
      const msgId = 'msg_ai_' + Date.now();
      
      const assistantMsg = {
        id: msgId,
        role: 'assistant',
        content: "",
      };
      
      setConversations(prev => ({
        ...prev,
        [currentChatId]: [...(prev[currentChatId] || []), assistantMsg]
      }));

      const finalResponse = await chatQuery(text, selectedLlmModel, selectedCollection, currentChatId, memory, (chunk) => {
        accumulatedContent += chunk;
        setConversations(prev => {
          const chatMsgs = prev[currentChatId] || [];
          return {
            ...prev,
            [currentChatId]: chatMsgs.map(m => m.id === msgId ? { ...m, content: accumulatedContent } : m)
          };
        });
      });
      
      setConversations(prev => {
        const chatMsgs = prev[currentChatId] || [];
        return {
          ...prev,
          [currentChatId]: chatMsgs.map(m => m.id === msgId ? { 
            ...m, 
            content: finalResponse.answer || accumulatedContent,
            stats: finalResponse.stats,
            citations: finalResponse.citations,
            messageId: finalResponse.messageId,
            pipelineData: finalResponse.pipeline_data || null
          } : m)
        };
      });

      if (finalResponse.pipeline_data) {
        setActivePipelineData(finalResponse.pipeline_data);
      }
      if (finalResponse.memory) {
        setConversationMemory(prev => ({
          ...prev,
          [currentChatId]: {
            summary: finalResponse.memory.summary || "",
            recentMessages: finalResponse.memory.recentMessages || []
          }
        }));
      }
      fetchSessions().then(setChatHistory).catch(console.error);
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
    <div className="flex h-screen bg-slate-50 dark:bg-slate-900 overflow-hidden font-sans transition-colors duration-200">
      
      {/* Sidebar navigation */}
      <Sidebar 
        activeView={activeView}
        setActiveView={(v) => {
          setActiveView(v);
          setMobileMenuOpen(false);
        }}
        chatHistory={chatHistory}
        activeChatId={activeChatId}
        setActiveChatId={handleSelectChat}
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
          isDarkMode={isDarkMode}
          toggleDarkMode={() => setIsDarkMode(!isDarkMode)}
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

          {activeView === 'cache' && (
            <CachePanelView />
          )}
        </div>

      </div>
    </div>
  );
}
