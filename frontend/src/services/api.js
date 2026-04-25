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
  changePassword: (data) => api.put('/auth/change-password', data),
  sendEmailCode: (email) => api.post('/auth/send-email-code', { email }),
  changeEmail: (data) => api.put('/auth/change-email', data),
  changePhone: (data) => api.put('/auth/change-phone', data),
  sendSmsCode: (phone, scene = 'register') => api.post('/auth/send-sms-code', { phone, scene }),
  loginSms: (data) => api.post('/auth/login-sms', data),
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

// ─── Share ──────────────────────────────────────────
export const shareAPI = {
  create: (kbId) => api.post(`/share/${kbId}`),
  list: (kbId) => api.get(`/share/${kbId}`),
  revoke: (linkId) => api.delete(`/share/${linkId}`),
  verify: (token) => api.get(`/share/verify/${token}`),
};

// ─── Admin ──────────────────────────────────────────
export const adminAPI = {
  listUsers: () => api.get('/admin/users'),
  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),
  updateUserPhone: (id, phone) => api.put(`/admin/users/${id}/phone`, { phone }),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
};

// ─── Guest ──────────────────────────────────────────
export const guestAPI = {
  getKB: (token) => api.get(`/guest/kb?token=${token}`),
  chat: (data) => api.post('/guest/chat', data),
};

// ─── Settings ───────────────────────────────────────
export const settingsAPI = {
  getModel: () => api.get('/settings/model'),
  updateModel: (data) => api.put('/settings/model', data),
  getProviders: () => api.get('/settings/providers'),
  getBaiduOCR: () => api.get('/settings/baidu-ocr'),
  updateBaiduOCR: (data) => api.put('/settings/baidu-ocr', data),
  getSms: () => api.get('/settings/sms'),
  updateSms: (data) => api.put('/settings/sms', data),
  getSmsStatus: () => api.get('/settings/sms/status'),
  getSession: () => api.get('/settings/session'),
  updateSession: (data) => api.put('/settings/session', data),
};

// ─── Payment ────────────────────────────────────────
export const paymentAPI = {
  getPlans: () => api.get('/payment/plans'),
  createOrder: (data) => api.post('/payment/create-order', data),
  getOrder: (orderNo) => api.get(`/payment/order/${orderNo}`),
  simulatePay: (orderNo) => api.post(`/payment/simulate-pay/${orderNo}`),
  getConfig: () => api.get('/payment/config'),
  updateConfig: (data) => api.put('/payment/config', data),
};

// ─── KB Market ──────────────────────────────────────
export const marketAPI = {
  list: () => api.get('/kb-market/'),
  create: (data) => api.post('/kb-market/', data),
  update: (id, data) => api.put(`/kb-market/${id}`, data),
  delete: (id) => api.delete(`/kb-market/${id}`),
  use: (id) => api.post(`/kb-market/${id}/use`),
};

// ─── Misc ───────────────────────────────────────────
export const miscAPI = {
  health: () => api.get('/health'),
  supportedFormats: () => api.get('/supported-formats'),
};

export default api;
