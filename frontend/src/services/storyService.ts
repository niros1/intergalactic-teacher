import { api, apiRequest } from './api'
import type {
  Story,
  StoryFilters,
  GenerateStoryRequest,
  CreateStoryRequest,
  SafetyCheckRequest,
  SafetyCheckResponse,
  CreateSessionRequest,
  SessionResponse,
  UpdateProgressRequest,
  MakeChoiceRequest,
  StorySession,
  StorySessionWithAnalytics,
  ApiResponse,
} from '../types'

class StoryService {
  /**
   * Get stories with optional filters
   */
  async getStories(filters?: StoryFilters): Promise<{
    stories: Story[]
    total: number
    hasMore: boolean
  }> {
    const params = filters ? { ...filters } : {}
    
    return await apiRequest<{
      stories: Story[]
      total: number
      hasMore: boolean
    }>(() =>
      api.get<ApiResponse<any>>('/stories', { params })
    )
  }

  /**
   * Get story recommendations for a specific child
   */
  async getStoryRecommendations(childId: string, limit: number = 5): Promise<Story[]> {
    return await apiRequest<Story[]>(() =>
      api.get<ApiResponse<Story[]>>(`/stories/recommendations/${childId}`, {
        params: { limit }
      })
    )
  }

  /**
   * Generate a new AI story
   */
  async generateStory(request: GenerateStoryRequest): Promise<Story> {
    return await apiRequest<Story>(() =>
      api.post<ApiResponse<Story>>('/stories/generate', request)
    )
  }

  /**
   * Create and save an AI-generated story
   */
  async createStoryWithAI(request: CreateStoryRequest): Promise<Story> {
    return await apiRequest<Story>(() =>
      api.post<ApiResponse<Story>>('/stories/create-with-ai', request)
    )
  }

  /**
   * Get a specific story by ID
   */
  async getStory(storyId: string): Promise<Story> {
    return await apiRequest<Story>(() =>
      api.get<ApiResponse<Story>>(`/stories/${storyId}`)
    )
  }

  /**
   * Check story content for safety
   */
  async checkStorySafety(storyId: string, content?: string): Promise<SafetyCheckResponse> {
    const request: SafetyCheckRequest = {
      content: content || '',
      language: 'hebrew' // Default to Hebrew, can be dynamic
    }

    return await apiRequest<SafetyCheckResponse>(() =>
      api.post<ApiResponse<SafetyCheckResponse>>(`/stories/${storyId}/check-safety`, request)
    )
  }

  /**
   * Start a new story reading session
   */
  async startStorySession(request: CreateSessionRequest): Promise<SessionResponse> {
    return await apiRequest<SessionResponse>(() =>
      api.post<ApiResponse<SessionResponse>>(`/stories/${request.storyId}/sessions`, request)
    )
  }

  /**
   * Update reading progress in a session
   */
  async updateSessionProgress(
    sessionId: string,
    progress: UpdateProgressRequest
  ): Promise<StorySession> {
    return await apiRequest<StorySession>(() =>
      api.put<ApiResponse<StorySession>>(`/stories/sessions/${sessionId}/progress`, progress)
    )
  }

  /**
   * Make a story choice during a session
   */
  async makeStoryChoice(
    sessionId: string,
    choice: MakeChoiceRequest
  ): Promise<{
    session: StorySession
    nextContent: string[]
    newChoices: any[]
    isStoryComplete: boolean
  }> {
    return await apiRequest<any>(() =>
      api.post<ApiResponse<any>>(`/stories/sessions/${sessionId}/choices`, choice)
    )
  }

  /**
   * Get all sessions for a specific story
   */
  async getStorySessions(storyId: string): Promise<StorySession[]> {
    return await apiRequest<StorySession[]>(() =>
      api.get<ApiResponse<StorySession[]>>(`/stories/${storyId}/sessions`)
    )
  }

  /**
   * Get a specific session with analytics
   */
  async getSessionWithAnalytics(sessionId: string): Promise<StorySessionWithAnalytics> {
    return await apiRequest<StorySessionWithAnalytics>(() =>
      api.get<ApiResponse<StorySessionWithAnalytics>>(`/stories/sessions/${sessionId}`)
    )
  }

  /**
   * Complete a story session
   */
  async completeSession(sessionId: string): Promise<{
    session: StorySession
    achievements: string[]
    points: number
  }> {
    return await apiRequest<any>(() =>
      api.post<ApiResponse<any>>(`/stories/sessions/${sessionId}/complete`)
    )
  }

  /**
   * Get child's story history
   */
  async getChildStoryHistory(
    childId: string,
    page: number = 1,
    limit: number = 10
  ): Promise<{
    sessions: StorySessionWithAnalytics[]
    total: number
    hasMore: boolean
  }> {
    return await apiRequest<any>(() =>
      api.get<ApiResponse<any>>(`/stories/child/${childId}/history`, {
        params: { page, limit }
      })
    )
  }

  /**
   * Get popular stories
   */
  async getPopularStories(limit: number = 10): Promise<Story[]> {
    return await apiRequest<Story[]>(() =>
      api.get<ApiResponse<Story[]>>('/stories/popular', {
        params: { limit }
      })
    )
  }

  /**
   * Get recently added stories
   */
  async getRecentStories(limit: number = 10): Promise<Story[]> {
    return await apiRequest<Story[]>(() =>
      api.get<ApiResponse<Story[]>>('/stories/recent', {
        params: { limit }
      })
    )
  }

  /**
   * Search stories by text
   */
  async searchStories(query: string, filters?: Partial<StoryFilters>): Promise<{
    stories: Story[]
    total: number
  }> {
    const params = {
      q: query,
      ...(filters || {})
    }

    return await apiRequest<any>(() =>
      api.get<ApiResponse<any>>('/stories/search', { params })
    )
  }

  /**
   * Rate a story
   */
  async rateStory(storyId: string, rating: number, review?: string): Promise<void> {
    await apiRequest<void>(() =>
      api.post<ApiResponse<void>>(`/stories/${storyId}/rate`, {
        rating,
        review
      })
    )
  }

  /**
   * Bookmark a story
   */
  async bookmarkStory(storyId: string): Promise<void> {
    await apiRequest<void>(() =>
      api.post<ApiResponse<void>>(`/stories/${storyId}/bookmark`)
    )
  }

  /**
   * Remove story bookmark
   */
  async removeBookmark(storyId: string): Promise<void> {
    await apiRequest<void>(() =>
      api.delete<ApiResponse<void>>(`/stories/${storyId}/bookmark`)
    )
  }

  /**
   * Get child's bookmarked stories
   */
  async getBookmarkedStories(childId: string): Promise<Story[]> {
    return await apiRequest<Story[]>(() =>
      api.get<ApiResponse<Story[]>>(`/stories/child/${childId}/bookmarks`)
    )
  }

  /**
   * Report inappropriate story content
   */
  async reportStory(storyId: string, reason: string, details?: string): Promise<void> {
    await apiRequest<void>(() =>
      api.post<ApiResponse<void>>(`/stories/${storyId}/report`, {
        reason,
        details
      })
    )
  }

  /**
   * Get story analytics for parent dashboard
   */
  async getStoryAnalytics(childId: string, period: 'week' | 'month' | 'year' = 'month') {
    return await apiRequest<{
      totalStoriesRead: number
      averageReadingTime: number
      favoriteThemes: string[]
      readingProgress: Array<{
        date: string
        storiesCompleted: number
        timeSpent: number
      }>
      comprehensionScores: number[]
    }>(() =>
      api.get<ApiResponse<any>>(`/stories/child/${childId}/analytics`, {
        params: { period }
      })
    )
  }

  /**
   * Pause a story session
   */
  async pauseSession(sessionId: string): Promise<void> {
    await apiRequest<void>(() =>
      api.post<ApiResponse<void>>(`/stories/sessions/${sessionId}/pause`)
    )
  }

  /**
   * Resume a paused story session
   */
  async resumeSession(sessionId: string): Promise<StorySession> {
    return await apiRequest<StorySession>(() =>
      api.post<ApiResponse<StorySession>>(`/stories/sessions/${sessionId}/resume`)
    )
  }

  /**
   * Generate story continuation based on child's choices
   */
  async generateStoryContinuation(
    storyId: string,
    sessionId: string,
    choiceId: string
  ): Promise<{
    newContent: string[]
    newChoices: any[]
    isComplete: boolean
  }> {
    return await apiRequest<any>(() =>
      api.post<ApiResponse<any>>(`/stories/${storyId}/continue`, {
        sessionId,
        choiceId
      })
    )
  }

  /**
   * Get story themes suitable for child's age and reading level
   */
  async getSuitableThemes(childId: string): Promise<{
    recommended: string[]
    all: Array<{
      name: string
      description: string
      ageAppropriate: boolean
      examples: string[]
    }>
  }> {
    return await apiRequest<any>(() =>
      api.get<ApiResponse<any>>(`/stories/themes/child/${childId}`)
    )
  }
}

// Create and export singleton instance
export const storyService = new StoryService()
export default storyService