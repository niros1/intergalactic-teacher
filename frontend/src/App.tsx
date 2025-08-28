// React import not needed with new JSX transform
import { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'

// Error components
import { ErrorBoundary } from './components/error'


// Pages
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import SetupPage from './pages/child/SetupPage'
import DashboardPage from './pages/child/DashboardPage'
import ChatReadingPage from './pages/reading/ChatReadingPage'

// Layout Components
import Layout from './components/layout/Layout'
import AuthLayout from './components/layout/AuthLayout'

function App() {
  const { isAuthenticated, isLoading, initializeAuth } = useAuthStore()

  useEffect(() => {
    // Initialize auth state from localStorage
    initializeAuth()
  }, [initializeAuth])

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div>Loading...</div>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/auth/login" element={
          <AuthLayout>
            <LoginPage />
          </AuthLayout>
        } />
        <Route path="/auth/register" element={
          <AuthLayout>
            <RegisterPage />
          </AuthLayout>
        } />

        {/* Protected routes */}
        <Route path="/child/setup" element={
          isAuthenticated ? (
            <Layout>
              <SetupPage />
            </Layout>
          ) : (
            <Navigate to="/auth/login" replace />
          )
        } />
        <Route path="/child/dashboard" element={
          isAuthenticated ? (
            <Layout>
              <DashboardPage />
            </Layout>
          ) : (
            <Navigate to="/auth/login" replace />
          )
        } />
        {/* Redirect old reading route to chat interface */}
        <Route path="/reading" element={
          <Navigate to="/chat-reading" replace />
        } />
        
        <Route path="/chat-reading" element={
          isAuthenticated ? (
            <Layout>
              <ChatReadingPage />
            </Layout>
          ) : (
            <Navigate to="/auth/login" replace />
          )
        } />

        {/* Root redirect */}
        <Route path="/" element={
          isAuthenticated ? (
            <Navigate to="/child/dashboard" replace />
          ) : (
            <Navigate to="/auth/login" replace />
          )
        } />

        {/* Catch all route */}
        <Route path="*" element={
          <Navigate to={isAuthenticated ? "/child/dashboard" : "/auth/login"} replace />
        } />
      </Routes>
      </Router>
    </ErrorBoundary>
  )
}

export default App
