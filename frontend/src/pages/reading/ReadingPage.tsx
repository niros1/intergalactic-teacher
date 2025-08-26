import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useStoryStore } from '../../stores/storyStore'
import { useChildStore } from '../../stores/childStore'

const ReadingPage: React.FC = () => {
  const navigate = useNavigate()
  const { currentStory, makeChoice, isLoading } = useStoryStore()
  const { currentChild } = useChildStore()
  const [currentParagraph, setCurrentParagraph] = useState(0)
  const [isReading, setIsReading] = useState(false)

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
    try {
      await makeChoice('1', {
        choiceId: choiceId,
        timestamp: new Date().toISOString()
      }) // Using session ID '1' as placeholder
      setCurrentParagraph(0) // Reset to beginning of new content
    } catch (error) {
      // Error is handled by the store
    }
  }

  const handleNextParagraph = () => {
    if (currentParagraph < currentStory.content.length - 1) {
      setCurrentParagraph(prev => prev + 1)
    }
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

  const isLastParagraph = currentParagraph === currentStory.content.length - 1
  const hasChoices = currentStory.choices.length > 0

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
            {currentStory.content[currentParagraph]}
          </div>

          {/* Paragraph Navigation */}
          <div className="text-center text-sm text-gray-500 mb-4">
            {currentChild.language === 'hebrew' 
              ? `פסקה ${currentParagraph + 1} מתוך ${currentStory.content.length}`
              : `Paragraph ${currentParagraph + 1} of ${currentStory.content.length}`}
          </div>

          {/* Choices */}
          {isLastParagraph && hasChoices && (
            <div className="mt-8">
              <h3 className="text-child-base font-bold text-gray-800 mb-4">
                {currentChild.language === 'hebrew' 
                  ? 'מה תרצה לעשות?' 
                  : 'What would you like to do?'}
              </h3>
              <div className="grid gap-4">
                {currentStory.choices.map(choice => (
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