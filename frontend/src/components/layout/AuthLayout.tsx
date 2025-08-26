import React, { type ReactNode } from 'react'

interface AuthLayoutProps {
  children: ReactNode
}

const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex flex-col">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-purple-100">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-center">
            <h1 className="text-2xl font-bold text-primary-700 flex items-center space-x-2">
              <span className="text-3xl">📚</span>
              <span>Interactive Reading</span>
            </h1>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          {children}
        </div>
      </div>

      {/* Footer */}
      <div className="bg-white/60 backdrop-blur-sm border-t border-purple-100 py-4">
        <div className="container mx-auto px-6 text-center">
          <p className="text-sm text-gray-600">
            A safe, educational platform for children's reading development
          </p>
        </div>
      </div>
    </div>
  )
}

export default AuthLayout