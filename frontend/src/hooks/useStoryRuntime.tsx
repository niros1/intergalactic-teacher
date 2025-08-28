import { useState, useCallback, useMemo, useEffect } from 'react';
import { useStoryStore } from '../stores/storyStore';
import { useChildStore } from '../stores/childStore';
import type { Choice } from '../types';

interface StoryMessage {
  id: string;
  role: 'assistant' | 'user' | 'system';
  content: Array<{ type: 'text'; text: string }>;
  createdAt: Date;
  metadata?: {
    chapterNumber?: number;
    paragraphIndex?: number;
    storyId?: string;
    choices?: Choice[];
  };
}

interface StoryRuntimeState {
  messages: StoryMessage[];
  currentParagraphIndex: number;
  isLoading: boolean;
  sessionId: string | null;
}

export const useStoryRuntime = () => {
  const { currentStory, makeChoice, isLoading, startSession } = useStoryStore();
  const { currentChild } = useChildStore();
  
  const [state, setState] = useState<StoryRuntimeState>({
    messages: [],
    currentParagraphIndex: 0,
    isLoading: false,
    sessionId: null,
  });

  // Initialize story session and first message
  const initializeStory = useCallback(async () => {
    if (!currentStory || !currentChild || state.sessionId) return;

    try {
      setState(prev => ({ ...prev, isLoading: true }));
      
      const sessionResponse = await startSession({
        storyId: currentStory.id,
        childId: currentChild.id
      });

      const sessionId = sessionResponse.session ? sessionResponse.session.id : (sessionResponse as any).id;
      
      // Create welcome message
      const welcomeMessage: StoryMessage = {
        id: 'welcome-1',
        role: 'assistant',
        content: [{ 
          type: 'text', 
          text: currentChild.language === 'hebrew' 
            ? `היי ${currentChild.name}! בואו נתחיל את הסיפור "${currentStory.title}"! מוכנים להרפתקה? 🌟`
            : `Hi ${currentChild.name}! Let's start the story "${currentStory.title}"! Ready for an adventure? 🌟`
        }],
        createdAt: new Date(),
        metadata: {
          storyId: currentStory.id,
          chapterNumber: currentStory.currentChapter
        }
      };

      setState(prev => ({
        ...prev,
        messages: [welcomeMessage],
        sessionId,
        isLoading: false
      }));

      // Auto-send first paragraph after welcome
      setTimeout(() => {
        sendNextParagraph();
      }, 1500);

    } catch (error) {
      console.error('Failed to initialize story:', error);
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [currentStory, currentChild, startSession, state.sessionId]);

  // Send next story paragraph
  const sendNextParagraph = useCallback(() => {
    if (!currentStory || !currentStory.content) return;

    const { currentParagraphIndex } = state;
    if (currentParagraphIndex >= currentStory.content.length) return;

    const paragraphText = currentStory.content[currentParagraphIndex];
    const isLastParagraph = currentParagraphIndex === currentStory.content.length - 1;

    const messageId = `story-${currentStory.currentChapter}-${currentParagraphIndex}`;
    
    const newMessage: StoryMessage = {
      id: messageId,
      role: 'assistant',
      content: [{ type: 'text', text: paragraphText }],
      createdAt: new Date(),
      metadata: {
        storyId: currentStory.id,
        chapterNumber: currentStory.currentChapter,
        paragraphIndex: currentParagraphIndex,
        ...(isLastParagraph && currentStory.choices && currentStory.choices.length > 0 
          ? { choices: currentStory.choices }
          : {})
      }
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, newMessage],
      currentParagraphIndex: currentParagraphIndex + 1
    }));

    // If it's the last paragraph and has choices, send choice options
    if (isLastParagraph && currentStory.choices && currentStory.choices.length > 0) {
      setTimeout(() => {
        sendChoiceOptions(currentStory.choices!);
      }, 1000);
    } else if (!isLastParagraph) {
      // Auto-send next paragraph after a delay
      setTimeout(() => {
        sendNextParagraph();
      }, 2000);
    }
  }, [currentStory, state.currentParagraphIndex]);

  // Send choice options
  const sendChoiceOptions = useCallback((choices: Choice[]) => {
    const isHebrew = currentChild?.language === 'hebrew';
    
    const choiceMessage: StoryMessage = {
      id: `choices-${Date.now()}`,
      role: 'assistant',
      content: [{ 
        type: 'text', 
        text: isHebrew ? 'מה תרצה לעשות?' : 'What would you like to do?'
      }],
      createdAt: new Date(),
      metadata: { choices }
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, choiceMessage]
    }));
  }, [currentChild?.language]);

  // Handle user choice selection
  const handleChoice = useCallback(async (choiceId: string, choiceText: string) => {
    if (!state.sessionId) return;

    try {
      setState(prev => ({ ...prev, isLoading: true }));

      // Add user choice message
      const userMessage: StoryMessage = {
        id: `choice-${Date.now()}`,
        role: 'user',
        content: [{ type: 'text', text: choiceText }],
        createdAt: new Date()
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, userMessage]
      }));

      // Make the choice via the story store
      await makeChoice(state.sessionId, {
        choiceId,
        timestamp: new Date().toISOString()
      });

      // Reset paragraph index for new chapter
      setState(prev => ({
        ...prev,
        currentParagraphIndex: 0,
        isLoading: false
      }));

      // Start sending new chapter content
      setTimeout(() => {
        sendNextParagraph();
      }, 500);

    } catch (error) {
      console.error('Failed to make choice:', error);
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [state.sessionId, makeChoice, sendNextParagraph]);

  // Simple runtime object for assistant-ui
  const runtime = useMemo(() => {
    return {
      messages: state.messages,
      isLoading: state.isLoading || isLoading,
      
      append: async (message: any) => {
        // Handle user messages (choices)
        if (message.role === 'user') {
          const content = Array.isArray(message.content) 
            ? message.content.find((c: any) => c.type === 'text')?.text || ''
            : message.content;

          // Check if this is a choice selection
          const lastMessage = state.messages[state.messages.length - 1];
          if (lastMessage?.metadata?.choices) {
            const choice = lastMessage.metadata.choices.find(c => 
              c.text.includes(content) || content.includes(c.text)
            );
            if (choice) {
              await handleChoice(choice.id, choice.text);
              return;
            }
          }

          // Handle "continue story" messages
          if (content.toLowerCase().includes('continue') || 
              content.toLowerCase().includes('next') ||
              content.toLowerCase().includes('המשך')) {
            sendNextParagraph();
          }
        }
      },
      
      thread: {
        mainItem: {
          id: 'main',
          messages: state.messages
        }
      }
    };
  }, [state, isLoading, handleChoice, sendNextParagraph]);

  // Auto-initialize when story is available
  useEffect(() => {
    if (currentStory && currentChild && !state.sessionId) {
      initializeStory();
    }
  }, [currentStory, currentChild, state.sessionId, initializeStory]);

  return runtime;
};