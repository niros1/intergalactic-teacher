import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useStoryStore } from '../../stores/storyStore'
import { useChildStore } from '../../stores/childStore'

const ReadingPage: React.FC = () => {
  const navigate = useNavigate()
  const { currentStory, makeChoice, isLoading, startSession } = useStoryStore()
  const { currentChild } = useChildStore()
  const [currentParagraph, setCurrentParagraph] = useState(0)
  const [isReading, setIsReading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)

  // Create a reading session when the component loads
  useEffect(() => {
    const createSession = async () => {
      if (currentStory && currentChild && !sessionId) {
        try {
          console.log('Creating session for story:', currentStory.id, 'child:', currentChild.id)
          const sessionResponse = await startSession({
            storyId: currentStory.id,
            childId: currentChild.id
          })
          console.log('Session response:', sessionResponse)
          // Handle both possible response formats
          let actualSessionId: string
          if (sessionResponse.session) {
            // Expected format: { session: StorySession, story: Story }
            actualSessionId = sessionResponse.session.id
          } else {
            // Direct session format: StorySession
            actualSessionId = (sessionResponse as any).id
          }
          console.log('Setting session ID:', actualSessionId)
          setSessionId(actualSessionId)
        } catch (error) {
          console.error('Failed to create story session:', error)
        }
      }
    }

    createSession()
  }, [currentStory, currentChild, sessionId, startSession])

  if (!currentStory || !currentChild) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="heading-child">
            {currentChild?.language === 'hebrew' ? 'טוען סיפור...' : 'Loading story...'}
          </h1>
        </div>
      </div>
    )
  }

  const handleChoice = async (choiceId: string) => {
    console.log('Making choice with sessionId:', sessionId, 'choiceId:', choiceId)
    
    if (!sessionId) {
      console.error('No session ID available for making choice')
      alert('Session not ready yet. Please wait a moment and try again.')
      return
    }

    try {
      await makeChoice(sessionId, {
        choiceId: choiceId,
        timestamp: new Date().toISOString()
      })
      setCurrentParagraph(0) // Reset to beginning of new chapter
    } catch (error) {
      console.error('Choice making failed:', error)
      // Error is handled by the store
    }
  }

  const handleContinueStory = async () => {
    console.log('Continuing story to next chapter for sessionId:', sessionId)
    
    if (!sessionId) {
      console.error('No session ID available for continuing story')
      alert('Session not ready yet. Please wait a moment and try again.')
      return
    }

    // For stories without choices, we need to create a way to advance to the next chapter
    // We can create a default "continue" choice or implement a separate endpoint
    // For now, let's use a special choice ID to indicate continuation
    try {
      await makeChoice(sessionId, {
        choiceId: 'continue',
        timestamp: new Date().toISOString()
      })
      setCurrentParagraph(0) // Reset to beginning of new chapter
    } catch (error) {
      console.error('Story continuation failed:', error)
      // Error is handled by the store
    }
  }

  const handleNextParagraph = () => {
    if (currentStory?.content && currentParagraph < currentStory.content.length - 1) {
      setCurrentParagraph(prev => prev + 1)
    }
    // Don't show alert here - let the choices section handle chapter transitions
  }

  const handlePreviousParagraph = () => {
    if (currentParagraph > 0) {
      setCurrentParagraph(prev => prev - 1)
    }
  }

  const handleTextToSpeech = () => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(currentStory.content[currentParagraph])
      
      // Set language based on story language
      utterance.lang = currentStory.language === 'hebrew' ? 'he-IL' : 'en-US'
      utterance.rate = 0.8 // Slower for children
      utterance.pitch = 1.1 // Slightly higher pitch for engagement
      
      setIsReading(true)
      utterance.onend = () => setIsReading(false)
      utterance.onerror = () => setIsReading(false)
      
      window.speechSynthesis.speak(utterance)
    }
  }

  const stopReading = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      setIsReading(false)
    }
  }

  const isLastParagraph = currentStory?.content ? currentParagraph === currentStory.content.length - 1 : false
  const hasChoices = currentStory?.choices ? currentStory.choices.length > 0 : false
  const hasMoreChapters = currentStory ? currentStory.currentChapter < currentStory.totalChapters : false

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => navigate('/child/dashboard')}
            className="btn-secondary"
          >
            {currentChild.language === 'hebrew' ? '← חזור' : '← Back'}
          </button>
          <div className="text-center">
            <h1 className="text-child-lg font-bold text-gray-800">
              {currentStory.title}
            </h1>
            <p className="text-sm text-gray-500">
              {currentChild.language === 'hebrew' 
                ? `פרק ${currentStory.currentChapter} מתוך ${currentStory.totalChapters}`
                : `Chapter ${currentStory.currentChapter} of ${currentStory.totalChapters}`}
            </p>
          </div>
          <div className="w-20"> {/* Spacer for layout balance */} </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="bg-gray-200 rounded-full h-3">
            <div 
              className="bg-primary-500 h-3 rounded-full transition-all duration-300"
              style={{ 
                width: `${((currentStory.currentChapter - 1) / currentStory.totalChapters) * 100}%` 
              }}
            />
          </div>
        </div>

        {/* Story Content */}
        <div className="card-child mb-8">
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={handlePreviousParagraph}
              disabled={currentParagraph === 0}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {currentChild.language === 'hebrew' ? '← קודם' : '← Previous'}
            </button>

            {/* Audio Controls */}
            <div className="flex items-center space-x-4">
              <button
                onClick={isReading ? stopReading : handleTextToSpeech}
                className={`btn-primary ${isReading ? 'bg-red-500 hover:bg-red-600' : ''}`}
              >
                {isReading 
                  ? (currentChild.language === 'hebrew' ? '⏹ עצור' : '⏹ Stop')
                  : (currentChild.language === 'hebrew' ? '🔊 הקרא לי' : '🔊 Read to me')}
              </button>
            </div>

            <button
              onClick={handleNextParagraph}
              disabled={isLastParagraph}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {currentChild.language === 'hebrew' ? 'הבא →' : 'Next →'}
            </button>
          </div>

          {/* Story Text */}
          <div 
            className={`text-child-lg leading-relaxed text-gray-800 p-6 bg-gray-50 rounded-child mb-6 ${
              currentChild.language === 'hebrew' ? 'text-right' : 'text-left'
            }`}
            dir={currentChild.language === 'hebrew' ? 'rtl' : 'ltr'}
          >
            {currentStory?.content?.[currentParagraph] || 'Loading content...'}
          </div>

          {/* Paragraph Navigation */}
          <div className="text-center text-sm text-gray-500 mb-4">
            {currentChild.language === 'hebrew' 
              ? `פסקה ${currentParagraph + 1} מתוך ${currentStory?.content?.length || 0}`
              : `Paragraph ${currentParagraph + 1} of ${currentStory?.content?.length || 0}`}
          </div>

          {/* Choices */}
          {(isLastParagraph && hasChoices) && (
            <div className="mt-8">
              <h3 className="text-child-base font-bold text-gray-800 mb-4">
                {currentChild.language === 'hebrew' 
                  ? 'מה תרצה לעשות?' 
                  : 'What would you like to do?'}
              </h3>
              {/* Debug info */}
              <div className="text-xs text-gray-500 mb-2">
                Session: {sessionId || 'Creating...'}
              </div>
              <div className="grid gap-4">
                {(currentStory?.choices || []).map(choice => (
                  <button
                    key={choice.id}
                    onClick={() => handleChoice(choice.id)}
                    disabled={isLoading}
                    className="card-child text-left p-4 hover:transform hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="text-child-base font-semibold text-primary-700">
                      {choice.text}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* More chapters available but no choices */}
          {isLastParagraph && !hasChoices && hasMoreChapters && !currentStory.isCompleted && (
            <div className="text-center mt-8">
              <h3 className="text-child-base font-bold text-gray-800 mb-4">
                {currentChild.language === 'hebrew' 
                  ? 'הפרק הסתיים!' 
                  : 'Chapter Complete!'}
              </h3>
              <p className="text-child-sm text-gray-600 mb-6">
                {currentChild.language === 'hebrew' 
                  ? `סיימת פרק ${currentStory?.currentChapter} מתוך ${currentStory?.totalChapters}. האם תרצה להמשיך לפרק הבא?`
                  : `You've completed chapter ${currentStory?.currentChapter} of ${currentStory?.totalChapters}. Ready for the next chapter?`}
              </p>
              <div className="space-y-3">
                <button
                  onClick={handleContinueStory}
                  disabled={isLoading}
                  className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {currentChild.language === 'hebrew' 
                    ? 'המשך לפרק הבא' 
                    : 'Continue to Next Chapter'}
                </button>
                <button
                  onClick={() => navigate('/child/dashboard')}
                  className="btn-secondary"
                >
                  {currentChild.language === 'hebrew' 
                    ? 'חזור לסיפורים' 
                    : 'Back to Stories'}
                </button>
              </div>
            </div>
          )}

          {/* Story Completed */}
          {isLastParagraph && !hasChoices && currentStory.isCompleted && (
            <div className="text-center mt-8">
              <div className="text-6xl mb-4">🎉</div>
              <h3 className="text-child-lg font-bold text-success-600 mb-4">
                {currentChild.language === 'hebrew' 
                  ? 'כל הכבוד! סיימת את הסיפור!' 
                  : 'Congratulations! You finished the story!'}
              </h3>
              <button
                onClick={() => navigate('/child/dashboard')}
                className="btn-success"
              >
                {currentChild.language === 'hebrew' 
                  ? 'חזור לסיפורים' 
                  : 'Back to Stories'}
              </button>
            </div>
          )}
        </div>

        {/* Loading Overlay */}
        {isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="card-child text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
              <h3 className="text-child-base font-bold mb-2">
                {currentChild.language === 'hebrew' 
                  ? 'ממשיך את הסיפור...' 
                  : 'Continuing your story...'}
              </h3>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ReadingPage