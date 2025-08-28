import axios from 'axios'
import type { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import type { ApiResponse } from '../types'

// Base API configuration
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
console.log(`[API] BASE_URL: ${BASE_URL}`);

// Custom error class for API errors
export class ApiResponseError extends Error {
  public code?: string
  public details?: any
  public status?: number

  constructor(message: string, code?: string, details?: any, status?: number) {
    super(message)
    this.name = 'ApiResponseError'
    this.code = code
    this.details = details
    this.status = status
  }
}

// Token management
class TokenManager {
  private static ACCESS_TOKEN_KEY = 'access_token'
  private static REFRESH_TOKEN_KEY = 'refresh_token'

  static getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY)
  }

  static getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY)
  }

  static setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken)
  }

  static clearTokens(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY)
    localStorage.removeItem(this.REFRESH_TOKEN_KEY)
  }

  static isTokenExpired(token: string): boolean {
    if (!token) return true

    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const currentTime = Date.now() / 1000
      return payload.exp < currentTime
    } catch {
      return true
    }
  }
}

// Create axios instance
const createApiInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Request interceptor for auth tokens
  instance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = TokenManager.getAccessToken()
      console.log('[API] Request to:', config.url, 'Token exists:', !!token)
      if (token && !TokenManager.isTokenExpired(token)) {
        config.headers.Authorization = `Bearer ${token}`
        console.log('[API] Authorization header set')
      } else if (token) {
        console.log('[API] Token expired, not setting Authorization header')
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  // Response interceptor for error handling and token refresh
  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      // Transform successful responses to our ApiResponse format
      if (response.data && typeof response.data === 'object') {
        return response
      }
      return {
        ...response,
        data: {
          data: response.data,
          success: true,
        },
      }
    },
    async (error) => {
      const originalRequest = error.config

      // Handle token refresh for 401 errors
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true

        const refreshToken = TokenManager.getRefreshToken()
        if (refreshToken && !TokenManager.isTokenExpired(refreshToken)) {
          try {
            const refreshResponse = await axios.post(`${BASE_URL}/auth/refresh`, {
              refreshToken,
            })

            const { accessToken, refreshToken: newRefreshToken } = refreshResponse.data.data
            TokenManager.setTokens(accessToken, newRefreshToken)

            // Retry the original request with the new token
            originalRequest.headers.Authorization = `Bearer ${accessToken}`
            return instance(originalRequest)
          } catch (refreshError) {
            // Refresh failed, redirect to login
            TokenManager.clearTokens()
            window.location.href = '/login'
            return Promise.reject(refreshError)
          }
        } else {
          // No valid refresh token, redirect to login
          TokenManager.clearTokens()
          window.location.href = '/login'
        }
      }

      // Transform error response to our ApiError format
      const apiError = transformError(error)
      return Promise.reject(apiError)
    }
  )

  return instance
}

// Transform axios errors to our custom error format
const transformError = (error: any): ApiResponseError => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response
    const message = data?.message || data?.error || 'An error occurred'
    const code = data?.code || `HTTP_${status}`
    const details = data?.details || data

    return new ApiResponseError(message, code, details, status)
  } else if (error.request) {
    // Network error
    return new ApiResponseError(
      'Network error. Please check your connection.',
      'NETWORK_ERROR',
      error.request
    )
  } else {
    // Other error
    return new ApiResponseError(
      error.message || 'An unexpected error occurred',
      'UNKNOWN_ERROR',
      error
    )
  }
}

// Create and export the API instance
export const api = createApiInstance()

// Export token manager for use in stores
export { TokenManager }

// Generic API request wrapper with better error handling
export const apiRequest = async <T>(
  requestFn: () => Promise<AxiosResponse<ApiResponse<T>>>
): Promise<T> => {
  try {
    const response = await requestFn()

    // Handle successful response
    // The backend returns data directly, not wrapped in a success/data structure
    return response.data as T
  } catch (error) {
    if (error instanceof ApiResponseError) {
      throw error
    }
    throw transformError(error)
  }
}

// Helper function to get user-friendly error messages
export const getErrorMessage = (error: any): string => {
  if (error instanceof ApiResponseError) {
    // Map specific error codes to user-friendly messages
    switch (error.code) {
      case 'NETWORK_ERROR':
        return 'בעיית רשת. אנא בדקו את החיבור לאינטרנט.'
      case 'HTTP_401':
        return 'נדרשת התחברות מחדש. אנא התחברו שוב.'
      case 'HTTP_403':
        return 'אין לכם הרשאה לבצע פעולה זו.'
      case 'HTTP_404':
        return 'המידע המבוקש לא נמצא.'
      case 'HTTP_500':
        return 'שגיאה בשרת. אנא נסו שוב מאוחר יותר.'
      default:
        return error.message
    }
  }

  return 'אירעה שגיאה. אנא נסו שוב.'
}

// Export types for use in services
export type { AxiosResponse } from 'axios'