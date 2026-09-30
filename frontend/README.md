# Parakh Web Frontend

React + Vite + Tailwind CSS responsive web interface for **Parakh**, an authoritative AI assistant for Indian Standards and BIS services.

## Features
- **Ask Parakh (Chat UI)**: Natural language Q&A with strict RAG citations, confidence indicators, and fast caching.
- **Citation Modal & Chips**: Clickable source chips opening a detailed panel with standard numbers, clauses, excerpts, and official BIS links.
- **Multilingual Support**: Live language switcher for English, Hindi (हिन्दी), Marathi (मराठी), and Tamil (தமிழ்).
- **Voice Input**: Web Speech API speech-to-text integration with Indian English, Hindi, Marathi, and Tamil recognition.
- **Follow-up Chips**: Interactive query suggestions to guide MSMEs and consumers.
- **Product Compliance Finder**: Free text product lookup matching against Indian Standards taxonomy, mandatory QCO rules, and testing labs.
- **License / HUID Verifier**: Format validation and official verification guidance for CM/L license numbers and 6-character HUID codes.
- **Feedback Loop**: Thumbs up/down feedback stored in the SQLite database via `POST /feedback`.
- **Official BIS Disclaimer**: Prominently displays the official helpline (1800-11-2417) and link to [www.bis.gov.in](https://www.bis.gov.in/).

## Getting Started

1. **Install Dependencies:**
   ```bash
   npm install
   ```

2. **Run Development Server:**
   ```bash
   npm run dev
   ```
   The frontend runs at `http://localhost:3000/` and automatically proxies requests to the backend at `http://127.0.0.1:8000/`.

3. **Production Build:**
   ```bash
   npm run build
   ```
