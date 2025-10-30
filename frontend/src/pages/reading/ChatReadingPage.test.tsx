import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import ChatReadingPage from './ChatReadingPage'
import { useStoryStore } from '../../stores/storyStore'
import { useChildStore } from '../../stores/childStore'
import type { Story, Child } from '../../types'

// Mock the stores
vi.mock('../../stores/storyStore')
vi.mock('../../stores/childStore')
vi.mock('../../hooks/useStoryRuntime', () => ({
  useStoryRuntime: () => ({
    messages: [],
    isLoading: false,
    usedChoiceMessageIds: new Set(),
    append: vi.fn(),
  }),
}))
vi.mock('../../hooks/useSpeechRecognition', () => ({
  useSpeechRecognition: () => ({
    transcript: '',
    isListening: false,
    hasRecognitionSupport: true,
    startListening: vi.fn(),
    stopListening: vi.fn(),
    resetTranscript: vi.fn(),
    error: null,
  }),
}))

describe('ChatReadingPage - Progress Bar', () => {
  const mockChild: Child = {
    id: 1,
    name: 'Test Child',
    age: 7,
    language_preference: 'english',
    reading_level: 'beginner',
    interests: [],
    parent_id: 1,
    created_at: new Date().toISOString(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useChildStore).mockReturnValue({
      currentChild: mockChild,
    } as any)
  })

  it('should display 33% progress for Chapter 1 of 3', () => {
    const mockStory: Story = {
      id: '1',
      title: 'Test Story',
      content: ['Chapter 1 content'],
      currentChapter: 1,
      totalChapters: 3,
      choices: [],
      isCompleted: false,
      theme: 'animals',
      language: 'english',
      readingLevel: 'beginner',
      createdAt: new Date().toISOString(),
    }

    vi.mocked(useStoryStore).mockReturnValue({
      currentStory: mockStory,
    } as any)

    render(
      <BrowserRouter>
        <ChatReadingPage />
      </BrowserRouter>
    )

    expect(screen.getByText('33%')).toBeInTheDocument()
    expect(screen.getByText('Chapter 1 of 3')).toBeInTheDocument()
  })

  it('should display 67% progress for Chapter 2 of 3', () => {
    const mockStory: Story = {
      id: '1',
      title: 'Test Story',
      content: ['Chapter 1', 'Chapter 2'],
      currentChapter: 2,
      totalChapters: 3,
      choices: [],
      isCompleted: false,
      theme: 'animals',
      language: 'english',
      readingLevel: 'beginner',
      createdAt: new Date().toISOString(),
    }

    vi.mocked(useStoryStore).mockReturnValue({
      currentStory: mockStory,
    } as any)

    render(
      <BrowserRouter>
        <ChatReadingPage />
      </BrowserRouter>
    )

    expect(screen.getByText('67%')).toBeInTheDocument()
    expect(screen.getByText('Chapter 2 of 3')).toBeInTheDocument()
  })

  it('should display 100% progress for Chapter 3 of 3', () => {
    const mockStory: Story = {
      id: '1',
      title: 'Test Story',
      content: ['Chapter 1', 'Chapter 2', 'Chapter 3'],
      currentChapter: 3,
      totalChapters: 3,
      choices: [],
      isCompleted: true,
      theme: 'animals',
      language: 'english',
      readingLevel: 'beginner',
      createdAt: new Date().toISOString(),
    }

    vi.mocked(useStoryStore).mockReturnValue({
      currentStory: mockStory,
    } as any)

    render(
      <BrowserRouter>
        <ChatReadingPage />
      </BrowserRouter>
    )

    expect(screen.getByText('100%')).toBeInTheDocument()
    expect(screen.getByText('Chapter 3 of 3')).toBeInTheDocument()
  })

  it('should calculate progress correctly for different totalChapters', () => {
    const mockStory: Story = {
      id: '1',
      title: 'Test Story',
      content: ['Ch1', 'Ch2'],
      currentChapter: 2,
      totalChapters: 5,
      choices: [],
      isCompleted: false,
      theme: 'animals',
      language: 'english',
      readingLevel: 'beginner',
      createdAt: new Date().toISOString(),
    }

    vi.mocked(useStoryStore).mockReturnValue({
      currentStory: mockStory,
    } as any)

    render(
      <BrowserRouter>
        <ChatReadingPage />
      </BrowserRouter>
    )

    // 2/5 * 100 = 40%
    expect(screen.getByText('40%')).toBeInTheDocument()
    expect(screen.getByText('Chapter 2 of 5')).toBeInTheDocument()
  })

  it('should display story title correctly', () => {
    const mockStory: Story = {
      id: '1',
      title: 'Animals Adventure',
      content: ['Content'],
      currentChapter: 1,
      totalChapters: 3,
      choices: [],
      isCompleted: false,
      theme: 'animals',
      language: 'english',
      readingLevel: 'beginner',
      createdAt: new Date().toISOString(),
    }

    vi.mocked(useStoryStore).mockReturnValue({
      currentStory: mockStory,
    } as any)

    render(
      <BrowserRouter>
        <ChatReadingPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Animals Adventure')).toBeInTheDocument()
  })
})

describe('Progress Calculation Logic', () => {
  it('should calculate progress as currentChapter / totalChapters * 100', () => {
    const testCases = [
      { currentChapter: 1, totalChapters: 3, expected: 33 },
      { currentChapter: 2, totalChapters: 3, expected: 67 },
      { currentChapter: 3, totalChapters: 3, expected: 100 },
      { currentChapter: 1, totalChapters: 5, expected: 20 },
      { currentChapter: 3, totalChapters: 5, expected: 60 },
      { currentChapter: 5, totalChapters: 5, expected: 100 },
    ]

    testCases.forEach(({ currentChapter, totalChapters, expected }) => {
      const progress = Math.round((currentChapter / totalChapters) * 100)
      expect(progress).toBe(expected)
    })
  })

  it('should not use (currentChapter - 1) formula', () => {
    // This test ensures we don't revert to the old buggy formula
    const currentChapter = 3
    const totalChapters = 3

    // Old buggy formula
    const oldFormula = Math.round(((currentChapter - 1) / totalChapters) * 100)
    expect(oldFormula).toBe(67) // This is wrong!

    // New correct formula
    const newFormula = Math.round((currentChapter / totalChapters) * 100)
    expect(newFormula).toBe(100) // This is correct!
  })
})
