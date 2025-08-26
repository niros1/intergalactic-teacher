import React, { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { processError, logError } from '../../utils/errorHandler'
import type { ProcessedError } from '../../utils/errorHandler'
import Button from '../ui/Button'

interface Props {
  children: ReactNode
  fallback?: (error: ProcessedError, resetError: () => void) => ReactNode
}

interface State {
  hasError: boolean
  error: any
  errorInfo: ErrorInfo | null
  processedError: ProcessedError | null
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      processedError: null
    }
  }

  static getDerivedStateFromError(error: any): Partial<State> {
    // Update state to show the fallback UI
    const processedError = processError(error, 'hebrew')
    return {
      hasError: true,
      error,
      processedError
    }
  }

  componentDidCatch(error: any, errorInfo: ErrorInfo) {
    // Log the error
    logError(error, 'React Error Boundary')
    
    this.setState({
      errorInfo
    })
  }

  resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      processedError: null
    })
  }

  render() {
    if (this.state.hasError && this.state.processedError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback(this.state.processedError, this.resetError)
      }

      // Default fallback UI
      return (
        <div className="min-h-screen bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
            {/* Error Icon */}
            <div className="mb-6">
              <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-red-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
              </div>
            </div>

            {/* Error Title */}
            <h1 className="text-2xl font-bold text-gray-900 mb-4 text-right">
              {this.state.processedError.title}
            </h1>

            {/* Error Message */}
            <p className="text-gray-600 mb-6 text-right leading-relaxed">
              {this.state.processedError.message}
            </p>

            {/* Action Buttons */}
            <div className="space-y-3">
              <Button
                onClick={this.resetError}
                className="w-full bg-blue-500 hover:bg-blue-600"
              >
                {this.state.processedError.action}
              </Button>

              <Button
                onClick={() => window.location.href = '/'}
                variant="secondary"
                className="w-full"
              >
                חזרו למסך הבית
              </Button>
            </div>

            {/* Development Error Details */}
            {import.meta.env.DEV && (
              <details className="mt-8 text-left">
                <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                  פרטי שגיאה טכניים (פיתוח)
                </summary>
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <pre className="text-xs text-gray-600 whitespace-pre-wrap break-words">
                    {this.state.error && this.state.error.toString()}
                    {this.state.errorInfo && this.state.errorInfo.componentStack}
                  </pre>
                </div>
              </details>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// HOC to wrap components with error boundary
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  fallback?: (error: ProcessedError, resetError: () => void) => ReactNode
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary fallback={fallback}>
      <Component {...props} />
    </ErrorBoundary>
  )
  
  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`
  
  return WrappedComponent
}

export default ErrorBoundary