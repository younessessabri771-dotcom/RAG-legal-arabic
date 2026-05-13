// App.jsx — Assemblage principal de l'application
import { useState } from 'react';
import { Toaster } from 'react-hot-toast';

import Header from './components/Layout/Header';
import ChatWindow from './components/Chat/ChatWindow';
import CollectionAccordion from './components/Collections/CollectionAccordion';
import { useChat } from './hooks/useChat';

export default function App() {
  const { messages, isLoading, sendMessage, clearChat } = useChat();
  // IDs des collections cochées (cibles du chat)
  const [selectedCollectionIds, setSelectedCollectionIds] = useState([]);

  const handleSend = (question) => {
    sendMessage(question, selectedCollectionIds);
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
          <CollectionAccordion
            selectedCollectionIds={selectedCollectionIds}
            onSelectionChange={setSelectedCollectionIds}
          />
        </aside>

        {/* Zone de chat */}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSend={handleSend}
          onClearChat={clearChat}
          selectedCollectionIds={selectedCollectionIds}
        />
      </div>
    </>
  );
}
