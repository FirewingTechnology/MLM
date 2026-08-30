import axios from 'axios';

const getBaseURL = () => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim() !== '') {
    let formatted = envUrl.trim();
    if (formatted.startsWith('/')) {
      return formatted;
    }
    
    let protocol = 'https://';
    if (formatted.startsWith('http://')) {
      protocol = 'http://';
    }

    // Strip protocol
    formatted = formatted.replace(/^https?:\/\//i, '');
    
    // If hostname has no dot (like 'mlm-backend-x11p' injected by Render blueprint), append .onrender.com
    const parts = formatted.split('/');
    let hostPart = parts[0];
    if (!hostPart.includes('.') && !hostPart.startsWith('localhost') && !hostPart.startsWith('127.0.0.1')) {
      hostPart = `${hostPart}.onrender.com`;
      parts[0] = hostPart;
      formatted = parts.join('/');
    }

    formatted = `${protocol}${formatted}`;

    if (!formatted.endsWith('/api') && !formatted.includes('/api/')) {
      formatted = `${formatted.replace(/\/$/, '')}/api`;
    }
    return formatted;
  }
  return '/api';
};

const api = axios.create({
  baseURL: getBaseURL(),
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token') || localStorage.getItem('mlm_demo_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        localStorage.removeItem('mlm_demo_token');
        localStorage.removeItem('mlm_demo_user');
        window.location.href = '/login?expired=true';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
