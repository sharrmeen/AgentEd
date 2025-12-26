# backend/app/schemas/__init__.py

"""
Pydantic schemas for API request/response validation.

Separated from core models to handle API-specific transformations.
"""

from app.schemas.common import (
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
    MessageResponse
)
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    LearningProfileResponse
)
from app.schemas.subject import (
    SubjectCreate,
    SubjectResponse,
    SubjectListResponse
)
from app.schemas.syllabus import (
    SyllabusResponse,
    SyllabusUploadResponse
)
from app.schemas.planner import (
    PlanGenerateRequest,
    PlanResponse,
    ObjectiveCompleteRequest,
    ObjectiveCompleteResponse,
    ChapterProgressResponse,
    PlannerStateResponse
)
from app.schemas.session import (
    SessionCreateRequest,
    SessionResponse,
    SessionListResponse
)
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryResponse
)
from app.schemas.notes import (
    NotesResponse,
    NotesListResponse
)
from app.schemas.quiz import (
    QuizResponse,
    QuizListResponse,
    QuizSubmitRequest,
    QuizResultResponse,
    QuizStatisticsResponse
)
from app.schemas.feedback import (
    FeedbackResponse,
    FeedbackListResponse
)
from app.schemas.agent import (
    AgentQueryRequest,
    AgentQueryResponse,
    AgentChatRequest,
    AgentChatResponse
)
