import axios from 'axios'

// Use VITE_API_URL from environment variables if provided, otherwise use relative path
const baseURL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

const api = axios.create({
  baseURL: baseURL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add auth token to requests
api.interceptors.request.use(
  (config) => {
    // Session-based auth, so we just send credentials
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Don't redirect on 401 if we're already on login page
    if (error.response?.status === 401 && !window.location.pathname.includes('/login')) {
      // Handle unauthorized
      window.location.href = '/login'
    }
    // Return error so components can handle it
    return Promise.reject(error)
  }
)

export default api


