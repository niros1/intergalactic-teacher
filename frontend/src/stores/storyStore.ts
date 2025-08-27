import { create } from 'zustand'
import { type StoryState, type Story, type GenerateStoryRequest, type StoryFilters, type CreateSessionRequest, type UpdateProgressRequest, type MakeChoiceRequest, type StorySession } from '../types'
import storyService from '../services/storyService'
import { getErrorMessage } from '../services/api'

interface StoryStore extends StoryState {
  setCurrentStory: (story: Story | null) => void
  generateStory: (request: GenerateStoryRequest) => Promise<Story>
  loadStories: (filters?: StoryFilters) => Promise<void>
  getStoryRecommendations: (childId: string, limit?: number) => Promise<Story[]>
  startSession: (request: CreateSessionRequest) => Promise<{ session: StorySession; story: Story }>
  updateProgress: (sessionId: string, progress: UpdateProgressRequest) => Promise<void>
  makeChoice: (sessionId: string, choice: MakeChoiceRequest) => Promise<void>
  completeSession: (sessionId: string) => Promise<{ achievements: string[]; points: number }>
  bookmarkStory: (storyId: string) => Promise<void>
  removeBookmark: (storyId: string) => Promise<void>
  rateStory: (storyId: string, rating: number, review?: string) => Promise<void>
  searchStories: (query: string, filters?: Partial<StoryFilters>) => Promise<Story[]>
  clearError: () => void
}

export const useStoryStore = create<StoryStore>((set, get) => ({
  currentStory: null,
  stories: [],
  isGenerating: false,
  isLoading: false,
  error: null,

  setCurrentStory: (story: Story | null) => {
    set({ currentStory: story })
    if (story) {
      localStorage.setItem('currentStory', JSON.stringify(story))
    } else {
      localStorage.removeItem('currentStory')
    }
  },

  generateStory: async (request: GenerateStoryRequest): Promise<Story> => {
    set({ isGenerating: true, error: null })
    try {
      const newStory = await storyService.generateStory(request)
      
      set(state => ({
        currentStory: newStory,
        stories: [newStory, ...state.stories],
        isGenerating: false
      }))
      
      localStorage.setItem('currentStory', JSON.stringify(newStory))
      return newStory
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({
        error: errorMessage,
        isGenerating: false
      })
      throw error
    }
  },

  loadStories: async (filters?: StoryFilters) => {
    set({ isLoading: true, error: null })
    try {
      const response = await storyService.getStories(filters)
      console.log('LoadStories response:', response)
      
      // Handle different response formats
      const stories = response.stories || response || []
      
      // Ensure stories is an array
      if (!Array.isArray(stories)) {
        console.warn('Expected stories array but got:', stories)
        set({ stories: [], isLoading: false })
        return
      }
      
      // Transform backend stories to frontend format
      const transformedStories = stories.map(story => ({
        ...story,
        id: story.id.toString(), // Ensure ID is string for frontend
        content: Array.isArray(story.content) 
          ? story.content 
          : [story.content || "Story content loading..."], // Convert string to array
        choices: story.choices || [], // Ensure choices array exists
        readingLevel: (story as any).difficulty_level || story.readingLevel,
        language: story.language,
        // Backend now returns current_chapter and is_completed from sessions
        currentChapter: (story as any).current_chapter || story.currentChapter || 1,
        totalChapters: (story as any).total_chapters || story.totalChapters || 3,
        isCompleted: (story as any).is_completed || story.isCompleted || false,
        theme: (story as any).themes?.[0] || story.theme || 'adventure', // Extract first theme
        createdAt: story.createdAt || (story as any).created_at
      }))
      
      set({
        stories: transformedStories,
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

  getStoryRecommendations: async (childId: string, limit?: number): Promise<Story[]> => {
    set({ isLoading: true, error: null })
    try {
      const recommendations = await storyService.getStoryRecommendations(childId, limit)
      set({ isLoading: false })
      return recommendations
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({
        error: errorMessage,
        isLoading: false
      })
      throw error
    }
  },

  startSession: async (request: CreateSessionRequest) => {
    set({ isLoading: true, error: null })
    try {
      const sessionResponse = await storyService.startStorySession(request)
      
      // Update current story if it's the one being started
      if (sessionResponse.story) {
        set({
          currentStory: sessionResponse.story,
          isLoading: false
        })
        localStorage.setItem('currentStory', JSON.stringify(sessionResponse.story))
      } else {
        set({ isLoading: false })
      }
      
      return sessionResponse
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({
        error: errorMessage,
        isLoading: false
      })
      throw error
    }
  },

  updateProgress: async (sessionId: string, progress: UpdateProgressRequest) => {
    try {
      await storyService.updateSessionProgress(sessionId, progress)
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({ error: errorMessage })
      throw error
    }
  },

  makeChoice: async (sessionId: string, choice: MakeChoiceRequest) => {
    set({ isLoading: true, error: null })
    try {
      const result = await storyService.makeStoryChoice(sessionId, choice)
      
      const { currentStory } = get()
      if (currentStory) {
        // Handle actual backend response format (cast to any to avoid type conflicts)
        const backendResult = result as any
        const branchContent = backendResult.branch_content || ""
        
        // Split branch content into paragraphs for display
        const contentParagraphs = branchContent ? 
          branchContent.split('\n\n').filter((p: string) => p.trim().length > 0) : 
          ["Continue reading..."]
        
        // Replace current content with new chapter content (don't append)
        const updatedStory: Story = {
          ...currentStory,
          content: contentParagraphs,  // Replace content with new chapter
          choices: backendResult.new_choices || [], // Use new_choices from backend response
          isCompleted: backendResult.is_ending || false,
          currentChapter: backendResult.next_chapter || (currentStory.currentChapter + 1)
        }
        
        // Also update the story in the stories array
        const updatedStories = get().stories.map(story => 
          story.id === updatedStory.id ? updatedStory : story
        )
        
        set({
          currentStory: updatedStory,
          stories: updatedStories,
          isLoading: false
        })
        
        localStorage.setItem('currentStory', JSON.stringify(updatedStory))
        
        // Log for debugging
        console.log('Choice processed successfully:', {
          newChapter: updatedStory.currentChapter,
          contentLength: contentParagraphs.length,
          isCompleted: updatedStory.isCompleted
        })
      } else {
        set({ isLoading: false })
      }
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({
        error: errorMessage,
        isLoading: false
      })
      throw error
    }
  },

  completeSession: async (sessionId: string) => {
    set({ isLoading: true, error: null })
    try {
      const result = await storyService.completeSession(sessionId)
      
      // Mark current story as completed if it matches
      const { currentStory } = get()
      if (currentStory) {
        const completedStory = { ...currentStory, isCompleted: true }
        set({
          currentStory: completedStory,
          isLoading: false
        })
        localStorage.setItem('currentStory', JSON.stringify(completedStory))
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

  bookmarkStory: async (storyId: string) => {
    try {
      await storyService.bookmarkStory(storyId)
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({ error: errorMessage })
      throw error
    }
  },

  removeBookmark: async (storyId: string) => {
    try {
      await storyService.removeBookmark(storyId)
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({ error: errorMessage })
      throw error
    }
  },

  rateStory: async (storyId: string, rating: number, review?: string) => {
    try {
      await storyService.rateStory(storyId, rating, review)
    } catch (error) {
      const errorMessage = getErrorMessage(error)
      set({ error: errorMessage })
      throw error
    }
  },

  searchStories: async (query: string, filters?: Partial<StoryFilters>): Promise<Story[]> => {
    set({ isLoading: true, error: null })
    try {
      const { stories } = await storyService.searchStories(query, filters)
      set({ isLoading: false })
      return stories
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

// Initialize current story from localStorage
const storedStory = localStorage.getItem('currentStory')
if (storedStory) {
  try {
    const story = JSON.parse(storedStory)
    useStoryStore.getState().setCurrentStory(story)
  } catch (error) {
    localStorage.removeItem('currentStory')
  }
}