import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'

const RegisterPage: React.FC = () => {
  const navigate = useNavigate()
  const { register, isLoading, error, clearError } = useAuthStore()
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    
    if (formData.password !== formData.confirmPassword) {
      // Handle password mismatch
      return
    }
    
    try {
      await register({
        name: formData.name,
        email: formData.email,
        password: formData.password,
      })
      navigate('/child/setup')
    } catch (error) {
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
    <div className="min-h-screen flex items-center justify-center py-8">
      <div className="card-child w-full max-w-md">
        <div className="text-center mb-6">
          <h1 className="heading-child">Join Our Reading Adventure!</h1>
          <p className="text-child text-gray-600">
            Create an account to start personalized stories
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-child font-semibold text-gray-700 mb-2">
              Your Name
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full px-4 py-3 text-child border-2 border-gray-200 rounded-child focus:border-primary-500 focus:outline-none transition-colors"
              required
            />
          </div>

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

          <div>
            <label className="block text-child font-semibold text-gray-700 mb-2">
              Confirm Password
            </label>
            <input
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
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
            {isLoading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-child text-gray-600">
            Already have an account?{' '}
            <Link to="/auth/login" className="text-primary-600 hover:text-primary-700 font-semibold">
              Sign in here
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage