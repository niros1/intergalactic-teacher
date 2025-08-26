import { api, apiRequest } from './api'
import type {
  Child,
  CreateChildRequest,
  UpdateChildRequest,
  ChildWithProgress,
  DashboardData,
  ReadingAssessmentRequest,
  ReadingAssessmentResult,
  ApiResponse,
} from '../types'

class ChildService {
  /**
   * Get all children for the authenticated user
   */
  async getChildren(): Promise<Child[]> {
    return await apiRequest<Child[]>(() =>
      api.get<ApiResponse<Child[]>>('/children')
    )
  }

  /**
   * Create a new child profile
   */
  async createChild(childData: CreateChildRequest): Promise<Child> {
    return await apiRequest<Child>(() =>
      api.post<ApiResponse<Child>>('/children', childData)
    )
  }

  /**
   * Get a specific child with progress data
   */
  async getChildWithProgress(childId: string): Promise<ChildWithProgress> {
    return await apiRequest<ChildWithProgress>(() =>
      api.get<ApiResponse<ChildWithProgress>>(`/children/${childId}`)
    )
  }

  /**
   * Update a child profile
   */
  async updateChild(childId: string, updates: UpdateChildRequest): Promise<Child> {
    return await apiRequest<Child>(() =>
      api.put<ApiResponse<Child>>(`/children/${childId}`, updates)
    )
  }

  /**
   * Delete a child profile
   */
  async deleteChild(childId: string): Promise<void> {
    await apiRequest<void>(() =>
      api.delete<ApiResponse<void>>(`/children/${childId}`)
    )
  }

  /**
   * Get dashboard data for a specific child
   */
  async getChildDashboard(childId: string): Promise<DashboardData> {
    return await apiRequest<DashboardData>(() =>
      api.get<ApiResponse<DashboardData>>(`/children/${childId}/dashboard`)
    )
  }

  /**
   * Conduct a reading assessment for a child
   */
  async conductReadingAssessment(
    childId: string,
    assessment: ReadingAssessmentRequest
  ): Promise<ReadingAssessmentResult> {
    return await apiRequest<ReadingAssessmentResult>(() =>
      api.post<ApiResponse<ReadingAssessmentResult>>(
        `/children/${childId}/reading-assessment`,
        assessment
      )
    )
  }

  /**
   * Upload child profile picture
   */
  async uploadProfilePicture(childId: string, file: File): Promise<string> {
    const formData = new FormData()
    formData.append('profilePicture', file)

    const response = await apiRequest<{ url: string }>(() =>
      api.post<ApiResponse<{ url: string }>>(
        `/children/${childId}/profile-picture`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )
    )

    return response.url
  }

  /**
   * Get child's reading statistics
   */
  async getChildStatistics(childId: string, period: 'week' | 'month' | 'year' = 'month') {
    return await apiRequest<{
      storiesRead: number
      totalReadingTime: number
      averageSessionLength: number
      wordsRead: number
      readingStreak: number
      favoriteTheme: string
      progressChart: Array<{
        date: string
        storiesRead: number
        timeSpent: number
      }>
    }>(() =>
      api.get<ApiResponse<any>>(`/children/${childId}/statistics`, {
        params: { period }
      })
    )
  }

  /**
   * Get child's achievements
   */
  async getChildAchievements(childId: string) {
    return await apiRequest<Array<{
      id: string
      title: string
      description: string
      icon: string
      unlockedAt: string
      progress: number
      target: number
    }>>(() =>
      api.get<ApiResponse<any>>(`/children/${childId}/achievements`)
    )
  }

  /**
   * Set child's reading goal
   */
  async setReadingGoal(childId: string, goal: {
    type: 'daily' | 'weekly' | 'monthly'
    target: number
    unit: 'stories' | 'minutes'
  }): Promise<void> {
    await apiRequest<void>(() =>
      api.post<ApiResponse<void>>(`/children/${childId}/reading-goal`, goal)
    )
  }

  /**
   * Get child's reading streaks
   */
  async getReadingStreak(childId: string) {
    return await apiRequest<{
      currentStreak: number
      longestStreak: number
      streakHistory: Array<{
        date: string
        completed: boolean
      }>
    }>(() =>
      api.get<ApiResponse<any>>(`/children/${childId}/reading-streak`)
    )
  }

  /**
   * Get child's recent activity
   */
  async getChildActivity(childId: string, limit: number = 10) {
    return await apiRequest<Array<{
      id: string
      type: 'story_completed' | 'achievement_unlocked' | 'goal_reached' | 'assessment_completed'
      title: string
      description: string
      timestamp: string
      metadata?: any
    }>>(() =>
      api.get<ApiResponse<any>>(`/children/${childId}/activity`, {
        params: { limit }
      })
    )
  }

  /**
   * Update child's interests based on reading behavior
   */
  async updateInterestsFromBehavior(childId: string): Promise<string[]> {
    const response = await apiRequest<{ interests: string[] }>(() =>
      api.post<ApiResponse<{ interests: string[] }>>(
        `/children/${childId}/update-interests`
      )
    )
    return response.interests
  }

  /**
   * Get recommended reading level adjustment
   */
  async getReadingLevelRecommendation(childId: string) {
    return await apiRequest<{
      currentLevel: string
      recommendedLevel: string
      reasoning: string
      confidence: number
    }>(() =>
      api.get<ApiResponse<any>>(`/children/${childId}/level-recommendation`)
    )
  }
}

// Create and export singleton instance
export const childService = new ChildService()
export default childService