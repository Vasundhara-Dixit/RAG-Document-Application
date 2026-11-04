import React, { useState, useEffect } from 'react';
import { NavRail } from './components/NavRail';
import { Header } from './components/Header';
import { SettingsModal, DEFAULT_BG_SETTINGS } from './components/SettingsModal';
import { ChatView } from './views/ChatView';
import { LibraryView } from './views/LibraryView';
import { EvalView } from './views/EvalView';
import { BackgroundSettings, ChatSession, DocumentRecord } from './types';
import { getHealth, listDocuments, uploadDocument } from './api';
import { loadSessions, saveSessions } from './utils/chatHistory';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'library' | 'eval'>('chat');
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [indexedChunks, setIndexedChunks] = useState(0);
  const [sessions, setSessions] = useState<ChatSession[]>(() => loadSessions());
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  // Background Glass & Profile Settings
  const [bgSettings, setBgSettings] = useState<BackgroundSettings>(() => {
    try {
      const saved = localStorage.getItem('reading_room_bg_settings');
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error('Failed to load bg settings:', e);
    }
    return DEFAULT_BG_SETTINGS;
  });

  const [archivistName, setArchivistName] = useState<string>(() => {
    return localStorage.getItem('reading_room_archivist_name') || 'Archivist Desk';
  });

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const refreshData = async () => {
    try {
      const [health, docs] = await Promise.all([getHealth(), listDocuments()]);
      setIndexedChunks(health.indexed_chunks);
      setDocuments(docs);
    } catch (e) {
      console.warn('Backend service currently unavailable, waiting for connection...', e);
    }
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectSession = (sessionId: string) => {
    setActiveSessionId(sessionId);
    setActiveTab('chat');
  };

  const handleNewSession = () => {
    setActiveSessionId(null);
    setActiveTab('chat');
  };

  const handleDeleteSession = (sessionId: string) => {
    setSessions((prev) => {
      const updated = prev.filter((s) => s.id !== sessionId);
      saveSessions(updated);
      return updated;
    });
    if (activeSessionId === sessionId) {
      setActiveSessionId(null);
    }
  };

  const handleSaveSession = (session: ChatSession) => {
    setSessions((prev) => {
      const existingIdx = prev.findIndex((s) => s.id === session.id);
      let updated: ChatSession[];
      if (existingIdx >= 0) {
        updated = [...prev];
        updated[existingIdx] = session;
      } else {
        updated = [session, ...prev];
      }
      saveSessions(updated);
      return updated;
    });
    setActiveSessionId(session.id);
  };

  const handleUploadFile = async (file: File): Promise<DocumentRecord> => {
    const doc = await uploadDocument(file);
    await refreshData();
    return doc;
  };

  const handleUpdateBgSettings = (newSettings: BackgroundSettings) => {
    setBgSettings(newSettings);
    try {
      localStorage.setItem('reading_room_bg_settings', JSON.stringify(newSettings));
    } catch (e) {
      console.error('Failed to save bg settings:', e);
    }
  };

  const handleUpdateArchivistName = (name: string) => {
    setArchivistName(name);
    try {
      localStorage.setItem('reading_room_archivist_name', name);
    } catch (e) {
      console.error('Failed to save archivist name:', e);
    }
  };

  const isGlassActive = Boolean(bgSettings.glassEnabled && bgSettings.wallpaperUrl);

  return (
    <div
      className={`flex h-screen w-screen overflow-hidden text-on-surface relative ${
        isGlassActive ? 'bg-transparent' : 'bg-background'
      }`}
    >
      {/* Fixed Custom Wallpaper Background (When Glass Enabled) */}
      {isGlassActive && (
        <>
          <div
            className="fixed inset-0 z-0 bg-cover bg-center bg-no-repeat transition-all duration-700 pointer-events-none"
            style={{ backgroundImage: `url(${bgSettings.wallpaperUrl})` }}
          />
          <div
            className="fixed inset-0 z-0 pointer-events-none transition-all duration-700"
            style={{
              backgroundColor: `rgba(253, 249, 246, ${bgSettings.overlayOpacity})`,
              backdropFilter:
                bgSettings.blurIntensity === 'high'
                  ? 'blur(22px)'
                  : bgSettings.blurIntensity === 'low'
                  ? 'blur(8px)'
                  : 'blur(14px)',
            }}
          />
        </>
      )}

      {/* Fixed Left Navigation Rail with Profile & Settings Access */}
      <NavRail
        activeTab={activeTab}
        onTabChange={setActiveTab}
        documentCount={documents.length}
        chunkCount={indexedChunks}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        onOpenSettings={() => setIsSettingsOpen(true)}
        isGlassEnabled={isGlassActive}
        archivistName={archivistName}
      />

      {/* Main Workspace Frame (offset for fixed NavRail and Header) */}
      <div className="pl-[232px] flex-1 flex flex-col h-full overflow-hidden relative z-10">
        {/* Fixed Top Header with Profile Avatar Button */}
        <Header
          activeTab={activeTab}
          onTabChange={setActiveTab}
          retrievalLabel="Hybrid BM25 + Dense RRF + Cross-Encoder"
          onOpenSettings={() => setIsSettingsOpen(true)}
          isGlassEnabled={isGlassActive}
        />

        {/* View Content Area (offset by 4rem / 64px for top Header) */}
        <main
          className={`relative w-full pt-16 flex-1 flex overflow-hidden ${
            isGlassActive ? 'bg-transparent' : 'bg-background'
          }`}
        >
          {activeTab === 'chat' && (
            <ChatView
              documents={documents}
              onNavigateToLibrary={() => setActiveTab('library')}
              sessions={sessions}
              activeSessionId={activeSessionId}
              onSaveSession={handleSaveSession}
              onUploadFile={handleUploadFile}
            />
          )}

          {activeTab === 'library' && (
            <LibraryView documents={documents} onRefresh={refreshData} />
          )}

          {activeTab === 'eval' && <EvalView />}
        </main>
      </div>

      {/* Profile & Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={bgSettings}
        onUpdateSettings={handleUpdateBgSettings}
        archivistName={archivistName}
        onUpdateArchivistName={handleUpdateArchivistName}
      />
    </div>
  );
};

export default App;
