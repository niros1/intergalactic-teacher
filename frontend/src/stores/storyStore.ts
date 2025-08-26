import { create } from 'zustand'
import { type StoryState, type Story, type GenerateStoryRequest, type Choice } from '../types'

interface StoryStore extends StoryState {
  setCurrentStory: (story: Story | null) => void
  generateStory: (request: GenerateStoryRequest) => Promise<void>
  loadStories: (childId: string) => Promise<void>
  makeChoice: (choiceId: string, storyId: string) => Promise<void>
  saveProgress: (storyId: string, currentPosition: number) => Promise<void>
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

  generateStory: async (request: GenerateStoryRequest) => {
    set({ isGenerating: true, error: null })
    try {
      // TODO: Replace with actual AI API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Mock story generation
      const mockChoices: Choice[] = [
        {
          id: 'choice-1',
          text: request.language === 'hebrew' ? 'ללכת לחקור את היער' : 'Explore the forest',
          impact: 'adventure',
          nextChapter: 2
        },
        {
          id: 'choice-2',
          text: request.language === 'hebrew' ? 'לחזור הביתה' : 'Go back home',
          impact: 'safety',
          nextChapter: 3
        }
      ]

      const newStory: Story = {
        id: Date.now().toString(),
        title: request.language === 'hebrew' 
          ? 'הרפתקה בחווה הקסומה' 
          : 'Adventure at the Magic Farm',
        content: request.language === 'hebrew' 
          ? [
              'פעם היה ילד בשם דני שהלך לבקר את סבא וסבתא שלו בכפר. בבוקר אחד, הוא שמע קולות מוזרים מהחווה הסמוכה.',
              'דני החליט ללכת ולחקור. כשהגיע לחווה, הוא ראה משהו מדהים - החיות דיברו ביניהן!',
              'עכשיו דני צריך להחליט מה לעשות...'
            ]
          : [
              'Once upon a time, there was a boy named Danny who went to visit his grandparents in the countryside. One morning, he heard strange sounds from the nearby farm.',
              'Danny decided to investigate. When he reached the farm, he saw something amazing - the animals were talking to each other!',
              'Now Danny needs to decide what to do...'
            ],
        language: request.language,
        readingLevel: request.readingLevel,
        theme: request.theme,
        choices: mockChoices,
        isCompleted: false,
        currentChapter: 1,
        totalChapters: 5,
        createdAt: new Date().toISOString()
      }
      
      set(state => ({
        currentStory: newStory,
        stories: [newStory, ...state.stories],
        isGenerating: false
      }))
      
      localStorage.setItem('currentStory', JSON.stringify(newStory))
    } catch (error) {
      set({
        error: 'Failed to generate story. Please try again.',
        isGenerating: false
      })
    }
  },

  loadStories: async (_childId: string) => {
    set({ isLoading: true, error: null })
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Mock data for now
      const mockStories: Story[] = []
      
      set({
        stories: mockStories,
        isLoading: false
      })
    } catch (error) {
      set({
        error: 'Failed to load stories. Please try again.',
        isLoading: false
      })
    }
  },

  makeChoice: async (choiceId: string, storyId: string) => {
    set({ isLoading: true, error: null })
    try {
      // TODO: Replace with actual API call to continue story
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      const { currentStory } = get()
      if (!currentStory || currentStory.id !== storyId) return
      
      const choice = currentStory.choices.find(c => c.id === choiceId)
      if (!choice) return
      
      // Mock story continuation
      const updatedStory: Story = {
        ...currentStory,
        currentChapter: choice.nextChapter || currentStory.currentChapter + 1,
        content: [
          ...currentStory.content,
          currentStory.language === 'hebrew' 
            ? `דני בחר ${choice.text.toLowerCase()}. מה יקרה עכשיו?`
            : `Danny chose to ${choice.text.toLowerCase()}. What happens next?`
        ],
        choices: [] // Will be populated with new choices
      }
      
      set({
        currentStory: updatedStory,
        isLoading: false
      })
      
      localStorage.setItem('currentStory', JSON.stringify(updatedStory))
    } catch (error) {
      set({
        error: 'Failed to process choice. Please try again.',
        isLoading: false
      })
    }
  },

  saveProgress: async (storyId: string, currentPosition: number) => {
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 200))
      
      // Mock progress saving - in reality this would save to backend
      console.log(`Progress saved for story ${storyId} at position ${currentPosition}`)
    } catch (error) {
      console.error('Failed to save progress:', error)
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