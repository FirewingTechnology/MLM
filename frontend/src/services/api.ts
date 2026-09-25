import axios from 'axios';

/**
 * Resolves the backend API base URL.
 * - In production: VITE_API_URL (e.g. "https://api.mystatusads333.com/api")
 * - In development fallback: "/api" (proxied through Vite to backend)
 */
export const getBaseURL = (): string => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim() !== '') {
    let formatted = envUrl.trim();

    // If it's a relative path, return clean relative base
    if (formatted.startsWith('/')) {
      return formatted.replace(/\/+$/, '');
    }

    // Ensure clean protocol (strictly enforce HTTPS for production and under HTTPS browser context)
    let protocol = 'https://';
    if (formatted.startsWith('http://')) {
      if (typeof window !== 'undefined' && window.location?.protocol === 'https:') {
        protocol = 'https://';
      } else if (formatted.includes('onrender.com') || formatted.includes('mystatusads333.com')) {
        protocol = 'https://';
      } else {
        protocol = 'http://';
      }
    }

    // Strip existing protocol for normalization
    formatted = formatted.replace(/^https?:\/\//i, '');

    // Remove any trailing slashes
    formatted = formatted.replace(/\/+$/, '');

    // Ensure /api suffix is present without duplication
    if (!formatted.endsWith('/api') && !formatted.includes('/api/')) {
      formatted = `${formatted}/api`;
    }

    return `${protocol}${formatted}`;
  }

  // If running in browser on Render, automatically default to the Render backend service
  if (typeof window !== 'undefined' && window.location?.hostname.includes('onrender.com')) {
    return 'https://mlm-backend-xl1p.onrender.com/api';
  }

  // Development default fallback
  return '/api';
};

/**
 * Extracts clean, user-friendly error message from Axios errors
 */
export const getApiErrorMessage = (error: unknown, fallbackMessage = 'An unexpected error occurred. Please try again.'): string => {
  if (axios.isAxiosError(error)) {
    // Backend standard error format: { error: { message: "..." } } or { detail: "..." }
    const resData = error.response?.data;
    if (resData) {
      if (typeof resData.error === 'object' && resData.error?.message) {
        return resData.error.message;
      }
      if (typeof resData.error === 'string') {
        return resData.error;
      }
      if (typeof resData.detail === 'string') {
        return resData.detail;
      }
      if (typeof resData.message === 'string') {
        return resData.message;
      }
    }
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      return 'Request timed out. Please check your internet connection and retry.';
    }
    if (!error.response && error.message === 'Network Error') {
      return 'Unable to connect to the backend server. Please verify network connectivity.';
    }
    if (error.response?.status === 403) {
      return 'Access denied. You do not have permission to perform this action.';
    }
    if (error.response?.status === 404) {
      return 'Requested resource was not found.';
    }
    if (error.response?.status === 429) {
      return 'Too many requests. Please slow down and try again later.';
    }
    if (error.response && error.response.status >= 500) {
      return 'The server encountered an error processing your request. Please try again later.';
    }
  } else if (error instanceof Error) {
    return error.message;
  }
  return fallbackMessage;
};

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for JWT Auth Header
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token') || localStorage.getItem('mlm_demo_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for token expiration & 401 handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const currentPath = window.location.pathname;
      if (!currentPath.includes('/login') && !currentPath.includes('/register')) {
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
