import { create } from 'zustand'
import { type StoryState, type Story, type GenerateStoryRequest, type StoryFilters, type CreateSessionRequest, type UpdateProgressRequest, type MakeChoiceRequest, type StorySession } from '../types'
import storyService from '../services/storyService'
import { getErrorMessage } from '../services/api'

interface StreamingState {
  isStreaming: boolean
  streamedContent: string
  streamProgress: string | null
}

interface StoryStore extends StoryState {
  streamingState: StreamingState
  setCurrentStory: (story: Story | null) => void
  generateStory: (request: GenerateStoryRequest) => Promise<Story>
  generateStoryStreaming: (request: GenerateStoryRequest, onChunk?: (chunk: string) => void) => Promise<Story>
  updateStreamingContent: (content: string) => void
  updateStreamingProgress: (progress: string | null) => void
  setIsStreaming: (isStreaming: boolean) => void
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
  streamingState: {
    isStreaming: false,
    streamedContent: '',
    streamProgress: null,
  },

  setCurrentStory: (story: Story | null) => {
    set({ currentStory: story })
    if (story) {
      localStorage.setItem('currentStory', JSON.stringify(story))
    } else {
      localStorage.removeItem('currentStory')
    }
  },

  setIsStreaming: (isStreaming: boolean) => {
    set(state => ({
      streamingState: {
        ...state.streamingState,
        isStreaming,
        ...(isStreaming ? {} : { streamedContent: '', streamProgress: null })
      }
    }))
  },

  updateStreamingContent: (content: string) => {
    set(state => ({
      streamingState: {
        ...state.streamingState,
        streamedContent: content
      }
    }))
  },

  updateStreamingProgress: (progress: string | null) => {
    set(state => ({
      streamingState: {
        ...state.streamingState,
        streamProgress: progress
      }
    }))
  },

  generateStoryStreaming: async (request: GenerateStoryRequest, onChunk?: (chunk: string) => void): Promise<Story> => {
    const { setIsStreaming, updateStreamingContent, updateStreamingProgress } = get()

    setIsStreaming(true)
    set({ error: null, isGenerating: true })

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const token = localStorage.getItem('access_token')

      if (!token) {
        throw new Error('Authentication required')
      }

      // Build URL with query parameters
      const url = new URL(`${API_URL}/stories/generate/stream`)
      url.searchParams.append('child_id', request.childId)
      url.searchParams.append('theme', request.theme)
      url.searchParams.append('chapter_number', request.chapter_number?.toString() || '1')
      if (request.title) {
        url.searchParams.append('title', request.title)
      }

      // Use fetch with EventSource-like handling
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/event-stream',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      let accumulatedContent = ''
      let finalStory: Story | null = null
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Process complete SSE messages (events are separated by double newlines)
        const events = buffer.split('\n\n')
        buffer = events.pop() || '' // Keep incomplete event in buffer

        for (const eventText of events) {
          if (!eventText.trim()) continue

          // Parse multi-line SSE event
          const eventLines = eventText.split('\n')
          let dataLine = ''

          for (const line of eventLines) {
            if (line.startsWith('data: ')) {
              dataLine = line.substring(6) // Remove 'data: ' prefix
              break
            }
          }

          if (!dataLine) continue

          try {
            console.log('🔍 Parsing JSON:', dataLine.substring(0, 200))
            const event = JSON.parse(dataLine)

            console.log('📨 SSE Event received:', event.type, event)

            switch (event.type) {
              case 'progress':
                if (event.progress) {
                  updateStreamingProgress(`${event.progress.stage}: ${event.progress.description}`)
                }
                break

              case 'content':
                // event.data contains {chunk: string, is_complete: boolean}
                if (event.data && event.data.chunk) {
                  accumulatedContent += event.data.chunk
                  updateStreamingContent(accumulatedContent)
                  onChunk?.(event.data.chunk)
                }
                break

              case 'safety_check':
                updateStreamingProgress(`Safety Check: ${event.status || 'Checking'}...`)
                break

              case 'complete':
                // The complete event now includes the full story object with real database ID
                console.log('✅ Complete event received, event.data:', event.data)
                if (event.data) {
                  const storyData = event.data
                  finalStory = {
                    id: storyData.id,  // Real database ID from backend
                    title: storyData.title,
                    content: storyData.content || [],  // Array of paragraphs
                    language: storyData.language || 'english',
                    readingLevel: storyData.readingLevel || 'beginner',
                    theme: storyData.theme,
                    choices: storyData.choices || [],
                    isCompleted: storyData.isCompleted || false,
                    currentChapter: storyData.currentChapter || 1,
                    totalChapters: storyData.totalChapters || 3,
                    createdAt: storyData.createdAt || new Date().toISOString(),
                  }
                  console.log('✅ finalStory created with ID:', finalStory.id)
                } else {
                  console.warn('⚠️ Complete event received but event.data is missing')
                }
                break

              case 'error':
                throw new Error(event.message || 'Unknown error occurred')
            }
          } catch (parseError) {
            console.error('Error parsing SSE event:', parseError)
          }
        }
      }

      setIsStreaming(false)

      if (!finalStory) {
        console.warn('⚠️ No finalStory from complete event - using fallback with timestamp ID')
        // Build story from accumulated data
        finalStory = {
          id: Date.now().toString(),
          title: request.title || `${request.theme} Adventure`,
          content: accumulatedContent.split('\n\n').filter(p => p.trim()),
          language: 'english',
          readingLevel: 'beginner',
          theme: request.theme,
          choices: [],
          isCompleted: false,
          currentChapter: request.chapter_number || 1,
          totalChapters: 3,
          createdAt: new Date().toISOString(),
        }
      }

      set(state => ({
        currentStory: finalStory,
        stories: [finalStory!, ...state.stories],
        isGenerating: false,
      }))

      localStorage.setItem('currentStory', JSON.stringify(finalStory))
      return finalStory

    } catch (error) {
      const errorMessage = getErrorMessage(error)
      setIsStreaming(false)
      set({ error: errorMessage, isGenerating: false })
      throw error
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

// Debug helper: Expose store to window for console access
if (typeof window !== 'undefined') {
  ;(window as any).storyStore = useStoryStore
  ;(window as any).debugStory = {
    getCurrentStory: () => useStoryStore.getState().currentStory,
    getAllStories: () => useStoryStore.getState().stories,
    getFullState: () => useStoryStore.getState(),
    inspectCurrentStoryContent: () => {
      const story = useStoryStore.getState().currentStory
      if (story) {
        console.log('📚 Current Story Debug Info:')
        console.log('- Title:', story.title)
        console.log('- Current Chapter:', story.currentChapter)
        console.log('- Total Chapters:', story.totalChapters)
        console.log('- Content:', story.content)
        console.log('- Choices:', story.choices)
        console.log('- Is Completed:', story.isCompleted)
        console.log('- Full Story Object:', story)
        return story
      } else {
        console.log('No current story found')
        return null
      }
    },
    cleanCurrentStory: () => {
      useStoryStore.getState().setCurrentStory(null)
      localStorage.removeItem('currentStory')
      console.log('✅ Current story cleared from store and localStorage')
    },
    cleanAllState: () => {
      const { setCurrentStory, clearError } = useStoryStore.getState()
      setCurrentStory(null)
      clearError()
      useStoryStore.setState({
        stories: [],
        isGenerating: false,
        isLoading: false,
        error: null
      })
      localStorage.removeItem('currentStory')
      console.log('✅ All story state cleared (stories, current story, errors, loading states)')
      console.log('⚠️  Note: This does not clear child store or session data')
    }
  }
  console.log('🔍 Debug helpers available:')
  console.log('- window.storyStore: Full Zustand store')
  console.log('- window.debugStory.getCurrentStory(): Get current story')
  console.log('- window.debugStory.getAllStories(): Get all stories')
  console.log('- window.debugStory.getFullState(): Get full store state')
  console.log('- window.debugStory.inspectCurrentStoryContent(): Detailed current story debug')
  console.log('- window.debugStory.cleanCurrentStory(): Clear current story only')
  console.log('- window.debugStory.cleanAllState(): Clear all story state')
}