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
    storyId?: string;
    choices?: Choice[];
  };
}

interface StoryRuntimeState {
  messages: StoryMessage[];
  isLoading: boolean;
  sessionId: string | null;
  isInitialized: boolean;
}

export const useStoryRuntime = () => {
  const { currentStory, makeChoice, isLoading, startSession } = useStoryStore();
  const { currentChild } = useChildStore();
  
  const [state, setState] = useState<StoryRuntimeState>({
    messages: [],
    isLoading: false,
    sessionId: null,
    isInitialized: false,
  });

  // Initialize story session and first message
  const initializeStory = useCallback(async () => {
    if (!currentStory || !currentChild || state.sessionId || state.isInitialized) return;

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
        isLoading: false,
        isInitialized: true
      }));

      // Don't auto-send first chapter here - let the content watcher handle it

    } catch (error) {
      console.error('Failed to initialize story:', error);
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [currentStory, currentChild, startSession, state.sessionId, state.isInitialized]);

  // Send current chapter as single chat message
  const sendCurrentChapter = useCallback(() => {
    if (!currentStory || !currentStory.content || currentStory.content.length === 0) return;

    // Combine all paragraphs into single chat message
    const chapterText = Array.isArray(currentStory.content) 
      ? currentStory.content.join('\n\n')
      : currentStory.content;

    const messageId = `chapter-${currentStory.currentChapter}`;
    
    const chapterMessage: StoryMessage = {
      id: messageId,
      role: 'assistant',
      content: [{ type: 'text', text: chapterText }],
      createdAt: new Date(),
      metadata: {
        storyId: currentStory.id,
        chapterNumber: currentStory.currentChapter
      }
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, chapterMessage]
    }));

    // Send choices if available
    if (currentStory.choices && currentStory.choices.length > 0) {
      setTimeout(() => {
        sendChoiceOptions(currentStory.choices!);
      }, 1000);
    }
  }, [currentStory]);

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

      // Make the choice via the story store - this will generate next chapter
      await makeChoice(state.sessionId, {
        choiceId,
        timestamp: new Date().toISOString()
      });

      setState(prev => ({ ...prev, isLoading: false }));

      // The makeChoice call will update currentStory in the store with new chapter content
      // We need to listen for that change and send the new chapter
      setTimeout(() => {
        sendCurrentChapter();
      }, 1000);

    } catch (error) {
      console.error('Failed to make choice:', error);
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [state.sessionId, makeChoice, sendCurrentChapter]);

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

          // Handle "start story" messages (yes, ready, continue, etc.)
          if (content.toLowerCase().includes('yes') ||
              content.toLowerCase().includes('ready') ||
              content.toLowerCase().includes('start') ||
              content.toLowerCase().includes('begin') ||
              content.toLowerCase().includes('continue') || 
              content.toLowerCase().includes('next') ||
              content.toLowerCase().includes('go') ||
              content.toLowerCase().includes('כן') ||
              content.toLowerCase().includes('מוכן') ||
              content.toLowerCase().includes('התחל') ||
              content.toLowerCase().includes('המשך')) {
            sendCurrentChapter();
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
  }, [state, isLoading, handleChoice, sendCurrentChapter]);

  // Auto-initialize when story is available
  useEffect(() => {
    if (currentStory && currentChild && !state.sessionId && !state.isInitialized) {
      initializeStory();
    }
  }, [currentStory, currentChild, state.sessionId, state.isInitialized, initializeStory]);

  // Watch for story content changes (new chapters from backend)
  useEffect(() => {
    if (currentStory && currentStory.content && state.sessionId) {
      // Check if we have messages and if the latest chapter is already displayed
      const lastStoryMessage = state.messages
        .filter(msg => msg.metadata?.chapterNumber)
        .pop();
      
      const currentChapterInMessages = lastStoryMessage?.metadata?.chapterNumber || 0;
      
      // If we have a new chapter from backend, send it to chat
      if (currentStory.currentChapter > currentChapterInMessages) {
        // Add a delay for better UX, especially for first chapter after welcome
        const delay = state.messages.length === 1 ? 1500 : 500; // Longer delay after welcome
        setTimeout(() => {
          sendCurrentChapter();
        }, delay);
      }
    }
  }, [currentStory?.currentChapter, currentStory?.content, state.sessionId, state.messages, sendCurrentChapter]);

  return runtime;
};