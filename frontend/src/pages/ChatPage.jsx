import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Bot,
  User,
  AlertCircle,
  FileText,
  Copy,
  Check,
  RotateCcw,
  BookOpen,
  ShieldCheck,
  ExternalLink,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { CitationModal } from '../components/CitationModal';
import { CitationChip } from '../components/CitationChip';
import { FollowUpChip } from '../components/FollowUpChip';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import { MicButton } from '../components/MicButton';
import { FeedbackButtons } from '../components/FeedbackButtons';
import { API_BASE, resilientFetch } from '../apiConfig';
import { getOfflineChatResponse } from '../offlineIntelligence';

const REFERENCE_STANDARDS = [
  {
    code: "IS 4151:2015",
    name: "Two-Wheeler Helmets",
    scheme: "Scheme-I (ISI)",
    mandatory: true,
    query: "What are the mandatory testing and certification requirements for motorcycle helmets under IS 4151:2015?"
  },
  {
    code: "IS 16102 (Part 1/2)",
    name: "LED Lamps & Bulbs",
    scheme: "Scheme-II (CRS)",
    mandatory: true,
    query: "What is the certification procedure and CRS registration requirement for LED lamps under IS 16102?"
  },
  {
    code: "IS 2347:2009",
    name: "Domestic Pressure Cookers",
    scheme: "Scheme-I (ISI)",
    mandatory: true,
    query: "What are the mandatory safety features and QCO requirements for pressure cookers under IS 2347?"
  },
  {
    code: "IS 1417:2016",
    name: "Gold & Gold Alloys / HUID",
    scheme: "Scheme-IV (Hallmarking)",
    mandatory: true,
    query: "Explain the mandatory gold hallmarking rules, recognized purities, and 6-digit HUID verification process under IS 1417."
  },
  {
    code: "IS 14543:2004",
    name: "Packaged Drinking Water",
    scheme: "Scheme-I (ISI)",
    mandatory: true,
    query: "What are the mandatory testing parameters and microbiological requirements for packaged drinking water under IS 14543?"
  },
  {
    code: "IS 1786:2008",
    name: "High Strength TMT Steel Bars",
    scheme: "Scheme-I (ISI)",
    mandatory: true,
    query: "What are the mechanical property requirements and QCO order status for TMT steel bars under IS 1786?"
  }
];

const INITIAL_SUGGESTIONS = {
  en: [
    "What is the standard for motorcycle helmets?",
    "Explain the ISI mark certification process and fee structure.",
    "Which testing labs are recognized for domestic pressure cookers?",
    "How does BIS verify 6-character HUID codes on gold jewellery?"
  ],
  hi: [
    "दोपहिया वाहन चालकों के लिए हेलमेट का कौन सा मानक लागू होता है?",
    "आईएसआई मार्क प्रमाणन प्रक्रिया और शुल्क संरचना क्या है?",
    "प्रेशर कुकर परीक्षण के लिए कौन सी मान्यता प्राप्त प्रयोगशालाएं हैं?",
    "सोने के आभूषणों पर 6-अंकीय HUID का सत्यापन कैसे करें?"
  ],
  mr: [
    "दुचाकी चालकांसाठी हेल्मेटचे कोणते मानक लागू आहे?",
    "ISI मार्क प्रमाणन प्रक्रिया आणि शुल्क तपशील काय आहे?",
    "प्रेशर कुकर चाचणीसाठी मान्यताप्राप्त प्रयोगशाळा कोणत्या आहेत?",
    "सोन्यावरील 6-अंकी HUID कोड कसा तपासावा?"
  ],
  ta: [
    "இருசக்கர வாகன ஹெல்மெட்டுகளுக்கான இந்திய தரம் என்ன?",
    "ISI முத்திரை சான்றிதழ் செயல்முறை மற்றும் கட்டண விவரங்கள் என்ன?",
    "பிரஷர் குக்கர் சோதனை ஆய்வகங்கள் எங்கு உள்ளன?",
    "தங்க நகைகளில் 6 இலக்க HUID-ஐ எவ்வாறு சரிபார்ப்பது?"
  ]
};

const formatTimestamp = () =>
  new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

const createMessageId = (prefix) => `${prefix}_${Date.now()}`;

const createWelcomeMessage = () => ({
  id: 'welcome-msg',
  role: 'assistant',
  content:
    "Welcome to Parakh, the Bureau of Indian Standards (BIS) regulatory compliance assistant. I provide verified information on Indian Standards (IS), mandatory Quality Control Orders (QCOs), certification schemes (ISI Mark, CRS, FMCS, Hallmarking/HUID), and recognized testing laboratories.\n\nYou can query by standard number (e.g., IS 4151), product category (e.g., LED bulbs, pressure cookers), or certification procedure.",
  citations: [
    {
      source: "Bureau of Indian Standards Act 2016",
      section: "Section 14 & 15",
      url: "https://www.bis.gov.in/"
    }
  ],
  followUp: [
    "What is the standard for motorcycle helmets?",
    "Explain the ISI mark certification process and fee structure.",
    "Which testing labs are recognized for domestic pressure cookers?"
  ],
  confidence: 1.0,
  timestamp: formatTimestamp()
});

export default function ChatPage() {
  const [messages, setMessages] = useState(() => [createWelcomeMessage()]);
  const [inputValue, setInputValue] = useState('');
  const [language, setLanguage] = useState('en');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(() => `sess_${Math.random().toString(36).substring(2, 11)}`);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [showCitationModal, setShowCitationModal] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  const scrollContainerRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, isLoading]);

  const handleSend = async (textToSend) => {
    const rawQuery = typeof textToSend === 'string' ? textToSend : (inputValue || '');
    const query = rawQuery.trim();
    if (!query || isLoading) return;

    setErrorMsg(null);
    setInputValue('');

    const userMessageId = createMessageId('user');
    const userMsg = {
      id: userMessageId,
      role: 'user',
      content: query,
      timestamp: formatTimestamp()
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    // Smooth scroll down immediately to display user's query
    setTimeout(() => {
      if (scrollContainerRef.current) {
        scrollContainerRef.current.scrollTo({
          top: scrollContainerRef.current.scrollHeight,
          behavior: 'smooth'
        });
      }
    }, 40);

    try {
      const response = await resilientFetch('/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question: query,
          session_id: sessionId,
          language: language
        })
      }, 4000);

      if (!response.ok) {
        throw new Error(`Server returned error status ${response.status}`);
      }

      const data = await response.json();

      const assistantMsg = {
        id: createMessageId('asst'),
        role: 'assistant',
        content: data.answer || "No response received.",
        citations: data.citations || [],
        followUp: data.follow_up_suggestions || data.follow_up_questions || data.followUp || [],
        confidence: data.confidence ?? 1.0,
        requestId: data.request_id,
        fromCache: data.from_cache,
        detectedLang: data.language,
        timestamp: formatTimestamp()
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.warn("Live backend unreachable, using built-in compliance intelligence:", err);
      const offline = getOfflineChatResponse(query, language);
      const assistantMsg = {
        id: createMessageId('asst'),
        role: 'assistant',
        content: offline.answer,
        citations: offline.citations || [],
        followUp: offline.follow_up_suggestions || offline.follow_up_questions || offline.followUp || [],
        confidence: offline.confidence,
        fromCache: true,
        detectedLang: language,
        timestamp: formatTimestamp()
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } finally {
      setIsLoading(false);
      setTimeout(() => {
        if (scrollContainerRef.current) {
          scrollContainerRef.current.scrollTo({
            top: scrollContainerRef.current.scrollHeight,
            behavior: 'smooth'
          });
        }
      }, 50);
      inputRef.current?.focus();
    }
  };

  const handleCitationClick = (citation) => {
    setSelectedCitation(citation);
    setShowCitationModal(true);
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleResetSession = () => {
    setMessages([createWelcomeMessage()]);
    setSessionId(`sess_${Math.random().toString(36).substring(2, 11)}`);
    setErrorMsg(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const currentSuggestions = INITIAL_SUGGESTIONS[language] || INITIAL_SUGGESTIONS.en;

  return (
    <div className="lg:grid lg:grid-cols-4 lg:gap-6 items-start">
      {/* Left Reference Panel - Desktop Only */}
      <aside className="hidden lg:block lg:col-span-1 bg-white border border-slate-200 rounded-lg p-4 space-y-5 shadow-xs sticky top-24">
        <div>
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-slate-700" />
              Standards Reference
            </span>
            <span className="text-[10px] text-slate-500 font-medium">Index</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">
            Click any core standard below to load verified regulatory requirements into the compliance engine.
          </p>
        </div>

        {/* Reference Standards List */}
        <div className="space-y-2">
          {REFERENCE_STANDARDS.map((std) => (
            <button
              key={std.code}
              type="button"
              onClick={() => handleSend(std.query)}
              className="w-full text-left p-2.5 rounded border border-slate-200 hover:border-slate-400 hover:bg-slate-50 transition-colors group cursor-pointer"
            >
              <div className="flex items-center justify-between gap-1">
                <span className="font-mono text-xs font-semibold text-slate-900 group-hover:text-blue-900">
                  {std.code}
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded font-medium bg-amber-50 text-amber-800 border border-amber-200">
                  QCO
                </span>
              </div>
              <div className="text-xs text-slate-600 font-medium truncate mt-0.5">
                {std.name}
              </div>
              <div className="text-[10px] text-slate-400 mt-1 flex items-center justify-between">
                <span>{std.scheme}</span>
                <ChevronRight className="w-3 h-3 text-slate-400 group-hover:text-slate-700" />
              </div>
            </button>
          ))}
        </div>

        {/* Regulatory Advisory Note */}
        <div className="p-3 bg-slate-50 border border-slate-200 rounded text-[11px] text-slate-600 space-y-1.5">
          <div className="font-semibold text-slate-800 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            Grounding Protocol
          </div>
          <p className="text-[11px] text-slate-500 leading-normal">
            Parakh synthesizes answers strictly from retrieved BIS gazettes and technical standard clauses. Factual claims include citations.
          </p>
        </div>
      </aside>

      {/* Main Conversational Workspace */}
      <section className="lg:col-span-3 flex flex-col bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden h-[calc(100dvh-8rem)] sm:h-[calc(100vh-9.5rem)] min-h-[440px]">
        {/* Workspace Toolbar */}
        <div className="flex items-center justify-between px-3 sm:px-4 py-2 sm:py-2.5 bg-slate-50 border-b border-slate-200 text-xs gap-2">
          <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
            <span className="font-semibold text-slate-800 text-xs truncate">Compliance Query</span>
            <span className="text-slate-400 hidden sm:inline">|</span>
            <span className="font-mono text-[11px] text-slate-500 hidden sm:inline truncate">{sessionId}</span>
          </div>

          <div className="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
            <LanguageSwitcher value={language} onChange={setLanguage} />
            <button
              type="button"
              onClick={handleResetSession}
              title="Reset conversation"
              className="p-1 text-slate-500 hover:text-slate-900 hover:bg-slate-200 rounded transition cursor-pointer shrink-0 touch-manipulation"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Mobile Standards Horizontal Pill Bar (Inside Workspace) */}
        <div className="lg:hidden px-2.5 py-1.5 bg-slate-100/90 border-b border-slate-200 flex items-center gap-1.5 overflow-x-auto no-scrollbar touch-scroll">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 shrink-0 flex items-center gap-1 mr-0.5">
            <BookOpen className="w-3 h-3 text-slate-600" />
            Standards:
          </span>
          {REFERENCE_STANDARDS.map((std) => (
            <button
              key={std.code}
              type="button"
              onClick={() => handleSend(std.query)}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-white hover:bg-slate-50 active:bg-slate-200 border border-slate-200 text-slate-800 shrink-0 transition shadow-2xs cursor-pointer touch-manipulation"
            >
              <span className="font-mono font-bold text-slate-900">{std.code}</span>
              <span className="text-slate-400">·</span>
              <span className="text-slate-600 truncate max-w-[100px]">{std.name}</span>
            </button>
          ))}
        </div>

        {/* Error notification banner if any */}
        {errorMsg && (
          <div className="px-4 py-2 bg-rose-50 border-b border-rose-200 text-rose-800 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{errorMsg}</span>
            </div>
            <button
              type="button"
              onClick={() => setErrorMsg(null)}
              className="text-rose-600 hover:text-rose-800 font-bold"
            >
              ✕
            </button>
          </div>
        )}

        {/* Messages Scroll View */}
        <div
          ref={scrollContainerRef}
          className="flex-1 overflow-y-auto touch-scroll p-3 sm:p-6 space-y-4 sm:space-y-5"
        >
          {messages.map((msg) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={msg.id}
                className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-7 h-7 rounded bg-[#0b2545] text-white flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold">
                    IS
                  </div>
                )}

                <div
                  className={`max-w-[94%] sm:max-w-[82%] rounded-md p-3 sm:p-4 space-y-2.5 sm:space-y-3 ${
                    isUser
                      ? 'bg-slate-900 text-white'
                      : 'bg-white border border-slate-200 text-slate-800'
                  }`}
                >
                  {/* Message Top Header */}
                  <div className="flex items-center justify-between text-[11px] gap-4 pb-2 border-b border-slate-100">
                    <span className={`font-semibold ${isUser ? 'text-slate-300' : 'text-slate-900'}`}>
                      {isUser ? 'You (Manufacturer / Importer)' : 'Parakh Compliance Engine'}
                    </span>
                    <div className="flex items-center gap-2 text-slate-400">
                      {!isUser && msg.confidence !== undefined && (
                        <span className="inline-flex items-center text-[10px] font-medium px-1.5 py-0.2 rounded bg-slate-100 text-slate-700 border border-slate-200">
                          {Math.round(msg.confidence * 100)}% Grounded
                        </span>
                      )}
                      <span>{msg.timestamp}</span>
                    </div>
                  </div>

                  {/* Message Text Content */}
                  <div className={`text-xs sm:text-sm leading-relaxed whitespace-pre-line ${isUser ? 'text-slate-100' : 'text-slate-800'}`}>
                    {msg.content}
                  </div>

                  {/* Citations section for Assistant responses */}
                  {!isUser && msg.citations && msg.citations.length > 0 && (
                    <div className="pt-2 border-t border-slate-100 space-y-1.5">
                      <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                        Source Citations:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.citations.map((c, idx) => (
                          <CitationChip
                            key={idx}
                            citation={c}
                            onClick={() => handleCitationClick(c)}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Follow-up suggestions */}
                  {!isUser && msg.followUp && msg.followUp.length > 0 && (
                    <div className="pt-2.5 border-t border-slate-100 space-y-2">
                      <div className="flex items-center gap-1.5 text-[11px] font-bold text-blue-900 uppercase tracking-wider">
                        <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                        <span>Recommended Follow-up Questions:</span>
                      </div>
                      <div className="flex flex-col gap-1.5">
                        {msg.followUp.map((sugg, idx) => (
                          <FollowUpChip
                            key={idx}
                            suggestion={sugg}
                            onClick={(text) => handleSend(text)}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Assistant Message Actions Bar */}
                  {!isUser && msg.id !== 'welcome-msg' && (
                    <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => copyToClipboard(msg.content, msg.id)}
                          className="inline-flex items-center gap-1 text-[11px] text-slate-500 hover:text-slate-800 transition cursor-pointer touch-manipulation"
                        >
                          {copiedId === msg.id ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-600" />
                              <span className="text-emerald-700">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>Copy Response</span>
                            </>
                          )}
                        </button>
                      </div>

                      <FeedbackButtons
                        question={messages.find((m, i) => messages[i + 1]?.id === msg.id)?.content || ''}
                        answer={msg.content}
                        requestId={msg.requestId}
                        sessionId={sessionId}
                        language={language}
                      />
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-7 h-7 rounded bg-slate-700 text-white flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold">
                    <User className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>
            );
          })}

          {/* Loading state indicator */}
          {isLoading && (
            <div className="flex gap-3 items-start">
              <div className="w-7 h-7 rounded bg-[#0b2545] text-white flex items-center justify-center shrink-0 text-xs font-bold">
                IS
              </div>
              <div className="bg-white border border-slate-200 rounded-md p-3.5 text-xs text-slate-600 flex items-center gap-2 shadow-xs">
                <span className="w-2 h-2 rounded-full bg-slate-600 animate-ping"></span>
                <span>Retrieving official BIS standard context and verifying citations...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input Box Area */}
        <div className="p-3 sm:p-4 bg-slate-50 border-t border-slate-200 space-y-2">
          {/* Quick Questions Row - Horizontal touch-scroll on mobile */}
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar touch-scroll pb-1">
            <span className="text-[10px] sm:text-[11px] font-semibold text-slate-500 mr-0.5 shrink-0 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-amber-500" />
              Suggested:
            </span>
            {currentSuggestions.slice(0, 4).map((sugg, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleSend(sugg)}
                className="text-[10px] sm:text-[11px] text-slate-700 bg-white hover:bg-slate-100 active:bg-slate-200 border border-slate-200 rounded px-2 py-0.5 transition cursor-pointer truncate max-w-[200px] sm:max-w-[280px] shrink-0 touch-manipulation"
                title={sugg}
              >
                {sugg}
              </button>
            ))}
          </div>

          {/* Input Console */}
          <div className="relative flex items-center bg-white border border-slate-300 rounded-md shadow-xs focus-within:border-slate-800 focus-within:ring-1 focus-within:ring-slate-800 transition">
            <textarea
              ref={inputRef}
              rows={1}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about Indian Standards, ISI licensing, testing labs, or QCOs..."
              className="flex-1 py-2 sm:py-2.5 pl-2.5 sm:pl-3 pr-1 sm:pr-2 text-xs sm:text-sm text-slate-900 bg-transparent outline-none resize-none placeholder:text-slate-400 font-sans"
              disabled={isLoading}
            />

            <div className="flex items-center gap-1 sm:gap-1.5 pr-1.5 sm:pr-2 shrink-0">
              <MicButton
                language={language}
                onTranscript={(transcript) => setInputValue(transcript)}
              />

              <button
                type="button"
                onClick={() => handleSend()}
                disabled={!inputValue.trim() || isLoading}
                className="px-2.5 sm:px-3.5 py-1.5 bg-[#0b2545] hover:bg-[#081a31] disabled:bg-slate-200 disabled:text-slate-400 text-white rounded text-xs font-semibold flex items-center gap-1 sm:gap-1.5 transition cursor-pointer disabled:cursor-not-allowed touch-manipulation"
              >
                <span>Send</span>
                <Send className="w-3 h-3" />
              </button>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[10px] sm:text-[11px] text-slate-400 gap-0.5">
            <span>Press Enter to send (Shift + Enter for new line).</span>
            <span className="hidden sm:inline">Strictly grounded in official BIS standards data.</span>
          </div>
        </div>
      </section>

      {/* Citation Details Modal */}
      <CitationModal
        show={showCitationModal}
        onClose={() => setShowCitationModal(false)}
        citation={selectedCitation}
      />
    </div>
  );
}
