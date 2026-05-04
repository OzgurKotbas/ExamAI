import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const authApi = {
  register: (data) =>
    api.post('/auth/register', data),

  login: (email, password) => {
    const form = new FormData();
    form.append('email', email);
    form.append('password', password);
    return api.post('/auth/login', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  me: () => api.get('/auth/me'),

  forgotPassword: (email) =>
    api.post('/auth/forgot-password', { email }),

  resetPassword: (data) =>
    api.post('/auth/reset-password', data),

  googleLogin: () => {
    window.location.href = `${API_BASE_URL}/api/v1/auth/google`;
  },

  updateProfile: (fullName, email, geminiApiKey) => {
    const form = new FormData();
    form.append('full_name', fullName);
    form.append('email', email);
    if (geminiApiKey !== undefined) {
      form.append('gemini_api_key', geminiApiKey || '');
    }
    return api.put('/auth/profile', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  changePassword: (currentPassword, newPassword) => {
    const form = new FormData();
    form.append('current_password', currentPassword);
    form.append('new_password', newPassword);
    return api.post('/auth/change-password', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// ─── Notes ────────────────────────────────────────────────────────────────────

export const notesApi = {
  upload: (files) => {
    const form = new FormData();
    files.forEach((file) => {
      form.append('files', file);
    });
    return api.post('/notes', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  list: () => api.get('/notes'),
};

// ─── Quizzes ──────────────────────────────────────────────────────────────────

export const quizzesApi = {
  create: (data) => api.post('/quizzes', data),

  getStatus: (quizId) => api.get(`/quizzes/${quizId}/status`),

  getQuestions: (quizId) => api.get(`/quizzes/${quizId}/questions`),

  list: () => api.get('/quizzes'),

  submit: (quizId, answers) =>
    api.post(`/quizzes/${quizId}/submit`, { quiz_id: quizId, answers }),

  getGradingStatus: (quizId, gradingId) =>
    api.get(`/quizzes/${quizId}/grading/${gradingId}/status`),

  getResults: (quizId, gradingId) =>
    api.get(`/quizzes/${quizId}/grading/${gradingId}`),

  delete: (quizId) => api.delete(`/quizzes/${quizId}`),

  getAnalytics: () => api.get('/quizzes/analytics'),
};

export default api;
