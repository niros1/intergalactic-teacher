import { ApiResponseError } from '../services/api'

// Error categories for better UX
export const ErrorCategory = {
  NETWORK: 'network',
  AUTHENTICATION: 'authentication',
  AUTHORIZATION: 'authorization',
  VALIDATION: 'validation',
  NOT_FOUND: 'not_found',
  SERVER_ERROR: 'server_error',
  UNKNOWN: 'unknown'
} as const

export type ErrorCategoryType = typeof ErrorCategory[keyof typeof ErrorCategory]

// Mapping of error codes to categories
const errorCategoryMap: Record<string, ErrorCategoryType> = {
  NETWORK_ERROR: ErrorCategory.NETWORK,
  HTTP_401: ErrorCategory.AUTHENTICATION,
  HTTP_403: ErrorCategory.AUTHORIZATION,
  HTTP_404: ErrorCategory.NOT_FOUND,
  HTTP_422: ErrorCategory.VALIDATION,
  HTTP_400: ErrorCategory.VALIDATION,
  HTTP_500: ErrorCategory.SERVER_ERROR,
  HTTP_502: ErrorCategory.SERVER_ERROR,
  HTTP_503: ErrorCategory.SERVER_ERROR,
}

// Hebrew error messages for user-friendly display
const hebrewErrorMessages: Record<ErrorCategoryType, Record<string, string>> = {
  [ErrorCategory.NETWORK]: {
    title: 'בעיית תקשורת',
    message: 'בעיה בחיבור לאינטרנט. אנא בדקו את החיבור ונסו שוב.',
    action: 'נסו שוב'
  },
  [ErrorCategory.AUTHENTICATION]: {
    title: 'נדרשת התחברות',
    message: 'ההתחברות פגה. אנא התחברו מחדש.',
    action: 'התחברו'
  },
  [ErrorCategory.AUTHORIZATION]: {
    title: 'אין הרשאה',
    message: 'אין לכם הרשאה לבצע פעולה זו.',
    action: 'חזרו למסך הראשי'
  },
  [ErrorCategory.VALIDATION]: {
    title: 'נתונים שגויים',
    message: 'יש לבדוק את הנתונים ולמלא את כל השדות הנדרשים.',
    action: 'תקנו ונסו שוב'
  },
  [ErrorCategory.NOT_FOUND]: {
    title: 'לא נמצא',
    message: 'המידע המבוקש לא נמצא במערכת.',
    action: 'חזרו למסך הראשי'
  },
  [ErrorCategory.SERVER_ERROR]: {
    title: 'שגיאת שרת',
    message: 'אירעה שגיאה במערכת. אנא נסו שוב מאוחר יותר.',
    action: 'נסו שוב מאוחר יותר'
  },
  [ErrorCategory.UNKNOWN]: {
    title: 'שגיאה לא צפויה',
    message: 'אירעה שגיאה לא צפויה. אנא נסו שוב.',
    action: 'נסו שוב'
  }
}

// English error messages (fallback)
const englishErrorMessages: Record<ErrorCategoryType, Record<string, string>> = {
  [ErrorCategory.NETWORK]: {
    title: 'Connection Problem',
    message: 'Network connection issue. Please check your internet connection and try again.',
    action: 'Try Again'
  },
  [ErrorCategory.AUTHENTICATION]: {
    title: 'Login Required',
    message: 'Your session has expired. Please log in again.',
    action: 'Log In'
  },
  [ErrorCategory.AUTHORIZATION]: {
    title: 'Access Denied',
    message: 'You do not have permission to perform this action.',
    action: 'Go Back'
  },
  [ErrorCategory.VALIDATION]: {
    title: 'Invalid Data',
    message: 'Please check your data and fill in all required fields.',
    action: 'Fix and Try Again'
  },
  [ErrorCategory.NOT_FOUND]: {
    title: 'Not Found',
    message: 'The requested information was not found.',
    action: 'Go Home'
  },
  [ErrorCategory.SERVER_ERROR]: {
    title: 'Server Error',
    message: 'A server error occurred. Please try again later.',
    action: 'Try Again Later'
  },
  [ErrorCategory.UNKNOWN]: {
    title: 'Unexpected Error',
    message: 'An unexpected error occurred. Please try again.',
    action: 'Try Again'
  }
}

export interface ProcessedError {
  category: ErrorCategoryType
  title: string
  message: string
  action: string
  originalError: any
  shouldRetry: boolean
  requiresAuth: boolean
}

// Process error and return user-friendly information
export const processError = (error: any, language: 'hebrew' | 'english' = 'hebrew'): ProcessedError => {
  let category: ErrorCategoryType = ErrorCategory.UNKNOWN
  // let originalMessage = ''

  if (error instanceof ApiResponseError) {
    category = errorCategoryMap[error.code || ''] || ErrorCategory.UNKNOWN
    // originalMessage = error.message
  } else if (error instanceof Error) {
    // originalMessage = error.message
    // Try to categorize based on message content
    if (error.message.includes('network') || error.message.includes('fetch')) {
      category = ErrorCategory.NETWORK
    }
  }

  const messages = language === 'hebrew' ? hebrewErrorMessages : englishErrorMessages
  const errorInfo = messages[category]

  return {
    category,
    title: errorInfo.title,
    message: errorInfo.message,
    action: errorInfo.action,
    originalError: error,
    shouldRetry: [ErrorCategory.NETWORK, ErrorCategory.SERVER_ERROR].includes(category as any),
    requiresAuth: category === ErrorCategory.AUTHENTICATION
  }
}

// Log error to console with additional context
export const logError = (error: any, context?: string) => {
  const errorInfo = {
    message: error?.message || 'Unknown error',
    stack: error?.stack,
    context,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: window.location.href
  }

  console.error('Application Error:', errorInfo)

  // In production, you might want to send this to an error tracking service
  if (!import.meta.env.DEV) {
    // Example: Send to error tracking service
    // errorTrackingService.captureError(errorInfo)
  }
}

// Handle errors in async operations with optional retry logic
export const handleAsyncError = async <T>(
  operation: () => Promise<T>,
  context?: string,
  maxRetries: number = 0,
  retryDelay: number = 1000
): Promise<T> => {
  let lastError: any
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation()
    } catch (error) {
      lastError = error
      
      const processedError = processError(error)
      
      // Log the error with context
      logError(error, `${context} (attempt ${attempt + 1}/${maxRetries + 1})`)
      
      // Don't retry for certain error types
      if (!processedError.shouldRetry || attempt === maxRetries) {
        break
      }
      
      // Wait before retrying
      if (attempt < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, retryDelay * (attempt + 1)))
      }
    }
  }
  
  throw lastError
}

// React hook for error handling in components
export const useErrorHandler = () => {
  const handleError = (error: any, context?: string) => {
    const processedError = processError(error, 'hebrew')
    logError(error, context)
    
    // You could dispatch to a global error state here
    // or show a toast notification
    
    return processedError
  }

  return { handleError, processError, logError }
}

// Specific error handlers for different domains
export const authErrorHandler = (error: any) => {
  const processedError = processError(error, 'hebrew')
  
  if (processedError.requiresAuth) {
    // Redirect to login
    window.location.href = '/login'
  }
  
  return processedError
}

export const childErrorHandler = (error: any) => {
  const processedError = processError(error, 'hebrew')
  
  // Add child-specific error handling logic
  if (processedError.category === ErrorCategory.NOT_FOUND) {
    // Child not found - maybe redirect to child selection
    console.log('Child not found, redirecting to child selection')
  }
  
  return processedError
}

export const storyErrorHandler = (error: any) => {
  const processedError = processError(error, 'hebrew')
  
  // Add story-specific error handling logic
  if (processedError.category === ErrorCategory.VALIDATION) {
    // Story generation failed due to validation
    console.log('Story generation validation error')
  }
  
  return processedError
}

// Export error categories for use in components
export { ErrorCategory as ErrorType }