import {
  ActionBarPrimitive,
  BranchPickerPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
} from "@assistant-ui/react";
import type { FC } from "react";
import { useState, useEffect, useRef } from "react";
import {
  ArrowDownIcon,
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CopyIcon,
  PencilIcon,
  RefreshCwIcon,
  SendHorizontalIcon,
  Volume2Icon,
  VolumeXIcon,
  MicIcon,
  MicOffIcon,
} from "lucide-react";
import { cn } from "../../lib/utils";

import { Button } from "./button";
import { MarkdownText } from "./markdown-text";
import { TooltipIconButton } from "./tooltip-icon-button";
import { useChildStore } from "../../stores/childStore";
import { useSpeechRecognition } from "../../hooks/useSpeechRecognition";

export const StoryThread: FC = () => {
  const { currentChild } = useChildStore();
  const isHebrew = currentChild?.language === 'hebrew';

  return (
    <ThreadPrimitive.Root
      className={cn("aui-root aui-thread-root", isHebrew && "rtl")}
      style={{
        ["--thread-max-width" as string]: "42rem",
      }}
      dir={isHebrew ? 'rtl' : 'ltr'}
    >
      <ThreadPrimitive.Viewport className="aui-thread-viewport">
        <StoryWelcome />

        <ThreadPrimitive.Messages
          components={{
            UserMessage: StoryUserMessage,
            EditComposer: StoryEditComposer,
            AssistantMessage: StoryAssistantMessage,
          }}
        />

        <ThreadPrimitive.If empty={false}>
          <div className="aui-thread-viewport-spacer" />
        </ThreadPrimitive.If>

        <div className="aui-thread-viewport-footer">
          <StoryScrollToBottom />
          <StoryComposer />
        </div>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
};

const StoryScrollToBottom: FC = () => {
  const { currentChild } = useChildStore();
  const isHebrew = currentChild?.language === 'hebrew';
  
  return (
    <ThreadPrimitive.ScrollToBottom asChild>
      <TooltipIconButton
        tooltip={isHebrew ? "גלול למטה" : "Scroll to bottom"}
        variant="outline"
        className="aui-thread-scroll-to-bottom"
      >
        <ArrowDownIcon />
      </TooltipIconButton>
    </ThreadPrimitive.ScrollToBottom>
  );
};

const StoryWelcome: FC = () => {
  const { currentChild } = useChildStore();
  const isHebrew = currentChild?.language === 'hebrew';
  
  return (
    <ThreadPrimitive.Empty>
      <div className="aui-thread-welcome-root">
        <div className="aui-thread-welcome-center">
          {/* Animated welcome character */}
          <div className="text-6xl mb-4 animate-bounce">
            {isHebrew ? "🧙‍♂️" : "🌟"}
          </div>
          <p className="aui-thread-welcome-message">
            {isHebrew ? "שלום! בוא נתחיל הרפתקה מדהימה! ✨" : "Hello! Let's begin an amazing adventure! ✨"}
          </p>
          <p className="text-child text-gray-600 mb-6">
            {isHebrew ? "אני כאן כדי לעזור לך לקרוא ולהבין את הסיפור" : "I'm here to help you read and understand the story"}
          </p>
        </div>
        <StoryWelcomeSuggestions />
      </div>
    </ThreadPrimitive.Empty>
  );
};

const StoryWelcomeSuggestions: FC = () => {
  const { currentChild } = useChildStore();
  const isHebrew = currentChild?.language === 'hebrew';
  
  const suggestions = [
    {
      emoji: "🚀",
      text: isHebrew ? "בואו נתחיל!" : "Let's begin!",
      prompt: isHebrew ? "בואו נתחיל!" : "Let's begin!"
    },
    {
      emoji: "📚",
      text: isHebrew ? "ספר לי על הסיפור" : "Tell me about the story",
      prompt: isHebrew ? "ספר לי על הסיפור" : "Tell me about the story"
    },
    {
      emoji: "🎭",
      text: isHebrew ? "מי הדמויות?" : "Who are the characters?",
      prompt: isHebrew ? "מי הדמויות בסיפור?" : "Who are the characters in the story?"
    },
    {
      emoji: "🔍",
      text: isHebrew ? "עזור לי להבין" : "Help me understand",
      prompt: isHebrew ? "עזור לי להבין את הסיפור" : "Help me understand the story"
    }
  ];
  
  return (
    <div className="aui-thread-welcome-suggestions">
      {suggestions.map((suggestion, index) => (
        <ThreadPrimitive.Suggestion
          key={index}
          className="aui-thread-welcome-suggestion"
          prompt={suggestion.prompt}
          method="replace"
          autoSend
        >
          <span className="aui-thread-welcome-suggestion-text">
            <span className="text-xl mr-2" style={{ animationDelay: `${index * 0.2}s` }}>
              {suggestion.emoji}
            </span>
            {suggestion.text}
          </span>
        </ThreadPrimitive.Suggestion>
      ))}
    </div>
  );
};

const StoryComposer: FC = () => {
  const { currentChild } = useChildStore();
  const isHebrew = currentChild?.language === 'hebrew';
  
  const {
    transcript,
    isListening,
    hasRecognitionSupport,
    startListening,
    stopListening,
    resetTranscript,
    error,
  } = useSpeechRecognition();

  // Auto-append transcript to the input using the composer's append method
  useEffect(() => {
    if (transcript && transcript.trim()) {
      // Get the current input element and append the transcript
      const inputElement = document.querySelector('.aui-composer-input') as HTMLTextAreaElement;
      if (inputElement) {
        const currentValue = inputElement.value;
        inputElement.value = currentValue + transcript;
        // Trigger input event to update the composer state
        inputElement.dispatchEvent(new Event('input', { bubbles: true }));
      }
      resetTranscript();
    }
  }, [transcript, resetTranscript]);

  const handleMicrophoneClick = () => {
    if (isListening) {
      stopListening();
    } else {
      const language = isHebrew ? 'he-IL' : 'en-US';
      startListening({ 
        language,
        continuous: false,
        interimResults: true 
      });
    }
  };
  
  return (
    <div className="relative">
      <ComposerPrimitive.Root className="aui-composer-root">
        <ComposerPrimitive.Input
          rows={1}
          autoFocus
          placeholder={isHebrew ? "כתוב הודעה או לחץ על המיקרופון..." : "Write a message or click the microphone..."}
          className="aui-composer-input"
        />
        
        <div className="flex items-center space-x-2">
          {/* Microphone Button */}
          {hasRecognitionSupport && (
            <TooltipIconButton
              tooltip={isHebrew ? 
                (isListening ? "עצור הקלטה" : "הקלט קול") : 
                (isListening ? "Stop recording" : "Record voice")
              }
              variant={isListening ? "destructive" : "outline"}
              className={cn(
                "aui-composer-microphone relative",
                isListening && "animate-pulse bg-red-500 hover:bg-red-600"
              )}
              onClick={handleMicrophoneClick}
            >
              {isListening ? (
                <>
                  <MicOffIcon />
                  {/* Pulsing recording indicator */}
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-400 rounded-full animate-ping" />
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full" />
                </>
              ) : (
                <MicIcon />
              )}
            </TooltipIconButton>
          )}
          
          <StoryComposerAction />
        </div>
      </ComposerPrimitive.Root>
      
      {/* Speech Recognition Error */}
      {error && (
        <div className="absolute bottom-full left-0 right-0 mb-2 p-2 bg-red-100 border border-red-300 rounded-lg text-red-700 text-sm z-10">
          <span className="text-lg mr-2">⚠️</span>
          {error}
        </div>
      )}
    </div>
  );
};

const StoryComposerAction: FC = () => {
  const { currentChild } = useChildStore();
  const isHebrew = currentChild?.language === 'hebrew';
  
  return (
    <>
      <ThreadPrimitive.If running={false}>
        <ComposerPrimitive.Send asChild>
          <TooltipIconButton
            tooltip={isHebrew ? "שלח" : "Send"}
            variant="default"
            className="aui-composer-send"
          >
            <SendHorizontalIcon />
          </TooltipIconButton>
        </ComposerPrimitive.Send>
      </ThreadPrimitive.If>
      <ThreadPrimitive.If running>
        <ComposerPrimitive.Cancel asChild>
          <TooltipIconButton
            tooltip={isHebrew ? "ביטול" : "Cancel"}
            variant="default"
            className="aui-composer-cancel"
          >
            <CircleStopIcon />
          </TooltipIconButton>
        </ComposerPrimitive.Cancel>
      </ThreadPrimitive.If>
    </>
  );
};

const StoryUserMessage: FC = () => {
  return (
    <MessagePrimitive.Root className="aui-user-message-root">
      <StoryUserActionBar />

      <div className="aui-user-message-content">
        <MessagePrimitive.Parts />
      </div>

      <StoryBranchPicker className="aui-user-branch-picker" />
    </MessagePrimitive.Root>
  );
};

const StoryUserActionBar: FC = () => {
  const { currentChild } = useChildStore();
  const isHebrew = currentChild?.language === 'hebrew';
  
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      className="aui-user-action-bar-root"
    >
      <ActionBarPrimitive.Edit asChild>
        <TooltipIconButton tooltip={isHebrew ? "ערוך" : "Edit"}>
          <PencilIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Edit>
    </ActionBarPrimitive.Root>
  );
};

const StoryEditComposer: FC = () => {
  const { currentChild } = useChildStore();
  const isHebrew = currentChild?.language === 'hebrew';
  
  return (
    <ComposerPrimitive.Root className="aui-edit-composer-root">
      <ComposerPrimitive.Input className="aui-edit-composer-input" />

      <div className="aui-edit-composer-footer">
        <ComposerPrimitive.Cancel asChild>
          <Button variant="ghost">{isHebrew ? "ביטול" : "Cancel"}</Button>
        </ComposerPrimitive.Cancel>
        <ComposerPrimitive.Send asChild>
          <Button>{isHebrew ? "שלח" : "Send"}</Button>
        </ComposerPrimitive.Send>
      </div>
    </ComposerPrimitive.Root>
  );
};

const StoryAssistantMessage: FC = () => {
  return (
    <MessagePrimitive.Root className="aui-assistant-message-root">
      <div className="aui-assistant-message-content">
        <MessagePrimitive.Parts components={{ Text: StoryMessageText }} />
      </div>

      <StoryAssistantActionBar />

      <StoryBranchPicker className="aui-assistant-branch-picker" />
    </MessagePrimitive.Root>
  );
};

// Custom message text component that handles audio and story-specific features
const StoryMessageText: FC<{ content: string }> = ({ content }) => {
  const { currentChild } = useChildStore();
  const isHebrew = currentChild?.language === 'hebrew';
  const [isPlaying, setIsPlaying] = useState(false);

  // Cleanup on unmount - stop any ongoing speech
  useEffect(() => {
    return () => {
      if (window.speechSynthesis && window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handleTextToSpeech = () => {
    console.log('Story thread - handleTextToSpeech called with content:', content);
    
    // Check if Speech Synthesis API is supported
    if (!('speechSynthesis' in window)) {
      console.error('Speech Synthesis API is not supported in this browser');
      alert(isHebrew ? 'הדפדפן לא תומך בהקראה' : 'Text-to-speech is not supported in this browser');
      return;
    }

    // If currently playing, stop it
    if (window.speechSynthesis.speaking) {
      console.log('Cancelling current speech');
      window.speechSynthesis.cancel();
      setIsPlaying(false);
      return;
    }

    // Validate content
    if (!content || content.trim().length === 0) {
      console.warn('No content to speak');
      return;
    }

    // Wait a bit to ensure any previous cancellation completes
    setTimeout(() => {
      const utterance = new SpeechSynthesisUtterance(content);
      
      // Set language and voice parameters
      utterance.lang = isHebrew ? 'he-IL' : 'en-US';
      utterance.rate = 0.8; // Slightly slower for better comprehension
      utterance.pitch = 1.1; // Slightly higher pitch for children
      utterance.volume = 1.0; // Full volume
      
      // Set up event handlers with detailed logging
      utterance.onstart = () => {
        console.log('Story thread - Speech started successfully');
        setIsPlaying(true);
      };
      
      utterance.onend = () => {
        console.log('Story thread - Speech ended');
        setIsPlaying(false);
      };
      
      utterance.onerror = (event) => {
        console.error('Story thread - Speech error:', event.error, event);
        setIsPlaying(false);
        
        // Show user-friendly error message
        const errorMessage = isHebrew ? 
          'שגיאה בהקראת הטקסט' : 
          'Error playing audio';
        alert(errorMessage);
      };

      // Start speaking
      try {
        window.speechSynthesis.speak(utterance);
        console.log('Story thread - Speech synthesis started successfully');
      } catch (error) {
        console.error('Story thread - Error starting speech synthesis:', error);
        setIsPlaying(false);
      }
    }, 100); // Small delay to ensure cancellation completes
  };

  return (
    <div className="story-message-text">
      <div className="story-content">
        <MarkdownText />
      </div>
      <div className="story-audio-controls">
        <button
          onClick={handleTextToSpeech}
          className={`story-audio-button ${isPlaying ? 'playing' : ''}`}
          title={isHebrew ? "הקרא לי" : "Read to me"}
        >
          {isPlaying ? (
            <VolumeXIcon size={18} />
          ) : (
            <Volume2Icon size={18} />
          )}
        </button>
        
        {/* Fun reaction buttons */}
        <div className="flex items-center space-x-2 ml-3">
          <button 
            className="text-lg hover:scale-125 transition-transform duration-200"
            title={isHebrew ? "אהבתי!" : "I love it!"}
          >
            ❤️
          </button>
          <button 
            className="text-lg hover:scale-125 transition-transform duration-200"
            title={isHebrew ? "כיף!" : "Fun!"}
          >
            😄
          </button>
          <button 
            className="text-lg hover:scale-125 transition-transform duration-200"
            title={isHebrew ? "מעניין!" : "Interesting!"}
          >
            🤔
          </button>
        </div>
      </div>
    </div>
  );
};

const StoryAssistantActionBar: FC = () => {
  const { currentChild } = useChildStore();
  const isHebrew = currentChild?.language === 'hebrew';
  
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      autohideFloat="single-branch"
      className="aui-assistant-action-bar-root"
    >
      <ActionBarPrimitive.Copy asChild>
        <TooltipIconButton tooltip={isHebrew ? "העתק" : "Copy"}>
          <MessagePrimitive.If copied>
            <CheckIcon />
          </MessagePrimitive.If>
          <MessagePrimitive.If copied={false}>
            <CopyIcon />
          </MessagePrimitive.If>
        </TooltipIconButton>
      </ActionBarPrimitive.Copy>
      <ActionBarPrimitive.Reload asChild>
        <TooltipIconButton tooltip={isHebrew ? "רענן" : "Refresh"}>
          <RefreshCwIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Reload>
    </ActionBarPrimitive.Root>
  );
};

const StoryBranchPicker: FC<BranchPickerPrimitive.Root.Props> = ({
  className,
  ...rest
}) => {
  return (
    <BranchPickerPrimitive.Root
      hideWhenSingleBranch
      className={cn("aui-branch-picker-root", className)}
      {...rest}
    >
      <BranchPickerPrimitive.Previous asChild>
        <TooltipIconButton tooltip="Previous">
          <ChevronLeftIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Previous>
      <span className="aui-branch-picker-state">
        <BranchPickerPrimitive.Number /> / <BranchPickerPrimitive.Count />
      </span>
      <BranchPickerPrimitive.Next asChild>
        <TooltipIconButton tooltip="Next">
          <ChevronRightIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Next>
    </BranchPickerPrimitive.Root>
  );
};

const CircleStopIcon = () => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 16 16"
      fill="currentColor"
      width="16"
      height="16"
    >
      <rect width="10" height="10" x="3" y="3" rx="2" />
    </svg>
  );
};