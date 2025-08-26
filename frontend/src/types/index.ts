// Core entity types
export interface User {
  id: string
  email: string
  name: string
  createdAt: string
  updatedAt: string
}

export interface Child {
  id: string
  parentId: string
  name: string
  age: number
  readingLevel: ReadingLevel
  language: Language
  interests: string[]
  profilePicture?: string
  createdAt: string
  updatedAt: string
}

export interface Story {
  id: string
  title: string
  content: string[]
  language: Language
  readingLevel: ReadingLevel
  theme: string
  choices: Choice[]
  isCompleted: boolean
  currentChapter: number
  totalChapters: number
  createdAt: string
}

export interface Choice {
  id: string
  text: string
  impact: string
  nextChapter?: number
}

export interface StorySession {
  id: string
  childId: string
  storyId: string
  startTime: string
  endTime?: string
  choicesMade: ChoiceMade[]
  currentPosition: number
  isCompleted: boolean
  timeSpent?: number
  wordsRead?: number
  pauseCount?: number
}

export interface ChoiceMade {
  choiceId: string
  selectedAt: string
  impact: string
  sessionId?: string
}

// Enum types
export type Language = 'hebrew' | 'english'
export type ReadingLevel = 'beginner' | 'intermediate' | 'advanced'
export type Theme = 'animals' | 'adventure' | 'fantasy' | 'science' | 'friendship' | 'family'

// UI state types
export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export interface ChildState {
  currentChild: Child | null
  children: Child[]
  isLoading: boolean
  error: string | null
}

export interface StoryState {
  currentStory: Story | null
  stories: Story[]
  isGenerating: boolean
  isLoading: boolean
  error: string | null
}

// API Response types
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface ApiError {
  message: string
  code?: string
  details?: any
}

// Authentication API types
export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  name: string
  email: string
  password: string
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ResetPasswordRequest {
  token: string
  newPassword: string
}

export interface AuthResponse {
  user: User
  accessToken: string
  refreshToken: string
}

export interface RefreshTokenRequest {
  refreshToken: string
}

// Child API types
export interface CreateChildRequest {
  name: string
  age: number
  readingLevel: ReadingLevel
  language: Language
  interests: string[]
  profilePicture?: string
}

export interface UpdateChildRequest {
  name?: string
  age?: number
  language?: Language
  interests?: string[]
  profilePicture?: string
}

export interface ChildWithProgress extends Child {
  progress: {
    storiesRead: number
    totalReadingTime: number
    currentLevel: ReadingLevel
    achievements: string[]
  }
}

export interface DashboardData {
  child: ChildWithProgress
  recentStories: Story[]
  recommendations: Story[]
  statistics: {
    storiesCompleted: number
    readingStreak: number
    favoriteTheme: Theme
    totalReadingTime: number
  }
}

export interface ReadingAssessmentRequest {
  answers: {
    questionId: string
    answer: string
  }[]
}

export interface ReadingAssessmentResult {
  readingLevel: ReadingLevel
  strengths: string[]
  recommendations: string[]
  score: number
}

// Story API types
export interface GenerateStoryRequest {
  childId: string
  theme: Theme
  language: Language
  readingLevel?: ReadingLevel
  previousChoices?: ChoiceMade[]
  customPrompt?: string
}

export interface CreateStoryRequest {
  title: string
  theme: Theme
  language: Language
  readingLevel: ReadingLevel
  prompt: string
  childId: string
}

export interface StoryFilters {
  theme?: Theme
  language?: Language
  readingLevel?: ReadingLevel
  completed?: boolean
  limit?: number
  offset?: number
}

export interface SafetyCheckRequest {
  content: string
  language: Language
}

export interface SafetyCheckResponse {
  isSafe: boolean
  issues: string[]
  suggestions: string[]
}

// Story Session API types
export interface CreateSessionRequest {
  storyId: string
  childId: string
}

export interface UpdateProgressRequest {
  currentPosition: number
  timeSpent: number
  wordsRead: number
}

export interface MakeChoiceRequest {
  choiceId: string
  timestamp: string
}

export interface SessionResponse {
  session: StorySession
  story: Story
}

// Extended Story Session with analytics
export interface StorySessionWithAnalytics extends StorySession {
  analytics: {
    readingSpeed: number
    comprehensionScore?: number
    engagementLevel: number
    timeSpent: number
  }
}