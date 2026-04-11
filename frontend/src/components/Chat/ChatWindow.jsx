// components/Chat/ChatWindow.jsx
import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import InputBar from './InputBar';

const SUGGESTIONS = [
  'ما هي شروط إبرام العقد؟',
  'ما هي حقوق المتهم في القانون؟',
  'اشرح مفهوم التقادم في القانون المدني',
  'ما هي أسباب فسخ العقد؟',
];

export default function ChatWindow({ messages, isLoading, onSend, onClearChat }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="chat-area">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <div className="empty-chat-icon">⚖️</div>
            <h2 className="empty-chat-title">مساعد الوثائق القانونية</h2>
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
