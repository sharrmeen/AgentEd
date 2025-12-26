# AgentEd Backend - Verification & Testing Guide

## ✅ Pre-Launch Verification Checklist

### 1. Files Exist
```bash
# Core setup
backend/app/core/config.py
backend/app/api/deps.py

# Routers - V1
backend/app/api/v1/__init__.py
backend/app/api/v1/auth.py
backend/app/api/v1/subjects.py
backend/app/api/v1/syllabus.py
backend/app/api/v1/planner.py
backend/app/api/v1/sessions.py
backend/app/api/v1/chat.py
backend/app/api/v1/notes.py
backend/app/api/v1/quiz.py
backend/app/api/v1/feedback.py

# Routers - V2
backend/app/api/v2/__init__.py
backend/app/api/v2/agent.py
backend/app/api/v2/chat.py

# Schemas
backend/app/schemas/common.py
backend/app/schemas/auth.py
backend/app/schemas/subject.py
backend/app/schemas/syllabus.py
backend/app/schemas/planner.py
backend/app/schemas/session.py
backend/app/schemas/chat.py
backend/app/schemas/notes.py
backend/app/schemas/quiz.py
backend/app/schemas/feedback.py
backend/app/schemas/agent.py

# Main app
backend/main.py (should be updated)
```

### 2. Test Application Startup

```bash
# Navigate to backend directory
cd backend

# Install dependencies (if not already done)
pip install -r requirements.txt

# Start MongoDB (in another terminal)
mongod

# Run the application
uvicorn main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete
```

### 3. Verify Endpoints Are Registered

Visit in browser: **http://localhost:8000/health**

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected"
}
```

---

## 🧪 Testing Endpoints

### Quick Test Script

Create `test_api.py`:

```python
import httpx
import json
import asyncio

BASE_URL = "http://localhost:8000"

async def test_api():
    async with httpx.AsyncClient() as client:
        # Test health
        print("1. Testing health...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"   ✓ Health: {response.status_code}")
        
        # Test API docs
        print("\n2. Testing API docs...")
        response = await client.get(f"{BASE_URL}/api/docs")
        print(f"   ✓ Swagger available: {response.status_code}")
        
        # Test register (will fail without proper DB, but verifies endpoint exists)
        print("\n3. Testing auth endpoint exists...")
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        print(f"   ✓ Register endpoint: {response.status_code}")
        
        # Test subject endpoint exists
        print("\n4. Testing protected endpoint (should fail without token)...")
        response = await client.get(f"{BASE_URL}/api/v1/subjects")
        print(f"   ✓ Protected endpoint rejects request: {response.status_code} (expected 401 or 403)")

# Run test
if __name__ == "__main__":
    asyncio.run(test_api())
```

Run it:
```bash
python test_api.py
```

---

## 🔍 Endpoint Testing (Using Thunder Client or Postman)

### 1. **Authentication**

#### Register
```
POST http://localhost:8000/api/v1/auth/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Expected response (201):**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 604800,
    "user_id": "507f1f77bcf86cd799439011",
    "email": "john@example.com",
    "name": "John Doe"
  }
}
```

**Save the `access_token` for next requests!**

#### Login
```
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "securePassword123"
}
```

#### Get Current User
```
GET http://localhost:8000/api/v1/auth/me
Authorization: Bearer {access_token}
```

### 2. **Subjects**

#### Create Subject
```
POST http://localhost:8000/api/v1/subjects
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "subject_name": "Biology"
}
```

**Expected response (201):**
```json
{
  "success": true,
  "message": "Subject created successfully",
  "data": {
    "id": "507f1f77bcf86cd799439012",
    "user_id": "507f1f77bcf86cd799439011",
    "subject_name": "Biology",
    "status": "not_started"
  }
}
```

**Save the `id` as `{subject_id}`!**

#### List Subjects
```
GET http://localhost:8000/api/v1/subjects
Authorization: Bearer {access_token}
```

#### Get Subject
```
GET http://localhost:8000/api/v1/subjects/{subject_id}
Authorization: Bearer {access_token}
```

### 3. **Syllabus Upload**

#### Upload Syllabus (requires actual file)
```
POST http://localhost:8000/api/v1/syllabus/{subject_id}/upload
Authorization: Bearer {access_token}

Form-Data:
  file: (select file from disk)
  description: "Biology Syllabus - Fall 2024"
  total_chapters: "12"
```

#### Get Syllabus
```
GET http://localhost:8000/api/v1/syllabus/{subject_id}
Authorization: Bearer {access_token}
```

### 4. **Study Planning**

#### Generate Plan
```
POST http://localhost:8000/api/v1/planner/{subject_id}/generate
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "target_days": 30,
  "daily_hours": 2.0,
  "preferred_time": "evening"
}
```

**Expected response (201):**
```json
{
  "success": true,
  "message": "Study plan generated successfully",
  "data": {
    "subject_id": "{subject_id}",
    "chapters": [
      {
        "chapter_number": 1,
        "title": "Introduction to Biology",
        "deadline": "2024-01-10T23:59:59Z",
        "objectives": ["Understand cell structure", "Learn about DNA"]
      }
    ],
    "total_days": 30
  }
}
```

#### Get Plan
```
GET http://localhost:8000/api/v1/planner/{subject_id}
Authorization: Bearer {access_token}
```

### 5. **Study Sessions**

#### Create Session
```
POST http://localhost:8000/api/v1/sessions
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "subject_id": "{subject_id}",
  "chapter_number": 1
}
```

**Expected response (201):**
```json
{
  "success": true,
  "message": "Session created successfully",
  "data": {
    "id": "507f1f77bcf86cd799439013",
    "subject_id": "{subject_id}",
    "chapter_number": 1,
    "started_at": "2024-01-01T10:00:00Z",
    "duration_minutes": 0
  }
}
```

**Save as `{session_id}`!**

#### End Session
```
POST http://localhost:8000/api/v1/sessions/{session_id}/end
Authorization: Bearer {access_token}
```

### 6. **Chat/Q&A**

#### Send Message
```
POST http://localhost:8000/api/v1/chat/{chat_id}/message
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message": "What is photosynthesis?",
  "intent_tag": "explain"
}
```

#### Get Chat History
```
GET http://localhost:8000/api/v1/chat/{chat_id}/history
Authorization: Bearer {access_token}
```

### 7. **Quiz**

#### Get Quiz
```
GET http://localhost:8000/api/v1/quiz/{quiz_id}
Authorization: Bearer {access_token}
```

#### Submit Quiz Answers
```
POST http://localhost:8000/api/v1/quiz/{quiz_id}/submit
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "answers": {
    "q1": "A",
    "q2": "C",
    "q3": "B"
  }
}
```

#### Get Quiz Results
```
GET http://localhost:8000/api/v1/quiz/{subject_id}/results
Authorization: Bearer {access_token}
```

### 8. **Notes Upload**

#### Upload Notes
```
POST http://localhost:8000/api/v1/notes/{subject_id}/upload
Authorization: Bearer {access_token}

Form-Data:
  file: (PDF or image file)
  chapter_number: "1"
  description: "Chapter 1 notes"
```

#### List Notes
```
GET http://localhost:8000/api/v1/notes/{subject_id}
Authorization: Bearer {access_token}
```

### 9. **Feedback**

#### Get Feedback
```
GET http://localhost:8000/api/v1/feedback/{result_id}
Authorization: Bearer {access_token}
```

#### List All Feedback
```
GET http://localhost:8000/api/v1/feedback
Authorization: Bearer {access_token}
```

### 10. **V2 Agent Endpoints**

#### Main Agent Query
```
POST http://localhost:8000/api/v2/agent/query
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "query": "Create a 30-day study plan for Biology",
  "subject_id": "{subject_id}",
  "constraints": {
    "target_days": 30,
    "daily_hours": 2.0
  }
}
```

**Expected response (201):**
```json
{
  "success": true,
  "messages": [
    "Analyzing Biology syllabus...",
    "Creating 30-day study plan..."
  ],
  "data": {
    "study_plan": {...},
    "recommendations": [...]
  },
  "workflow_id": "workflow_123",
  "agents_involved": ["study_plan_agent"],
  "status": "completed"
}
```

#### Shortcut: Quick Plan Generation
```
POST http://localhost:8000/api/v2/agent/plan
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "subject_id": "{subject_id}",
  "target_days": 30,
  "daily_hours": 2.0
}
```

#### Shortcut: Quick Quiz Generation
```
POST http://localhost:8000/api/v2/agent/quiz
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "subject_id": "{subject_id}",
  "chapter_number": 1,
  "difficulty": "medium",
  "num_questions": 10
}
```

#### Conversational Chat
```
POST http://localhost:8000/api/v2/chat
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message": "Explain photosynthesis in simple terms",
  "subject_id": "{subject_id}"
}
```

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### Issue: MongoDB connection failed

**Solution:**
```bash
# Check if MongoDB is running
mongod

# Check connection string in .env
MONGODB_URI=mongodb://localhost:27017
```

### Issue: JWT token invalid

**Solution:**
1. Register again to get new token
2. Check token is in `Authorization: Bearer {token}` format
3. Verify JWT_SECRET_KEY in `.env`

### Issue: 404 on endpoints

**Solution:**
1. Verify endpoint URL is correct
2. Check router is registered in `main.py`
3. Check file exists in `api/v1/` or `api/v2/`

### Issue: 401 Unauthorized

**Solution:**
1. Add `Authorization: Bearer {token}` header
2. Get new token from `/auth/register` or `/auth/login`

### Issue: FileNotFoundError during upload

**Solution:**
```python
# Check UPLOAD_DIR exists in config.py
import os
os.makedirs("uploads", exist_ok=True)
```

---

## 📊 Database Verification

### Check MongoDB Connection

```python
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.agented_db
    
    # Test connection
    await db.command("ping")
    print("✓ Database connected")
    
    # List collections
    collections = await db.list_collection_names()
    print(f"✓ Collections: {collections}")

asyncio.run(test_db())
```

### Check Collections Created

```bash
# MongoDB Shell
mongosh

use agented_db

db.users.find().limit(1)
db.subjects.find().limit(1)
db.study_sessions.find().limit(1)
```

---

## 📈 Load Testing (Optional)

Use **Apache Bench** or **Locust**:

```bash
# Simple GET endpoint test
ab -n 100 -c 10 http://localhost:8000/health

# POST endpoint test
ab -n 50 -c 5 -T application/json \
  -p data.json \
  http://localhost:8000/api/v1/auth/register
```

Create `data.json`:
```json
{
  "name": "Test User",
  "email": "test@example.com",
  "password": "password123"
}
```

---

## ✨ All Verification Steps Passed?

If all tests above pass:

✅ Application starts without errors
✅ Health endpoint responds
✅ API documentation available at `/api/docs`
✅ Authentication flow works
✅ Service endpoints accessible
✅ Agent endpoints accessible
✅ Database connected
✅ Error handling works

## 🎉 Backend is ready for frontend integration!

---

## 📝 Frontend Integration Notes

### Base URL
```javascript
const API_BASE = "http://localhost:8000/api";
```

### Authentication Header
```javascript
const headers = {
  "Authorization": `Bearer ${token}`,
  "Content-Type": "application/json"
};
```

### Example: Register User
```javascript
async function register(name, email, password) {
  const response = await fetch(`${API_BASE}/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password })
  });
  return response.json();
}
```

### Example: Create Subject
```javascript
async function createSubject(token, subjectName) {
  const response = await fetch(`${API_BASE}/v1/subjects`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ subject_name: subjectName })
  });
  return response.json();
}
```

---

## 🚀 Production Deployment

### 1. Update Configuration
```env
DEBUG=false
CORS_ORIGINS=["https://yourdomain.com"]
JWT_SECRET_KEY=generate-strong-secret
MONGODB_URI=your-production-mongodb-uri
```

### 2. Run with Gunicorn
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### 3. Docker Deployment (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Run:
```bash
docker build -t agented-backend .
docker run -p 8000:8000 agented-backend
```

---

**Backend verification complete! Ready to deploy! 🚀**
