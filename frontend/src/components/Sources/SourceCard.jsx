// components/Sources/SourceCard.jsx
import { useState } from 'react';

export default function SourceCard({ source, index }) {
  const [expanded, setExpanded] = useState(false);
  const score = source.relevance_score;
  const pct = Math.round(score * 100);

  return (
    <div className={`source-card ${expanded ? 'source-card-expanded' : ''}`} onClick={() => setExpanded(!expanded)}>
      <div className="source-card-header">
        <span style={{ fontSize: 12 }}>📄</span>
        <span className="source-doc-name">{source.document_name}</span>
        <span className="source-page">ص. {source.page_number}</span>
        <span className="source-score">{pct}%</span>
        <span className="source-toggle">{expanded ? '▲' : '▼'}</span>
      </div>
      <p className={`source-excerpt ${expanded ? 'source-excerpt-full' : ''}`}>
        {source.chunk_text}
      </p>
    </div>
  );
}
