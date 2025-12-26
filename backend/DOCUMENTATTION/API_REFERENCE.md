# AgentEd Backend - Complete API Reference

**Base URL:** `http://localhost:8000/api`

**Documentation:** `http://localhost:8000/api/docs` (Swagger UI)

---

## 📋 Table of Contents

1. [Authentication (V1)](#authentication-v1)
2. [Subjects (V1)](#subjects-v1)
3. [Syllabus (V1)](#syllabus-v1)
4. [Study Planning (V1)](#study-planning-v1)
5. [Study Sessions (V1)](#study-sessions-v1)
6. [Chat/Q&A (V1)](#chatqa-v1)
7. [Notes (V1)](#notes-v1)
8. [Quiz (V1)](#quiz-v1)
9. [Feedback (V1)](#feedback-v1)
10. [Agents (V2)](#agents-v2)
11. [Agent Chat (V2)](#agent-chat-v2)
12. [Common Response Formats](#common-response-formats)
13. [Status Codes](#status-codes)
14. [Error Handling](#error-handling)

---

# V1 Routes - Direct Service Calls

## Authentication (V1)

All authentication endpoints are public (no token required).

### Register User

```http
POST /v1/auth/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Parameters:**
| Name | Type | Required | Rules |
|------|------|----------|-------|
| name | string | Yes | 1-100 chars |
| email | string | Yes | Valid email format |
| password | string | Yes | Min 6 characters |

**Response (201 Created):**
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

**Errors:**
- `400` - Invalid email or password too short
- `409` - User already exists
- `500` - Server error

---

### Login

```http
POST /v1/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Parameters:**
| Name | Type | Required |
|------|------|----------|
| email | string | Yes |
| password | string | Yes |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Login successful",
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

**Errors:**
- `401` - Invalid credentials
- `404` - User not found
- `500` - Server error

---

### Get Current User Profile

```http
GET /v1/auth/me
Authorization: Bearer {access_token}
```

**Headers:**
| Name | Value | Required |
|------|-------|----------|
| Authorization | Bearer {token} | Yes |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "User profile retrieved",
  "data": {
    "id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "student",
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

**Errors:**
- `401` - Invalid or expired token
- `404` - User not found

---

### Get Learning Profile

```http
GET /v1/auth/profile/learning
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Learning profile retrieved",
  "data": {
    "user_id": "507f1f77bcf86cd799439011",
    "total_subjects": 3,
    "total_study_hours": 15.5,
    "average_quiz_score": 85.5,
    "learning_style": "visual",
    "completed_chapters": 12,
    "total_chapters": 50,
    "last_session": "2024-01-15T18:30:00Z"
  }
}
```

---

## Subjects (V1)

All subject endpoints require authentication.

### Create Subject

```http
POST /v1/subjects
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "subject_name": "Biology"
}
```

**Parameters:**
| Name | Type | Required | Rules |
|------|------|----------|-------|
| subject_name | string | Yes | Unique per user, 1-100 chars |

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Subject created successfully",
  "data": {
    "id": "507f1f77bcf86cd799439012",
    "user_id": "507f1f77bcf86cd799439011",
    "subject_name": "Biology",
    "status": "not_started",
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

**Errors:**
- `400` - Invalid subject name or duplicate
- `401` - Unauthorized
- `500` - Server error

---

### List Subjects

```http
GET /v1/subjects
Authorization: Bearer {access_token}
```

**Query Parameters:**
| Name | Type | Required | Values |
|------|------|----------|--------|
| status | string | No | `not_started`, `in_progress`, `completed` |
| limit | integer | No | Default: 50 |
| skip | integer | No | Default: 0 |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Subjects retrieved",
  "data": [
    {
      "id": "507f1f77bcf86cd799439012",
      "user_id": "507f1f77bcf86cd799439011",
      "subject_name": "Biology",
      "status": "in_progress",
      "created_at": "2024-01-01T10:00:00Z"
    },
    {
      "id": "507f1f77bcf86cd799439013",
      "user_id": "507f1f77bcf86cd799439011",
      "subject_name": "Chemistry",
      "status": "not_started",
      "created_at": "2024-01-02T10:00:00Z"
    }
  ]
}
```

---

### Get Subject Details

```http
GET /v1/subjects/{subject_id}
Authorization: Bearer {access_token}
```

**Path Parameters:**
| Name | Type | Format |
|------|------|--------|
| subject_id | string | MongoDB ObjectId |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Subject retrieved",
  "data": {
    "id": "507f1f77bcf86cd799439012",
    "user_id": "507f1f77bcf86cd799439011",
    "subject_name": "Biology",
    "status": "in_progress",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-15T18:30:00Z"
  }
}
```

**Errors:**
- `400` - Invalid ObjectId format
- `401` - Unauthorized
- `404` - Subject not found

---

### Delete Subject

```http
DELETE /v1/subjects/{subject_id}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Subject deleted successfully"
}
```

**Errors:**
- `400` - Invalid ObjectId
- `401` - Unauthorized
- `403` - Not subject owner
- `404` - Subject not found

---

## Syllabus (V1)

All syllabus endpoints require authentication and subject ownership.

### Upload Syllabus

```http
POST /v1/syllabus/{subject_id}/upload
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: (PDF or image file)
description: "Biology Syllabus - Fall 2024"
total_chapters: "12"
```

**Form Parameters:**
| Name | Type | Required | Notes |
|------|------|----------|-------|
| file | file | Yes | PDF, PNG, JPG (max 50MB) |
| description | string | No | 0-500 chars |
| total_chapters | integer | No | 1-500 |

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Syllabus uploaded successfully",
  "data": {
    "subject_id": "507f1f77bcf86cd799439012",
    "file_url": "https://storage.example.com/syllabi/507f.pdf",
    "file_size": 2048000,
    "uploaded_at": "2024-01-01T10:00:00Z",
    "pages": 45,
    "chapters_detected": 12,
    "ocr_processed": true
  }
}
```

**Errors:**
- `400` - Invalid file or subject not found
- `401` - Unauthorized
- `413` - File too large
- `415` - Unsupported file type

---

### Get Syllabus

```http
GET /v1/syllabus/{subject_id}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Syllabus retrieved",
  "data": {
    "subject_id": "507f1f77bcf86cd799439012",
    "file_url": "https://storage.example.com/syllabi/507f.pdf",
    "file_size": 2048000,
    "uploaded_at": "2024-01-01T10:00:00Z",
    "pages": 45,
    "chapters_detected": 12,
    "chapters": [
      {
        "number": 1,
        "title": "Introduction to Biology",
        "pages": "1-5"
      },
      {
        "number": 2,
        "title": "Cell Structure",
        "pages": "6-15"
      }
    ]
  }
}
```

**Errors:**
- `401` - Unauthorized
- `404` - Syllabus not found

---

### Delete Syllabus

```http
DELETE /v1/syllabus/{subject_id}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Syllabus deleted successfully"
}
```

---

## Study Planning (V1)

All planning endpoints require authentication.

### Generate Study Plan

```http
POST /v1/planner/{subject_id}/generate
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "target_days": 30,
  "daily_hours": 2.0,
  "preferred_time": "evening"
}
```

**Parameters:**
| Name | Type | Required | Rules |
|------|------|----------|-------|
| target_days | integer | Yes | 1-365 |
| daily_hours | float | Yes | 0.5-12.0 |
| preferred_time | string | No | `morning`, `afternoon`, `evening` |

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Study plan generated successfully",
  "data": {
    "subject_id": "507f1f77bcf86cd799439012",
    "total_days": 30,
    "daily_hours": 2.0,
    "start_date": "2024-01-15T00:00:00Z",
    "end_date": "2024-02-14T23:59:59Z",
    "chapters": [
      {
        "chapter_number": 1,
        "title": "Introduction to Biology",
        "deadline": "2024-01-22T23:59:59Z",
        "hours_allocated": 4.0,
        "objectives": [
          "Understand cell structure",
          "Learn about DNA",
          "Study photosynthesis"
        ]
      }
    ],
    "total_chapters": 12
  }
}
```

**Errors:**
- `400` - Invalid parameters or missing syllabus
- `401` - Unauthorized
- `404` - Subject not found

---

### Get Current Plan

```http
GET /v1/planner/{subject_id}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Plan retrieved",
  "data": {
    "subject_id": "507f1f77bcf86cd799439012",
    "total_days": 30,
    "daily_hours": 2.0,
    "start_date": "2024-01-15T00:00:00Z",
    "end_date": "2024-02-14T23:59:59Z",
    "chapters": [
      {
        "chapter_number": 1,
        "title": "Introduction to Biology",
        "deadline": "2024-01-22T23:59:59Z",
        "hours_allocated": 4.0,
        "objectives": [
          "Understand cell structure",
          "Learn about DNA",
          "Study photosynthesis"
        ],
        "completed_objectives": ["Understand cell structure"],
        "progress_percentage": 33
      }
    ]
  }
}
```

---

### Mark Objective Complete

```http
POST /v1/planner/objective/complete
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "subject_id": "507f1f77bcf86cd799439012",
  "chapter_number": 1,
  "objective": "Understand cell structure"
}
```

**Parameters:**
| Name | Type | Required |
|------|------|----------|
| subject_id | string | Yes |
| chapter_number | integer | Yes |
| objective | string | Yes |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Objective marked complete",
  "data": {
    "subject_id": "507f1f77bcf86cd799439012",
    "chapter_number": 1,
    "objective": "Understand cell structure",
    "completed_at": "2024-01-18T15:30:00Z",
    "chapter_progress": 50
  }
}
```

---

### Get Chapter Progress

```http
GET /v1/planner/{subject_id}/chapter/{chapter_number}
Authorization: Bearer {access_token}
```

**Path Parameters:**
| Name | Type |
|------|------|
| subject_id | string (ObjectId) |
| chapter_number | integer |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Chapter progress retrieved",
  "data": {
    "subject_id": "507f1f77bcf86cd799439012",
    "chapter_number": 1,
    "title": "Introduction to Biology",
    "deadline": "2024-01-22T23:59:59Z",
    "objectives": [
      {
        "objective": "Understand cell structure",
        "completed": true,
        "completed_at": "2024-01-18T15:30:00Z"
      },
      {
        "objective": "Learn about DNA",
        "completed": false,
        "completed_at": null
      }
    ],
    "progress_percentage": 50,
    "estimated_completion": "2024-01-21T18:00:00Z"
  }
}
```

---

## Study Sessions (V1)

All session endpoints require authentication.

### Create Study Session

```http
POST /v1/sessions
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "subject_id": "507f1f77bcf86cd799439012",
  "chapter_number": 1
}
```

**Parameters:**
| Name | Type | Required |
|------|------|----------|
| subject_id | string | Yes |
| chapter_number | integer | Yes |

**Preconditions:**
- Subject must exist
- Syllabus must be uploaded
- Plan must be generated

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Session created successfully",
  "data": {
    "id": "507f1f77bcf86cd799439013",
    "user_id": "507f1f77bcf86cd799439011",
    "subject_id": "507f1f77bcf86cd799439012",
    "chapter_number": 1,
    "started_at": "2024-01-18T15:30:00Z",
    "ended_at": null,
    "duration_minutes": 0,
    "status": "active"
  }
}
```

**Errors:**
- `400` - Missing syllabus or plan
- `401` - Unauthorized
- `404` - Subject not found

---

### Get Session Details

```http
GET /v1/sessions/{session_id}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Session retrieved",
  "data": {
    "id": "507f1f77bcf86cd799439013",
    "user_id": "507f1f77bcf86cd799439011",
    "subject_id": "507f1f77bcf86cd799439012",
    "chapter_number": 1,
    "started_at": "2024-01-18T15:30:00Z",
    "ended_at": "2024-01-18T17:30:00Z",
    "duration_minutes": 120,
    "status": "completed"
  }
}
```

---

### List Subject Sessions

```http
GET /v1/sessions/subject/{subject_id}
Authorization: Bearer {access_token}
```

**Query Parameters:**
| Name | Type | Required | Values |
|------|------|----------|--------|
| status | string | No | `active`, `completed` |
| limit | integer | No | Default: 50 |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Sessions retrieved",
  "data": [
    {
      "id": "507f1f77bcf86cd799439013",
      "user_id": "507f1f77bcf86cd799439011",
      "subject_id": "507f1f77bcf86cd799439012",
      "chapter_number": 1,
      "started_at": "2024-01-18T15:30:00Z",
      "ended_at": "2024-01-18T17:30:00Z",
      "duration_minutes": 120,
      "status": "completed"
    }
  ]
}
```

---

### End Session

```http
POST /v1/sessions/{session_id}/end
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Session ended",
  "data": {
    "id": "507f1f77bcf86cd799439013",
    "user_id": "507f1f77bcf86cd799439011",
    "subject_id": "507f1f77bcf86cd799439012",
    "chapter_number": 1,
    "started_at": "2024-01-18T15:30:00Z",
    "ended_at": "2024-01-18T17:30:00Z",
    "duration_minutes": 120,
    "status": "completed"
  }
}
```

---

## Chat/Q&A (V1)

All chat endpoints require authentication.

### Send Message

```http
POST /v1/chat/{chat_id}/message
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message": "What is photosynthesis?",
  "intent_tag": "explain"
}
```

**Parameters:**
| Name | Type | Required | Notes |
|------|------|----------|-------|
| message | string | Yes | Question or statement |
| intent_tag | string | No | `explain`, `summarize`, `clarify`, etc. |

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Message sent",
  "data": {
    "chat_id": "507f1f77bcf86cd799439014",
    "message_id": "507f1f77bcf86cd799439015",
    "user_message": "What is photosynthesis?",
    "agent_response": "Photosynthesis is the process...",
    "source": "cache",
    "confidence": 0.95,
    "created_at": "2024-01-18T15:35:00Z"
  }
}
```

---

### Get Chat Metadata

```http
GET /v1/chat/{chat_id}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Chat retrieved",
  "data": {
    "id": "507f1f77bcf86cd799439014",
    "user_id": "507f1f77bcf86cd799439011",
    "subject_id": "507f1f77bcf86cd799439012",
    "created_at": "2024-01-18T15:30:00Z",
    "message_count": 25,
    "last_message_at": "2024-01-18T16:45:00Z"
  }
}
```

---

### Get Chat History

```http
GET /v1/chat/{chat_id}/history
Authorization: Bearer {access_token}
```

**Query Parameters:**
| Name | Type | Required | Notes |
|------|------|----------|-------|
| limit | integer | No | Default: 50 |
| skip | integer | No | Default: 0 |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Chat history retrieved",
  "data": [
    {
      "message_id": "507f1f77bcf86cd799439015",
      "user_message": "What is photosynthesis?",
      "agent_response": "Photosynthesis is...",
      "source": "cache",
      "confidence": 0.95,
      "created_at": "2024-01-18T15:35:00Z"
    },
    {
      "message_id": "507f1f77bcf86cd799439016",
      "user_message": "Can you elaborate?",
      "agent_response": "Sure! Photosynthesis occurs...",
      "source": "agent",
      "created_at": "2024-01-18T15:40:00Z"
    }
  ]
}
```

---

## Notes (V1)

All notes endpoints require authentication.

### Upload Notes

```http
POST /v1/notes/{subject_id}/upload
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: (PDF or image file)
chapter_number: "1"
description: "Chapter 1 notes from lecture"
```

**Form Parameters:**
| Name | Type | Required | Notes |
|------|------|----------|-------|
| file | file | Yes | PDF, PNG, JPG (max 50MB) |
| chapter_number | integer | No | Associated chapter |
| description | string | No | 0-500 chars |

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Notes uploaded successfully",
  "data": {
    "id": "507f1f77bcf86cd799439016",
    "subject_id": "507f1f77bcf86cd799439012",
    "chapter_number": 1,
    "file_url": "https://storage.example.com/notes/507f.pdf",
    "file_size": 1024000,
    "uploaded_at": "2024-01-18T16:00:00Z",
    "ingestion_status": "processed"
  }
}
```

---

### List Notes

```http
GET /v1/notes/{subject_id}
Authorization: Bearer {access_token}
```

**Query Parameters:**
| Name | Type | Required | Notes |
|------|------|----------|-------|
| chapter_number | integer | No | Filter by chapter |
| limit | integer | No | Default: 50 |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Notes retrieved",
  "data": [
    {
      "id": "507f1f77bcf86cd799439016",
      "subject_id": "507f1f77bcf86cd799439012",
      "chapter_number": 1,
      "file_url": "https://storage.example.com/notes/507f.pdf",
      "file_size": 1024000,
      "uploaded_at": "2024-01-18T16:00:00Z"
    }
  ]
}
```

---

### Get Note Details

```http
GET /v1/notes/{note_id}/detail
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Note retrieved",
  "data": {
    "id": "507f1f77bcf86cd799439016",
    "subject_id": "507f1f77bcf86cd799439012",
    "chapter_number": 1,
    "file_url": "https://storage.example.com/notes/507f.pdf",
    "file_size": 1024000,
    "uploaded_at": "2024-01-18T16:00:00Z",
    "description": "Chapter 1 notes from lecture",
    "pages": 10,
    "summary": "This document covers..."
  }
}
```

---

### Delete Note

```http
DELETE /v1/notes/{note_id}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Note deleted successfully"
}
```

---

## Quiz (V1)

All quiz endpoints require authentication.

### Get Quiz

```http
GET /v1/quiz/{quiz_id}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Quiz retrieved",
  "data": {
    "id": "507f1f77bcf86cd799439017",
    "subject_id": "507f1f77bcf86cd799439012",
    "chapter_number": 1,
    "title": "Chapter 1 Quiz",
    "description": "Test your knowledge of photosynthesis",
    "questions": [
      {
        "id": "q1",
        "question": "What is photosynthesis?",
        "type": "multiple_choice",
        "options": [
          "Process of converting light to chemical energy",
          "Process of converting chemical energy to light",
          "Process of breaking down glucose",
          "Process of absorbing water"
        ]
      },
      {
        "id": "q2",
        "question": "Which organelle is responsible for photosynthesis?",
        "type": "multiple_choice",
        "options": [
          "Mitochondria",
          "Chloroplast",
          "Nucleus",
          "Ribosome"
        ]
      }
    ],
    "total_questions": 10,
    "time_limit_minutes": 30,
    "passing_percentage": 70
  }
}
```

**Note:** Answer keys are not included in the GET response.

---

### List Quizzes

```http
GET /v1/quiz
Authorization: Bearer {access_token}
```

**Query Parameters:**
| Name | Type | Required | Notes |
|------|------|----------|-------|
| subject_id | string | No | Filter by subject |
| chapter_number | integer | No | Filter by chapter |
| quiz_type | string | No | `chapter`, `practice`, `final` |
| limit | integer | No | Default: 50 |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Quizzes retrieved",
  "data": [
    {
      "id": "507f1f77bcf86cd799439017",
      "subject_id": "507f1f77bcf86cd799439012",
      "chapter_number": 1,
      "title": "Chapter 1 Quiz",
      "description": "Test your knowledge",
      "total_questions": 10,
      "time_limit_minutes": 30,
      "passing_percentage": 70
    }
  ]
}
```

---

### Submit Quiz

```http
POST /v1/quiz/{quiz_id}/submit
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "answers": {
    "q1": "A",
    "q2": "B",
    "q3": "C"
  },
  "time_taken_seconds": 1800
}
```

**Parameters:**
| Name | Type | Required | Notes |
|------|------|----------|-------|
| answers | object | Yes | Map of question_id to selected answer |
| time_taken_seconds | integer | No | Time spent on quiz |

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Quiz submitted successfully",
  "data": {
    "result_id": "507f1f77bcf86cd799439018",
    "quiz_id": "507f1f77bcf86cd799439017",
    "score": 80,
    "total_points": 100,
    "correct_answers": 8,
    "total_questions": 10,
    "passing": true,
    "submitted_at": "2024-01-18T17:30:00Z",
    "feedback": "Great job! You passed the quiz."
  }
}
```

---

### Get Quiz Statistics

```http
GET /v1/quiz/{subject_id}/statistics
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Statistics retrieved",
  "data": {
    "subject_id": "507f1f77bcf86cd799439012",
    "total_quizzes_taken": 5,
    "average_score": 82.5,
    "highest_score": 95,
    "lowest_score": 70,
    "pass_rate": 80,
    "total_study_time_minutes": 450,
    "by_chapter": [
      {
        "chapter_number": 1,
        "quizzes_taken": 2,
        "average_score": 85,
        "pass_rate": 100
      }
    ]
  }
}
```

---

## Feedback (V1)

All feedback endpoints require authentication.

### Get Feedback Report

```http
GET /v1/feedback/{result_id}
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Feedback retrieved",
  "data": {
    "id": "507f1f77bcf86cd799439019",
    "result_id": "507f1f77bcf86cd799439018",
    "user_id": "507f1f77bcf86cd799439011",
    "subject_id": "507f1f77bcf86cd799439012",
    "performance_level": "good",
    "score": 80,
    "strengths": [
      "Excellent understanding of photosynthesis",
      "Strong grasp of cellular respiration"
    ],
    "weaknesses": [
      "Needs more practice on enzyme kinetics",
      "Review protein synthesis mechanisms"
    ],
    "revision_items": [
      {
        "topic": "Enzyme kinetics",
        "resource": "Chapter 5, pages 45-50",
        "priority": "high"
      }
    ],
    "next_steps": [
      "Practice enzyme kinetics problems",
      "Review protein synthesis",
      "Take practice quiz 2"
    ],
    "motivation_message": "Great progress! Keep up the hard work.",
    "generated_at": "2024-01-18T17:35:00Z"
  }
}
```

---

### List Feedback Reports

```http
GET /v1/feedback
Authorization: Bearer {access_token}
```

**Query Parameters:**
| Name | Type | Required | Notes |
|------|------|----------|-------|
| subject_id | string | No | Filter by subject |
| limit | integer | No | Default: 50 |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Feedback reports retrieved",
  "data": [
    {
      "id": "507f1f77bcf86cd799439019",
      "result_id": "507f1f77bcf86cd799439018",
      "subject_id": "507f1f77bcf86cd799439012",
      "performance_level": "good",
      "score": 80,
      "generated_at": "2024-01-18T17:35:00Z"
    }
  ]
}
```

---

# V2 Routes - Agent Workflows

## Agents (V2)

Intelligent multi-agent orchestration endpoints.

### Query Agent

```http
POST /v2/agent/query
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "query": "Create a 30-day study plan for Biology that focuses on cellular biology",
  "subject_id": "507f1f77bcf86cd799439012",
  "constraints": {
    "target_days": 30,
    "daily_hours": 2.0,
    "focus_areas": ["cellular biology", "genetics"]
  }
}
```

**Parameters:**
| Name | Type | Required | Notes |
|------|------|----------|-------|
| query | string | Yes | Natural language request |
| subject_id | string | No | Subject context |
| constraints | object | No | Task-specific constraints |

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Agent query processed",
  "data": {
    "study_plan": {
      "chapters": [...],
      "total_days": 30,
      "recommendations": [...]
    },
    "reasoning": "Created a focused plan emphasizing cellular biology and genetics...",
    "confidence": 0.92
  },
  "workflow_id": "workflow_1234567890",
  "agents_involved": ["study_plan_agent", "resource_agent"],
  "status": "completed",
  "execution_time_ms": 2500
}
```

---

### Quick Plan Generation

```http
POST /v2/agent/plan
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "subject_id": "507f1f77bcf86cd799439012",
  "target_days": 30,
  "daily_hours": 2.0,
  "preferences": {
    "learning_style": "visual",
    "pace": "moderate"
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Study plan generated",
  "data": {
    "study_plan": {
      "chapters": [...],
      "total_days": 30,
      "daily_hours": 2.0,
      "estimated_completion": "2024-02-14T23:59:59Z"
    }
  },
  "workflow_id": "workflow_1234567890",
  "status": "completed"
}
```

---

### Quick Quiz Generation

```http
POST /v2/agent/quiz
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "subject_id": "507f1f77bcf86cd799439012",
  "chapter_number": 1,
  "difficulty": "medium",
  "num_questions": 10,
  "question_types": ["multiple_choice", "short_answer"]
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Quiz generated",
  "data": {
    "quiz": {
      "id": "507f1f77bcf86cd799439020",
      "subject_id": "507f1f77bcf86cd799439012",
      "chapter_number": 1,
      "title": "Biology Chapter 1 Quiz",
      "questions": [...]
    }
  },
  "workflow_id": "workflow_1234567890",
  "status": "completed"
}
```

---

## Agent Chat (V2)

Conversational interface with intelligent agent routing.

### Send Message

```http
POST /v2/chat
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message": "Explain photosynthesis in simple terms",
  "subject_id": "507f1f77bcf86cd799439012",
  "context": {
    "chapter_number": 1,
    "learning_style": "visual"
  }
}
```

**Parameters:**
| Name | Type | Required | Notes |
|------|------|----------|-------|
| message | string | Yes | User message or question |
| subject_id | string | No | Subject context |
| context | object | No | Additional context |

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Agent response",
  "data": {
    "response": "Photosynthesis is the process where plants use sunlight...",
    "elaboration": "Think of it like a solar panel that converts light to food...",
    "visual_description": "Imagine chloroplasts as tiny green factories...",
    "follow_up_suggestions": [
      "What is the light-dependent reaction?",
      "How does photosynthesis relate to cellular respiration?"
    ]
  },
  "workflow_id": "workflow_1234567890",
  "agents_involved": ["resource_agent"],
  "status": "completed"
}
```

---

### Explain Concept

```http
POST /v2/chat/explain
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "concept": "DNA replication",
  "subject_id": "507f1f77bcf86cd799439012",
  "detail_level": "intermediate"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Concept explanation",
  "data": {
    "concept": "DNA replication",
    "simple_explanation": "DNA replication is when...",
    "detailed_explanation": "During DNA replication, the double helix...",
    "steps": [
      "Helicase unwinds the DNA double helix",
      "DNA polymerase creates new strands",
      "Ligase seals the sugar-phosphate backbone"
    ],
    "analogies": "It's like making a photocopy of a document...",
    "related_concepts": ["DNA transcription", "Semiconservative replication"]
  },
  "workflow_id": "workflow_1234567890",
  "status": "completed"
}
```

---

### Summarize Topic

```http
POST /v2/chat/summarize
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "topic": "Photosynthesis",
  "subject_id": "507f1f77bcf86cd799439012",
  "length": "short"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Topic summary",
  "data": {
    "topic": "Photosynthesis",
    "short_summary": "Process of converting light to chemical energy in plants",
    "long_summary": "Photosynthesis is a fundamental biological process...",
    "key_points": [
      "Converts light energy to chemical energy",
      "Occurs in chloroplasts",
      "Produces glucose and oxygen",
      "Two main stages: light-dependent and light-independent reactions"
    ],
    "formulas": [
      "6CO2 + 6H2O + light → C6H12O6 + 6O2"
    ]
  },
  "workflow_id": "workflow_1234567890",
  "status": "completed"
}
```

---

### Practice Tips

```http
POST /v2/chat/practice
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "topic": "Enzyme kinetics",
  "subject_id": "507f1f77bcf86cd799439012",
  "difficulty": "intermediate"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Practice tips",
  "data": {
    "topic": "Enzyme kinetics",
    "tips": [
      "Start with understanding Michaelis-Menten equation",
      "Practice plotting velocity vs substrate concentration",
      "Work through inhibition examples"
    ],
    "practice_problems": [
      {
        "problem": "Calculate Vmax given enzyme kinetics data",
        "hint": "Lineweaver-Burk plot will help",
        "difficulty": "intermediate"
      }
    ],
    "resources": [
      {
        "type": "video",
        "title": "Enzyme Kinetics Explained",
        "duration_minutes": 15
      },
      {
        "type": "practice_set",
        "title": "20 enzyme kinetics problems",
        "difficulty": "intermediate"
      }
    ]
  },
  "workflow_id": "workflow_1234567890",
  "status": "completed"
}
```

---

# Common Response Formats

## Success Response

All successful responses follow this format:

```json
{
  "success": true,
  "message": "Descriptive success message",
  "data": {
    "...": "Response-specific data structure"
  }
}
```

---

## Paginated Response

```json
{
  "success": true,
  "message": "Items retrieved",
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 50,
    "skip": 0,
    "page": 1,
    "pages": 3
  }
}
```

---

# Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Successful GET request |
| 201 | Created | Successful POST request |
| 204 | No Content | Successful DELETE request |
| 400 | Bad Request | Invalid parameters, validation error |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | User lacks permission (not owner) |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists (e.g., duplicate user) |
| 413 | Payload Too Large | File too large |
| 415 | Unsupported Media Type | Wrong file type |
| 422 | Unprocessable Entity | Semantic validation error |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Database connection error |

---

# Error Handling

## Standard Error Response

```json
{
  "success": false,
  "message": "Error description",
  "detail": "Additional error details (in debug mode)"
}
```

## Examples

### Validation Error
```json
{
  "success": false,
  "message": "Invalid request parameters",
  "detail": {
    "email": "Invalid email format",
    "password": "Password must be at least 6 characters"
  }
}
```

### Authentication Error
```json
{
  "success": false,
  "message": "Invalid or expired token"
}
```

### Not Found Error
```json
{
  "success": false,
  "message": "Subject not found",
  "detail": "Subject with ID '507f1f77bcf86cd799439099' does not exist"
}
```

### Ownership Error
```json
{
  "success": false,
  "message": "Permission denied",
  "detail": "You don't have permission to access this resource"
}
```

---

## Summary

- **Total Endpoints**: 30+
- **Authentication**: JWT Bearer tokens
- **Base URL**: `http://localhost:8000/api`
- **Documentation**: Auto-generated at `/api/docs`
- **Response Format**: Standardized JSON with `success`, `message`, `data` fields
- **Error Handling**: Consistent error responses with appropriate status codes

All endpoints are fully documented with request/response examples, parameter descriptions, and error scenarios.
