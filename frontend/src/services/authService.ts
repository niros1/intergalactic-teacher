import { api, apiRequest, TokenManager } from './api'
import type {
  LoginRequest,
  RegisterRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  AuthResponse,
  RefreshTokenRequest,
  User,
  ApiResponse,
} from '../types'

class AuthService {
  /**
   * Register a new user
   */
  async register(userData: RegisterRequest): Promise<AuthResponse> {
    const response = await apiRequest<AuthResponse>(() =>
      api.post<ApiResponse<AuthResponse>>('/auth/register', userData)
    )

    // Store tokens after successful registration
    TokenManager.setTokens(response.accessToken, response.refreshToken)
    
    return response
  }

  /**
   * Login user with email and password
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiRequest<AuthResponse>(() =>
      api.post<ApiResponse<AuthResponse>>('/auth/login', credentials)
    )

    console.log('[AuthService] Login response:', response)
    
    // Store tokens after successful login
    if (response.accessToken && response.refreshToken) {
      TokenManager.setTokens(response.accessToken, response.refreshToken)
      console.log('[AuthService] Tokens stored successfully')
    } else {
      console.error('[AuthService] Missing tokens in login response')
    }
    
    return response
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshToken(): Promise<AuthResponse> {
    const refreshToken = TokenManager.getRefreshToken()
    
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    const request: RefreshTokenRequest = { refreshToken }
    
    const response = await apiRequest<AuthResponse>(() =>
      api.post<ApiResponse<AuthResponse>>('/auth/refresh', request)
    )

    // Update stored tokens
    TokenManager.setTokens(response.accessToken, response.refreshToken)
    
    return response
  }

  /**
   * Logout user and clear tokens
   */
  async logout(): Promise<void> {
    try {
      // Attempt to call logout endpoint to invalidate server-side session
      const refreshToken = TokenManager.getRefreshToken()
      if (refreshToken) {
        await apiRequest<void>(() =>
          api.post<ApiResponse<void>>('/auth/logout', { refreshToken })
        )
      }
    } catch (error) {
      // Continue with logout even if server call fails
      console.warn('Server logout failed:', error)
    } finally {
      // Always clear local tokens
      TokenManager.clearTokens()
    }
  }

  /**
   * Request password reset email
   */
  async forgotPassword(email: string): Promise<void> {
    const request: ForgotPasswordRequest = { email }
    
    await apiRequest<void>(() =>
      api.post<ApiResponse<void>>('/auth/forgot-password', request)
    )
  }

  /**
   * Reset password using reset token
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    const request: ResetPasswordRequest = { token, newPassword }
    
    await apiRequest<void>(() =>
      api.post<ApiResponse<void>>('/auth/reset-password', request)
    )
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    return await apiRequest<User>(() =>
      api.get<ApiResponse<User>>('/users/me')
    )
  }

  /**
   * Update user profile
   */
  async updateProfile(updates: Partial<User>): Promise<User> {
    return await apiRequest<User>(() =>
      api.put<ApiResponse<User>>('/users/me', updates)
    )
  }

  /**
   * Check if user is authenticated (has valid tokens)
   */
  isAuthenticated(): boolean {
    const accessToken = TokenManager.getAccessToken()
    const refreshToken = TokenManager.getRefreshToken()
    
    console.log('[AuthService] Token check:', {
      hasAccessToken: !!accessToken,
      hasRefreshToken: !!refreshToken,
      accessTokenExpired: accessToken ? TokenManager.isTokenExpired(accessToken) : 'N/A',
      refreshTokenExpired: refreshToken ? TokenManager.isTokenExpired(refreshToken) : 'N/A'
    })
    
    // Check if we have tokens and at least one is not expired
    return !!(
      accessToken && refreshToken && 
      (!TokenManager.isTokenExpired(accessToken) || !TokenManager.isTokenExpired(refreshToken))
    )
  }

  /**
   * Get stored access token
   */
  getAccessToken(): string | null {
    return TokenManager.getAccessToken()
  }

  /**
   * Get stored refresh token
   */
  getRefreshToken(): string | null {
    return TokenManager.getRefreshToken()
  }

  /**
   * Clear all authentication data
   */
  clearAuthData(): void {
    TokenManager.clearTokens()
  }

  /**
   * Initialize auth state from stored tokens
   * Returns user data if tokens are valid, null otherwise
   */
  async initializeAuth(): Promise<User | null> {
    console.log('[AuthService] Checking if authenticated...')
    if (!this.isAuthenticated()) {
      console.log('[AuthService] Not authenticated (no valid tokens)')
      return null
    }

    try {
      console.log('[AuthService] Fetching current user...')
      const user = await this.getCurrentUser()
      console.log('[AuthService] Successfully fetched user:', user)
      return user
    } catch (error) {
      console.error('[AuthService] Failed to get current user:', error)
      // If getting current user fails, clear invalid tokens
      this.clearAuthData()
      return null
    }
  }
}

// Create and export singleton instance
export const authService = new AuthService()
export default authService