import React, { useEffect, useState } from 'react'
import type { ProcessedError } from '../../utils/errorHandler'

interface ErrorToastProps {
  error: ProcessedError
  onDismiss: () => void
  autoHide?: boolean
  duration?: number
}

export const ErrorToast: React.FC<ErrorToastProps> = ({
  error,
  onDismiss,
  autoHide = true,
  duration = 5000
}) => {
  const [isVisible, setIsVisible] = useState(true)
  const [isExiting, setIsExiting] = useState(false)

  useEffect(() => {
    if (autoHide) {
      const timer = setTimeout(() => {
        handleDismiss()
      }, duration)

      return () => clearTimeout(timer)
    }
  }, [autoHide, duration])

  const handleDismiss = () => {
    setIsExiting(true)
    setTimeout(() => {
      setIsVisible(false)
      onDismiss()
    }, 300) // Animation duration
  }

  if (!isVisible) return null

  const getColorClasses = () => {
    switch (error.category) {
      case 'network':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      case 'authentication':
      case 'authorization':
        return 'bg-red-50 border-red-200 text-red-800'
      case 'validation':
        return 'bg-orange-50 border-orange-200 text-orange-800'
      case 'server_error':
        return 'bg-red-50 border-red-200 text-red-800'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800'
    }
  }

  const getIconColor = () => {
    switch (error.category) {
      case 'network':
        return 'text-yellow-500'
      case 'authentication':
      case 'authorization':
      case 'server_error':
        return 'text-red-500'
      case 'validation':
        return 'text-orange-500'
      default:
        return 'text-gray-500'
    }
  }

  const getIcon = () => {
    switch (error.category) {
      case 'network':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M12 2a10 10 0 100 20 10 10 0 000-20z" />
          </svg>
        )
      case 'authentication':
      case 'authorization':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        )
      case 'validation':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        )
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )
    }
  }

  return (
    <div
      className={`
        fixed top-4 right-4 z-50 max-w-md w-full transform transition-all duration-300 ease-in-out
        ${isExiting ? 'translate-x-full opacity-0' : 'translate-x-0 opacity-100'}
      `}
    >
      <div className={`
        rounded-lg border p-4 shadow-lg
        ${getColorClasses()}
      `}>
        <div className="flex items-start">
          <div className={`flex-shrink-0 ${getIconColor()}`}>
            {getIcon()}
          </div>
          
          <div className="mr-3 flex-1">
            <h3 className="text-sm font-semibold text-right">
              {error.title}
            </h3>
            <p className="mt-1 text-sm text-right">
              {error.message}
            </p>
            
            {error.shouldRetry && (
              <div className="mt-3 flex justify-end">
                <button
                  onClick={handleDismiss}
                  className="text-sm font-medium underline hover:no-underline"
                >
                  {error.action}
                </button>
              </div>
            )}
          </div>
          
          <div className="flex-shrink-0 mr-1">
            <button
              onClick={handleDismiss}
              className="inline-flex rounded-md p-1.5 hover:bg-white hover:bg-opacity-20 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2"
            >
              <span className="sr-only">סגור</span>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Hook for managing error toasts
export const useErrorToast = () => {
  const [errors, setErrors] = useState<Array<{ id: string; error: ProcessedError }>>([])

  const showError = (error: ProcessedError) => {
    const id = Date.now().toString()
    setErrors(prev => [...prev, { id, error }])
  }

  const dismissError = (id: string) => {
    setErrors(prev => prev.filter(e => e.id !== id))
  }

  const clearAll = () => {
    setErrors([])
  }

  const ErrorToastContainer = () => (
    <>
      {errors.map(({ id, error }) => (
        <ErrorToast
          key={id}
          error={error}
          onDismiss={() => dismissError(id)}
        />
      ))}
    </>
  )

  return { showError, clearAll, ErrorToastContainer }
}

export default ErrorToast