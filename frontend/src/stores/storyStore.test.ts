import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useStoryStore } from './storyStore'
import type { Story } from '../types'

// Mock fetch
global.fetch = vi.fn()

describe('storyStore - makeChoice and Chapter Progression', () => {
  beforeEach(() => {
    // Reset store state
    useStoryStore.setState({
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
    })

    // Clear all mocks
    vi.clearAllMocks()

    // Ensure localStorage has access token - use the global mock from setup.ts
    global.localStorage.setItem('access_token', 'mock-test-token')
  })

  describe('Chapter Number Handling', () => {
    it('should increment chapter from 1 to 2 after first choice', async () => {
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

      useStoryStore.setState({ currentStory: mockStory })

      // Mock SSE stream response for chapter 2
      const mockReader = {
        read: vi.fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode('event: story_chunk\ndata: {"type":"content","data":{"chunk":"Chapter 2 content"}}\n\n'),
          })
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode('event: story_chunk\ndata: {"type":"complete","data":{"currentChapter":2,"choices":[{"id":"1","text":"Choice 1"}]}}\n\n'),
          })
          .mockResolvedValueOnce({ done: true }),
      }

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as any)

      const store = useStoryStore.getState()
      await store.makeChoice('session-1', {
        choiceId: 'choice-1',
        optionIndex: 0,
        timestamp: new Date().toISOString(),
      })

      const updatedStory = useStoryStore.getState().currentStory
      expect(updatedStory?.currentChapter).toBe(2)
    })

    it('should increment chapter from 2 to 3 after second choice', async () => {
      const mockStory: Story = {
        id: '1',
        title: 'Test Story',
        content: ['Chapter 1 content', 'Chapter 2 content'],
        currentChapter: 2,
        totalChapters: 3,
        choices: [],
        isCompleted: false,
        theme: 'animals',
        language: 'english',
        readingLevel: 'beginner',
        createdAt: new Date().toISOString(),
      }

      useStoryStore.setState({ currentStory: mockStory })

      const mockReader = {
        read: vi.fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode('event: story_chunk\ndata: {"type":"content","data":{"chunk":"Chapter 3 content"}}\n\n'),
          })
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode('event: story_chunk\ndata: {"type":"complete","data":{"currentChapter":2,"choices":[]}}\n\n'),
          })
          .mockResolvedValueOnce({ done: true }),
      }

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as any)

      const store = useStoryStore.getState()
      await store.makeChoice('session-1', {
        choiceId: 'choice-2',
        optionIndex: 0,
        timestamp: new Date().toISOString(),
      })

      const updatedStory = useStoryStore.getState().currentStory
      // Should be 3, even though backend incorrectly sent 2
      expect(updatedStory?.currentChapter).toBe(3)
    })

    it('should not exceed totalChapters', async () => {
      const mockStory: Story = {
        id: '1',
        title: 'Test Story',
        content: ['Chapter 1', 'Chapter 2', 'Chapter 3'],
        currentChapter: 3,
        totalChapters: 3,
        choices: [],
        isCompleted: false,
        theme: 'animals',
        language: 'english',
        readingLevel: 'beginner',
        createdAt: new Date().toISOString(),
      }

      useStoryStore.setState({ currentStory: mockStory })

      const mockReader = {
        read: vi.fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode('event: story_chunk\ndata: {"type":"content","data":{"chunk":"Final content"}}\n\n'),
          })
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode('event: story_chunk\ndata: {"type":"complete","data":{"currentChapter":3,"choices":[],"isCompleted":true}}\n\n'),
          })
          .mockResolvedValueOnce({ done: true }),
      }

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as any)

      const store = useStoryStore.getState()
      await store.makeChoice('session-1', {
        choiceId: 'choice-3',
        optionIndex: 0,
        timestamp: new Date().toISOString(),
      })

      const updatedStory = useStoryStore.getState().currentStory
      expect(updatedStory?.currentChapter).toBe(3)
      expect(updatedStory?.currentChapter).toBeLessThanOrEqual(3)
    })

    it('should mark story as completed when reaching last chapter', async () => {
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

      useStoryStore.setState({ currentStory: mockStory })

      const mockReader = {
        read: vi.fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode('event: story_chunk\ndata: {"type":"content","data":{"chunk":"Final chapter"}}\n\n'),
          })
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode('event: story_chunk\ndata: {"type":"complete","data":{"currentChapter":3,"choices":[],"isCompleted":false}}\n\n'),
          })
          .mockResolvedValueOnce({ done: true }),
      }

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as any)

      const store = useStoryStore.getState()
      await store.makeChoice('session-1', {
        choiceId: 'final-choice',
        optionIndex: 0,
        timestamp: new Date().toISOString(),
      })

      const updatedStory = useStoryStore.getState().currentStory
      expect(updatedStory?.currentChapter).toBe(3)
      expect(updatedStory?.isCompleted).toBe(true)
      expect(updatedStory?.choices).toEqual([]) // Choices should be cleared
    })
  })

  describe('Choices Extraction', () => {
    it('should extract choices from event.data.choices', async () => {
      const mockStory: Story = {
        id: '1',
        title: 'Test Story',
        content: ['Chapter 1'],
        currentChapter: 1,
        totalChapters: 3,
        choices: [],
        isCompleted: false,
        theme: 'animals',
        language: 'english',
        readingLevel: 'beginner',
        createdAt: new Date().toISOString(),
      }

      useStoryStore.setState({ currentStory: mockStory })

      const mockChoices = [
        { id: '1', text: 'Choice A', description: 'Desc A' },
        { id: '2', text: 'Choice B', description: 'Desc B' },
      ]

      const mockReader = {
        read: vi.fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode('event: story_chunk\ndata: {"type":"content","data":{"chunk":"Content"}}\n\n'),
          })
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(`event: story_chunk\ndata: {"type":"complete","data":{"currentChapter":2,"choices":${JSON.stringify(mockChoices)}}}\n\n`),
          })
          .mockResolvedValueOnce({ done: true }),
      }

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as any)

      const store = useStoryStore.getState()
      await store.makeChoice('session-1', {
        choiceId: 'test-choice',
        optionIndex: 0,
        timestamp: new Date().toISOString(),
      })

      const updatedStory = useStoryStore.getState().currentStory
      expect(updatedStory?.choices).toEqual(mockChoices)
      expect(updatedStory?.choices?.length).toBe(2)
    })
  })
})
