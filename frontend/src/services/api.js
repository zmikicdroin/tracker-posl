import axios from 'axios';

// Detect API URL based on environment
const getApiUrl = () => {
  // If accessing from network, use the host's IP
  const hostname = window.location.hostname;
  
  // If localhost or 127.0.0.1, use localhost
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:5000/api';
  }
  
  // Otherwise use the same hostname with port 5000
  return `http://${hostname}:5000/api`;
};

const API_URL = getApiUrl();

console.log('API URL:', API_URL); // Debug log

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_URL,
  timeout: 10000, // 10 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Automatically attach JWT token to every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors globally
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle token expiration
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname;
      
      // Only redirect to login if not already there
      if (currentPath !== '/login' && currentPath !== '/') {
        localStorage.removeItem('token');
        window.location.href = '/';
      }
    }
    
    // Handle network errors
    if (!error.response) {
      console.error('Network error - Backend server may be down');
      error.message = 'Unable to connect to server. Please check if the backend is running.';
    }
    
    return Promise.reject(error);
  }
);

// ============================================
// AUTH ENDPOINTS
// ============================================

export const register = (username, email, password) => {
  return api.post('/register', { 
    username, 
    email, 
    password 
  });
};

export const login = (username, password) => {
  return api.post('/login', { 
    username, 
    password 
  });
};

export const logout = () => {
  localStorage.removeItem('token');
  window.location.href = '/';
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};

// ============================================
// APPLICATION ENDPOINTS
// ============================================

export const getApplications = () => {
  return api.get('/applications');
};

export const getApplication = (id) => {
  return api.get(`/applications/${id}`);
};

export const createApplication = (formData) => {
  return api.post('/applications', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const updateApplication = (id, formData) => {
  return api.put(`/applications/${id}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const updateApplicationStatus = (id, status) => {
  return api.patch(`/applications/${id}/status`, { status });
};

export const deleteApplication = (id) => {
  return api.delete(`/applications/${id}`);
};

export const downloadCV = (filename) => {
  return api.get(`/uploads/${filename}`, {
    responseType: 'blob',
  });
};

// ============================================
// STATISTICS ENDPOINTS
// ============================================

export const getStats = () => {
  return api.get('/stats');
};

// ============================================
// HELPER FUNCTIONS
// ============================================

export const formatDateForAPI = (date) => {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const createApplicationFormData = (data, cvFile = null) => {
  const formData = new FormData();
  
  formData.append('company', data.company);
  formData.append('application_date', data.application_date);
  
  if (data.cover_letter) {
    formData.append('cover_letter', data.cover_letter);
  }
  
  if (data.status) {
    formData.append('status', data.status);
  }
  
  if (cvFile) {
    formData.append('cv', cvFile);
  }
  
  return formData;
};

export const getErrorMessage = (error) => {
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  
  if (error.message) {
    return error.message;
  }
  
  return 'An unexpected error occurred';
};

export default api;