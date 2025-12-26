# backend/app/services/feedback_service.py

"""
FeedbackService - Learning insights and personalization.

Responsibilities:
- Analyze quiz performance
- Generate personalized feedback
- Recommend revision content
- Update user learning profile
- Notify Study Plan Agent for adaptation
- Provide motivational guidance

Focus: Learning insights + personalization
"""

from datetime import datetime, timedelta
from bson import ObjectId
from typing import List, Optional, Dict

from app.core.database import db
from app.core.models.feedback import (
    FeedbackReport, ConceptAnalysis, RevisionItem,
    LearningInsight, FeedbackSummary
)
from app.core.models.quiz import QuizResult
from app.core.models.user import SubjectProfile, LearningProfile
from app.services.quiz_service import QuizService
from app.services.planner_service import PlannerService
from app.services.retrieval import RetrievalService


class FeedbackService:
    """
    Feedback and learning analytics service.
    
    Workflow:
    1. Quiz completed → generate_feedback()
    2. Analyze performance → _analyze_concepts()
    3. Generate insights → _generate_insights()
    4. Create revision plan → _create_revision_plan()
    5. Update user profile → _update_user_profile()
    6. Notify planner → _notify_planner_agent()
    7. Store feedback report
    """
    
    # ============================
    # GENERATE FEEDBACK
    # ============================
    
    @staticmethod
    async def generate_feedback(
        *,
        user_id: ObjectId,
        result_id: ObjectId
    ) -> FeedbackReport:
        """
        Generate comprehensive feedback from quiz result.
        
        This is the main entry point called after quiz completion.
        
        Process:
        1. Fetch quiz result
        2. Analyze concept mastery
        3. Generate insights
        4. Create revision plan
        5. Update user profile
        6. Notify planner if needed
        7. Store feedback
        """
        # Fetch quiz result
        quiz_result = await QuizService.get_quiz_result(
            user_id=user_id,
            result_id=result_id
        )
        
        if not quiz_result:
            raise ValueError("Quiz result not found")
        
        # Fetch quiz details
        quiz = await QuizService.get_quiz_by_id(
            user_id=user_id,
            quiz_id=quiz_result.quiz_id
        )
        
        if not quiz:
            raise ValueError("Quiz not found")
        
        # Get planner context
        planner_context = await FeedbackService._get_planner_context(
            user_id=user_id,
            subject_id=quiz_result.subject_id
        )
        
        # -------------------------
        # 1️⃣ Analyze Concepts
        # -------------------------
        concept_analysis = FeedbackService._analyze_concepts(quiz_result)
        
        # -------------------------
        # 2️⃣ Generate Insights
        # -------------------------
        insights = FeedbackService._generate_insights(
            quiz_result=quiz_result,
            concept_analysis=concept_analysis,
            planner_context=planner_context
        )
        
        # -------------------------
        # 3️⃣ Create Revision Plan
        # -------------------------
        revision_plan = await FeedbackService._create_revision_plan(
            user_id=user_id,
            subject_id=quiz_result.subject_id,
            weak_concepts=quiz_result.weak_areas,
            quiz=quiz
        )
        
        # -------------------------
        # 4️⃣ Determine Performance Level
        # -------------------------
        percentage = quiz_result.percentage
        
        if percentage >= 80:
            performance_level = "excellent"
            motivational_message = f"🎉 Outstanding work! You scored {percentage:.1f}%! Your understanding is strong."
            encouragement = "Keep up this excellent performance!"
        elif percentage >= 60:
            performance_level = "good"
            motivational_message = f"👍 Good job! You scored {percentage:.1f}%. You're on the right track."
            encouragement = "Focus on the weak areas to reach excellence!"
        else:
            performance_level = "needs_improvement"
            motivational_message = f"💪 You scored {percentage:.1f}%. Don't be discouraged—learning takes time!"
            encouragement = "Review the concepts below and try again. You've got this!"
        
        # -------------------------
        # 5️⃣ Determine Next Steps
        # -------------------------
        next_steps = []
        
        if quiz_result.weak_areas:
            next_steps.append(f"Review these concepts: {', '.join(quiz_result.weak_areas[:3])}")
        
        next_steps.append("Practice more questions on weak areas")
        
        if planner_context:
            next_chapter = planner_context.get("current_chapter", 0) + 1
            next_steps.append(f"Continue to Chapter {next_chapter}")
        
        # -------------------------
        # 6️⃣ Create Feedback Report
        # -------------------------
        feedback_col = db.feedback_reports()
        
        feedback_doc = {
            "user_id": user_id,
            "quiz_result_id": result_id,
            "quiz_id": quiz_result.quiz_id,
            "subject_id": quiz_result.subject_id,
            "session_id": quiz_result.session_id,
            
            "assessment_type": quiz.quiz_type,
            
            "score": quiz_result.score,
            "max_score": quiz_result.max_score,
            "percentage": quiz_result.percentage,
            "performance_level": performance_level,
            
            "performance_summary": FeedbackService._generate_performance_summary(
                quiz_result, concept_analysis
            ),
            
            "strengths": quiz_result.strengths,
            "strength_details": [
                ca.model_dump() for ca in concept_analysis
                if ca.mastery_level == "strong"
            ],
            
            "weak_areas": quiz_result.weak_areas,
            "weakness_details": [
                ca.model_dump() for ca in concept_analysis
                if ca.mastery_level == "needs_attention"
            ],
            
            "revision_tips": FeedbackService._generate_revision_tips(quiz_result.weak_areas),
            "revision_items": [r.model_dump() for r in revision_plan],
            "estimated_revision_time": sum(r.estimated_time or 0 for r in revision_plan) / 60,  # Hours
            
            "recommended_resources": [],  # Populated by retrieval
            "recommended_chapters": [quiz.chapter_number] if quiz.chapter_number else [],
            
            "insights": [i.model_dump() for i in insights],
            
            "motivational_message": motivational_message,
            "encouragement": encouragement,
            
            "overall_progress": planner_context,
            "progress_change": FeedbackService._determine_progress_change(
                quiz_result.percentage
            ),
            
            "next_steps": next_steps,
            "suggested_next_topic": None,  # Can be set based on plan
            
            "study_plan_updated": False,  # Will be updated if planner notified
            "schedule_adjustments": [],
            
            "generated_by": "feedback_agent",
            "processing_time": None,
            "created_at": datetime.utcnow()
        }
        
        insert_result = await feedback_col.insert_one(feedback_doc)
        feedback_doc["_id"] = insert_result.inserted_id
        
        feedback = FeedbackReport(**feedback_doc)
        
        # -------------------------
        # 7️⃣ Update User Profile
        # -------------------------
        await FeedbackService._update_user_profile(
            user_id=user_id,
            subject_id=quiz_result.subject_id,
            quiz_result=quiz_result,
            feedback=feedback
        )
        
        # -------------------------
        # 8️⃣ Notify Planner (if needed)
        # -------------------------
        if quiz_result.percentage < 60:  # Poor performance
            await FeedbackService._notify_planner_agent(
                user_id=user_id,
                subject_id=quiz_result.subject_id,
                weak_areas=quiz_result.weak_areas
            )
        
        # Mark quiz result as feedback generated
        results_col = db.quiz_results()
        await results_col.update_one(
            {"_id": result_id},
            {"$set": {"feedback_generated": True}}
        )
        
        return feedback
    
    # ============================
    # CONCEPT ANALYSIS
    # ============================
    
    @staticmethod
    def _analyze_concepts(quiz_result: QuizResult) -> List[ConceptAnalysis]:
        """
        Analyze mastery level for each concept.
        
        Returns list of ConceptAnalysis objects.
        """
        analyses = []
        
        for concept, accuracy in quiz_result.concept_scores.items():
            # Count questions on this concept
            questions_on_concept = sum(
                1 for qr in quiz_result.question_results
                if concept in qr.get("concepts_tested", [])
            )
            
            correct_answers = int(questions_on_concept * accuracy / 100)
            
            # Determine mastery level
            if accuracy >= 80:
                mastery_level = "strong"
                suggestion = f"Excellent grasp of {concept}! Keep practicing to maintain."
            elif accuracy >= 60:
                mastery_level = "developing"
                suggestion = f"Good understanding of {concept}. More practice will strengthen it."
            else:
                mastery_level = "needs_attention"
                suggestion = f"Review {concept} thoroughly. Focus on fundamentals."
            
            needs_revision = accuracy < 60
            
            analyses.append(ConceptAnalysis(
                concept=concept,
                questions_on_concept=questions_on_concept,
                correct_answers=correct_answers,
                accuracy_percentage=accuracy,
                mastery_level=mastery_level,
                needs_revision=needs_revision,
                suggestion=suggestion
            ))
        
        return analyses
    
    # ============================
    # INSIGHTS GENERATION
    # ============================
    
    @staticmethod
    def _generate_insights(
        *,
        quiz_result: QuizResult,
        concept_analysis: List[ConceptAnalysis],
        planner_context: Optional[Dict]
    ) -> List[LearningInsight]:
        """
        Generate actionable learning insights.
        """
        insights = []
        
        # Insight 1: Strengths
        if quiz_result.strengths:
            insights.append(LearningInsight(
                insight_type="strength",
                title="Your Strengths",
                description=f"You're excelling in: {', '.join(quiz_result.strengths[:3])}",
                action_items=[
                    "Continue practicing these concepts",
                    "Help others who struggle with these topics"
                ]
            ))
        
        # Insight 2: Weaknesses
        if quiz_result.weak_areas:
            insights.append(LearningInsight(
                insight_type="weakness",
                title="Areas for Improvement",
                description=f"Focus needed on: {', '.join(quiz_result.weak_areas[:3])}",
                action_items=[
                    "Review notes for these concepts",
                    "Practice more questions",
                    "Ask for help if stuck"
                ]
            ))
        
        # Insight 3: Progress pattern
        if planner_context:
            completed = planner_context.get("completed_chapters", 0)
            total = planner_context.get("total_chapters", 1)
            progress_percent = (completed / total * 100) if total > 0 else 0
            
            insights.append(LearningInsight(
                insight_type="pattern",
                title="Overall Progress",
                description=f"You've completed {completed}/{total} chapters ({progress_percent:.1f}%)",
                action_items=[
                    f"Continue to Chapter {completed + 1}",
                    "Maintain consistent study pace"
                ]
            ))
        
        return insights
    
    # ============================
    # REVISION PLAN
    # ============================
    
    @staticmethod
    async def _create_revision_plan(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        weak_concepts: List[str],
        quiz: "Quiz"
    ) -> List[RevisionItem]:
        """
        Create targeted revision plan based on weak concepts.
        
        Links to actual content from notes (via RetrievalService).
        """
        if not weak_concepts:
            return []
        
        revision_items = []
        retrieval_service = RetrievalService()
        
        for concept in weak_concepts[:5]:  # Top 5 weak concepts
            # Try to find relevant content
            try:
                results = retrieval_service.query(
                    question=f"Content about {concept}",
                    user_id=str(user_id),
                    chapter=str(quiz.chapter_number) if quiz.chapter_number else None,
                    k=1
                )
                
                source_file = results[0]["metadata"].get("source_file") if results else None
            except:
                source_file = None
            
            # Determine priority
            priority = "high"  # All weak areas are high priority
            
            # Estimate time
            estimated_time = 20  # 20 minutes per concept
            
            revision_items.append(RevisionItem(
                concept=concept,
                reason=f"Accuracy below 60% on this concept",
                priority=priority,
                source_file=source_file,
                chapter_number=quiz.chapter_number,
                section=None,
                estimated_time=estimated_time,
                recommended_approach="review_notes"
            ))
        
        return revision_items
    
    # ============================
    # HELPER METHODS
    # ============================
    
    @staticmethod
    async def _get_planner_context(
        *,
        user_id: ObjectId,
        subject_id: ObjectId
    ) -> Optional[Dict]:
        """Get current progress from PlannerService."""
        try:
            planner = await PlannerService.get_planner_state(
                user_id=user_id,
                subject_id=subject_id
            )
            
            if planner:
                return {
                    "total_chapters": planner.total_chapters,
                    "completed_chapters": len(planner.completed_chapters),
                    "current_chapter": planner.current_chapter,
                    "completion_percent": planner.completion_percent
                }
        except:
            pass
        
        return None
    
    @staticmethod
    def _generate_performance_summary(
        quiz_result: QuizResult,
        concept_analysis: List[ConceptAnalysis]
    ) -> str:
        """Generate overall performance summary."""
        percentage = quiz_result.percentage
        
        if percentage >= 80:
            return f"Excellent performance! You demonstrated strong understanding across {len(concept_analysis)} concepts."
        elif percentage >= 60:
            return f"Good effort! You showed competence in most areas, with room for improvement in {len(quiz_result.weak_areas)} concepts."
        else:
            return f"This quiz highlighted {len(quiz_result.weak_areas)} areas that need more attention. Don't worry—focused revision will help!"
    
    @staticmethod
    def _generate_revision_tips(weak_areas: List[str]) -> List[str]:
        """Generate specific revision tips."""
        if not weak_areas:
            return ["Keep practicing to maintain your strong performance!"]
        
        tips = [
            f"Review fundamentals of: {', '.join(weak_areas[:3])}",
            "Read through your notes for these concepts",
            "Practice additional questions on these topics",
            "Create summary notes in your own words",
            "Teach these concepts to someone else"
        ]
        
        return tips[:5]
    
    @staticmethod
    def _determine_progress_change(percentage: float) -> str:
        """Determine if performance is improving/stable/declining."""
        # This would ideally compare with previous attempts
        # For now, simplified
        if percentage >= 70:
            return "improving"
        elif percentage >= 50:
            return "stable"
        else:
            return "declining"
    
    # ============================
    # USER PROFILE UPDATE
    # ============================
    
    @staticmethod
    async def _update_user_profile(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        quiz_result: QuizResult,
        feedback: FeedbackReport
    ):
        """
        Update user's learning profile with quiz results.
        
        Updates:
        - Subject profile (strengths, weaknesses, concept mastery)
        - Overall statistics
        """
        users_col = db.users()
        
        # This would update the user's learning_profile
        # Simplified version:
        await users_col.update_one(
            {"_id": user_id},
            {
                "$inc": {
                    "learning_profile.total_quizzes_completed": 1
                },
                "$set": {
                    "learning_profile.last_active": datetime.utcnow()
                }
            }
        )
    
    # ============================
    # NOTIFY PLANNER
    # ============================
    
    @staticmethod
    async def _notify_planner_agent(
        *,
        user_id: ObjectId,
        subject_id: ObjectId,
        weak_areas: List[str]
    ):
        """
        Notify Study Plan Agent to adjust schedule based on weak areas.
        
        Could trigger auto-replanning or schedule adjustment.
        """
        # This could:
        # 1. Add extra revision sessions
        # 2. Slow down pace on difficult chapters
        # 3. Suggest review before moving forward
        
        # For now, just log
        print(f"📢 Planner notified: User {user_id} needs revision on {weak_areas}")
    
    # ============================
    # GET FEEDBACK
    # ============================
    
    @staticmethod
    async def get_feedback_by_result(
        *,
        user_id: ObjectId,
        result_id: ObjectId
    ) -> Optional[FeedbackReport]:
        """Retrieve feedback for a quiz result."""
        feedback_col = db.feedback_reports()
        
        doc = await feedback_col.find_one({
            "user_id": user_id,
            "quiz_result_id": result_id
        })
        
        return FeedbackReport(**doc) if doc else None
    
    @staticmethod
    async def list_feedback_reports(
        *,
        user_id: ObjectId,
        subject_id: Optional[ObjectId] = None,
        limit: int = 20
    ) -> List[FeedbackReport]:
        """List recent feedback reports."""
        feedback_col = db.feedback_reports()
        
        query = {"user_id": user_id}
        if subject_id:
            query["subject_id"] = subject_id
        
        cursor = feedback_col.find(query).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(None)
        
        return [FeedbackReport(**doc) for doc in docs]