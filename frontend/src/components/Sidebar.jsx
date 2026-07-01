import React, { useState } from 'react';
import { 
  MessageSquarePlus, 
  Files, 
  Settings, 
  BarChart3, 
  Search, 
  Layers, 
  Database,
  Sliders,
  ChevronRight,
  TrendingUp,
  Cpu,
  User,
  ShieldCheck,
  Compass
} from 'lucide-react';

export default function Sidebar({ 
  activeView, 
  setActiveView, 
  chatHistory, 
  activeChatId, 
  setActiveChatId, 
  onNewChat,
  mobileMenuOpen,
  setMobileMenuOpen
}) {
  const [searchTerm, setSearchTerm] = useState('');

  const navItems = [
    { id: 'chat', label: 'Chat Interface', icon: MessageSquarePlus },
    { id: 'documents', label: 'Documents', icon: Files },
    { id: 'analytics', label: 'Analytics Dashboard', icon: BarChart3 },
    { id: 'settings', label: 'System Settings', icon: Settings },
  ];

  const filteredHistory = chatHistory.filter(chat => 
    chat.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <>
      {/* Mobile Overlay Backdrop */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/50 z-40 md:hidden animate-in fade-in"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      <aside className={`fixed inset-y-0 left-0 z-50 w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 flex flex-col h-full select-none transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${
        mobileMenuOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'
      }`}>
      {/* Brand logo & title */}
      <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center space-x-2.5">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-blue-400 flex items-center justify-center text-white shadow-premium">
          <Layers className="w-5 h-5" />
        </div>
        <div>
          <h1 className="font-semibold text-slate-800 dark:text-slate-100 leading-none text-[15px]">AetherRAG</h1>
          <span className="text-[11px] font-medium text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-900/30 px-1.5 py-0.5 rounded mt-1 inline-block">
            Enterprise Suite
          </span>
        </div>
      </div>

      {/* Action Area: New Chat */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-medium text-[13px] shadow-premium transition-all duration-150 active:scale-[0.98]"
        >
          <MessageSquarePlus className="w-4 h-4" />
          <span>New Chat Session</span>
        </button>
      </div>

      {/* Main Navigation Links */}
      <div className="px-2 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-left text-[13px] font-medium transition-all duration-150 ${
                isActive 
                  ? 'bg-brand-50 dark:bg-brand-900/40 text-brand-700 dark:text-brand-400 shadow-subtle' 
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-brand-600' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {isActive && <div className="w-1.5 h-1.5 rounded-full bg-brand-600" />}
            </button>
          );
        })}
      </div>

      <div className="border-t border-slate-100 dark:border-slate-800 my-3" />

      {/* Chat History Section */}
      <div className="flex-1 flex flex-col min-h-0 px-3">
        <div className="flex items-center justify-between mb-2 px-1">
          <span className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            Chat History
          </span>
          <span className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-500 font-bold">
            {chatHistory.length}
          </span>
        </div>

        {/* History Search bar */}
        <div className="relative mb-2">
          <Search className="absolute left-2.5 top-2.5 w-3.5 h-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search sessions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full text-[12px] bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 hover:border-slate-200 dark:hover:border-slate-700 focus:bg-white dark:focus:bg-slate-950 focus:border-brand-300 focus:ring-1 focus:ring-brand-100 rounded-lg pl-8 pr-3 py-1.5 outline-none transition-all dark:text-slate-200"
          />
        </div>

        {/* History List */}
        <div className="flex-grow overflow-y-auto space-y-1 pr-1">
          {filteredHistory.map((chat) => {
            const isSelected = activeChatId === chat.id;
            return (
              <button
                key={chat.id}
                onClick={() => {
                  setActiveView('chat');
                  setActiveChatId(chat.id);
                }}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-left transition-all text-[12px] ${
                  isSelected && activeView === 'chat'
                    ? 'bg-slate-100 dark:bg-slate-800 font-semibold text-slate-900 dark:text-slate-100 border-l-2 border-brand-600'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                <div className="truncate pr-1 flex items-center space-x-2">
                  <span className="text-slate-400 font-mono text-[10px]">#</span>
                  <span className="truncate">{chat.title}</span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-slate-300 flex-shrink-0" />
              </button>
            );
          })}
          {filteredHistory.length === 0 && (
            <div className="text-center py-6 text-slate-400 text-[11px]">
              No sessions match search
            </div>
          )}
        </div>
      </div>

      {/* Footer Profile */}
      <div className="p-3 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
        <div className="flex items-center space-x-3 p-1.5 hover:bg-slate-200/50 dark:hover:bg-slate-800 rounded-xl cursor-pointer transition-all">
          <div className="w-9 h-9 rounded-full bg-brand-100 dark:bg-brand-900/50 flex items-center justify-center text-brand-700 dark:text-brand-400 font-bold text-xs border border-brand-200 dark:border-brand-800">
            SR
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[12px] font-semibold text-slate-800 dark:text-slate-200 truncate">Sarbjeet Randhawa</p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate flex items-center space-x-1">
              <ShieldCheck className="w-3 h-3 text-emerald-500 inline mr-0.5" />
              <span>Admin Access</span>
            </p>
          </div>
        </div>
      </div>
    </aside>
    </>
  );
}
