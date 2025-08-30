import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStoryStore } from '../../stores/storyStore';
import { useChildStore } from '../../stores/childStore';
import { useStoryRuntime } from '../../hooks/useStoryRuntime';

const ChatReadingPage: React.FC = () => {
  const navigate = useNavigate();
  const { currentStory } = useStoryStore();
  const { currentChild } = useChildStore();
  const runtime = useStoryRuntime();
  const [inputValue, setInputValue] = useState('');

  // Check if we have the necessary data
  if (!currentStory || !currentChild) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="heading-child">
            {currentChild?.language_preference === 'hebrew' ? 'טוען סיפור...' : 'Loading story...'}
          </h1>
          <button
            onClick={() => navigate('/child/dashboard')}
            className="btn-secondary mt-4"
          >
            {currentChild?.language_preference === 'hebrew' ? '← חזור' : '← Back'}
          </button>
        </div>
      </div>
    );
  }

  const isHebrew = currentChild.language_preference === 'hebrew';

  const handleSendMessage = async () => {
    if (inputValue.trim() && runtime.append) {
      await runtime.append({
        role: 'user',
        content: inputValue.trim()
      });
      setInputValue('');
    }
  };

  const handleChoiceClick = async (choiceText: string) => {
    if (runtime.append) {
      await runtime.append({
        role: 'user',
        content: choiceText
      });
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden" style={{
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 100%)'
    }}>
      {/* Floating decorative elements */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-10 left-10 w-8 h-8 text-yellow-400 animate-bounce" style={{ animationDelay: '0s' }}>⭐</div>
        <div className="absolute top-32 right-16 w-6 h-6 text-pink-400 animate-bounce" style={{ animationDelay: '1s' }}>🌟</div>
        <div className="absolute bottom-32 left-20 w-7 h-7 text-blue-400 animate-bounce" style={{ animationDelay: '2s' }}>✨</div>
        <div className="absolute bottom-20 right-32 w-6 h-6 text-purple-400 animate-bounce" style={{ animationDelay: '1.5s' }}>🎈</div>
      </div>

      <div className="max-w-4xl mx-auto p-2 sm:p-4 relative z-10">
        {/* Enhanced Header */}
        <div className="flex flex-col sm:flex-row items-center justify-between mb-4 sm:mb-6 bg-white/90 backdrop-blur-sm rounded-3xl shadow-2xl p-4 sm:p-6 border-2 border-white/50">
          <button
            onClick={() => navigate('/child/dashboard')}
            className="btn-secondary text-sm sm:text-base mb-3 sm:mb-0 order-2 sm:order-1"
          >
            {isHebrew ? '← חזור' : '← Back'}
          </button>
          
          <div className="text-center flex-1 order-1 sm:order-2">
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-black mb-2" style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              {currentStory.title}
            </h1>
            <div className="flex items-center justify-center space-x-2 text-sm sm:text-base text-gray-600">
              <span className="text-lg">📖</span>
              <span>
                {isHebrew 
                  ? `פרק ${currentStory.currentChapter} מתוך ${currentStory.totalChapters}`
                  : `Chapter ${currentStory.currentChapter} of ${currentStory.totalChapters}`}
              </span>
            </div>
          </div>

          {/* Enhanced Progress indicator */}
          <div className="w-full sm:w-20 flex justify-center sm:justify-end order-3 mt-3 sm:mt-0">
            <div className="text-center">
              <div className="w-24 sm:w-16 h-3 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500 ease-out rounded-full"
                  style={{ 
                    width: `${((currentStory.currentChapter - 1) / currentStory.totalChapters) * 100}%` 
                  }}
                />
              </div>
              <div className="text-xs mt-1 font-bold text-gray-600">
                {Math.round(((currentStory.currentChapter - 1) / currentStory.totalChapters) * 100)}%
              </div>
            </div>
          </div>
        </div>

        {/* Chat Interface */}
        <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl overflow-hidden border-2 border-white/50" 
             style={{ height: 'calc(100vh - 200px)', minHeight: '400px' }}>
          
          {/* Messages Area */}
          <div className="h-full flex flex-col">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {runtime.messages && runtime.messages.map((message: any) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-slideIn`}
                >
                  <div 
                    className={`max-w-[80%] p-4 rounded-2xl shadow-lg ${
                      message.role === 'user' 
                        ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white' 
                        : 'bg-gradient-to-r from-blue-100 to-purple-100 text-gray-800'
                    }`}
                    style={{
                      direction: isHebrew ? 'rtl' : 'ltr',
                    }}
                  >
                    <div className="text-base sm:text-lg font-medium leading-relaxed">
                      {message.content[0]?.text || ''}
                    </div>
                    
                    {/* Story Choices */}
                    {message.metadata?.choices && (
                      <div className="mt-4 space-y-2">
                        {message.metadata.choices.map((choice: any) => (
                          <button
                            key={choice.id}
                            onClick={() => handleChoiceClick(choice.text)}
                            className="w-full p-3 bg-white/90 text-gray-800 rounded-xl hover:bg-white transition-all transform hover:scale-105 shadow-md text-left"
                            style={{ direction: isHebrew ? 'rtl' : 'ltr' }}
                          >
                            <span className="text-lg mr-2">
                              {choice.id === 'choice1' ? '🌟' : choice.id === 'choice2' ? '🎯' : '🚀'}
                            </span>
                            {choice.text}
                          </button>
                        ))}
                        <div className="text-center mt-3 text-sm text-gray-500 italic">
                          {isHebrew ? 'או כתב משהו משלך למטה!' : 'Or type your own response below!'}
                        </div>
                      </div>
                    )}

                    {/* Audio button for assistant messages */}
                    {message.role === 'assistant' && (
                      <button 
                        className="mt-2 p-2 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
                        onClick={() => {
                          // Audio playback logic here
                          console.log('Playing audio for:', message.content[0]?.text);
                        }}
                      >
                        🔊
                      </button>
                    )}
                  </div>
                </div>
              ))}
              
              {runtime.isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gradient-to-r from-gray-100 to-gray-200 rounded-2xl p-4 shadow-lg">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-200 p-4 bg-white/80 backdrop-blur-sm">
              {/* Helpful hint for custom input */}
              {runtime.messages && runtime.messages.length > 1 && (
                <div className="mb-3 text-center text-sm text-gray-600 px-2">
                  <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-2 border border-purple-100">
                    <span className="text-purple-600 font-medium">
                      {isHebrew 
                        ? '💭 אתה יכול לכתוב כל דבר - הסיפור יתאים לרעיונות שלך!'
                        : '💭 You can type anything - the story will adapt to your ideas!'}
                    </span>
                  </div>
                </div>
              )}
              
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder={isHebrew ? 'כתב כל דבר... הסיפור יענה!' : 'Type anything... the story will respond!'}
                  className="flex-1 p-3 border-2 border-purple-200 rounded-2xl focus:border-purple-400 focus:outline-none text-lg"
                  style={{ direction: isHebrew ? 'rtl' : 'ltr' }}
                />
                <button
                  onClick={handleSendMessage}
                  className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-2xl hover:from-purple-600 hover:to-pink-600 transition-all transform hover:scale-105 shadow-lg font-bold"
                >
                  {isHebrew ? 'שלח' : 'Send'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Story info footer */}
        <div className="mt-4 text-center">
          <div className="inline-flex flex-wrap items-center justify-center gap-2 sm:gap-4 text-xs sm:text-sm bg-white/90 backdrop-blur-sm rounded-3xl shadow-xl px-4 py-3 border-2 border-white/50">
            <div className="flex items-center space-x-1">
              <span className="text-base">🎯</span>
              <span className="font-semibold text-gray-700">
                {isHebrew ? 'רמה:' : 'Level:'} {currentStory.readingLevel}
              </span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-base">🌍</span>
              <span className="font-semibold text-gray-700">
                {isHebrew ? 'שפה:' : 'Language:'} {currentStory.language === 'hebrew' ? 'עברית' : 'English'}
              </span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-base">🎨</span>
              <span className="font-semibold text-gray-700">
                {isHebrew ? 'נושא:' : 'Theme:'} {currentStory.theme}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatReadingPage;