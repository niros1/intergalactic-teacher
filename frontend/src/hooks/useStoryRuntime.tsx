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
  usedChoiceMessageIds: Set<string>;
}

export const useStoryRuntime = () => {
  const { currentStory, makeChoice, isLoading, startSession, streamingState } = useStoryStore();
  const { currentChild } = useChildStore();

  const [state, setState] = useState<StoryRuntimeState>({
    messages: [],
    isLoading: false,
    sessionId: null,
    isInitialized: false,
    usedChoiceMessageIds: new Set(),
  });

  // Initialize story session and first message
  const initializeStory = useCallback(async () => {
    if (!currentStory || !currentChild || state.sessionId || state.isInitialized) return;

    try {
      setState(prev => ({ ...prev, isLoading: true }));

      const sessionResponse = await startSession({
        storyId: currentStory.id,
        childId: currentChild.id.toString()
      });

      const sessionId = sessionResponse.session ? sessionResponse.session.id.toString() : (sessionResponse as any).id.toString();

      // Create welcome message
      const welcomeMessage: StoryMessage = {
        id: 'welcome-1',
        role: 'assistant',
        content: [{
          type: 'text',
          text: currentChild.language_preference === 'hebrew'
            ? `היי ${currentChild.name}! בואו נתחיל את הסיפור "${currentStory.title}"! מוכנים להרפתקה? 🌟`
            : `Hi ${currentChild.name}! Let's start the story "${currentStory.title}"! Ready for an adventure? 🌟`
        }],
        createdAt: new Date(),
        metadata: {
          storyId: currentStory.id,
          chapterNumber: currentStory.currentChapter
        }
      };

      // For existing stories, load all previous chapters
      const messagesToAdd: StoryMessage[] = [welcomeMessage];

      // If this is an existing story with content, add all chapters up to current
      // BUT: Don't load content if we're currently streaming (story is being generated)
      if (currentStory.content && currentStory.content.length > 0 && !streamingState.isStreaming) {
        // If content is an array, each element is a separate chapter
        if (Array.isArray(currentStory.content)) {
          // Add each chapter as a separate message
          currentStory.content.forEach((chapterContent, index) => {
            const chapterNumber = index + 1;
            const chapterMessage: StoryMessage = {
              id: `chapter-${chapterNumber}-${Date.now()}-${index}`,
              role: 'assistant',
              content: [{ type: 'text', text: chapterContent }],
              createdAt: new Date(Date.now() + index * 1000), // Slight delay for ordering
              metadata: {
                storyId: currentStory.id,
                chapterNumber: chapterNumber
              }
            };
            messagesToAdd.push(chapterMessage);
          });
        } else {
          // Single content block - treat as one chapter
          const chapterMessage: StoryMessage = {
            id: `chapter-${currentStory.currentChapter}-${Date.now()}`,
            role: 'assistant',
            content: [{ type: 'text', text: currentStory.content }],
            createdAt: new Date(),
            metadata: {
              storyId: currentStory.id,
              chapterNumber: currentStory.currentChapter
            }
          };
          messagesToAdd.push(chapterMessage);
        }

        // Add choices if available (only after the last chapter)
        if (currentStory.choices && currentStory.choices.length > 0) {
          // Get the contextual question from the first choice (they all have the same question)
          const choiceQuestion = currentStory.choices[0]?.choice_question;

          // Only add a question message if we have a choice_question from the backend
          // Otherwise, the question is already in the story content
          if (choiceQuestion) {
            const choiceMessage: StoryMessage = {
              id: `choices-${Date.now()}`,
              role: 'assistant',
              content: [{
                type: 'text',
                text: choiceQuestion
              }],
              createdAt: new Date(Date.now() + 2000), // Add after all chapters
              metadata: {
                choices: currentStory.choices,
                chapterNumber: currentStory.currentChapter
              }
            };
            messagesToAdd.push(choiceMessage);
          } else {
            // No separate question message - choices will be shown directly
            // The question is already embedded in the story content
            const choiceMessage: StoryMessage = {
              id: `choices-${Date.now()}`,
              role: 'assistant',
              content: [], // No text content, just metadata with choices
              createdAt: new Date(Date.now() + 2000),
              metadata: {
                choices: currentStory.choices,
                chapterNumber: currentStory.currentChapter
              }
            };
            messagesToAdd.push(choiceMessage);
          }
        }
      }

      setState(prev => ({
        ...prev,
        messages: messagesToAdd,
        sessionId,
        isLoading: false,
        isInitialized: true
      }));

      // Don't auto-send first chapter here since we already added it

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

    const messageId = `chapter-${currentStory.currentChapter}-${Date.now()}`;

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
        // Check if choices for this chapter are already in messages
        const hasChoicesForCurrentChapter = state.messages.some(msg =>
          msg.metadata?.choices && msg.metadata?.chapterNumber === currentStory.currentChapter
        );

        if (!hasChoicesForCurrentChapter) {
          sendChoiceOptions(currentStory.choices!);
        }
      }, 1000);
    }
  }, [currentStory]);

  // Send choice options
  const sendChoiceOptions = useCallback((choices: Choice[]) => {
    // Get the contextual question from the first choice (they all have the same question)
    const choiceQuestion = choices[0]?.choice_question;

    // Only add a question message if we have a choice_question from the backend
    // Otherwise, the question is already in the story content
    if (choiceQuestion) {
      const choiceMessage: StoryMessage = {
        id: `choices-${Date.now()}`,
        role: 'assistant',
        content: [{
          type: 'text',
          text: choiceQuestion
        }],
        createdAt: new Date(),
        metadata: { choices, chapterNumber: currentStory?.currentChapter }
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, choiceMessage]
      }));
    } else {
      // No separate question message - choices will be shown directly
      const choiceMessage: StoryMessage = {
        id: `choices-${Date.now()}`,
        role: 'assistant',
        content: [], // No text content, just metadata with choices
        createdAt: new Date(),
        metadata: { choices, chapterNumber: currentStory?.currentChapter }
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, choiceMessage]
      }));
    }
  }, [currentStory?.currentChapter]);

  // Handle user choice selection
  const handleChoice = useCallback(async (choiceId: string, optionIndex: number, choiceText: string, messageId: string) => {
    if (!state.sessionId) return;

    try {
      setState(prev => ({ ...prev, isLoading: true }));

      // Mark this message's choices as used
      setState(prev => {
        const newUsedIds = new Set(prev.usedChoiceMessageIds);
        newUsedIds.add(messageId);
        return {
          ...prev,
          usedChoiceMessageIds: newUsedIds
        };
      });

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
        optionIndex,
        timestamp: new Date().toISOString()
      });

      setState(prev => ({ ...prev, isLoading: false }));

      // The makeChoice call will update currentStory in the store with new chapter content
      // The useEffect watching currentStory changes will handle sending the new chapter automatically

    } catch (error) {
      console.error('Failed to make choice:', error);
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [state.sessionId, makeChoice, sendCurrentChapter]);

  // Handle custom text input as a story choice
  const handleCustomChoice = useCallback(async (customText: string) => {
    if (!state.sessionId || !customText.trim()) return;

    try {
      setState(prev => ({ ...prev, isLoading: true }));

      // Add user custom message
      const userMessage: StoryMessage = {
        id: `custom-choice-${Date.now()}`,
        role: 'user',
        content: [{ type: 'text', text: customText }],
        createdAt: new Date()
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, userMessage]
      }));

      // Make the custom choice via the story store using a generic choice ID
      await makeChoice(state.sessionId, {
        choiceId: 'custom-choice',
        optionIndex: 0,
        timestamp: new Date().toISOString(),
        customText: customText.trim()
      });

      setState(prev => ({ ...prev, isLoading: false }));

    } catch (error) {
      console.error('Failed to make custom choice:', error);
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [state.sessionId, makeChoice]);

  // Simple runtime object for assistant-ui
  const runtime = useMemo(() => {
    return {
      messages: state.messages,
      isLoading: state.isLoading || isLoading,
      usedChoiceMessageIds: state.usedChoiceMessageIds,

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
              await handleChoice(choice.id, choice.option_index, choice.text, lastMessage.id);
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
            return;
          }

          // If we have an active session and it's not just a start command,
          // treat any user input as a custom choice that should advance the story
          if (state.sessionId && content.trim().length > 0) {
            await handleCustomChoice(content);
            return;
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
  }, [state, isLoading, handleChoice, handleCustomChoice, sendCurrentChapter]);

  // Auto-initialize when story is available
  useEffect(() => {
    if (currentStory && currentChild && !state.sessionId && !state.isInitialized) {
      initializeStory();
    }
  }, [currentStory, currentChild, state.sessionId, state.isInitialized, initializeStory]);

  // Watch for streaming content during story generation
  useEffect(() => {
    // console.log('🔄 Streaming useEffect triggered:', {
    //   isStreaming: streamingState.isStreaming,
    //   contentLength: streamingState.streamedContent?.length,
    //   isInitialized: state.isInitialized
    // });

    if (streamingState.isStreaming && streamingState.streamedContent && state.isInitialized) {
      // Find or create the streaming message
      const streamingMessageId = `streaming-${currentStory?.id || 'temp'}`;
      const existingMessageIndex = state.messages.findIndex(m => m.id === streamingMessageId);

      // console.log('📝 Updating streaming message:', {
      //   messageId: streamingMessageId,
      //   existingIndex: existingMessageIndex,
      //   contentPreview: streamingState.streamedContent.substring(0, 50)
      // });

      if (existingMessageIndex >= 0) {
        // Update existing streaming message
        setState(prev => {
          const newMessages = [...prev.messages];
          newMessages[existingMessageIndex] = {
            ...newMessages[existingMessageIndex],
            content: [{ type: 'text', text: streamingState.streamedContent }]
          };
          return { ...prev, messages: newMessages };
        });
      } else {
        // Create new streaming message
        const streamingMessage: StoryMessage = {
          id: streamingMessageId,
          role: 'assistant',
          content: [{ type: 'text', text: streamingState.streamedContent }],
          createdAt: new Date(),
          metadata: {
            storyId: currentStory?.id,
            chapterNumber: currentStory?.currentChapter
          }
        };
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, streamingMessage]
        }));
      }
    }
  }, [streamingState.isStreaming, streamingState.streamedContent, state.isInitialized, state.messages, currentStory?.id, currentStory?.currentChapter]);

  // Watch for story content changes (new chapters from backend)
  useEffect(() => {
    if (currentStory && currentStory.content && state.sessionId && state.isInitialized) {
      // Check if we have messages and if the latest chapter is already displayed
      const lastStoryMessage = state.messages
        .filter(msg => msg.metadata?.chapterNumber)
        .pop();

      const currentChapterInMessages = lastStoryMessage?.metadata?.chapterNumber || 0;

      // If we have a new chapter from backend that's not yet displayed, send it to chat
      if (currentStory.currentChapter > currentChapterInMessages) {
        // Add a delay for better UX, especially for first chapter after welcome
        const delay = state.messages.length === 1 ? 1500 : 500; // Longer delay after welcome
        setTimeout(() => {
          sendCurrentChapter();
        }, delay);
      }
    }
  }, [currentStory?.currentChapter, currentStory?.content, state.sessionId, state.messages, state.isInitialized, sendCurrentChapter]);

  // Watch for choices after streaming completes
  useEffect(() => {
    // When streaming stops and we have choices, add them to messages
    if (!streamingState.isStreaming && currentStory?.choices && currentStory.choices.length > 0 && state.isInitialized) {
      // Check if choices are already displayed for current chapter
      const hasChoicesForCurrentChapter = state.messages.some(msg =>
        msg.metadata?.choices && msg.metadata?.chapterNumber === currentStory.currentChapter
      );

      if (!hasChoicesForCurrentChapter) {
        console.log('💡 Streaming finished - adding choices to messages:', currentStory.choices);
        setTimeout(() => {
          sendChoiceOptions(currentStory.choices!);
        }, 500); // Small delay after streaming stops
      }
    }
  }, [streamingState.isStreaming, currentStory?.choices, currentStory?.currentChapter, state.isInitialized, state.messages, sendChoiceOptions]);

  return runtime;
};