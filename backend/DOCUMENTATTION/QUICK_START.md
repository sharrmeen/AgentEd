# AgentEd Backend - Quick Start Guide for Developers

## 🚀 Get Started in 5 Minutes

### 1. Prerequisites

```bash
# Check Python version (need 3.10+)
python --version

# Check MongoDB is running
mongod --version
```

### 2. Setup Environment

```bash
# Navigate to backend
cd backend

# Create .env file
cat > .env << EOF
# Application
DEBUG=true
APP_NAME=AgentEd
APP_VERSION=1.0.0

# Database
MONGODB_URI=mongodb://localhost:27017
DB_NAME=agented_db

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173", "*"]

# API
API_V1_PREFIX=/api/v1
API_V2_PREFIX=/api/v2
EOF
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Application

```bash
# Terminal 1: Start MongoDB
mongod

# Terminal 2: Start FastAPI
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify Installation

Visit **http://localhost:8000/health**

Expected response:
```json
{"status": "healthy", "version": "1.0.0", "database": "connected"}
```

✅ **Backend is running!**

---

## 📚 API Documentation

**Swagger UI:** http://localhost:8000/api/docs
**ReDoc:** http://localhost:8000/api/redoc

Try any endpoint directly from the Swagger UI!

---

## 🧪 Quick Test

### 1. Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "password123"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "user_id": "507f1f77bcf86cd799439011"
  }
}
```

### 2. Save Token

```bash
export TOKEN="eyJhbGc..."  # Copy from response above
```

### 3. Create Subject

```bash
curl -X POST http://localhost:8000/api/v1/subjects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"subject_name": "Biology"}'
```

### 4. List Subjects

```bash
curl -X GET http://localhost:8000/api/v1/subjects \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🏗️ Project Structure Overview

```
backend/
├── main.py                          # FastAPI app entry
├── requirements.txt                 # Dependencies
├── .env                             # Configuration
│
├── app/
│   ├── api/                         # Router layer
│   │   ├── deps.py                  # Dependency injection
│   │   ├── v1/                      # Service routes
│   │   │   ├── auth.py
│   │   │   ├── subjects.py
│   │   │   └── ... (7 more routers)
│   │   └── v2/                      # Agent routes
│   │       ├── agent.py
│   │       └── chat.py
│   │
│   ├── core/                        # Core logic
│   │   ├── config.py                # Settings
│   │   ├── database.py              # MongoDB
│   │   └── models/                  # Pydantic models
│   │
│   ├── services/                    # Business logic (unchanged)
│   │   ├── subject_service.py
│   │   ├── chat_service.py
│   │   └── ... (14 more services)
│   │
│   ├── schemas/                     # Request/response validation
│   │   ├── auth.py
│   │   ├── subject.py
│   │   └── ... (10 more schemas)
│   │
│   └── agents/                      # LangGraph agents (unchanged)
│       ├── orchestration/
│       ├── planner_agent.py
│       └── ... (3 more agents)
│
├── chroma_db/                       # Vector database
└── data/                            # Upload storage
```

---

## 🔑 Key Files to Understand

### `main.py` - Application Entry Point

```python
# Start app:
app = FastAPI(...)

# Register routers:
app.include_router(api_router, prefix="/api")

# Configure middleware:
app.add_middleware(CORSMiddleware, ...)

# Lifespan management:
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect database
    # Shutdown: close connections
```

**What to do:** Edit `.env` variables, add middleware if needed.

---

### `app/core/config.py` - Settings

```python
class Settings(BaseSettings):
    # Database
    MONGODB_URI: str
    DB_NAME: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    
    # API
    API_V1_PREFIX: str
    API_V2_PREFIX: str
```

**What to do:** Add new settings here, load from `.env`.

---

### `app/api/deps.py` - Authentication & Dependencies

```python
# Create tokens
def create_access_token(data: dict) -> str:
    return encode(data, SECRET_KEY, algorithm=ALGORITHM)

# Verify tokens
def verify_token(token: str) -> dict:
    return decode(token, SECRET_KEY, algorithms=[ALGORITHM])

# Extract current user
async def get_current_user(token: str = Depends(security)) -> dict:
    return {"id": user_id, "email": user_email}

# Get database
def get_database() -> AsyncIOMotorDatabase:
    return db
```

**What to do:** Use `Depends()` in router endpoints.

---

### `app/api/v1/*` - Service Routes

```python
@router.post("/subjects")
async def create_subject(
    request: SubjectCreate,
    user_id: ObjectId = Depends(get_user_id)
):
    # Call service
    subject = await SubjectService.create_subject(
        user_id=user_id,
        subject_name=request.subject_name
    )
    
    # Return response
    return SubjectResponse(**subject.dict())
```

**Pattern:**
1. Define endpoint with path & method
2. Accept request body (validated with Pydantic)
3. Get dependencies (user_id, db, etc.)
4. Call service method
5. Return response

---

### `app/schemas/auth.py` - Request/Response Models

```python
class UserRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
```

**What to do:** Add/modify models for new endpoints.

---

## 💡 Common Tasks

### Add a New Endpoint

1. **Create schema** (`app/schemas/new_resource.py`):
```python
class NewResourceCreate(BaseModel):
    name: str
    description: str
```

2. **Create router** (`app/api/v1/new_resource.py`):
```python
@router.post("/new-resources")
async def create(
    request: NewResourceCreate,
    user_id: ObjectId = Depends(get_user_id)
):
    result = await NewResourceService.create(
        user_id=user_id,
        **request.dict()
    )
    return {"success": True, "data": result}
```

3. **Register router** (`app/api/v1/__init__.py`):
```python
from . import new_resource
router.include_router(new_resource.router)
```

---

### Modify a Service Call

Find the endpoint in `app/api/v1/*` that uses the service:

```python
# Before: This is what you see in the endpoint
result = await SomeService.some_method(user_id=user_id, param=param)

# Services are in app/services/
# Edit the service method if needed (e.g., add new parameters)
# Then update the endpoint to pass new parameters
```

---

### Add Authentication to an Endpoint

```python
# Make endpoint private:
@router.get("/my-endpoint")
async def my_endpoint(
    user_id: ObjectId = Depends(get_user_id)  # Add this
):
    # Now only authenticated users can access
    pass

# Or make endpoint public:
@router.get("/my-endpoint")
async def my_endpoint(
    current_user: dict = Depends(get_optional_user)  # Use this
):
    if current_user:
        # User is authenticated
        user_id = current_user["id"]
    else:
        # User is public
        pass
```

---

### Add Validation to Request

```python
from pydantic import BaseModel, Field, EmailStr

class MyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=0, le=150)  # 0-150
    tags: List[str] = []

# Pydantic automatically validates:
# - Type checking
# - Required fields
# - Min/max lengths
# - Email format
# - Range validation
```

---

## 🐛 Debugging Tips

### Print Logs

```python
import logging

logger = logging.getLogger(__name__)

# In endpoint:
logger.info(f"Creating subject: {subject_name}")
logger.error(f"Error creating subject: {str(e)}")
```

**View logs** in the terminal where you started the app.

---

### Check Database

```bash
# MongoDB shell
mongosh

# Switch to database
use agented_db

# Check collections
db.subjects.find()
db.users.find()
```

---

### Test Token Manually

```python
from app.api.deps import verify_token

# Decode token without validation
import jwt
jwt.decode(token, options={"verify_signature": False})
```

---

### Check Endpoint is Registered

```python
# In Python REPL:
from main import app

# List all routes:
for route in app.routes:
    print(route.path, route.methods)
```

---

## ⚡ Performance Tips

1. **Enable query indexing** in `database.py`:
```python
await db.users.create_index("email", unique=True)
await db.subjects.create_index([("user_id", 1), ("subject_name", 1)])
```

2. **Use async/await properly**:
```python
# Bad: blocks
result = SomeSync.call()

# Good: uses async
result = await SomeAsync.call()
```

3. **Avoid N+1 queries**:
```python
# Bad: queries in loop
for subject_id in subject_ids:
    subject = await SubjectService.get(subject_id)  # N queries

# Good: single query
subjects = await SubjectService.get_many(subject_ids)  # 1 query
```

---

## 🔐 Security Checklist

- ✅ Never commit `.env` to git
- ✅ Use strong `JWT_SECRET_KEY` in production
- ✅ Validate user_id on all endpoints
- ✅ Check ownership before allowing modifications
- ✅ Hash passwords (services do this)
- ✅ Validate file uploads
- ✅ Rate limit endpoints (if needed)

---

## 📱 Testing with Frontend

### React/Vue Frontend Example

```javascript
// Get token
const response = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
const { data } = await response.json();
localStorage.setItem('token', data.access_token);

// Use token
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json'
};
const response = await fetch('/api/v1/subjects', { headers });
```

---

## 🚀 Ready to Code!

You now have:
- ✅ FastAPI server running on port 8000
- ✅ MongoDB connected
- ✅ 30+ API endpoints ready
- ✅ Auto-generated documentation at `/api/docs`
- ✅ Complete API reference (see [API_REFERENCE.md](API_REFERENCE.md))

### Next Steps:

1. **Explore the API:** Open http://localhost:8000/api/docs
2. **Test endpoints:** Use Swagger UI or postman
3. **Build frontend:** Connect to `http://localhost:8000/api`
4. **Review code:** Read through `app/api/v1/` routers
5. **Add features:** Extend endpoints as needed

---

## 📖 Documentation Files

- **[FASTAPI_INTEGRATION.md](FASTAPI_INTEGRATION.md)** - Complete architecture overview
- **[API_REFERENCE.md](API_REFERENCE.md)** - Detailed endpoint documentation
- **[VERIFICATION_TESTING_GUIDE.md](VERIFICATION_TESTING_GUIDE.md)** - Testing procedures

---

## 💬 Questions?

Check these files in order:
1. Router implementation in `app/api/v1/` or `app/api/v2/`
2. Service implementation in `app/services/`
3. Schema definition in `app/schemas/`
4. Configuration in `app/core/config.py`

---

**Happy coding! 🎉**
