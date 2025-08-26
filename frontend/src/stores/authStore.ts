import { create } from 'zustand'
import { type AuthState, type User, type LoginRequest, type RegisterRequest } from '../types'

interface AuthStore extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>
  register: (userData: RegisterRequest) => Promise<void>
  logout: () => void
  setUser: (user: User | null) => void
  clearError: () => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (credentials: LoginRequest) => {
    set({ isLoading: true, error: null })
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Mock successful login
      const mockUser: User = {
        id: '1',
        email: credentials.email,
        name: 'Parent User',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }
      
      set({ 
        user: mockUser, 
        isAuthenticated: true, 
        isLoading: false 
      })
      
      // Store user data in localStorage
      localStorage.setItem('user', JSON.stringify(mockUser))
    } catch (error) {
      set({ 
        error: 'Login failed. Please check your credentials.', 
        isLoading: false 
      })
    }
  },

  register: async (userData: RegisterRequest) => {
    set({ isLoading: true, error: null })
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Mock successful registration
      const newUser: User = {
        id: Date.now().toString(),
        email: userData.email,
        name: userData.name,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }
      
      set({ 
        user: newUser, 
        isAuthenticated: true, 
        isLoading: false 
      })
      
      localStorage.setItem('user', JSON.stringify(newUser))
    } catch (error) {
      set({ 
        error: 'Registration failed. Please try again.', 
        isLoading: false 
      })
    }
  },

  logout: () => {
    set({ 
      user: null, 
      isAuthenticated: false, 
      error: null 
    })
    localStorage.removeItem('user')
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
}))

// Initialize auth state from localStorage
const storedUser = localStorage.getItem('user')
if (storedUser) {
  try {
    const user = JSON.parse(storedUser)
    useAuthStore.getState().setUser(user)
  } catch (error) {
    localStorage.removeItem('user')
  }
}