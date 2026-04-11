// components/Documents/DocumentList.jsx
import { useEffect, useState, useCallback } from 'react';
import { listDocuments, deleteDocument, getDocumentStatus } from '../../services/api';
import toast from 'react-hot-toast';

export default function DocumentList({ refreshTrigger }) {
  const [docs, setDocs] = useState([]);

  const fetchDocs = useCallback(async () => {
    try {
      const res = await listDocuments();
      setDocs(res.documents || []);
    } catch {
      // Silencieux si le backend n'est pas encore démarré
    }
  }, []);

  useEffect(() => { fetchDocs(); }, [fetchDocs, refreshTrigger]);

  // Polling pour les documents en cours d'indexation
  useEffect(() => {
    const processing = docs.filter(d => d.status === 'processing' || d.status === 'queued');
    if (processing.length === 0) return;
    const t = setInterval(fetchDocs, 4000);
    return () => clearInterval(t);
  }, [docs, fetchDocs]);

  const handleDelete = async (docId, filename) => {
    if (!confirm(`Supprimer "${filename}" ?`)) return;
    try {
      await deleteDocument(docId);
      toast.success('Document supprimé');
      fetchDocs();
    } catch {
      toast.error('Erreur suppression');
    }
  };

  if (docs.length === 0) {
    return (
      <div className="empty-docs">
        📂<br />
        Aucun document indexé.<br />
        Uploadez un PDF juridique.
      </div>
    );
  }

  return (
    <div className="doc-list">
      {docs.map((doc) => (
        <div key={doc.document_id} className="doc-item">
          <div className="doc-icon">📄</div>
          <div className="doc-info">
            <div className="doc-name" title={doc.filename}>{doc.filename}</div>
            <div className="doc-meta">
              {doc.page_count > 0 ? `${doc.page_count} pages · ${doc.chunk_count} chunks` : 'Traitement...'}
            </div>
          </div>
          <span className={`doc-status ${doc.status}`}>{doc.status}</span>
          <button
            className="doc-delete-btn"
            onClick={() => handleDelete(doc.document_id, doc.filename)}
            title="Supprimer"
          >✕</button>
        </div>
      ))}
    </div>
  );
}
