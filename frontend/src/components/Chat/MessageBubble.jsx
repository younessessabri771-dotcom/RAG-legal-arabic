// components/Chat/MessageBubble.jsx
import ReactMarkdown from 'react-markdown';
import SourceCard from '../Sources/SourceCard';
import { motion } from 'framer-motion';

function isArabic(text) {
  return /[\u0600-\u06FF]/.test(text);
}

export default function MessageBubble({ message }) {
  const { role, content, sources } = message;
  const arabic = isArabic(content);

  return (
    <motion.div
      className={`message-row ${role}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <div className="message-avatar">
        {role === 'assistant' ? '⚖️' : '👤'}
      </div>
      <div className="message-content">
        <div className={`message-bubble ${arabic ? 'arabic-text' : ''}`}>
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>

        {/* Sources */}
        {sources && sources.length > 0 && (
          <div className="sources-container">
            <div className="sources-title">📚 المصادر • Sources</div>
            {sources.map((src, i) => (
              <SourceCard key={i} source={src} index={i + 1} />
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
