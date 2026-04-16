# AgentEd - AI-Powered Study Companion

An intelligent, multi-agent learning platform that provides personalized study assistance, curriculum planning, quiz generation, and performance feedback using advanced AI and RAG (Retrieval-Augmented Generation).

##  Features

- **Multi-Agent Architecture**: LangGraph-based orchestration for intelligent workflows
- **Intelligent Resource Agent**: Knowledge retrieval with intent-based prompts (explain, summarize, answer)
- **Study Planner Agent**: AI-powered curriculum design and study scheduling
- **Quiz Agent**: Dynamic assessment generation from study materials
- **Feedback Agent**: Performance analysis and improvement recommendations
- **Multi-Modal Support**: Handles PDFs, images, and text documents
- **Vector RAG**: ChromaDB-powered semantic search for accurate knowledge retrieval
- **Real-time Chat**: Interactive learning through conversational AI
- **User Authentication**: Secure JWT-based authentication
- **Progress Tracking**: MongoDB-backed session management and history

##  Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18+ and npm/pnpm
- **MongoDB**: Local or cloud instance (MongoDB Atlas)
- **API Keys**:
  - Google Gemini API key
  - Tavily Search API key (optional, for web search)
- **RAM**: Minimum 8GB (16GB recommended for optimal performance)

## Quick Start

### 1. Clone & Setup

```bash
# Navigate to project root
cd AgentEd
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# On Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Edit `backend/.env` with your settings:

```env
# Application
APP_NAME=AgentEd
APP_VERSION=1.0.0
DEBUG=true

# MongoDB Atlas (required)
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/?retryWrites=true&w=majority
DB_NAME=agented_db

# API Keys (REQUIRED - Get from respective services)
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
GEMINI_MODEL=gemini-2.5-flash-lite

# JWT Secret (generated, can keep as-is or regenerate)
JWT_SECRET_KEY=your_jwt_secret_key

# App URL / CORS / Hosts
APP_URL_BASE=https://app.yourdomain.com
CORS_ORIGINS=["https://app.yourdomain.com"]
ALLOWED_HOSTS=["api.yourdomain.com","app.yourdomain.com"]

# Pinecone Vector Storage
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=your_pinecone_index
PINECONE_NAMESPACE=default
MAX_CHUNK_SIZE=1200

# Object Storage (S3-compatible)
STORAGE_PROVIDER=s3
S3_KEY=your_s3_key
S3_SECRET=your_s3_secret
S3_BUCKET=your_bucket
S3_ENDPOINT=https://s3.your-region.backblazeb2.com
S3_REGION=your-region
S3_FORCE_PATH_STYLE=true

# File Upload Settings
MAX_UPLOAD_SIZE=10485760  # 10 MB
ALLOWED_EXTENSIONS=["pdf", "docx", "png", "jpg", "jpeg"]
```

**Important**: Update `GEMINI_API_KEY` and `TAVILY_API_KEY` with your actual API credentials.

### 4. Start Backend

```bash
# From backend directory (with venv activated)
python main.py
```

Backend will run on the host/port configured for your environment.
- API Docs: `/api/docs`
- ReDoc: `/api/redoc`

### 5. Frontend Setup

In a new terminal:

```bash
# Navigate to frontend
cd frontend

# Install dependencies (using pnpm, or npm/yarn)
pnpm install
# OR
npm install

# Start development server
pnpm dev
# OR
npm run dev
```

Frontend will run on `http://localhost:3000`

### 6. Verify Databases

Ensure MongoDB is running:

```bash
# Windows (if installed locally)
mongod

# Or use MongoDB Atlas cloud instance
# Update MONGODB_URI in .env
```

ChromaDB will auto-initialize in `./chroma_db` directory.

## Project Structure

```
AgentEd/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── agents/            # LangGraph agents (Resource, Quiz, Planner, Feedback)
│   │   ├── api/               # API routes (v1, v2)
│   │   ├── core/              # Config, database, models
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── services/          # Business logic (chat, embedding, RAG, etc.)
│   │   └── __init__.py
│   ├── main.py                # FastAPI app entry point
│   ├── requirements.txt        # Python dependencies
│   └── .env                    # Environment configuration
├── frontend/                   # Next.js React frontend
│   ├── app/                    # Next.js app directory
│   │   ├── page.tsx           # Home page
│   │   ├── layout.tsx         # Root layout
│   │   ├── dashboard/         # Dashboard pages
│   │   ├── quiz/              # Quiz interface
│   │   ├── notes/             # Notes management
│   │   ├── login/             # Authentication pages
│   │   └── settings/
│   ├── components/            # Reusable React components
│   ├── hooks/                 # Custom React hooks
│   ├── lib/                   # Utility functions and API client
│   ├── public/                # Static assets
│   ├── package.json           # Node dependencies
│   └── tsconfig.json
├── chroma_db/                 # Legacy local vector data (not used in cloud runtime)
├── mongodb/                   # Legacy local Mongo files (not used in cloud runtime)
├── requirements.txt           # Root Python dependencies
└── README.md                  # This file
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login & get JWT token

### Chat & Learning
- `POST /api/v1/chat/send` - Send message to resource agent
- `GET /api/v1/chat/history` - Get chat history

### Notes
- `POST /api/v1/notes/upload` - Upload study materials
- `GET /api/v1/notes/list` - List uploaded notes

### Quiz
- `POST /api/v1/quiz/generate` - Generate quiz from materials
- `POST /api/v1/quiz/submit` - Submit quiz answers

### Study Planning
- `POST /api/v1/planner/generate-plan` - Generate study plan
- `GET /api/v1/planner/status` - Get current plan status

### Feedback
- `GET /api/v1/feedback/analysis` - Get performance analysis

Full API documentation is available at `/api/docs` when backend is running.

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Run specific test file
pytest test_agents.py -v
```

### Linting & Formatting

```bash
# Backend (optional, if linters configured)
cd backend
# black . && isort .

# Frontend
cd frontend
pnpm lint
```

## Troubleshooting

### MongoDB Connection Error
```
Error: Cannot connect to MongoDB Atlas cluster
```
**Solution**: 
- Verify `MONGODB_URI` in `backend/.env` uses a valid Atlas URI.
- Verify Atlas network access and database user credentials.

### API Key Errors
```
Error: Invalid GEMINI_API_KEY
```
**Solution**:
- Get free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- Get Tavily key from [Tavily Search API](https://tavily.com)
- Update `.env` file with valid keys

### Port Already in Use
```
Error: Address already in use
```
**Solution**:
- Backend: Change `host` and `port` in `backend/main.py`
- Frontend: `pnpm dev -- -p 3001` (use different port)

### Virtual Environment Issues (Windows)
```
'venv\Scripts\activate' is not recognized
```
**Solution**: Use PowerShell or `venv\Scripts\activate.bat` in CMD

### Dependencies Installation Issues
```bash
# Clear pip cache and reinstall
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                │
│            React UI Components + Hooks              │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP/REST API
┌──────────────────▼──────────────────────────────────┐
│                FastAPI Backend                      │
├─────────────────────────────────────────────────────┤
│  Routes → Schemas → Services → Agents              │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │     LangGraph Multi-Agent Orchestration     │   │
│  │  - Resource Agent (Explain/Summarize/Answer)│   │
│  │  - Quiz Agent (Assessment Generation)       │   │
│  │  - Planner Agent (Study Scheduling)         │   │
│  │  - Feedback Agent (Performance Analysis)    │   │
│  └─────────────────────────────────────────────┘   │
└─────────┬────────────────────── ┬────────────────────┘
          │                       │
     ┌────▼────┐           ┌──────▼───────┐
     │ MongoDB  │          │  ChromaDB    │
     │(Sessions │          │  (Embeddings │
     │  &Cache) │          │   & RAG)     │
     └──────────┘          └──────────────┘
```

## Deployment

### Environment Variables for Production
```env
DEBUG=false
CORS_ORIGINS=["https://yourdomain.com"]
MONGODB_URI=mongodb+srv://...  # MongoDB Atlas
# Use strong JWT_SECRET_KEY in production
```

### Docker (Optional)
```bash
docker-compose up
```

## License

Built for hackathon - 2025

## Contributing

This is a hackathon submission. All contributions welcome!

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Verify all API keys are correctly set in `.env`
3. Ensure MongoDB and all services are running
4. Check the API documentation at `/api/docs`

---

**Ready to learn?** Start the backend and frontend, then navigate to `http://localhost:3000`!