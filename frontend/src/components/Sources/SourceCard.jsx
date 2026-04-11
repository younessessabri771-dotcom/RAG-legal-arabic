// components/Sources/SourceCard.jsx
export default function SourceCard({ source, index }) {
  const score = source.relevance_score;
  const pct = Math.round(score * 100);

  return (
    <div className="source-card">
      <div className="source-card-header">
        <span style={{ fontSize: 12 }}>📄</span>
        <span className="source-doc-name">{source.document_name}</span>
        <span className="source-page">ص. {source.page_number}</span>
        <span className="source-score">{pct}%</span>
      </div>
      <p className="source-excerpt">{source.chunk_text}</p>
    </div>
  );
}
