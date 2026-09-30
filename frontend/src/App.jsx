import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import {
  MessageSquare,
  Search,
  ShieldCheck,
  ExternalLink,
  PhoneCall,
  FileText,
  Building,
  CheckCircle2,
} from 'lucide-react';
import ChatPage from './pages/ChatPage';
import RecommendPage from './pages/RecommendPage';
import VerificationPage from './pages/VerificationPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans antialiased">
        {/* Top Government / Official Identification Bar */}
        <div className="bg-[#0b2545] text-slate-300 text-xs py-1.5 px-4 sm:px-8 border-b border-white/10 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-[11px] sm:text-xs">
            <span className="font-semibold text-slate-100 tracking-wide">
              GOVERNMENT OF INDIA
            </span>
            <span className="text-slate-500">•</span>
            <span className="text-slate-300 hidden md:inline">
              Ministry of Consumer Affairs, Food & Public Distribution
            </span>
            <span className="text-slate-500 hidden md:inline">•</span>
            <span className="text-slate-200 font-medium">
              Bureau of Indian Standards (BIS) Intelligence Workbench
            </span>
          </div>

          <div className="flex items-center gap-4 text-[11px] sm:text-xs">
            <a
              href="tel:1800112417"
              className="hover:text-white flex items-center gap-1.5 transition text-slate-300"
            >
              <PhoneCall className="w-3 h-3 text-amber-400" />
              <span>National BIS Helpline: <strong className="text-white">1800-11-2417</strong></span>
            </a>
            <span className="hidden sm:inline text-slate-600">|</span>
            <a
              href="https://www.bis.gov.in/"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-white flex items-center gap-1 transition text-slate-300 hover:underline"
            >
              <span>bis.gov.in</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
          </div>
        </div>

        {/* Main Application Navbar */}
        <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-xs">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16 gap-4">
              {/* Product Identity */}
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded bg-[#0b2545] text-white flex items-center justify-center font-bold text-sm tracking-wider">
                  IS
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-bold tracking-tight text-[#0b2545]">
                      PARAKH
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-300">
                      SIH 2026
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 font-medium leading-none hidden sm:block">
                    National Standards & BIS Compliance Intelligence
                  </p>
                </div>
              </div>

              {/* Navigation Tabs - Clean, functional segmented style */}
              <nav className="flex items-center gap-1">
                <NavLink
                  to="/"
                  end
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-2 text-xs sm:text-sm font-medium rounded-md transition-colors cursor-pointer ${
                      isActive
                        ? 'bg-slate-900 text-white shadow-xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                >
                  <MessageSquare className="w-4 h-4" />
                  <span>Compliance Q&A</span>
                </NavLink>

                <NavLink
                  to="/recommend"
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-2 text-xs sm:text-sm font-medium rounded-md transition-colors cursor-pointer ${
                      isActive
                        ? 'bg-slate-900 text-white shadow-xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                >
                  <Search className="w-4 h-4" />
                  <span>Product-to-Standard</span>
                </NavLink>

                <NavLink
                  to="/verify"
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-2 text-xs sm:text-sm font-medium rounded-md transition-colors cursor-pointer ${
                      isActive
                        ? 'bg-slate-900 text-white shadow-xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                >
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>Verify License / HUID</span>
                </NavLink>
              </nav>

              {/* Status Indicator */}
              <div className="hidden lg:flex items-center gap-2 pl-4 border-l border-slate-200 text-xs text-slate-500">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Registry: Active</span>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/recommend" element={<RecommendPage />} />
            <Route path="/verify" element={<VerificationPage />} />
          </Routes>
        </main>

        {/* Enterprise Government/Regulatory Footer */}
        <footer className="bg-white border-t border-slate-200 mt-auto text-xs text-slate-600">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 pb-6 border-b border-slate-200">
              {/* Col 1 */}
              <div className="space-y-2">
                <span className="font-semibold text-slate-900 uppercase tracking-wider text-[11px] block">
                  Bureau of Indian Standards
                </span>
                <p className="text-slate-500 text-xs leading-relaxed">
                  National Standards Body of India established under the BIS Act 2016 for the harmonious development of standardisation, conformity assessment, and quality assurance.
                </p>
              </div>

              {/* Col 2 */}
              <div className="space-y-2">
                <span className="font-semibold text-slate-900 uppercase tracking-wider text-[11px] block">
                  Official Portals
                </span>
                <ul className="space-y-1.5 text-xs">
                  <li>
                    <a href="https://www.bis.gov.in/" target="_blank" rel="noopener noreferrer" className="hover:text-slate-900 flex items-center gap-1">
                      <span>BIS Main Portal</span>
                      <ExternalLink className="w-3 h-3 text-slate-400" />
                    </a>
                  </li>
                  <li>
                    <a href="https://www.manakonline.in/" target="_blank" rel="noopener noreferrer" className="hover:text-slate-900 flex items-center gap-1">
                      <span>Manakonline (e-Licensing)</span>
                      <ExternalLink className="w-3 h-3 text-slate-400" />
                    </a>
                  </li>
                  <li>
                    <a href="https://www.services.bis.gov.in/" target="_blank" rel="noopener noreferrer" className="hover:text-slate-900 flex items-center gap-1">
                      <span>BIS e-Services Registry</span>
                      <ExternalLink className="w-3 h-3 text-slate-400" />
                    </a>
                  </li>
                </ul>
              </div>

              {/* Col 3 */}
              <div className="space-y-2">
                <span className="font-semibold text-slate-900 uppercase tracking-wider text-[11px] block">
                  Certification Schemes
                </span>
                <ul className="space-y-1.5 text-xs text-slate-500">
                  <li>Scheme-I: ISI Mark (Product Certification)</li>
                  <li>Scheme-II: Compulsory Registration Scheme (CRS)</li>
                  <li>Scheme-IV: Hallmarking of Gold & Silver (HUID)</li>
                  <li>Foreign Manufacturers Certification Scheme (FMCS)</li>
                </ul>
              </div>

              {/* Col 4 */}
              <div className="space-y-2">
                <span className="font-semibold text-slate-900 uppercase tracking-wider text-[11px] block">
                  Consumer Assistance
                </span>
                <p className="text-slate-500 text-xs leading-relaxed">
                  National Helpline: <strong className="text-slate-800">1800-11-2417</strong><br />
                  Email: <span className="font-mono text-slate-700">complaints@bis.gov.in</span><br />
                  BIS Care App: Available on Android & iOS for instantaneous HUID & ISI verification.
                </p>
              </div>
            </div>

            {/* Bottom Row */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-slate-500">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-800">Parakh Workbench</span>
                <span>• Strict RAG Grounding on Official BIS Standards & Gazette QCO Orders</span>
              </div>
              <div className="text-slate-500">
                Advisory assistance tool. For binding legal certification, refer to official BIS Gazettes.
              </div>
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}
