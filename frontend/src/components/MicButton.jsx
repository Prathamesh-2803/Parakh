import React, { useState, useEffect, useEffectEvent, useRef } from 'react';
import { Mic, MicOff } from 'lucide-react';
import { SUPPORTED_LANGUAGES } from '../languages';

export function MicButton({ language = 'en', onTranscript, className = '' }) {
  const [isListening, setIsListening] = useState(false);
  const [isSupported] = useState(
    () => typeof window !== 'undefined' && Boolean(window.SpeechRecognition || window.webkitSpeechRecognition)
  );
  const recognitionRef = useRef(null);
  const reportTranscript = useEffectEvent((transcript) => onTranscript?.(transcript));

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) return;

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;

      const langConfig = SUPPORTED_LANGUAGES.find((l) => l.code === language);
      recognition.lang = langConfig ? langConfig.speechCode : 'en-IN';

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) reportTranscript(transcript);
        setIsListening(false);
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition notice:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    } catch (err) {
      console.warn('Web Speech API initialization error:', err);
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [language]);

  const toggleListening = () => {
    if (!isSupported) {
      alert('Speech recognition is not supported in this browser. Please use Chrome, Edge, or a Web Speech-compatible browser.');
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      try {
        const langConfig = SUPPORTED_LANGUAGES.find((l) => l.code === language);
        if (recognitionRef.current) {
          recognitionRef.current.lang = langConfig ? langConfig.speechCode : 'en-IN';
          recognitionRef.current.start();
        }
      } catch (e) {
        console.error('Failed to start speech recognition:', e);
      }
    }
  };

  if (!isSupported) {
    return (
      <button
        type="button"
        disabled
        title="Web Speech API not supported in this browser"
        className={`p-2 rounded-md bg-slate-100 text-slate-300 border border-slate-200 cursor-not-allowed ${className}`}
      >
        <MicOff className="w-4 h-4" />
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggleListening}
      title={isListening ? 'Listening... click to stop' : `Voice input in ${language}`}
      className={`relative p-2 rounded-md border transition-colors flex items-center justify-center cursor-pointer ${
        isListening
          ? 'bg-red-600 text-white border-red-700 ring-2 ring-red-200'
          : 'bg-white hover:bg-slate-100 text-slate-700 border-slate-300'
      } ${className}`}
    >
      <Mic className="w-4 h-4" />
    </button>
  );
}
