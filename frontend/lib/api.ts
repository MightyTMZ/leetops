import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/jwt/refresh/`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          localStorage.setItem('access_token', access);
          
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/jwt/create/', { email, password });
    return response.data;
  },
  
  refreshToken: async (refreshToken: string) => {
    const response = await api.post('/auth/jwt/refresh/', { refresh: refreshToken });
    return response.data;
  },
  
  register: async (email: string, password: string, username: string, first_name: string, last_name: string) => {
    const response = await api.post('/auth/users/', {
      email,
      password,
      username,
      first_name,
      last_name,
    });
    return response.data;
  },
  
  getUserProfile: async () => {
    const response = await api.get('/auth/users/me/');
    return response.data;
  },
  
  updateProfile: async (data: any) => {
    const response = await api.patch('/auth/users/me/', data);
    return response.data;
  },
  
  changePassword: async (currentPassword: string, newPassword: string) => {
    const response = await api.post('/auth/users/set_password/', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },
};

// Company API
export const companyAPI = {
  getCompanies: async () => {
    const response = await api.get('/api/companies/');
    return response.data;
  },
  
  getCompany: async (companyId: number) => {
    const response = await api.get(`/api/companies/${companyId}/`);
    return response.data;
  },
};

// Simulation API
export const simulationAPI = {
  startSimulation: async (companyId: number, durationHours: number = 8) => {
    const response = await api.post('/api/simulation/start/', {
      company_id: companyId,
      duration_hours: durationHours,
    });
    return response.data;
  },
  
  generateIncident: async (sessionId: string, severity?: string, timeOfDay?: string) => {
    const response = await api.post('/api/simulation/incident/generate/', {
      session_id: sessionId,
      severity,
      time_of_day: timeOfDay,
    });
    return response.data;
  },
  
  resolveIncident: async (data: {
    incidentId: string;
    sessionId: string;
    resolutionApproach: string;
    codeChanges?: string;
    commandsExecuted?: string[];
    solutionType: 'root_cause' | 'workaround' | 'escalation' | 'abandonment';
    wasSuccessful: boolean;
  }) => {
    const response = await api.post('/api/simulation/incident/resolve/', data);
    return response.data;
  },
  
  endSimulation: async (sessionId: string) => {
    const response = await api.post('/api/simulation/end/', {
      session_id: sessionId,
    });
    return response.data;
  },
};

// User Rating API
export const ratingAPI = {
  getUserRating: async () => {
    const response = await api.get('/api/user/rating/');
    return response.data;
  },
};

// Admin API
export const adminAPI = {
  initializeCompanies: async () => {
    const response = await api.post('/api/admin/initialize-companies/');
    return response.data;
  },
};

export default api;
