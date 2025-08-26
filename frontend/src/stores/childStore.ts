import { create } from 'zustand'
import { type ChildState, type Child, type CreateChildRequest } from '../types'

interface ChildStore extends ChildState {
  setCurrentChild: (child: Child | null) => void
  addChild: (childData: CreateChildRequest) => Promise<void>
  updateChild: (childId: string, updates: Partial<Child>) => Promise<void>
  loadChildren: (parentId: string) => Promise<void>
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

  addChild: async (childData: CreateChildRequest) => {
    set({ isLoading: true, error: null })
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const newChild: Child = {
        id: Date.now().toString(),
        parentId: '1', // TODO: Get from auth store
        name: childData.name,
        age: childData.age,
        readingLevel: 'beginner',
        language: childData.language,
        interests: childData.interests,
        profilePicture: childData.profilePicture,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }
      
      set(state => ({
        children: [...state.children, newChild],
        currentChild: newChild,
        isLoading: false
      }))
      
      localStorage.setItem('currentChild', JSON.stringify(newChild))
    } catch (error) {
      set({
        error: 'Failed to create child profile. Please try again.',
        isLoading: false
      })
    }
  },

  updateChild: async (childId: string, updates: Partial<Child>) => {
    set({ isLoading: true, error: null })
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 500))
      
      set(state => ({
        children: state.children.map(child =>
          child.id === childId
            ? { ...child, ...updates, updatedAt: new Date().toISOString() }
            : child
        ),
        currentChild: state.currentChild?.id === childId
          ? { ...state.currentChild, ...updates, updatedAt: new Date().toISOString() }
          : state.currentChild,
        isLoading: false
      }))
    } catch (error) {
      set({
        error: 'Failed to update child profile. Please try again.',
        isLoading: false
      })
    }
  },

  loadChildren: async (_parentId: string) => {
    set({ isLoading: true, error: null })
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Mock data for now
      const mockChildren: Child[] = []
      
      set({
        children: mockChildren,
        isLoading: false
      })
    } catch (error) {
      set({
        error: 'Failed to load children profiles. Please try again.',
        isLoading: false
      })
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
    useChildStore.getState().setCurrentChild(child)
  } catch (error) {
    localStorage.removeItem('currentChild')
  }
}