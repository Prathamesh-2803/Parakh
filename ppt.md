# Parakh: AI Assistant for Indian Standards and BIS Services

## Project Overview
Parakh is an AI-powered assistant designed to help manufacturers, importers, and consumers navigate Indian Standards (IS) and Bureau of Indian Standards (BIS) compliance requirements. The system provides accurate, grounded information about product standards, certification processes, testing laboratories, and regulatory requirements.

## Key Features

### 1. Multi-modal Input
- **Text Description**: Users can describe products in natural language
- **Image Upload/Scan**: Users can upload product photos or use camera for visual recognition
- **OCR Integration**: Extracts product information from labels, ISI marks, and HUID codes

### 2. Intelligent Compliance Mapping
- **Product-to-Standard Recommendation**: Maps user inputs to relevant Indian Standards
- **Mandatory vs. Voluntary Certification**: Identifies QCO (Quality Control Order) mandates
- **Licensing Schemes**: Recommends appropriate BIS certification schemes (ISI, CRS, FMCS, etc.)

### 3. Comprehensive Information Delivery
- **Standard Details**: Provides specific IS numbers and their requirements
- **Testing Laboratories**: Lists BIS-recognized labs for product testing
- **Certification Process**: Outlines application procedures, fees, and timelines
- **Verification Tools**: Explains HUID verification and hallmark validation

### 4. Multi-language Support
- English (primary)
- Hindi
- Marathi
- Tamil

### 5. Offline-capable Mock Mode
- **MOCK_LLM=true**: Enables full functionality without API keys
- **Contextual Follow-up Q&A**: Provides meaningful responses to follow-up questions using conversation history
- **Structured Knowledge Base**: Contains domain-specific Q&A for helmets, LED lamps, pressure cookers, gold jewelry, and packaged water

## Technical Architecture

### Backend (FastAPI)
- **Framework**: Python FastAPI for RESTful API
- **LLM Providers**: 
  - Mock mode (zero-cost development/testing)
  - Google Gemini (primary)
  - Groq (fallback)
- **Retrieval System**: Hybrid BM25 + Vector search with Reciprocal Rank Fusion
- **Intent Classification**: Rule-based zero-LLM classification
- **Caching**: In-memory cache for frequent queries
- **Database**: SQLite for product taxonomy and standard information

### Frontend (React + Vite + Tailwind CSS)
- **Framework**: React 18 with Vite bundler
- **Styling**: Tailwind CSS for responsive, professional design
- **State Management**: React hooks (useState, useEffect, useRef)
- **Components**: Modular, reusable UI components
- **Icons**: Lucide React for consistent iconography
- **Multilingual**: Language switching with preserved technical terms

### Core Components

#### 1. LLM Gateway (`backend/app/core/llm.py`)
- Handles multi-provider LLM routing (Mock → Gemini → Groq)
- Implements mock mode with contextual follow-up capabilities
- Provides structured JSON responses with citations and confidence scores
- Includes language-specific response generation

#### 2. Context Gathering (`backend/app/core/retrieval.py`)
- SQL-based product taxonomy lookup
- Hybrid retrieval (BM25 + ChromaDB vector embeddings)
- Reciprocal Rank Fusion for result ranking
- Context grounding for LLM prompts

#### 3. Intent Classification (`backend/app/core/router.py`)
- Rule-based classification of user queries
- Routes to appropriate handling paths (recommendation, verification, etc.)
- Zero LLM cost for intent detection

#### 4. Safety and Validation (`backend/app/core/safety.py`)
- Input sanitization
- Prompt injection detection
- Response validation

#### 5. Prompt Engineering (`backend/app/core/prompts.py`)
- Strict grounding prompts to prevent hallucination
- Multilingual instruction templates
- Safe fallback responses for out-of-scope queries

#### 6. Chat Endpoint (`backend/app/api/chat.py`)
- Main RAG pipeline orchestration
- Caching layer
- Conversation history management
- Structured JSON response parsing

#### 7. Recommendation Endpoint (`backend/app/api/recommend.py`)
- Product-to-standard mapping
- Compliance roadmap generation
- Testing laboratory recommendations

#### 8. Scan Endpoint (`backend/app/api/scan.py`)
- Image processing pipeline
- OCR preprocessing (multi-pass enhancement)
- AI vision classification (PyTorch CNN)
- Product code matching
- Mark verification (ISI, HUID)

### Data Sources
- **Product Taxonomy**: Curated database of products, materials, and associated IS standards
- **Standard Information**: Indian Standards details from BIS publications
- **Laboratory Directory**: BIS-recognized testing facilities
- **QCO Orders**: Quality Control Orders mandating certification
- **License Database**: Sample BIS license information for demo

## User Flow

### Text-based Query
1. User enters product description in preferred language
2. System detects language and checks cache
3. Query classified as BIS-related
4. Intent determined (recommendation/verification/etc.)
5. Context gathered from SQL database and vector store
6. Conversation history added for follow-up capability
7. Grounded prompt built with strict instructions
8. Single LLM call made (Mock/Gemini/Groq)
9. Structured JSON response parsed and validated
10. Response cached and returned with UI rendering

### Image-based Query
1. User uploads photo or captures via camera
2. Image validated (type, size limits)
3. OCR preprocessing applied for text extraction
4. AI vision model predicts product category
5. Product code matching attempted (if visible)
6. Manual fallback if both OCR and vision uncertain
7. Successful identification triggers recommendation flow
8. Results include vision confidence and identification method

## Key Technical Innovations

### 1. Contextual Follow-up in Mock Mode
- Extracts topic and standard from conversation history
- Matches follow-up questions against domain-specific knowledge base
- Provides detailed, accurate responses without API calls
- Maintains JSON structure with citations and suggestions

### 2. Hybrid Retrieval System
- Combines keyword-based (BM25) and semantic (vector) search
- Uses Reciprocal Rank Fusion to merge results optimally
- Improves recall for both exact matches and conceptual queries

### 3. Strict Grounding Prompts
- Prevents LLM hallucination by requiring context-based answers
- Forces citation of every factual claim
- Preserves IS standard numbers and technical terms across languages
- Provides safe fallback when context insufficient

### 4. Multilingual Preservation
- Translates explanatory text while keeping IS numbers, scheme codes, and URLs in Latin script
- Ensures technical accuracy across all supported languages

### 5. Professional Frontend Design
- Clean, enterprise-grade UI without excessive animations or decorative elements
- Consistent spacing, typography, and color scheme
- Functional interactions with clear feedback
- Responsive design across device sizes
- Meaningful empty/loading/error states

## Current Status
- **Backend**: Fully functional with all endpoints operational
- **Frontend**: Professional design implemented across all pages
- **Mock Mode**: Complete contextual follow-up capability working
- **Multi-language**: English, Hindi, Marathi, Tamil supported
- **Image Scan**: OCR + AI vision pipeline operational
- **Testing**: Comprehensive test suite validating follow-up functionality

## Deployment Readiness
The system is designed for easy deployment:
- Docker containerization available
- Environment variable configuration
- Modular architecture for easy maintenance
- Zero-cost development mode for demonstrations
- Production-ready with proper API key configuration

## Use Cases
1. **Manufacturers**: Determine required BIS certifications for new products
2. **Importers**: Verify compliance of imported goods with Indian Standards
3. **Consumers**: Check authenticity of ISI marks and hallmarked jewelry
4. **Startups**: Navigate regulatory landscape for innovative products
5. **MSMEs**: Access certification information without expert consultants

## Smart India Hackathon 2026 Relevance
Parakh addresses the SIH 2026 theme of "Technology for Governance and Compliance" by:
- Leveraging AI to simplify regulatory navigation
- Promoting quality and safety standards awareness
- Supporting Make-in-India initiatives through easier compliance
- Enabling consumer protection through verification tools
- Demonstrating indigenous technological capability in standards domain

---
*Generated for Smart India Hackathon 2026 presentation preparation. All information reflects the current state of the Parakh repository as of 2026-09-30.*