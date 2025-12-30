# backend/app/services/quiz_service.py

"""
QuizService - Complete quiz lifecycle management.

Responsibilities:
- Generate and store quizzes (from Quiz Agent output)
- Fetch quizzes by various criteria
- Accept user submissions
- Evaluate answers (scoring, correctness)
- Store quiz results with concept analysis
- Integrate with Quiz Agent for generation

Focus: Quiz lifecycle + scoring
"""

from datetime import datetime
from bson import ObjectId
from typing import List, Optional, Dict

from app.core.database import db
from app.core.models.quiz import (
    Quiz, QuizQuestion, QuizResult, QuestionResult,
    QuizSubmission, QuizAttemptCreate
)


class QuizService:
    """
    Quiz lifecycle management service.
    
    Workflow:
    1. Quiz Agent generates quiz → store_quiz()
    2. User starts quiz → get_quiz_by_id()
    3. User submits answers → submit_quiz()
    4. System evaluates → _evaluate_submission()
    5. Results stored → QuizResult
    6. FeedbackService processes results
    """
    
    # ============================
    # CREATE / STORE QUIZ
    # ============================
    
    @staticmethod
    async def create_quiz(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        subject_name: str,
        chapter_number: Optional[int],
        chapter_title: str,
        quiz_data: Dict,
        quiz_metadata: Optional[Dict] = None,
        quiz_type: str = "practice",
        session_id: Optional[ObjectId] = None,
        time_limit: Optional[int] = None,
        pass_percentage: float = 60.0
    ) -> Quiz:
        """
        Create and store a quiz (API wrapper).
        
        Called by API endpoint after quiz generation.
        Handles both old format (quiz_data as list) and new format (quiz_data as dict).
        
        Args:
            user_id: User ID
            subject_id: Subject ID
            subject_name: Subject name
            chapter_number: Chapter number
            chapter_title: Chapter title
            quiz_data: Generated quiz data from agent
                Can be:
                - List of questions (from agent "quiz" field)
                - Dict with "title", "questions", "total_marks", "topic"
            quiz_metadata: Optional metadata dict from agent
                {"title": "...", "topic": "...", "total_marks": int, "total_questions": int}
            quiz_type: "practice" | "revision" | "mock_exam"
            session_id: Optional study session ID
            time_limit: Optional time limit in minutes
            pass_percentage: Pass threshold percentage
        """
        # Handle case where quiz_data is a list of questions (from agent output)
        if isinstance(quiz_data, list):
            questions = quiz_data
            # Use metadata if provided, otherwise construct defaults
            if quiz_metadata:
                title = quiz_metadata.get("title", f"{quiz_type.title()} Quiz")
                topic = quiz_metadata.get("topic", chapter_title)
                total_marks = quiz_metadata.get("total_marks", len(questions))
            else:
                title = f"{quiz_type.title()} Quiz"
                topic = chapter_title
                total_marks = len(questions)
        else:
            # quiz_data is already a dict
            questions = quiz_data.get("questions", [])
            title = quiz_data.get("title", f"{quiz_type.title()} Quiz")
            topic = quiz_data.get("topic", chapter_title)
            total_marks = quiz_data.get("total_marks", len(questions))
        
        # Ensure subject_name is not None or empty
        if not subject_name or subject_name == "Unknown":
            # Try to fetch from database
            from app.services.subject_service import SubjectService
            try:
                subject = await SubjectService.get_subject_by_id(
                    user_id=user_id,
                    subject_id=subject_id
                )
                subject_name = subject.subject_name if subject else "Unknown Subject"
            except:
                subject_name = "Unknown Subject"
        
        return await QuizService.store_quiz(
            user_id=user_id,
            subject_id=subject_id,
            subject=subject_name,
            chapter=chapter_title,
            chapter_number=chapter_number,
            title=title,
            description=f"Quiz: {topic}",
            questions=questions,
            quiz_type=quiz_type,
            session_id=session_id,
            time_limit=time_limit,
            pass_percentage=pass_percentage,
            source_content=None
        )
    
    @staticmethod
    async def store_quiz(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        subject: str,
        chapter: str,
        chapter_number: Optional[int],
        title: str,
        description: str,
        questions: List[Dict],  # From Quiz Agent
        quiz_type: str = "practice",
        session_id: Optional[ObjectId] = None,
        time_limit: Optional[int] = None,
        pass_percentage: float = 60.0,
        source_content: Optional[str] = None
    ) -> Quiz:
        """
        Store a generated quiz in MongoDB.
        
        Called by Quiz Agent after quiz generation.
        
        Args:
            questions: List of dicts from Quiz Agent output
                [{
                    "question_number": 1,
                    "question_text": "...",
                    "question_type": "mcq",
                    "options": [...],
                    "correct_answer": "...",
                    "explanation": "...",
                    "marks": 1,
                    "concepts": ["..."]
                }]
        """
        quizzes_col = db.quizzes()
        
        # Convert dict questions to QuizQuestion models
        quiz_questions = []
        total_marks = 0
        
        for q in questions:
            question = QuizQuestion(
                question_id=ObjectId(),
                question_number=q.get("question_number", len(quiz_questions) + 1),
                text=q.get("question_text", q.get("text", "")),
                question_type=q.get("question_type", "mcq"),
                options=q.get("options", []),
                correct_answer=q.get("correct_answer", ""),
                explanation=q.get("explanation", ""),
                difficulty=q.get("difficulty", "medium"),
                marks=q.get("marks", 1),
                concepts=q.get("concepts", []),
                learning_objectives=q.get("objectives", q.get("learning_objectives", []))
            )
            quiz_questions.append(question)
            total_marks += question.marks
        
        # Create quiz document
        quiz_doc = {
            "user_id": user_id,
            "subject_id": subject_id,
            "session_id": session_id,
            "subject": subject,
            "chapter": chapter,
            "chapter_number": chapter_number,
            "title": title,
            "description": description,
            "quiz_type": quiz_type,
            "questions": [q.model_dump() for q in quiz_questions],
            "total_marks": total_marks,
            "time_limit": time_limit,
            "pass_percentage": pass_percentage,
            "generated_by": "quiz_agent",
            "source_content": source_content,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await quizzes_col.insert_one(quiz_doc)
        quiz_doc["_id"] = result.inserted_id
        
        return Quiz(**quiz_doc)
    
    # ============================
    # FETCH QUIZZES
    # ============================
    
    @staticmethod
    async def get_quiz_by_id(
        *,
        user_id: ObjectId,
        quiz_id: ObjectId
    ) -> Optional[Quiz]:
        """
        Retrieve quiz by ID (ownership enforced).
        """
        quizzes_col = db.quizzes()
        
        doc = await quizzes_col.find_one({
            "_id": quiz_id,
            "user_id": user_id
        })
        
        return Quiz(**doc) if doc else None
    
    @staticmethod
    async def list_quizzes_by_subject(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        chapter_number: Optional[int] = None,
        quiz_type: Optional[str] = None
    ) -> List[Quiz]:
        """
        List all quizzes for a subject.
        
        Optional filters:
        - chapter_number: specific chapter
        - quiz_type: "practice" | "revision" | "mock_exam"
        """
        quizzes_col = db.quizzes()
        
        query = {
            "user_id": user_id,
            "subject_id": subject_id,
            "is_active": True
        }
        
        if chapter_number is not None:
            query["chapter_number"] = chapter_number
        
        if quiz_type:
            query["quiz_type"] = quiz_type
        
        cursor = quizzes_col.find(query).sort("created_at", -1)
        docs = await cursor.to_list(None)
        
        return [Quiz(**doc) for doc in docs]
    
    @staticmethod
    async def list_quizzes_by_session(
        *,
        user_id: ObjectId,
        session_id: ObjectId
    ) -> List[Quiz]:
        """
        List all quizzes for a study session.
        """
        quizzes_col = db.quizzes()
        
        cursor = quizzes_col.find({
            "user_id": user_id,
            "session_id": session_id
        }).sort("created_at", -1)
        
        docs = await cursor.to_list(None)
        return [Quiz(**doc) for doc in docs]
    
    # ============================
    # SUBMIT & EVALUATE QUIZ
    # ============================
    
    @staticmethod
    async def submit_quiz(
        *,
        user_id: ObjectId,
        submission: QuizSubmission,
        started_at: datetime
    ) -> QuizResult:
        """
        Accept user submission and evaluate answers.
        
        Process:
        1. Fetch quiz
        2. Evaluate each answer
        3. Calculate score
        4. Analyze concepts
        5. Store result
        6. Return QuizResult
        
        Args:
            submission: User's answers {question_number → answer}
            started_at: When user started the quiz
        """
        quiz_id = ObjectId(submission.quiz_id)
        
        # Fetch quiz
        quiz = await QuizService.get_quiz_by_id(
            user_id=user_id,
            quiz_id=quiz_id
        )
        
        if not quiz:
            raise ValueError("Quiz not found")
        
        # Evaluate submission
        evaluation = await QuizService._evaluate_submission(
            quiz=quiz,
            user_answers=submission.answers
        )
        
        # Calculate time taken
        completed_at = datetime.utcnow()
        time_taken = (completed_at - started_at).total_seconds() / 60  # Minutes
        
        # Determine pass/fail
        percentage = evaluation["percentage"]
        passed = percentage >= quiz.pass_percentage
        
        # Store result
        results_col = db.quiz_results()
        
        result_doc = {
            "user_id": user_id,
            "quiz_id": quiz_id,
            "subject_id": quiz.subject_id,
            "session_id": quiz.session_id,
            
            "score": evaluation["score"],
            "max_score": evaluation["max_score"],
            "percentage": percentage,
            "passed": passed,
            
            "question_results": evaluation["question_results"],
            
            "correct_count": evaluation["correct_count"],
            "incorrect_count": evaluation["incorrect_count"],
            "skipped_count": evaluation["skipped_count"],
            
            "started_at": started_at,
            "completed_at": completed_at,
            "time_taken": time_taken,
            
            "concept_scores": evaluation["concept_scores"],
            "strengths": evaluation["strengths"],
            "weak_areas": evaluation["weak_areas"],
            
            "feedback_generated": False,
            "created_at": datetime.utcnow()
        }
        
        insert_result = await results_col.insert_one(result_doc)
        result_doc["_id"] = insert_result.inserted_id
        
        return QuizResult(**result_doc)
    
    @staticmethod
    async def _evaluate_submission(
        *,
        quiz: Quiz,
        user_answers: Dict[str, str]  # question_number → answer
    ) -> Dict:
        """
        Evaluate user's answers against correct answers.
        
        Returns:
        {
            "score": float,
            "max_score": float,
            "percentage": float,
            "correct_count": int,
            "incorrect_count": int,
            "skipped_count": int,
            "question_results": [...],
            "concept_scores": {...},
            "strengths": [...],
            "weak_areas": [...]
        }
        """
        question_results = []
        score = 0.0
        max_score = 0.0
        correct_count = 0
        incorrect_count = 0
        skipped_count = 0
        
        # Track concept performance
        concept_correct = {}  # concept → correct_count
        concept_total = {}    # concept → total_count
        
        for question in quiz.questions:
            q_num = str(question["question_number"])
            user_answer = user_answers.get(q_num, "").strip()
            correct_answer = question["correct_answer"].strip()
            
            # Check correctness
            is_correct = user_answer.lower() == correct_answer.lower()
            
            marks_awarded = question["marks"] if is_correct else 0.0
            score += marks_awarded
            max_score += question["marks"]
            
            if not user_answer:
                skipped_count += 1
            elif is_correct:
                correct_count += 1
            else:
                incorrect_count += 1
            
            # Track concept performance
            concepts = question.get("concepts", [])
            for concept in concepts:
                if concept not in concept_total:
                    concept_total[concept] = 0
                    concept_correct[concept] = 0
                
                concept_total[concept] += 1
                if is_correct:
                    concept_correct[concept] += 1
            
            # Store question result
            question_results.append({
                "question_id": question["question_id"],
                "question_number": question["question_number"],
                "question_text": question["text"],
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "marks_awarded": marks_awarded,
                "max_marks": question["marks"],
                "concepts_tested": concepts
            })
        
        # Calculate concept scores
        concept_scores = {}
        strengths = []
        weak_areas = []
        
        for concept, total in concept_total.items():
            correct = concept_correct[concept]
            accuracy = (correct / total * 100) if total > 0 else 0
            concept_scores[concept] = accuracy
            
            if accuracy >= 80:
                strengths.append(concept)
            elif accuracy < 60:
                weak_areas.append(concept)
        
        percentage = (score / max_score * 100) if max_score > 0 else 0
        
        return {
            "score": score,
            "max_score": max_score,
            "percentage": round(percentage, 2),
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "skipped_count": skipped_count,
            "question_results": question_results,
            "concept_scores": concept_scores,
            "strengths": strengths,
            "weak_areas": weak_areas
        }
    
    # ============================
    # GET QUIZ RESULTS
    # ============================
    
    @staticmethod
    async def get_quiz_result(
        *,
        user_id: ObjectId,
        result_id: ObjectId
    ) -> Optional[QuizResult]:
        """
        Retrieve quiz result by ID.
        """
        results_col = db.quiz_results()
        
        doc = await results_col.find_one({
            "_id": result_id,
            "user_id": user_id
        })
        
        return QuizResult(**doc) if doc else None
    
    @staticmethod
    async def list_quiz_results(
        *,
        user_id: ObjectId,
        subject_id: Optional[ObjectId] = None,
        quiz_id: Optional[ObjectId] = None,
        limit: int = 50
    ) -> List[QuizResult]:
        """
        List quiz results with optional filters.
        """
        results_col = db.quiz_results()
        
        query = {"user_id": user_id}
        
        if subject_id:
            query["subject_id"] = subject_id
        
        if quiz_id:
            query["quiz_id"] = quiz_id
        
        cursor = results_col.find(query).sort("completed_at", -1).limit(limit)
        docs = await cursor.to_list(None)
        
        return [QuizResult(**doc) for doc in docs]
    
    # ============================
    # STATISTICS
    # ============================
    
    @staticmethod
    async def get_quiz_statistics(
        *,
        user_id: ObjectId,
        subject_id: ObjectId
    ) -> Dict:
        """
        Get aggregated quiz statistics for a subject.
        
        Returns:
        {
            "total_quizzes": int,
            "total_attempts": int,
            "average_score": float,
            "highest_score": float,
            "pass_rate": float
        }
        """
        results_col = db.quiz_results()
        
        cursor = results_col.find({
            "user_id": user_id,
            "subject_id": subject_id
        })
        
        results = await cursor.to_list(None)
        
        if not results:
            return {
                "total_quizzes": 0,
                "total_attempts": 0,
                "average_score": 0.0,
                "highest_score": 0.0,
                "pass_rate": 0.0
            }
        
        total_attempts = len(results)
        total_score = sum(r["percentage"] for r in results)
        passed_count = sum(1 for r in results if r["passed"])
        
        return {
            "total_quizzes": len(set(r["quiz_id"] for r in results)),
            "total_attempts": total_attempts,
            "average_score": round(total_score / total_attempts, 2),
            "highest_score": round(max(r["percentage"] for r in results), 2),
            "pass_rate": round((passed_count / total_attempts * 100), 2)
        }