
# backend/app/api/v1/quiz.py

"""
Quiz endpoints - Quiz lifecycle management.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from typing import Optional

from app.services.quiz_service import QuizService
from app.services.feedback_service import FeedbackService
from app.agents.orchestration.workflow import run_workflow
from app.schemas.quiz import (
    QuizGenerateRequest,
    QuizResponse,
    QuizListResponse,
    QuizListItem,
    QuizSubmitRequest,
    QuizResultResponse,
    QuizResultListResponse,
    QuizStatisticsResponse
)
from app.api.deps import get_user_id

router = APIRouter()


@router.post("", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def generate_quiz(
    request: QuizGenerateRequest,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Generate a new quiz for a subject/chapter.
    
    Prerequisites:
    - Subject must exist
    - Study plan must be generated (for chapter context)
    
    Args:
        request: Quiz generation parameters
        - subject_id: Subject ID
        - chapter_number: Chapter to quiz on (optional)
        - num_questions: Number of questions (1-50, default 10)
        - quiz_type: "practice" | "revision" | "mock_exam"
        - difficulty: "easy" | "medium" | "hard" | "mixed" (optional)
    
    Returns:
        Generated quiz ready to take
    """
    try:
        subject_obj_id = ObjectId(request.subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        # Use agent workflow to generate quiz
        workflow_result = await run_workflow(
            user_id=str(user_id),
            user_query=f"Generate a {request.quiz_type} quiz with {request.num_questions} questions",
            subject_id=request.subject_id,
            chapter_number=request.chapter_number,
            constraints={
                "num_questions": request.num_questions,
                "quiz_type": request.quiz_type,
                "difficulty": request.difficulty or "mixed"
            }
        )
        
        # Extract quiz from workflow result
        quiz_data = workflow_result.get("quiz")
        quiz_metadata = workflow_result.get("quiz_metadata")
        
        # Debug: Check workflow result status
        if workflow_result.get("errors"):
            print(f"❌ Workflow errors: {workflow_result.get('errors')}")
        print(f"📊 Workflow result keys: {list(workflow_result.keys())}")
        print(f"📊 Agent trace: {workflow_result.get('agent_trace')}")
        
        if not quiz_data:
            # Provide more detailed error message
            error_msgs = workflow_result.get("errors", [])
            if error_msgs:
                raise ValueError(f"Quiz generation failed: {'; '.join(error_msgs)}")
            else:
                raise ValueError("No quiz generated. Check workflow execution.")
        
        # Store quiz in database
        chapter_title = workflow_result.get("chapter_title")
        quiz = await QuizService.create_quiz(
            user_id=user_id,
            subject_id=subject_obj_id,
            subject_name=workflow_result.get("subject_name", "Unknown"),
            chapter_number=request.chapter_number,
            chapter_title=chapter_title or f"Chapter {request.chapter_number}" if request.chapter_number else "General",
            quiz_data=quiz_data,
            quiz_metadata=quiz_metadata,
            quiz_type=request.quiz_type
        )
        
        # Extract metadata for response
        if quiz_metadata:
            quiz_title = quiz_metadata.get("title", f"{request.quiz_type.title()} Quiz")
            quiz_topic = quiz_metadata.get("topic", chapter_title or f"Chapter {request.chapter_number}" if request.chapter_number else "General")
            total_marks = quiz_metadata.get("total_marks", request.num_questions)
        else:
            quiz_title = f"{request.quiz_type.title()} Quiz"
            quiz_topic = chapter_title or f"Chapter {request.chapter_number}" if request.chapter_number else "General"
            total_marks = request.num_questions
        
        # Build chapter string for display
        chapter_display = ""
        if request.chapter_number:
            if chapter_title:
                chapter_display = f"Chapter {request.chapter_number}: {chapter_title}"
            else:
                chapter_display = f"Chapter {request.chapter_number}"
        else:
            chapter_display = "General"
        
        # Convert questions to response format
        questions_list = quiz_data if isinstance(quiz_data, list) else quiz_data.get("questions", [])
        question_responses = [
            {
                "question_id": str(q.get("question_id", i)),
                "question_number": q.get("question_number", i+1),
                "text": q.get("text", q.get("question_text", "")),
                "question_type": q.get("question_type", "mcq"),
                "options": q.get("options", []),
                "difficulty": q.get("difficulty", "medium"),
                "marks": q.get("marks", 1)
            }
            for i, q in enumerate(questions_list)
        ]
        
        return QuizResponse(
            id=str(quiz.id) if hasattr(quiz, 'id') else str(quiz.get("_id")),
            subject_id=request.subject_id,
            subject=quiz.subject if hasattr(quiz, 'subject') else quiz.get("subject", "Unknown"),
            chapter=chapter_display,
            chapter_number=request.chapter_number,
            title=quiz_title,
            description=f"{len(questions_list)} questions • {request.difficulty or 'mixed'} difficulty",
            quiz_type=request.quiz_type,
            questions=question_responses,
            total_marks=total_marks,
            time_limit=request.num_questions * 3,  # 3 minutes per question
            pass_percentage=60.0,
            created_at=quiz.get("created_at") if isinstance(quiz, dict) else quiz.created_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Get a quiz to take.
    
    Args:
        quiz_id: Quiz ID
        
    Returns:
        Quiz with questions (answer keys hidden)
    """
    try:
        quiz_obj_id = ObjectId(quiz_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid quiz ID format"
        )
    
    try:
        quiz = await QuizService.get_quiz_by_id(
            user_id=user_id,
            quiz_id=quiz_obj_id
        )
        
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        # Convert questions to response format (without answers)
        question_responses = [
            {
                "question_id": str(q.question_id),
                "question_number": q.question_number,
                "text": q.text,
                "question_type": q.question_type,
                "options": q.options,
                "difficulty": q.difficulty,
                "marks": q.marks
            }
            for q in quiz.questions
        ]
        
        return QuizResponse(
            id=str(quiz.id),
            subject_id=str(quiz.subject_id),
            subject=quiz.subject,
            chapter=quiz.chapter,
            chapter_number=quiz.chapter_number,
            title=quiz.title,
            description=quiz.description,
            quiz_type=quiz.quiz_type,
            questions=question_responses,
            total_marks=quiz.total_marks,
            time_limit=quiz.time_limit,
            pass_percentage=quiz.pass_percentage,
            created_at=quiz.created_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("")
async def list_quizzes(
    subject_id: Optional[str] = None,
    chapter_number: Optional[int] = None,
    quiz_type: Optional[str] = None,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    List all quizzes with optional filters.
    
    Query Parameters:
        subject_id: Filter by subject
        chapter_number: Filter by chapter
        quiz_type: Filter by type (practice, revision, mock_exam)
        
    Returns:
        List of quizzes
    """
    try:
        subject_obj_id = ObjectId(subject_id) if subject_id else None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        quizzes = await QuizService.list_quizzes_by_subject(
            user_id=user_id,
            subject_id=subject_obj_id,
            chapter_number=chapter_number,
            quiz_type=quiz_type
        )
        
        from datetime import datetime
        
        # Convert Quiz objects to dicts
        quiz_responses = []
        for q in quizzes:
            try:
                if isinstance(q, dict):
                    # Already a dict from database
                    quiz_dict = {
                        "id": str(q.get("_id", "")),
                        "title": q.get("title", ""),
                        "chapter": q.get("chapter", ""),
                        "chapter_number": q.get("chapter_number"),
                        "quiz_type": q.get("quiz_type", ""),
                        "total_marks": q.get("total_marks", 0),
                        "questions_count": len(q.get("questions", [])),
                        "time_limit": q.get("time_limit"),
                        "created_at": q.get("created_at", datetime.utcnow())
                    }
                else:
                    # Quiz model object
                    quiz_dict = {
                        "id": str(q._id if hasattr(q, '_id') else q.id),
                        "title": q.title or "",
                        "chapter": q.chapter or "",
                        "chapter_number": getattr(q, 'chapter_number', None),
                        "quiz_type": q.quiz_type or "",
                        "total_marks": q.total_marks or 0,
                        "questions_count": len(q.questions or []),
                        "time_limit": getattr(q, 'time_limit', None),
                        "created_at": q.created_at or datetime.utcnow()
                    }
                print(f"✓ Converted quiz: {quiz_dict.get('id')} - {quiz_dict.get('title')}")
                quiz_responses.append(quiz_dict)
            except Exception as e:
                print(f"✗ Error converting quiz: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"Total quizzes: {len(quiz_responses)}")
        if quiz_responses:
            print(f"First quiz keys: {list(quiz_responses[0].keys())}")
        
        return {
            "quizzes": quiz_responses,
            "total": len(quiz_responses)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{quiz_id}/submit", response_model=QuizResultResponse)
async def submit_quiz(
    quiz_id: str,
    request: QuizSubmitRequest,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Submit quiz answers.
    
    Automatically evaluates answers and stores results.
    
    Args:
        quiz_id: Quiz ID
        request: Submitted answers with start time
        
    Returns:
        Quiz results with scoring
    """
    try:
        quiz_obj_id = ObjectId(quiz_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid quiz ID format"
        )
    
    try:
        # Build QuizSubmission object for service
        from app.core.models.quiz import QuizSubmission
        
        # Debug: Log received answers
        print(f"📝 Received quiz submission:")
        print(f"   quiz_id: {quiz_id}")
        print(f"   answers: {request.answers}")
        print(f"   started_at: {request.started_at}")
        
        submission = QuizSubmission(
            quiz_id=quiz_id,
            answers=request.answers,
            time_taken=None
        )
        
        # Submit quiz
        result = await QuizService.submit_quiz(
            user_id=user_id,
            submission=submission,
            started_at=request.started_at
        )
        
        # Generate feedback for the quiz result
        try:
            await FeedbackService.generate_feedback(
                user_id=user_id,
                result_id=ObjectId(str(result.id))
            )
            print(f"✅ Feedback generated for result: {result.id}")
        except Exception as feedback_err:
            print(f"⚠️ Could not generate feedback: {str(feedback_err)}")
            # Don't fail the endpoint if feedback generation fails
        
        # Convert question results
        question_results = [
            {
                "question_id": str(qr.question_id),
                "question_number": qr.question_number,
                "question_text": qr.question_text,
                "user_answer": qr.user_answer,
                "correct_answer": qr.correct_answer,
                "is_correct": qr.is_correct,
                "marks_obtained": qr.marks_awarded,
                "marks_possible": qr.max_marks,
                "explanation": qr.explanation if hasattr(qr, 'explanation') else "",
                "concepts": qr.concepts_tested if hasattr(qr, 'concepts_tested') else []
            }
            for qr in result.question_results
        ]
        
        return QuizResultResponse(
            id=str(result.id),
            quiz_id=str(result.quiz_id),
            subject_id=str(result.subject_id),
            score=result.score,
            max_score=result.max_score,
            percentage=result.percentage,
            passed=result.passed,
            time_taken_seconds=result.time_taken_seconds if hasattr(result, 'time_taken_seconds') else int(result.time_taken * 60) if hasattr(result, 'time_taken') else 0,
            question_results=question_results,
            strengths=result.strengths if hasattr(result, 'strengths') else [],
            weak_areas=result.weak_areas if hasattr(result, 'weak_areas') else [],
            completed_at=result.completed_at if hasattr(result, 'completed_at') else None
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{quiz_id}/result", response_model=QuizResultResponse)
async def get_quiz_result(
    quiz_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Get the most recent result for a specific quiz.
    
    Args:
        quiz_id: Quiz ID
        
    Returns:
        Most recent quiz result for this quiz
    """
    try:
        quiz_obj_id = ObjectId(quiz_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid quiz ID format"
        )
    
    try:
        # Get the most recent result for this quiz
        results = await QuizService.list_quiz_results(
            user_id=user_id,
            quiz_id=quiz_obj_id,
            limit=1
        )
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No results found for this quiz"
            )
        
        result = results[0]
        
        # Convert question results
        question_results = [
            {
                "question_id": str(qr.question_id),
                "question_number": qr.question_number,
                "question_text": qr.question_text,
                "user_answer": qr.user_answer,
                "correct_answer": qr.correct_answer,
                "is_correct": qr.is_correct,
                "marks_obtained": qr.marks_awarded,
                "marks_possible": qr.max_marks,
                "explanation": qr.explanation if hasattr(qr, 'explanation') else "",
                "concepts": qr.concepts_tested if hasattr(qr, 'concepts_tested') else []
            }
            for qr in result.question_results
        ]
        
        return QuizResultResponse(
            id=str(result.id),
            quiz_id=str(result.quiz_id),
            subject_id=str(result.subject_id),
            score=result.score,
            max_score=result.max_score,
            percentage=result.percentage,
            passed=result.passed,
            time_taken_seconds=result.time_taken_seconds if hasattr(result, 'time_taken_seconds') else int(result.time_taken * 60) if hasattr(result, 'time_taken') else 0,
            question_results=question_results,
            strengths=result.strengths if hasattr(result, 'strengths') else [],
            weak_areas=result.weak_areas if hasattr(result, 'weak_areas') else [],
            completed_at=result.completed_at if hasattr(result, 'completed_at') else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{subject_id}/results", response_model=QuizResultListResponse)
async def get_quiz_results(
    subject_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Get all quiz results for a subject.
    
    Args:
        subject_id: Subject ID
        
    Returns:
        List of quiz results
    """
    try:
        subject_obj_id = ObjectId(subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        results = await QuizService.list_quiz_results(
            user_id=user_id,
            subject_id=subject_obj_id
        )
        
        result_responses = []
        for r in results:
            # Fetch quiz to get title
            quiz = await QuizService.get_quiz_by_id(
                user_id=user_id,
                quiz_id=ObjectId(r.quiz_id)
            )
            quiz_title = quiz.title if quiz else "Quiz"
            
            result_responses.append({
                "id": str(r.id),
                "quiz_id": str(r.quiz_id),
                "quiz_title": quiz_title,
                "score": r.score,
                "max_score": r.max_score,
                "percentage": r.percentage,
                "passed": r.passed,
                "completed_at": r.completed_at
            })
        
        return QuizResultListResponse(
            results=result_responses,
            total=len(result_responses)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{subject_id}/statistics", response_model=QuizStatisticsResponse)
async def get_quiz_statistics(
    subject_id: str,
    user_id: ObjectId = Depends(get_user_id)
):
    """
    Get quiz performance statistics for a subject.
    
    Args:
        subject_id: Subject ID
        
    Returns:
        Aggregated statistics
    """
    try:
        subject_obj_id = ObjectId(subject_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subject ID format"
        )
    
    try:
        stats = await QuizService.get_quiz_statistics(
            user_id=user_id,
            subject_id=subject_obj_id
        )
        
        return QuizStatisticsResponse(**stats)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
