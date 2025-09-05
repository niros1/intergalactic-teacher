import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { useChildStore } from '../../stores/childStore'

const Header: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const { currentChild } = useChildStore()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/auth/login')
    setShowUserMenu(false)
  }

  return (
    <header className="bg-white/90 backdrop-blur-sm border-b-2 border-purple-100 sticky top-0 z-40">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo/Brand */}
          <button
            onClick={() => navigate('/child/dashboard')}
            className="flex items-center space-x-3 hover:opacity-80 transition-opacity"
          >
            <span className="text-3xl">📚</span>
            <div>
              <h1 className="text-xl font-bold text-primary-700">
                Interactive Reading
              </h1>
              {currentChild && (
                <p className="text-sm text-gray-600">
                  {currentChild.language === 'hebrew' 
                    ? `שלום ${currentChild.name}` 
                    : `Hello, ${currentChild.name}`}
                </p>
              )}
            </div>
          </button>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            <button
              onClick={() => navigate('/child/dashboard')}
              className="text-child font-semibold text-gray-700 hover:text-primary-600 transition-colors"
            >
              {currentChild?.language === 'hebrew' ? 'סיפורים' : 'Stories'}
            </button>
            
            {/* Parent Dashboard Link - Future Feature */}
            <button
              onClick={() => {
                // TODO: Navigate to parent dashboard
                console.log('Parent dashboard coming soon!')
              }}
              className="text-child font-semibold text-gray-700 hover:text-primary-600 transition-colors"
            >
              {currentChild?.language === 'hebrew' ? 'דוח הורה' : 'Parent View'}
            </button>
          </nav>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 bg-primary-100 hover:bg-primary-200 rounded-child px-4 py-2 transition-colors"
            >
              <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center text-white font-bold">
                {user?.name.charAt(0).toUpperCase()}
              </div>
              <span className="text-child font-semibold text-gray-700">
                {user?.name}
              </span>
              <span className="text-gray-500">▼</span>
            </button>

            {/* Dropdown Menu */}
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-child shadow-child-lg border border-gray-100 py-2 z-50">
                <div className="px-4 py-2 border-b border-gray-100">
                  <p className="text-sm font-semibold text-gray-800">{user?.name}</p>
                  <p className="text-xs text-gray-500">{user?.email}</p>
                </div>
                
                <button
                  onClick={() => {
                    navigate('/child/edit')
                    setShowUserMenu(false)
                  }}
                  className="w-full text-left px-4 py-2 text-child text-gray-700 hover:bg-primary-50 transition-colors"
                >
                  {currentChild?.language === 'hebrew' ? 'הגדרות ילד' : 'Child Settings'}
                </button>
                
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-child text-red-600 hover:bg-red-50 transition-colors"
                >
                  {currentChild?.language === 'hebrew' ? 'התנתק' : 'Sign Out'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden mt-4 flex items-center justify-center space-x-8">
          <button
            onClick={() => navigate('/child/dashboard')}
            className="text-child font-semibold text-gray-700 hover:text-primary-600 transition-colors"
          >
            {currentChild?.language === 'hebrew' ? 'סיפורים' : 'Stories'}
          </button>
          
          <button
            onClick={() => {
              // TODO: Navigate to parent dashboard
              console.log('Parent dashboard coming soon!')
            }}
            className="text-child font-semibold text-gray-700 hover:text-primary-600 transition-colors"
          >
            {currentChild?.language === 'hebrew' ? 'דוח הורה' : 'Parent View'}
          </button>
        </div>
      </div>

      {/* Close dropdown when clicking outside */}
      {showUserMenu && (
        <div 
          className="fixed inset-0 z-30"
          onClick={() => setShowUserMenu(false)}
        />
      )}
    </header>
  )
}

export default Header