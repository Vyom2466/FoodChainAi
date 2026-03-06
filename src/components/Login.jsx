import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [otp, setOtp] = useState('')
  const [userId, setUserId] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showOTP, setShowOTP] = useState(false)
  const { login, verifyOTP } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    try {
      const response = await login(username, password)
      if (response.requires_otp) {
        setUserId(response.user_id)
        setShowOTP(true)
        setSuccess('OTP sent to your email. Please check and enter it below.')
      } else {
        navigate('/dashboard')
      }
    } catch (err) {
      console.error('Login error details:', err)
      const errorMsg = err.error || err.message || 'Login failed. Please check your credentials and try again.'
      setError(errorMsg)
    }
  }

  const handleOTPSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    try {
      await verifyOTP(userId, otp)
      navigate('/dashboard')
    } catch (err) {
      console.error('OTP verification error details:', err)
      const errorMsg = err.error || err.message || 'Invalid OTP. Please try again.'
      setError(errorMsg)
    }
  }

  return (
    <div className="row justify-content-center">
      <div className="col-md-5">
        <div className="card p-4">
          <h4 className="mb-3">Login</h4>
          
          {error && (
            <div className="alert alert-danger alert-dismissible fade show">
              {error}
              <button
                type="button"
                className="btn-close"
                onClick={() => setError('')}
              ></button>
            </div>
          )}
          
          {success && (
            <div className="alert alert-success alert-dismissible fade show">
              {success}
              <button
                type="button"
                className="btn-close"
                onClick={() => setSuccess('')}
              ></button>
            </div>
          )}

          {!showOTP ? (
            <form onSubmit={handleSubmit}>
              <div className="mb-2">
                <label className="form-label">Username</label>
                <input
                  type="text"
                  className="form-control"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
              <div className="mb-2">
                <label className="form-label">Password</label>
                <input
                  type="password"
                  className="form-control"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn btn-primary w-100">
                Login
              </button>
            </form>
          ) : (
            <form onSubmit={handleOTPSubmit}>
              <div className="mb-2">
                <label className="form-label">Enter OTP</label>
                <input
                  type="text"
                  className="form-control"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  placeholder="6-digit OTP"
                  maxLength="6"
                  required
                />
              </div>
              <button type="submit" className="btn btn-primary w-100">
                Verify OTP
              </button>
              <button
                type="button"
                className="btn btn-link w-100 mt-2"
                onClick={() => {
                  setShowOTP(false)
                  setOtp('')
                  setUserId(null)
                }}
              >
                Back to Login
              </button>
            </form>
          )}

          <div className="mt-3 text-center">
            <Link to="/register">Register your restaurant</Link>
          </div>
          <div className="mt-3 small-muted text-center">
            Demo: demo_rest / demo123
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login

