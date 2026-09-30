# Parakh: AI Assistant for Indian Standards and BIS Services

Parakh is an authoritative AI assistant prototype developed for the Smart India Hackathon, designed to provide accurate, grounded information about Indian Standards (IS) and Bureau of Indian Standards (BIS) services including ISI mark, CRS, FMCS, Hallmarking/HUID, recognized labs, and license verification.

## Features

- **Grounded Answers Only**: All responses are strictly derived from retrieved BIS context with mandatory citations.
- **Multilingual Support**: Supports English, Hindi, Marathi, and Tamil.
- **Channel-Agnostic Core**: Central APIs serving web, WhatsApp, and voice interfaces (web interface implemented).
- **Live Verification**: Real-time BIS license and HUID verification with curated fallback datasets.
- **Feedback Loop**: User feedback stored for continuous improvement.
- **Safety & Security**: Prompt injection detection, input sanitization, rate limiting, and PII-free logging.
- **Demo Mode**: Pre-warmed cache for instant demo responses.

## Architecture

```mermaid
graph TD
    A[User Query] --> B{Input Sanitization<br/>& Safety Check}
    B -->|Safe| C[Language Detection]
    B -->|Unsafe| D[Safe Fallback Response]
    C --> E[Intent Classification<br/>(Rule-based, Zero LLM)]
    E --> F[Context Gathering]
    F --> G[SQL Tools: Standards, Labs, AHCs, License/HUID]
    F --> H[Hybrid Retrieval:<br/>BM25 + Vector (BAAI/bge-m3)]
    G & H --> I[Context Fusion]
    I --> J[Build Grounded Prompt]
    J --> K[Single LLM Call:<br/>Gemini with Groq Fallback]
    K --> L[Parse & Validate Citations]
    L --> M[Cache Response]
    M --> N[Return Grounded Answer<br/>with Citations]
    N --> O[User Feedback<br/>Thumbs Up/Down]
    O --> P[Async SQLite Storage]
```

## Components

### Backend (FastAPI)
- `POST /chat`: Main RAG endpoint with intent routing, hybrid retrieval, and grounded generation.
- `POST /recommend`: Product-to-compliance recommendation using taxonomy matching.
- `POST /verify`: License (CM/L) and HUID verification.
- `POST /feedback`: User feedback collection.
- `GET /health`: Comprehensive health check including LLM provider status.

### Frontend (React + Vite + Tailwind)
- Chat UI with streaming responses and citation modal.
- Multilingual language switcher.
- Voice input via Web Speech API.
- Product compliance finder and license/HUID verifier.
- Feedback thumbs up/down.
- Mobile-responsive design.

## Setup

### Prerequisites
- Python 3.9+
- Node.js 16+ and npm
- Git

### Backend Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
    cd Parakh
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env to add your API keys (optional for mock mode)
   ```
4. Initialize the database and ingest sample data (optional):
   ```bash
   python -m backend.app.ingestion.run
   ```
5. Start the development server:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
   The API will be available at `http://127.0.0.1:8000`.

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:3000` and will proxy API requests to the backend.

## Demo Mode

The system includes a pre-warmed cache for four demo queries to ensure instant responses during demonstrations:

1. **Product Lookup**: "What is the standard for motorcycle helmets?"
2. **Scheme Explanation**: "Explain the ISI mark certification process."
3. **Verification**: "Verify BIS license CM/L-4151201"
4. **Hindi Query**: "दोपहिया वाहन चालकों के लिए हेलमेट का मानक क्या है?"

To run the demo script:
```bash
python backend/app/demo_runner.py
```

## Evaluation

To run the 50-question golden set evaluation:
```bash
python backend/eval_golden_set.py
```
This requires the backend to be running. The script will report:
- Retrieval Hit-Rate
- Citation Validity Rate
- Correctly Refused Rate
- Average Latency

## License

This project is developed for the Smart India Hackathon. Please refer to the LICENSE file for details.

## Contact

For questions or support, please open an issue in the repository.
