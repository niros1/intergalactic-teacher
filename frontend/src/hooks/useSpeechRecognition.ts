import { useState, useRef, useCallback, useEffect } from 'react';

export interface SpeechRecognitionConfig {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  maxAlternatives?: number;
}

export interface UseSpeechRecognitionReturn {
  transcript: string;
  interimTranscript: string;
  finalTranscript: string;
  isListening: boolean;
  hasRecognitionSupport: boolean;
  startListening: (config?: SpeechRecognitionConfig) => void;
  stopListening: () => void;
  resetTranscript: () => void;
  error: string | null;
}

// Type declarations for Web Speech API
declare global {
  interface Window {
    SpeechRecognition?: new() => SpeechRecognition;
    webkitSpeechRecognition?: new() => SpeechRecognition;
  }
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  grammars: SpeechGrammarList;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  onaudioend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onaudiostart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
  onnomatch: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
  onsoundend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onsoundstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onspeechend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onspeechstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  serviceURI: string;
  start(): void;
  stop(): void;
  abort(): void;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: 'no-speech' | 'aborted' | 'audio-capture' | 'network' | 'not-allowed' | 'service-not-allowed' | 'bad-grammar' | 'language-not-supported';
  message?: string;
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechGrammarList {
  length: number;
  addFromString(string: string, weight?: number): void;
  addFromURI(src: string, weight?: number): void;
  item(index: number): SpeechGrammar;
  [index: number]: SpeechGrammar;
}

interface SpeechGrammar {
  src: string;
  weight: number;
}

export const useSpeechRecognition = (): UseSpeechRecognitionReturn => {
  const [transcript, setTranscript] = useState<string>('');
  const [interimTranscript, setInterimTranscript] = useState<string>('');
  const [finalTranscript, setFinalTranscript] = useState<string>('');
  const [isListening, setIsListening] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const restartTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Check for browser support
  const hasRecognitionSupport = !!(
    typeof window !== 'undefined' &&
    (window.SpeechRecognition || window.webkitSpeechRecognition)
  );

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
    setFinalTranscript('');
    setError(null);
  }, []);

  const getErrorMessage = (errorType: string, isHebrew: boolean): string => {
    const errors: Record<string, { en: string; he: string }> = {
      'not-allowed': {
        en: 'Microphone access denied. Please allow microphone access in your browser settings.',
        he: 'הגישה למיקרופון נדחתה. אנא אפשר גישה למיקרופון בהגדרות הדפדפן.'
      },
      'no-speech': {
        en: 'No speech detected. Please try speaking clearly.',
        he: 'לא זוהה דיבור. אנא נסה לדבר בבירור.'
      },
      'audio-capture': {
        en: 'Microphone not found. Please check your microphone connection.',
        he: 'מיקרופון לא נמצא. אנא בדוק את החיבור של המיקרופון.'
      },
      'network': {
        en: 'Network error. Please check your internet connection.',
        he: 'שגיאת רשת. אנא בדוק את החיבור לאינטרנט.'
      },
      'language-not-supported': {
        en: 'Language not supported. Please try switching to English.',
        he: 'השפה לא נתמכת. אנא נסה לעבור לאנגלית.'
      },
      default: {
        en: 'Speech recognition error occurred. Please try again.',
        he: 'אירעה שגיאה בזיהוי הדיבור. אנא נסה שוב.'
      }
    };

    const errorInfo = errors[errorType] || errors.default;
    return isHebrew ? errorInfo.he : errorInfo.en;
  };

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    if (restartTimeoutRef.current) {
      clearTimeout(restartTimeoutRef.current);
      restartTimeoutRef.current = null;
    }
    setIsListening(false);
  }, []);

  const startListening = useCallback((config: SpeechRecognitionConfig = {}) => {
    if (!hasRecognitionSupport) {
      const isHebrew = config.language?.includes('he');
      setError(getErrorMessage('not-allowed', !!isHebrew));
      return;
    }

    setError(null);
    resetTranscript();

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition!;
      recognitionRef.current = new SpeechRecognition();

      recognitionRef.current.continuous = config.continuous ?? true;
      recognitionRef.current.interimResults = config.interimResults ?? true;
      recognitionRef.current.lang = config.language ?? 'en-US';
      recognitionRef.current.maxAlternatives = config.maxAlternatives ?? 1;

      recognitionRef.current.onstart = () => {
        setIsListening(true);
        setError(null);
      };

      recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          const transcriptPart = result[0].transcript;

          if (result.isFinal) {
            finalTranscript += transcriptPart + ' ';
          } else {
            interimTranscript += transcriptPart;
          }
        }

        setInterimTranscript(interimTranscript);
        setFinalTranscript(prev => prev + finalTranscript);
        setTranscript(prev => prev + finalTranscript + interimTranscript);
      };

      recognitionRef.current.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error('Speech recognition error:', event.error);
        const isHebrew = config.language?.includes('he');
        setError(getErrorMessage(event.error, !!isHebrew));
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
        
        // Auto-restart for continuous recognition
        if (config.continuous && recognitionRef.current && !error) {
          restartTimeoutRef.current = setTimeout(() => {
            if (recognitionRef.current) {
              recognitionRef.current.start();
            }
          }, 100);
        }
      };

      recognitionRef.current.start();
    } catch (err) {
      console.error('Failed to start speech recognition:', err);
      const isHebrew = config.language?.includes('he');
      setError(getErrorMessage('not-allowed', !!isHebrew));
    }
  }, [hasRecognitionSupport, error, resetTranscript]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (restartTimeoutRef.current) {
        clearTimeout(restartTimeoutRef.current);
      }
    };
  }, []);

  // Combine final and interim transcripts
  useEffect(() => {
    setTranscript(finalTranscript + interimTranscript);
  }, [finalTranscript, interimTranscript]);

  return {
    transcript,
    interimTranscript,
    finalTranscript,
    isListening,
    hasRecognitionSupport,
    startListening,
    stopListening,
    resetTranscript,
    error,
  };
};