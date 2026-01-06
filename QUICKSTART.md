# Quick Start (5 Minutes)

## For Hackathon Judges - Fastest Way to Run

### Step 1: Run Setup (2 min)
```bash
setup.bat
```
This automatically:
- Creates Python virtual environment
- Installs all Python dependencies
- Installs all Node.js dependencies
- Creates required folders

### Step 2: Get API Key (1 min)
1. Go to: https://aistudio.google.com/app/apikey
2. Get your **free** Gemini API key
3. Edit `backend\.env` and paste it:
   ```
   GEMINI_API_KEY=your_key_here
   ```

### Step 3: Start Project (1 min)
```bash
run.bat
```

### Step 4: Open Browser (1 min)
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/api/docs

---

## Troubleshooting (Quick Fixes)

### "MongoDB connection failed"
**Fix**: Start MongoDB in another terminal:
```bash
mongod
```
Or use MongoDB Atlas (cloud) - update `MONGODB_URI` in `backend\.env`

### "Port 3000/8000 already in use"
**Fix**: Kill the process or use different ports in the code

### "API Key error"
**Fix**: Make sure you pasted the correct key in `backend\.env` and restarted

### "Node/Python not found"
**Fix**: Install from:
- Python: https://www.python.org/
- Node.js: https://nodejs.org/

---

## What Does This Do?

AgentEd is an AI-powered study companion with:
- Chat with AI tutor (explains concepts)
- Upload study materials (PDFs, images)
- Generate quizzes from your notes
- Get personalized study plans
- Track your progress

---

## File Breakdown

| File | Purpose |
|------|---------|
| `setup.bat` | One-time setup (install dependencies) |
| `run.bat` | Start backend + frontend |
| `backend\.env` | Config file (add your API keys here) |
| `frontend/` | React UI |
| `backend/` | FastAPI server |

---

## Need More Details?

See `README.md` for complete documentation including:
- Full API reference
- Architecture diagram
- Advanced configuration
- Development guide
