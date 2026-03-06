import React, { createContext, useState, useContext, useEffect } from 'react'
import api from '../services/api'

const AuthContext = createContext()

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is already logged in (from session)
    const checkAuth = async () => {
      try {
        // We'll implement a check endpoint or rely on API calls
        // For now, user will be set when login succeeds
        setLoading(false)
      } catch (error) {
        setLoading(false)
      }
    }
    checkAuth()
  }, [])

  const login = async (username, password) => {
    try {
      const response = await api.post('/api/login', { username, password })
      return response.data
    } catch (error) {
      console.error('Login error:', error)
      const errorMessage = error.response?.data?.error || error.message || 'Login failed'
      throw { error: errorMessage }
    }
  }

  const verifyOTP = async (userId, otp) => {
    try {
      const response = await api.post('/api/verify-otp', { user_id: userId, otp })
      if (response.data.user) {
        setUser(response.data.user)
      }
      return response.data
    } catch (error) {
      console.error('OTP verification error:', error)
      const errorMessage = error.response?.data?.error || error.message || 'OTP verification failed'
      throw { error: errorMessage }
    }
  }

  const logout = async () => {
    try {
      await api.post('/api/logout')
    } catch (error) {
      console.error('Logout error:', error)
    }
    setUser(null)
  }

  const register = async (userData) => {
    try {
      const response = await api.post('/api/register', userData)
      return response.data
    } catch (error) {
      console.error('Registration error:', error)
      const errorMessage = error.response?.data?.error || error.message || 'Registration failed'
      throw { error: errorMessage }
    }
  }

  const value = {
    user,
    login,
    verifyOTP,
    logout,
    register,
    loading
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

