// hooks/useChat.js — Gestion de l'état du chat
import { useState, useCallback, useRef } from 'react';
import { sendQuery } from '../services/api';
import { v4 as uuidv4 } from 'uuid';

export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const sessionId = useRef(uuidv4());

  const addMessage = useCallback((role, content, sources = []) => {
    setMessages((prev) => [
      ...prev,
      { id: uuidv4(), role, content, sources, timestamp: new Date() },
    ]);
  }, []);

  const sendMessage = useCallback(async (question) => {
    if (!question.trim() || isLoading) return;

    // Ajout du message utilisateur
    addMessage('user', question);
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendQuery(question, sessionId.current);
      addMessage('assistant', response.answer, response.sources || []);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Erreur serveur';
      setError(msg);
      addMessage('assistant', `❌ ${msg}`, []);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, addMessage]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    sessionId.current = uuidv4();
  }, []);

  return {
    messages,
    isLoading,
    error,
    sessionId: sessionId.current,
    sendMessage,
    clearChat,
  };
};
