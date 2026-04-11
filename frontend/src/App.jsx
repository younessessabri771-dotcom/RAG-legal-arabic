// App.jsx — Assemblage principal de l'application
import { useState } from 'react';
import { Toaster } from 'react-hot-toast';

import Header from './components/Layout/Header';
import UploadZone from './components/Documents/UploadZone';
import DocumentList from './components/Documents/DocumentList';
import ChatWindow from './components/Chat/ChatWindow';
import { useChat } from './hooks/useChat';

export default function App() {
  const { messages, isLoading, sendMessage, clearChat } = useChat();
  const [refreshDocs, setRefreshDocs] = useState(0);

  const handleUploaded = () => {
    // Rafraîchit la liste des documents après un upload
    setRefreshDocs((n) => n + 1);
  };

  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1a1e2a',
            color: '#e8eaf0',
            border: '1px solid #2a2f3e',
            borderRadius: '10px',
          },
        }}
      />

      <div className="app-layout">
        {/* Header */}
        <Header onClearChat={clearChat} />

        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-section-title">📤 Upload Document</div>
          <UploadZone onUploaded={handleUploaded} />

          <div className="sidebar-section-title">📚 Documents Indexés</div>
          <DocumentList refreshTrigger={refreshDocs} />
        </aside>

        {/* Zone de chat */}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSend={sendMessage}
          onClearChat={clearChat}
        />
      </div>
    </>
  );
}
