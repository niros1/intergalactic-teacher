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
}

export interface ChoiceMade {
  choiceId: string
  selectedAt: string
  impact: string
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

// API types
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  name: string
  email: string
  password: string
}

export interface CreateChildRequest {
  name: string
  age: number
  language: Language
  interests: string[]
  profilePicture?: string
}

export interface GenerateStoryRequest {
  childId: string
  theme: Theme
  language: Language
  readingLevel: ReadingLevel
  previousChoices?: ChoiceMade[]
}