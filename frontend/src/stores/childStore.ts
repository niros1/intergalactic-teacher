import { create } from 'zustand'
import { type ChildState, type Child, type CreateChildRequest, type UpdateChildRequest, type ChildWithProgress, type DashboardData, type ReadingAssessmentRequest, type ReadingAssessmentResult } from '../types'
import childService from '../services/childService'
import { getErrorMessage } from '../services/api'

interface ChildStore extends ChildState {
  setCurrentChild: (child: Child | null) => void
  addChild: (childData: CreateChildRequest) => Promise<Child>
  updateChild: (childId: string, updates: UpdateChildRequest) => Promise<Child>
  deleteChild: (childId: string) => Promise<void>
  loadChildren: () => Promise<void>
  getChildWithProgress: (childId: string) => Promise<ChildWithProgress>
  getDashboard: (childId: string) => Promise<DashboardData>
  conductAssessment: (childId: string, assessment: ReadingAssessmentRequest) => Promise<ReadingAssessmentResult>
  uploadProfilePicture: (childId: string, file: File) => Promise<string>
  clearError: () => void
}

export const useChildStore = create<ChildStore>((set) => ({
  currentChild: null,
  children: [],
  isLoading: false,
  error: null,

  setCurrentChild: (child: Child | null) => {
    set({ currentChild: child })
    if (child) {
      localStorage.setItem('currentChild', JSON.stringify(child))
    } else {
      localStorage.removeItem('currentChild')
    }
  },

  addChild: async (childData: CreateChildRequest): Promise<Child> => {
    set({ isLoading: true, error: null })
    try {
      const newChild = await childService.createChild(childData)
      
      set(state => ({
        children: [...state.children, newChild],
        currentChild: newChild,
        isLoading: false
      }))
      
      localStorage.setItem('currentChild', JSON.stringify(newChild))
      return newChild
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({
        error: errorMessage,
        isLoading: false
      })
      throw error
    }
  },

  updateChild: async (childId: string, updates: UpdateChildRequest): Promise<Child> => {
    set({ isLoading: true, error: null })
    try {
      const updatedChild = await childService.updateChild(childId, updates)
      
      set(state => ({
        children: state.children.map(child =>
          child.id === childId ? updatedChild : child
        ),
        currentChild: state.currentChild?.id === childId
          ? updatedChild
          : state.currentChild,
        isLoading: false
      }))
      
      // Update localStorage if this is the current child
      const state = useChildStore.getState()
      if (state.currentChild?.id === childId) {
        localStorage.setItem('currentChild', JSON.stringify(updatedChild))
      }
      
      return updatedChild
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({
        error: errorMessage,
        isLoading: false
      })
      throw error
    }
  },

  loadChildren: async () => {
    set({ isLoading: true, error: null })
    try {
      const children = await childService.getChildren()
      
      set({
        children,
        isLoading: false
      })
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({
        error: errorMessage,
        isLoading: false
      })
      throw error
    }
  },

  deleteChild: async (childId: string) => {
    set({ isLoading: true, error: null })
    try {
      await childService.deleteChild(childId)
      
      set(state => {
        const newChildren = state.children.filter(child => child.id !== childId)
        const newCurrentChild = state.currentChild?.id === childId ? null : state.currentChild
        
        if (newCurrentChild === null) {
          localStorage.removeItem('currentChild')
        }
        
        return {
          children: newChildren,
          currentChild: newCurrentChild,
          isLoading: false
        }
      })
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({
        error: errorMessage,
        isLoading: false
      })
      throw error
    }
  },

  getChildWithProgress: async (childId: string): Promise<ChildWithProgress> => {
    set({ isLoading: true, error: null })
    try {
      const childWithProgress = await childService.getChildWithProgress(childId)
      set({ isLoading: false })
      return childWithProgress
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({
        error: errorMessage,
        isLoading: false
      })
      throw error
    }
  },

  getDashboard: async (childId: string): Promise<DashboardData> => {
    set({ isLoading: true, error: null })
    try {
      const dashboardData = await childService.getChildDashboard(childId)
      set({ isLoading: false })
      return dashboardData
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({
        error: errorMessage,
        isLoading: false
      })
      throw error
    }
  },

  conductAssessment: async (childId: string, assessment: ReadingAssessmentRequest): Promise<ReadingAssessmentResult> => {
    set({ isLoading: true, error: null })
    try {
      const result = await childService.conductReadingAssessment(childId, assessment)
      
      // Update child's reading level if assessment provides it
      if (result.readingLevel) {
        set(state => ({
          children: state.children.map(child =>
            child.id === childId
              ? { ...child, readingLevel: result.readingLevel }
              : child
          ),
          currentChild: state.currentChild?.id === childId
            ? { ...state.currentChild, readingLevel: result.readingLevel }
            : state.currentChild,
          isLoading: false
        }))
        
        // Update localStorage if this is the current child
        const state = useChildStore.getState()
        if (state.currentChild?.id === childId) {
          const updatedChild = { ...state.currentChild, readingLevel: result.readingLevel }
          localStorage.setItem('currentChild', JSON.stringify(updatedChild))
        }
      } else {
        set({ isLoading: false })
      }
      
      return result
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({
        error: errorMessage,
        isLoading: false
      })
      throw error
    }
  },

  uploadProfilePicture: async (childId: string, file: File): Promise<string> => {
    set({ isLoading: true, error: null })
    try {
      const pictureUrl = await childService.uploadProfilePicture(childId, file)
      
      // Update child's profile picture
      set(state => ({
        children: state.children.map(child =>
          child.id === childId
            ? { ...child, profilePicture: pictureUrl }
            : child
        ),
        currentChild: state.currentChild?.id === childId
          ? { ...state.currentChild, profilePicture: pictureUrl }
          : state.currentChild,
        isLoading: false
      }))
      
      // Update localStorage if this is the current child
      const state = useChildStore.getState()
      if (state.currentChild?.id === childId) {
        const updatedChild = { ...state.currentChild, profilePicture: pictureUrl }
        localStorage.setItem('currentChild', JSON.stringify(updatedChild))
      }
      
      return pictureUrl
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({
        error: errorMessage,
        isLoading: false
      })
      throw error
    }
  },

  clearError: () => {
    set({ error: null })
  },
}))

// Initialize current child from localStorage
const storedChild = localStorage.getItem('currentChild')
if (storedChild) {
  try {
    const child = JSON.parse(storedChild)
    // Ensure child has interests array
    if (!child.interests || !Array.isArray(child.interests)) {
      child.interests = []
    }
    useChildStore.getState().setCurrentChild(child)
  } catch (error) {
    localStorage.removeItem('currentChild')
  }
}