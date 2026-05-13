// components/Collections/CollectionAccordion.jsx
// Sidebar accordion pour la gestion des Document Collections
import { useState, useEffect, useRef, useCallback } from 'react';
import toast from 'react-hot-toast';
import {
  listCollections,
  createCollection,
  deleteCollection,
  uploadToCollection,
  deleteDocumentFromCollection,
  getDocumentStatusInCollection,
} from '../../services/api';

// ────────────────────────────────────────────
// Icônes SVG inline (pas de dépendance externe)
// ────────────────────────────────────────────
const IconFolder = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/>
  </svg>
);
const IconChevronRight = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
  </svg>
);
const IconChevronDown = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z"/>
  </svg>
);
const IconTrash = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
  </svg>
);
const IconUpload = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
    <path d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z"/>
  </svg>
);
const IconFile = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
    <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
  </svg>
);
const IconPlus = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
  </svg>
);

// ────────────────────────────────────────────
// Statut d'un document
// ────────────────────────────────────────────
const statusConfig = {
  queued:     { label: 'En attente', color: '#6b7280', dot: '#6b7280' },
  processing: { label: 'Traitement…', color: '#f59e0b', dot: '#f59e0b' },
  indexed:    { label: 'Indexé', color: '#10b981', dot: '#10b981' },
  error:      { label: 'Erreur', color: '#ef4444', dot: '#ef4444' },
};

// ────────────────────────────────────────────
// Item de document individuel
// ────────────────────────────────────────────
function DocumentItem({ doc, collectionId, onDeleted }) {
  const [status, setStatus] = useState(doc.status);
  const pollingRef = useRef(null);

  useEffect(() => {
    if (status === 'queued' || status === 'processing') {
      pollingRef.current = setInterval(async () => {
        try {
          const data = await getDocumentStatusInCollection(collectionId, doc.document_id);
          setStatus(data.status);
          if (data.status === 'indexed' || data.status === 'error') {
            clearInterval(pollingRef.current);
          }
        } catch {
          clearInterval(pollingRef.current);
        }
      }, 3000);
    }
    return () => clearInterval(pollingRef.current);
  }, [status, collectionId, doc.document_id]);

  const handleDelete = async () => {
    if (!confirm(`Supprimer "${doc.filename}" ?`)) return;
    try {
      await deleteDocumentFromCollection(collectionId, doc.document_id);
      toast.success('Document supprimé');
      onDeleted(doc.document_id);
    } catch {
      toast.error('Erreur lors de la suppression');
    }
  };

  const cfg = statusConfig[status] || statusConfig.queued;

  return (
    <div className="col-doc-item">
      <IconFile />
      <span className="col-doc-name" title={doc.filename}>{doc.filename}</span>
      <span className="col-doc-status" style={{ color: cfg.dot }}>●</span>
      <button
        className="col-icon-btn col-icon-btn--danger"
        onClick={handleDelete}
        title="Supprimer"
      >
        <IconTrash />
      </button>
    </div>
  );
}

// ────────────────────────────────────────────
// Item de collection (un accordéon)
// ────────────────────────────────────────────
function CollectionItem({ collection, isSelected, onToggleSelect, onDeleted, onDocumentsChanged }) {
  const [isOpen, setIsOpen] = useState(false);
  const [docs, setDocs] = useState(collection.documents || []);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = async (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    setIsUploading(true);
    try {
      for (const file of files) {
        const res = await uploadToCollection(collection.collection_id, file);
        setDocs((prev) => [
          ...prev,
          {
            document_id: res.document_id,
            filename: res.filename,
            status: 'queued',
            page_count: 0,
            chunk_count: 0,
            uploaded_at: new Date().toISOString(),
          },
        ]);
        toast.success(`"${res.filename}" en cours d'indexation…`);
      }
      onDocumentsChanged();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erreur upload');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleDocDeleted = (docId) => {
    setDocs((prev) => prev.filter((d) => d.document_id !== docId));
    onDocumentsChanged();
  };

  const handleDeleteCollection = async (e) => {
    e.stopPropagation();
    if (!confirm(`Supprimer la collection "${collection.name}" et tous ses documents ?`)) return;
    try {
      await deleteCollection(collection.collection_id);
      toast.success(`Collection "${collection.name}" supprimée`);
      onDeleted(collection.collection_id);
    } catch {
      toast.error('Erreur lors de la suppression');
    }
  };

  return (
    <div className={`col-item ${isOpen ? 'col-item--open' : ''}`}>
      {/* Header de la collection */}
      <div className="col-item-header">
        {/* Checkbox de sélection */}
        <input
          type="checkbox"
          className="col-checkbox"
          checked={isSelected}
          onChange={() => onToggleSelect(collection.collection_id)}
          onClick={(e) => e.stopPropagation()}
          title="Sélectionner pour le chat"
          id={`col-check-${collection.collection_id}`}
        />

        {/* Accordéon toggle */}
        <div
          className="col-item-toggle"
          onClick={() => setIsOpen(!isOpen)}
        >
          <span className="col-chevron">
            {isOpen ? <IconChevronDown /> : <IconChevronRight />}
          </span>
          <IconFolder />
          <span className="col-name">{collection.name}</span>
          <span className="col-badge">{docs.length}</span>
        </div>

        {/* Bouton supprimer collection */}
        <button
          className="col-icon-btn col-icon-btn--danger"
          onClick={handleDeleteCollection}
          title="Supprimer la collection"
        >
          <IconTrash />
        </button>
      </div>

      {/* Contenu accordéon */}
      {isOpen && (
        <div className="col-item-body">
          {/* Liste des documents */}
          {docs.length === 0 ? (
            <p className="col-empty">Aucun document. Uploadez un PDF ci-dessous.</p>
          ) : (
            docs.map((doc) => (
              <DocumentItem
                key={doc.document_id}
                doc={doc}
                collectionId={collection.collection_id}
                onDeleted={handleDocDeleted}
              />
            ))
          )}

          {/* Bouton upload */}
          <button
            className="col-upload-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
          >
            {isUploading ? (
              <span className="col-spinner" />
            ) : (
              <IconUpload />
            )}
            {isUploading ? 'Upload en cours…' : 'Ajouter des PDFs'}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            multiple
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
        </div>
      )}
    </div>
  );
}

// ────────────────────────────────────────────
// Accordéon principal
// ────────────────────────────────────────────
export default function CollectionAccordion({ selectedCollectionIds, onSelectionChange }) {
  const [collections, setCollections] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [showInput, setShowInput] = useState(false);
  const inputRef = useRef(null);

  const fetchCollections = useCallback(async () => {
    try {
      const data = await listCollections();
      setCollections(data.collections || []);
    } catch {
      // silencieux
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCollections();
  }, [fetchCollections]);

  useEffect(() => {
    if (showInput) inputRef.current?.focus();
  }, [showInput]);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setIsCreating(true);
    try {
      const res = await createCollection(newName.trim());
      setCollections((prev) => [
        ...prev,
        {
          collection_id: res.collection_id,
          name: res.name,
          document_count: 0,
          created_at: new Date().toISOString(),
          documents: [],
        },
      ]);
      toast.success(`Collection "${res.name}" créée`);
      setNewName('');
      setShowInput(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erreur création');
    } finally {
      setIsCreating(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleCreate();
    if (e.key === 'Escape') { setShowInput(false); setNewName(''); }
  };

  const handleToggleSelect = (collectionId) => {
    const current = new Set(selectedCollectionIds);
    if (current.has(collectionId)) {
      current.delete(collectionId);
    } else {
      current.add(collectionId);
    }
    onSelectionChange(Array.from(current));
  };

  const handleCollectionDeleted = (collectionId) => {
    setCollections((prev) => prev.filter((c) => c.collection_id !== collectionId));
    // Désélectionner si sélectionné
    if (selectedCollectionIds.includes(collectionId)) {
      onSelectionChange(selectedCollectionIds.filter((id) => id !== collectionId));
    }
  };

  return (
    <div className="col-accordion">
      {/* En-tête */}
      <div className="col-accordion-header">
        <span className="sidebar-section-title" style={{ margin: 0 }}>
          📁 Document Collections
        </span>
        {selectedCollectionIds.length > 0 && (
          <span className="col-selected-badge">
            {selectedCollectionIds.length} sélectionnée{selectedCollectionIds.length > 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Liste des collections */}
      {isLoading ? (
        <p className="col-empty">Chargement…</p>
      ) : collections.length === 0 ? (
        <p className="col-empty">Aucune collection. Créez-en une ci-dessous.</p>
      ) : (
        collections.map((col) => (
          <CollectionItem
            key={col.collection_id}
            collection={col}
            isSelected={selectedCollectionIds.includes(col.collection_id)}
            onToggleSelect={handleToggleSelect}
            onDeleted={handleCollectionDeleted}
            onDocumentsChanged={fetchCollections}
          />
        ))
      )}

      {/* Formulaire nouvelle collection */}
      {showInput ? (
        <div className="col-new-form">
          <input
            ref={inputRef}
            className="col-new-input"
            type="text"
            placeholder="Nom de la collection…"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={handleKeyDown}
            maxLength={60}
          />
          <button
            className="col-new-confirm"
            onClick={handleCreate}
            disabled={isCreating || !newName.trim()}
          >
            {isCreating ? '…' : '✓'}
          </button>
          <button
            className="col-new-cancel"
            onClick={() => { setShowInput(false); setNewName(''); }}
          >
            ✕
          </button>
        </div>
      ) : (
        <button
          className="col-new-btn"
          onClick={() => setShowInput(true)}
        >
          <IconPlus /> Nouvelle Collection
        </button>
      )}
    </div>
  );
}
