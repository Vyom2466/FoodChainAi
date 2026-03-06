import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
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


