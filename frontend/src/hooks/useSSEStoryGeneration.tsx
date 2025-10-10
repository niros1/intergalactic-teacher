import { useState, useCallback, useRef, useEffect } from 'react';

export interface SSEEvent {
  type: 'content' | 'safety_check' | 'complete' | 'error' | 'progress';
  chunk?: string;
  status?: string;
  score?: number;
  story?: any;
  message?: string;
  progress?: {
    stage: string;
    description: string;
  };
}

export interface SSEOptions {
  onContent?: (chunk: string) => void;
  onSafetyCheck?: (status: string, score: number) => void;
  onComplete?: (story: any) => void;
  onError?: (error: string) => void;
  onProgress?: (stage: string, description: string) => void;
}

interface UseSSEStoryGenerationResult {
  isStreaming: boolean;
  streamedContent: string;
  currentProgress: { stage: string; description: string } | null;
  error: string | null;
  startStreaming: (endpoint: string, requestData: any) => void;
  stopStreaming: () => void;
  resetStream: () => void;
}

export const useSSEStoryGeneration = (options?: SSEOptions): UseSSEStoryGenerationResult => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedContent, setStreamedContent] = useState('');
  const [currentProgress, setCurrentProgress] = useState<{ stage: string; description: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const accumulatedContentRef = useRef<string>('');

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, []);

  const stopStreaming = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const resetStream = useCallback(() => {
    stopStreaming();
    setStreamedContent('');
    accumulatedContentRef.current = '';
    setCurrentProgress(null);
    setError(null);
  }, [stopStreaming]);

  const startStreaming = useCallback((endpoint: string, requestData: any) => {
    // Reset state
    resetStream();
    setError(null);
    setIsStreaming(true);

    // Build URL with query parameters
    const url = new URL(endpoint, window.location.origin);
    Object.keys(requestData).forEach(key => {
      if (requestData[key] !== undefined && requestData[key] !== null) {
        url.searchParams.append(key, String(requestData[key]));
      }
    });

    // Get auth token from localStorage
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Authentication required');
      setIsStreaming(false);
      return;
    }

    // Create EventSource with auth header
    // Note: EventSource doesn't support custom headers natively
    // We'll pass the token as a query parameter or use a different approach
    const urlWithAuth = `${url.toString()}&token=${encodeURIComponent(token)}`;

    try {
      const eventSource = new EventSource(urlWithAuth);
      eventSourceRef.current = eventSource;

      // Handle incoming messages
      eventSource.onmessage = (event) => {
        try {
          const data: SSEEvent = JSON.parse(event.data);

          switch (data.type) {
            case 'content':
              if (data.chunk) {
                accumulatedContentRef.current += data.chunk;
                setStreamedContent(accumulatedContentRef.current);
                options?.onContent?.(data.chunk);
              }
              break;

            case 'progress':
              if (data.progress) {
                setCurrentProgress(data.progress);
                options?.onProgress?.(data.progress.stage, data.progress.description);
              }
              break;

            case 'safety_check':
              if (data.status && data.score !== undefined) {
                options?.onSafetyCheck?.(data.status, data.score);
              }
              break;

            case 'complete':
              if (data.story) {
                options?.onComplete?.(data.story);
              }
              stopStreaming();
              break;

            case 'error':
              const errorMsg = data.message || 'An error occurred during streaming';
              setError(errorMsg);
              options?.onError?.(errorMsg);
              stopStreaming();
              break;
          }
        } catch (err) {
          console.error('Error parsing SSE event:', err);
          setError('Failed to parse streaming data');
          stopStreaming();
        }
      };

      // Handle errors
      eventSource.onerror = (err) => {
        console.error('SSE connection error:', err);
        setError('Connection error. Please try again.');
        options?.onError?.('Connection error');
        stopStreaming();
      };

    } catch (err) {
      console.error('Error creating EventSource:', err);
      setError('Failed to start streaming');
      setIsStreaming(false);
    }
  }, [options, resetStream, stopStreaming]);

  return {
    isStreaming,
    streamedContent,
    currentProgress,
    error,
    startStreaming,
    stopStreaming,
    resetStream,
  };
};
