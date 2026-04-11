// components/Chat/InputBar.jsx
import { useState, useRef, useCallback } from 'react';

export default function InputBar({ onSend, isLoading }) {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  const handleSend = useCallback(() => {
    if (!value.trim() || isLoading) return;
    onSend(value.trim());
    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  }, [value, isLoading, onSend]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e) => {
    setValue(e.target.value);
    // Auto-resize
    const ta = textareaRef.current;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 150) + 'px';
  };

  return (
    <div className="input-bar-container">
      <div className="input-bar">
        <textarea
          ref={textareaRef}
          className="input-textarea"
          placeholder="اكتب سؤالك القانوني هنا... / Posez votre question juridique..."
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={1}
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={!value.trim() || isLoading}
          title="Envoyer"
        >
          {isLoading ? '⏳' : '➤'}
        </button>
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', marginTop: 8 }}>
        Entrée pour envoyer · Shift+Entrée pour nouvelle ligne
      </div>
    </div>
  );
}
