// services/api.js — Toutes les calls vers le backend FastAPI
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min (GPT-4o Vision peut être lent)
});

// ---- Documents ----

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

export const sendQuery = async (question, sessionId = null, topK = 5) => {
  const res = await api.post('/api/chat/query', {
    question,
    session_id: sessionId,
    top_k: topK,
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
