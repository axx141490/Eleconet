/**
 * API service layer - handles all HTTP requests to the backend.
 */
import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-redirect on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth ───────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

// ─── Knowledge Base ─────────────────────────────────
export const kbAPI = {
  list: () => api.get('/kb/'),
  create: (data) => api.post('/kb/', data),
  get: (id) => api.get(`/kb/${id}`),
  update: (id, data) => api.put(`/kb/${id}`, data),
  delete: (id) => api.delete(`/kb/${id}`),
  uploadFiles: (kbId, files, onProgress) => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    return api.post(`/kb/${kbId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    });
  },
  deleteDocument: (kbId, docId) => api.delete(`/kb/${kbId}/documents/${docId}`),
  getDocumentStatus: (kbId, docId) => api.get(`/kb/${kbId}/documents/${docId}/status`),
};

// ─── Chat ───────────────────────────────────────────
export const chatAPI = {
  send: (data) => api.post('/chat/', data),
  listConversations: () => api.get('/chat/conversations'),
  getConversation: (id) => api.get(`/chat/conversations/${id}`),
  deleteConversation: (id) => api.delete(`/chat/conversations/${id}`),
};

// ─── Stats ──────────────────────────────────────────
export const statsAPI = {
  get: () => api.get('/stats/'),
};

// ─── Settings ───────────────────────────────────────
export const settingsAPI = {
  getModel: () => api.get('/settings/model'),
  updateModel: (data) => api.put('/settings/model', data),
  getProviders: () => api.get('/settings/providers'),
};

// ─── Misc ───────────────────────────────────────────
export const miscAPI = {
  health: () => api.get('/health'),
  supportedFormats: () => api.get('/supported-formats'),
};

export default api;
