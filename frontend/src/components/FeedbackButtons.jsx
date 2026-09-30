import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Check, MessageSquare } from 'lucide-react';
import { API_BASE } from '../apiConfig';

export function FeedbackButtons({
  question = '',
  answer = '',
  requestId = null,
  sessionId = null,
  language = 'en',
  className = ''
}) {
  const [rating, setRating] = useState(null);
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCommentBox, setShowCommentBox] = useState(false);
  const [commentText, setCommentText] = useState('');

  const handleRate = async (selectedRating) => {
    if (submitted || isSubmitting) return;

    setRating(selectedRating);
    if (selectedRating === 'negative') {
      setShowCommentBox(true);
      return;
    }

    await submitFeedback(selectedRating, null);
  };

  const submitFeedback = async (selectedRating, comment) => {
    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          request_id: requestId,
          session_id: sessionId,
          question: question || 'Direct Feedback',
          answer: answer || 'Direct Feedback',
          rating: selectedRating,
          comment: comment || null,
          language: language
        })
      });

      if (response.ok) {
        setSubmitted(true);
        setShowCommentBox(false);
      }
    } catch (err) {
      console.warn('Feedback submission notice:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className={`inline-flex items-center gap-1.5 text-xs text-emerald-800 bg-emerald-50 px-2 py-1 rounded-md border border-emerald-200 ${className}`}>
        <Check className="w-3.5 h-3.5 text-emerald-600" />
        <span>Feedback recorded</span>
      </div>
    );
  }

  return (
    <div className={`relative inline-flex items-center gap-1 ${className}`}>
      <span className="text-xs text-slate-500 mr-1 hidden sm:inline">Was this accurate?</span>
      <button
        type="button"
        onClick={() => handleRate('positive')}
        disabled={isSubmitting}
        title="Yes, accurate and helpful"
        className={`p-1.5 rounded-md border transition-colors cursor-pointer ${
          rating === 'positive'
            ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
            : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100 border-slate-200 bg-white'
        }`}
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>

      <button
        type="button"
        onClick={() => handleRate('negative')}
        disabled={isSubmitting}
        title="No, needs clarification or correction"
        className={`p-1.5 rounded-md border transition-colors cursor-pointer ${
          rating === 'negative'
            ? 'bg-rose-50 text-rose-700 border-rose-300'
            : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100 border-slate-200 bg-white'
        }`}
      >
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>

      {showCommentBox && (
        <div className="absolute bottom-8 right-0 z-30 w-72 bg-white border border-slate-300 rounded-md shadow-lg p-3 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-800 border-b border-slate-100 pb-1.5">
            <span className="flex items-center gap-1.5">
              <MessageSquare className="w-3.5 h-3.5 text-slate-600" />
              Provide Feedback
            </span>
            <button
              type="button"
              onClick={() => setShowCommentBox(false)}
              className="text-slate-400 hover:text-slate-600 text-xs cursor-pointer"
            >
              ✕
            </button>
          </div>
          <textarea
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            placeholder="Specify missing standards, clauses, or incorrect requirements..."
            rows={3}
            className="w-full text-xs p-2 border border-slate-300 rounded-md outline-none focus:border-slate-800 resize-none font-sans"
          />
          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={() => setShowCommentBox(false)}
              className="px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-100 rounded-md transition"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => submitFeedback('negative', commentText)}
              disabled={isSubmitting}
              className="px-3 py-1 text-xs font-medium bg-slate-900 text-white rounded-md hover:bg-slate-800 transition"
            >
              Submit Feedback
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
