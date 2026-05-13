// services/api.js — Toutes les calls vers le backend FastAPI
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min (GPT-4o Vision peut être lent)
});

// ---- Document Collections ----

export const listCollections = async () => {
  const res = await api.get('/api/collections');
  return res.data;
};

export const createCollection = async (name) => {
  const res = await api.post('/api/collections', { name });
  return res.data;
};

export const deleteCollection = async (collectionId) => {
  const res = await api.delete(`/api/collections/${collectionId}`);
  return res.data;
};

export const uploadToCollection = async (collectionId, file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post(`/api/collections/${collectionId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total));
    },
  });
  return res.data;
};

export const getDocumentStatusInCollection = async (collectionId, documentId) => {
  const res = await api.get(`/api/collections/${collectionId}/documents/${documentId}/status`);
  return res.data;
};

export const deleteDocumentFromCollection = async (collectionId, documentId) => {
  const res = await api.delete(`/api/collections/${collectionId}/documents/${documentId}`);
  return res.data;
};

// ---- Documents (legacy — conservé pour compatibilité) ----

export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/api/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total));
    },
  });
  return res.data;
};

export const listDocuments = async () => {
  const res = await api.get('/api/documents/list');
  return res.data;
};

export const getDocumentStatus = async (documentId) => {
  const res = await api.get(`/api/documents/${documentId}/status`);
  return res.data;
};

export const deleteDocument = async (documentId) => {
  const res = await api.delete(`/api/documents/${documentId}`);
  return res.data;
};

// ---- Chat ----

export const sendQuery = async (question, sessionId = null, topK = 5, collectionIds = null) => {
  const res = await api.post('/api/chat/query', {
    question,
    session_id: sessionId,
    top_k: topK,
    collection_ids: collectionIds,
  });
  return res.data;
};

export const getChatHistory = async (sessionId) => {
  const res = await api.get(`/api/chat/history/${sessionId}`);
  return res.data;
};

export const clearChatHistory = async (sessionId) => {
  const res = await api.delete(`/api/chat/history/${sessionId}`);
  return res.data;
};

// ---- Health ----

export const getHealth = async () => {
  const res = await api.get('/api/health');
  return res.data;
};
