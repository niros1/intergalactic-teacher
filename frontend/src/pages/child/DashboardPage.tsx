import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useChildStore } from '../../stores/childStore'
import { useStoryStore } from '../../stores/storyStore'
import { type Theme } from '../../types'

const DashboardPage: React.FC = () => {
  const navigate = useNavigate()
  const { currentChild, loadChildren, isLoading: childLoading } = useChildStore()
  const { generateStory, stories, isGenerating, loadStories } = useStoryStore()

  // Load children and stories when component mounts
  useEffect(() => {
    // If no current child, load children first
    if (!currentChild) {
      console.log('No current child found, loading children...')
      loadChildren()
    }
  }, [currentChild, loadChildren])

  // Load existing stories when we have a current child
  useEffect(() => {
    if (currentChild && loadStories) {
      console.log(`Loading stories for child ID: ${currentChild.id}`)
      // Load stories for this specific child
      loadStories({ childId: currentChild.id.toString() })
    }
  }, [currentChild, loadStories])

  const storyThemes: { id: Theme; label: string; emoji: string; description: string }[] = [
    { 
      id: 'animals', 
      label: 'Animals', 
      emoji: '🐾', 
      description: 'Meet friendly animals and learn about nature' 
    },
    { 
      id: 'adventure', 
      label: 'Adventure', 
      emoji: '🗺️', 
      description: 'Go on exciting journeys and discover new places' 
    },
    { 
      id: 'fantasy', 
      label: 'Fantasy', 
      emoji: '🧙‍♂️', 
      description: 'Enter magical worlds with wizards and dragons' 
    },
    { 
      id: 'science', 
      label: 'Science', 
      emoji: '🔬', 
      description: 'Explore how things work and make discoveries' 
    },
    { 
      id: 'friendship', 
      label: 'Friendship', 
      emoji: '👫', 
      description: 'Learn about kindness and making friends' 
    },
    { 
      id: 'family', 
      label: 'Family', 
      emoji: '👨‍👩‍👧‍👦', 
      description: 'Heartwarming stories about families and love' 
    },
  ]

  const handleStartNewStory = async (theme: Theme) => {
    if (!currentChild) return

    try {
      await generateStory({
        childId: currentChild.id.toString(),
        theme,
        language: currentChild.language_preference as any,
        readingLevel: currentChild.reading_level as any,
      })
      navigate('/chat-reading')
    } catch (error) {
      // Error is handled by the store
    }
  }


  if (!currentChild) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="heading-child">Welcome!</h1>
          <p className="text-child">
            {childLoading ? 'Loading your profile...' : 'Setting up your reading adventure...'}
          </p>
          {childLoading && (
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto mt-4"></div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-6xl mx-auto">
        {/* Welcome Header */}
        <div className="text-center mb-8">
          <h1 className="heading-child">
            {currentChild.language_preference === 'hebrew' 
              ? `שלום ${currentChild.name}!` 
              : `Welcome back, ${currentChild.name}!`}
          </h1>
          <p className="text-child text-gray-600">
            {currentChild.language_preference === 'hebrew' 
              ? 'מוכן להתחיל הרפתקה חדשה?' 
              : 'Ready for a new reading adventure?'}
          </p>
        </div>

        {/* Continue Reading Stories */}
        {stories && stories.filter(story => !story.isCompleted).length > 0 && (
          <div className="mb-8">
            <h2 className="text-child-lg font-bold text-gray-800 mb-6">
              {currentChild.language_preference === 'hebrew' ? 'המשך לקרוא' : 'Continue Reading'}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {stories.filter(story => !story.isCompleted).map(story => (
                <div key={story.id} className="card-child">
                  <h3 className="text-child-base font-bold text-gray-800 mb-2">
                    {story.title}
                  </h3>
                  <p className="text-sm text-gray-500 mb-3">
                    {currentChild.language_preference === 'hebrew' 
                      ? `פרק ${story.currentChapter} מתוך ${story.totalChapters}` 
                      : `Chapter ${story.currentChapter} of ${story.totalChapters}`}
                  </p>
                  <button 
                    className="btn-primary text-sm w-full flex items-center justify-center gap-2"
                    onClick={() => {
                      // Set as current story and navigate to chat reading
                      useStoryStore.getState().setCurrentStory(story)
                      navigate('/chat-reading')
                    }}
                  >
                    💬 {currentChild.language_preference === 'hebrew' ? 'המשך' : 'Continue'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Story Themes */}
        <div className="mb-8">
          <h2 className="text-child-lg font-bold text-gray-800 mb-6">
            {currentChild.language_preference === 'hebrew' 
              ? 'בחר סיפור חדש' 
              : 'Choose a New Story'}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {(currentChild && currentChild.interests && currentChild.interests.length > 0 
              ? storyThemes.filter(theme => currentChild.interests.includes(theme.id)) 
              : storyThemes)
              .map(theme => (
                <button
                  key={theme.id}
                  onClick={() => handleStartNewStory(theme.id)}
                  disabled={isGenerating}
                  className="card-child text-left p-6 hover:transform hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className="text-4xl mb-3">{theme.emoji}</div>
                  <h3 className="text-child-base font-bold text-gray-800 mb-2">
                    {theme.label}
                  </h3>
                  <p className="text-child-sm text-gray-600">
                    {theme.description}
                  </p>
                </button>
              ))}
          </div>
        </div>

        {/* Completed Stories */}
        {stories && stories.filter(story => story.isCompleted).length > 0 && (
          <div>
            <h2 className="text-child-lg font-bold text-gray-800 mb-6">
              {currentChild.language_preference === 'hebrew' 
                ? 'סיפורים שהושלמו' 
                : 'Completed Stories'}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {stories.filter(story => story.isCompleted).slice(0, 6).map(story => (
                <div key={story.id} className="card-child">
                  <h3 className="text-child-base font-bold text-gray-800 mb-2">
                    {story.title}
                  </h3>
                  <p className="text-sm text-gray-500 mb-3">
                    {currentChild.language_preference === 'hebrew' ? 'הושלם' : 'Completed'}
                  </p>
                  <button 
                    className="btn-secondary text-sm w-full flex items-center justify-center gap-2"
                    onClick={() => {
                      // Set as current story and navigate to chat reading
                      useStoryStore.getState().setCurrentStory(story)
                      navigate('/chat-reading')
                    }}
                  >
                    💬 {currentChild.language_preference === 'hebrew' ? 'קרא שוב' : 'Read Again'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Loading State */}
        {isGenerating && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="card-child text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
              <h3 className="text-child-base font-bold mb-2">
                {currentChild.language_preference === 'hebrew' 
                  ? 'יוצר סיפור מיוחד עבורך...' 
                  : 'Creating a special story for you...'}
              </h3>
              <p className="text-child-sm text-gray-600">
                {currentChild.language_preference === 'hebrew' 
                  ? 'זה ייקח כמה שניות' 
                  : 'This will take a few seconds'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DashboardPage