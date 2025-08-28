import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'

const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const { login, isLoading, error, clearError, isAuthenticated } = useAuthStore()
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })

  // Navigate when authentication state changes
  useEffect(() => {
    if (isAuthenticated) {
      console.log('[LoginPage] Authenticated state changed, navigating to dashboard...')
      navigate('/child/dashboard')
    }
  }, [isAuthenticated, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    
    try {
      console.log('[LoginPage] Attempting login...')
      await login(formData)
      console.log('[LoginPage] Login completed')
      // Navigation will happen in useEffect when isAuthenticated changes
    } catch (error) {
      console.error('[LoginPage] Login failed:', error)
      // Error is handled by the store
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="card-child w-full max-w-md">
        <div className="text-center mb-6">
          <h1 className="heading-child">Welcome Back!</h1>
          <p className="text-child text-gray-600">
            Sign in to continue reading adventures
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-child font-semibold text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-3 text-child border-2 border-gray-200 rounded-child focus:border-primary-500 focus:outline-none transition-colors"
              required
            />
          </div>

          <div>
            <label className="block text-child font-semibold text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-3 text-child border-2 border-gray-200 rounded-child focus:border-primary-500 focus:outline-none transition-colors"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 border-2 border-red-200 rounded-child p-4">
              <p className="text-child text-red-600">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-child text-gray-600">
            Don't have an account?{' '}
            <Link to="/auth/register" className="text-primary-600 hover:text-primary-700 font-semibold">
              Sign up here
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage