// components/Chat/ChatWindow.jsx
import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import InputBar from './InputBar';

const SUGGESTIONS = [
  'ما هو السن القانوني الأدنى لسياقة الدراجات من صنف "أم" (AM)؟',
  'ما هما الاختباران اللذان يجتازهما المترشح بنجاح للحصول على رخصة السياقة؟',
  'إلى من يجب على السائق الإدلاء برخصة سياقته له؟',
];

export default function ChatWindow({ messages, isLoading, onSend, onClearChat, selectedCollectionIds = [] }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="chat-area">
      {/* Bandeau collections sélectionnées */}
      {selectedCollectionIds.length > 0 ? (
        <div className="col-target-banner">
          🎯 Question ciblée sur {selectedCollectionIds.length} collection{selectedCollectionIds.length > 1 ? 's' : ''}
          &nbsp;— {selectedCollectionIds.length * 5} chunks max au LLM
        </div>
      ) : (
        <div className="col-target-banner col-target-banner--warn">
          ⚠️ Aucune collection sélectionnée — recherche dans toute la base
        </div>
      )}

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <div className="empty-chat-icon">⚖️</div>
            <h2 className="empty-chat-title">مستشارك القانوني الذكي</h2>
            <p className="empty-chat-subtitle">
              ابدأ بتحميل وثائقك القانونية من الشريط الجانبي، ثم اطرح أسئلتك هنا.
            </p>
            <div className="suggestion-chips">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="chip" onClick={() => onSend(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))
        )}

        {/* Typing indicator */}
        {isLoading && (
          <div className="message-row assistant">
            <div className="message-avatar">⚖️</div>
            <div className="typing-indicator">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <InputBar onSend={onSend} isLoading={isLoading} />
    </div>
  );
}
