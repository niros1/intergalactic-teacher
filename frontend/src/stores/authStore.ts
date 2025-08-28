import { create } from 'zustand'
import { type AuthState, type User, type LoginRequest, type RegisterRequest } from '../types'
import authService from '../services/authService'
import { getErrorMessage } from '../services/api'

interface AuthStore extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>
  register: (userData: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  setUser: (user: User | null) => void
  clearError: () => void
  forgotPassword: (email: string) => Promise<void>
  resetPassword: (token: string, newPassword: string) => Promise<void>
  initializeAuth: () => Promise<void>
  updateProfile: (updates: Partial<User>) => Promise<void>
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true, // Start with loading true since we need to check auth on mount
  error: null,

  login: async (credentials: LoginRequest) => {
    console.log('[AuthStore] Starting login...')
    set({ isLoading: true, error: null })
    try {
      const authResponse = await authService.login(credentials)
      console.log('[AuthStore] Got auth response:', authResponse)
      
      set({ 
        user: authResponse.user, 
        isAuthenticated: true, 
        isLoading: false 
      })
      console.log('[AuthStore] Auth state updated')
      
      // Store user data in localStorage
      localStorage.setItem('user', JSON.stringify(authResponse.user))
      console.log('[AuthStore] User data stored in localStorage')
    } catch (error) {
      console.error('[AuthStore] Login failed:', error)
      const errorMessage = getErrorMessage(error)
      set({ 
        error: errorMessage, 
        isLoading: false 
      })
      throw error // Re-throw so components can handle it
    }
  },

  register: async (userData: RegisterRequest) => {
    set({ isLoading: true, error: null })
    try {
      const authResponse = await authService.register(userData)
      
      set({ 
        user: authResponse.user, 
        isAuthenticated: true, 
        isLoading: false 
      })
      
      localStorage.setItem('user', JSON.stringify(authResponse.user))
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({ 
        error: errorMessage, 
        isLoading: false 
      })
      throw error // Re-throw so components can handle it
    }
  },

  logout: async () => {
    set({ isLoading: true })
    try {
      await authService.logout()
    } catch (error) {
      // Continue with logout even if server call fails
      console.warn('Server logout failed:', error)
    } finally {
      set({ 
        user: null, 
        isAuthenticated: false, 
        error: null,
        isLoading: false
      })
      localStorage.removeItem('user')
    }
  },

  setUser: (user: User | null) => {
    set({ 
      user, 
      isAuthenticated: !!user 
    })
  },

  clearError: () => {
    set({ error: null })
  },

  forgotPassword: async (email: string) => {
    set({ isLoading: true, error: null })
    try {
      await authService.forgotPassword(email)
      set({ isLoading: false })
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({ 
        error: errorMessage, 
        isLoading: false 
      })
      throw error
    }
  },

  resetPassword: async (token: string, newPassword: string) => {
    set({ isLoading: true, error: null })
    try {
      await authService.resetPassword(token, newPassword)
      set({ isLoading: false })
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({ 
        error: errorMessage, 
        isLoading: false 
      })
      throw error
    }
  },

  initializeAuth: async () => {
    console.log('[AuthStore] Initializing auth...')
    // Don't override if we're already authenticated (e.g., from a recent login)
    const currentState = useAuthStore.getState()
    if (currentState.isAuthenticated) {
      console.log('[AuthStore] Already authenticated, skipping initialization')
      set({ isLoading: false })
      return
    }
    
    set({ isLoading: true })
    try {
      const user = await authService.initializeAuth()
      console.log('[AuthStore] User from initializeAuth:', user)
      if (user) {
        console.log('[AuthStore] Setting authenticated state with user:', user)
        set({ 
          user, 
          isAuthenticated: true, 
          isLoading: false 
        })
        localStorage.setItem('user', JSON.stringify(user))
      } else {
        console.log('[AuthStore] No user returned, clearing auth')
        set({ 
          user: null, 
          isAuthenticated: false, 
          isLoading: false 
        })
        localStorage.removeItem('user')
      }
    } catch (error) {
      console.error('[AuthStore] Error during initializeAuth:', error)
      set({ 
        user: null, 
        isAuthenticated: false, 
        isLoading: false 
      })
      localStorage.removeItem('user')
    }
  },

  updateProfile: async (updates: Partial<User>) => {
    set({ isLoading: true, error: null })
    try {
      const updatedUser = await authService.updateProfile(updates)
      set({ 
        user: updatedUser, 
        isLoading: false 
      })
      localStorage.setItem('user', JSON.stringify(updatedUser))
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({ 
        error: errorMessage, 
        isLoading: false 
      })
      throw error
    }
  },
}))