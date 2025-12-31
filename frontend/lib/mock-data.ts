// 🎭 MOCK DATA LAYER - FOR UI DEMO ONLY
// This file contains all mock/dummy data to replace backend API calls
// All functions are tagged with [MOCK] for easy identification

// Simulate API delay for realistic UI experience
const mockDelay = (ms = 500) => new Promise((resolve) => setTimeout(resolve, ms))

// Mock user data
const MOCK_USER = {
  id: "user-demo-123",
  email: "demo@agented.com",
  name: "Demo Student",
  created_at: "2024-01-15T10:00:00Z",
}

// Mock subjects data
const MOCK_SUBJECTS = [
  {
    id: "subj-1",
    user_id: "user-demo-123",
    name: "Advanced Mathematics",
    difficulty: "hard",
    hours_per_week: 10,
    target_date: "2024-06-30",
    syllabus_file: "calculus_syllabus.pdf",
    chapters_count: 12,
    completed_chapters: 5,
    progress: 42,
    created_at: "2024-01-20T10:00:00Z",
  },
  {
    id: "subj-2",
    user_id: "user-demo-123",
    name: "Computer Science Fundamentals",
    difficulty: "medium",
    hours_per_week: 8,
    target_date: "2024-07-15",
    syllabus_file: "cs_fundamentals.pdf",
    chapters_count: 10,
    completed_chapters: 7,
    progress: 70,
    created_at: "2024-01-25T10:00:00Z",
  },
  {
    id: "subj-3",
    user_id: "user-demo-123",
    name: "Physics: Mechanics",
    difficulty: "hard",
    hours_per_week: 6,
    target_date: "2024-08-01",
    syllabus_file: "physics_mechanics.pdf",
    chapters_count: 8,
    completed_chapters: 2,
    progress: 25,
    created_at: "2024-02-01T10:00:00Z",
  },
]

// Mock chapters data
const MOCK_CHAPTERS: Record<string, any[]> = {
  "subj-1": [
    {
      id: "ch-1",
      subject_id: "subj-1",
      number: 1,
      title: "Limits and Continuity",
      status: "completed",
      duration_minutes: 45,
    },
    { id: "ch-2", subject_id: "subj-1", number: 2, title: "Derivatives", status: "completed", duration_minutes: 60 },
    {
      id: "ch-3",
      subject_id: "subj-1",
      number: 3,
      title: "Integration Techniques",
      status: "completed",
      duration_minutes: 75,
    },
    {
      id: "ch-4",
      subject_id: "subj-1",
      number: 4,
      title: "Applications of Integration",
      status: "completed",
      duration_minutes: 50,
    },
    {
      id: "ch-5",
      subject_id: "subj-1",
      number: 5,
      title: "Differential Equations",
      status: "completed",
      duration_minutes: 90,
    },
    {
      id: "ch-6",
      subject_id: "subj-1",
      number: 6,
      title: "Series and Sequences",
      status: "in-progress",
      duration_minutes: 0,
    },
    {
      id: "ch-7",
      subject_id: "subj-1",
      number: 7,
      title: "Multivariable Calculus",
      status: "pending",
      duration_minutes: 0,
    },
    { id: "ch-8", subject_id: "subj-1", number: 8, title: "Vector Calculus", status: "pending", duration_minutes: 0 },
  ],
  "subj-2": [
    {
      id: "ch-9",
      subject_id: "subj-2",
      number: 1,
      title: "Data Structures",
      status: "completed",
      duration_minutes: 120,
    },
    { id: "ch-10", subject_id: "subj-2", number: 2, title: "Algorithms", status: "completed", duration_minutes: 100 },
    {
      id: "ch-11",
      subject_id: "subj-2",
      number: 3,
      title: "Time Complexity",
      status: "completed",
      duration_minutes: 45,
    },
  ],
  "subj-3": [
    { id: "ch-12", subject_id: "subj-3", number: 1, title: "Kinematics", status: "completed", duration_minutes: 60 },
    {
      id: "ch-13",
      subject_id: "subj-3",
      number: 2,
      title: "Newton's Laws",
      status: "in-progress",
      duration_minutes: 30,
    },
  ],
}

// Mock chapter detail
const MOCK_CHAPTER_DETAIL = {
  id: "ch-6",
  subject_id: "subj-1",
  number: 6,
  title: "Series and Sequences",
  content: `# Series and Sequences

## Introduction
In this chapter, we explore the fundamental concepts of infinite series and sequences. Understanding these concepts is crucial for advanced calculus and mathematical analysis.

## Key Topics

### 1. Sequences
A sequence is an ordered list of numbers. Each number in the sequence is called a term.

**Example:** 1, 4, 9, 16, 25, ... (perfect squares)

### 2. Convergence
A sequence converges if its terms approach a specific value as n approaches infinity.

### 3. Series
A series is the sum of the terms of a sequence. We denote this as Σ.

### 4. Tests for Convergence
- **Ratio Test**: Used for series with factorials or exponentials
- **Root Test**: Useful for series with nth powers
- **Integral Test**: Compares series to integrals
- **Comparison Test**: Compares to known convergent/divergent series

## Practice Problems
1. Determine if the series Σ(1/n²) converges
2. Find the sum of the geometric series with r = 1/2
3. Apply the ratio test to Σ(n!/n^n)

## Summary
Series and sequences form the foundation for understanding limits, convergence, and many advanced mathematical concepts.`,
  status: "in-progress",
  notes: "Focus on convergence tests",
  created_at: "2024-01-20T10:00:00Z",
}

// Mock quizzes
const MOCK_QUIZZES: Record<string, any[]> = {
  "subj-1": [
    {
      id: "quiz-1",
      subject_id: "subj-1",
      title: "Limits and Continuity Quiz",
      chapter_number: 1,
      difficulty: "medium",
      total_questions: 10,
      completed: true,
      score: 85,
      created_at: "2024-02-01T10:00:00Z",
    },
    {
      id: "quiz-2",
      subject_id: "subj-1",
      title: "Derivatives Assessment",
      chapter_number: 2,
      difficulty: "hard",
      total_questions: 15,
      completed: true,
      score: 92,
      created_at: "2024-02-05T10:00:00Z",
    },
    {
      id: "quiz-3",
      subject_id: "subj-1",
      title: "Integration Practice",
      chapter_number: 3,
      difficulty: "medium",
      total_questions: 12,
      completed: false,
      score: null,
      created_at: "2024-02-10T10:00:00Z",
    },
  ],
  "subj-2": [
    {
      id: "quiz-4",
      subject_id: "subj-2",
      title: "Data Structures Final",
      chapter_number: 1,
      difficulty: "hard",
      total_questions: 20,
      completed: true,
      score: 78,
      created_at: "2024-02-15T10:00:00Z",
    },
  ],
  "subj-3": [],
}

// Mock quiz detail
const MOCK_QUIZ_DETAIL = {
  id: "quiz-3",
  subject_id: "subj-1",
  title: "Integration Practice",
  chapter_number: 3,
  difficulty: "medium",
  questions: [
    {
      id: "q-1",
      question: "What is the integral of x² dx?",
      options: ["x³/3 + C", "2x + C", "x³ + C", "3x² + C"],
      correct_answer: 0,
    },
    {
      id: "q-2",
      question: "Which technique is best for ∫ x·eˣ dx?",
      options: ["Substitution", "Integration by parts", "Partial fractions", "Direct integration"],
      correct_answer: 1,
    },
    {
      id: "q-3",
      question: "Evaluate ∫₀¹ 2x dx",
      options: ["0", "1", "2", "4"],
      correct_answer: 1,
    },
  ],
}

// Mock quiz result
const MOCK_QUIZ_RESULT = {
  id: "result-1",
  quiz_id: "quiz-2",
  user_id: "user-demo-123",
  score: 92,
  total_questions: 15,
  correct_answers: 14,
  time_taken: 1200,
  answers: [
    { question_id: "q-1", selected: 0, correct: 0, is_correct: true },
    { question_id: "q-2", selected: 1, correct: 1, is_correct: true },
    { question_id: "q-3", selected: 2, correct: 1, is_correct: false },
  ],
  completed_at: "2024-02-05T11:30:00Z",
}

// Mock analytics stats
const MOCK_STATS = {
  total_subjects: 3,
  active_subjects: 2,
  completed_chapters: 14,
  total_study_hours: 15.5,
  quizzes_taken: 3,
  average_score: 85,
  current_streak: 7,
}

// Mock analytics data
const MOCK_ANALYTICS_DATA = {
  weekly_progress: [
    { week: "Week 1", hours: 8, chapters: 2 },
    { week: "Week 2", hours: 12, chapters: 3 },
    { week: "Week 3", hours: 10, chapters: 2 },
    { week: "Week 4", hours: 15, chapters: 4 },
  ],
  subject_performance: [
    { subject: "Math", score: 88 },
    { subject: "CS", score: 92 },
    { subject: "Physics", score: 75 },
  ],
  quiz_scores: [
    { date: "Feb 1", score: 85 },
    { date: "Feb 5", score: 92 },
    { date: "Feb 10", score: 78 },
    { date: "Feb 15", score: 88 },
  ],
}

// Mock feedback data
const MOCK_FEEDBACK = {
  subject_id: "subj-1",
  overall_performance: 85,
  strengths: [
    "Strong understanding of derivatives and their applications",
    "Excellent problem-solving skills in integration techniques",
    "Good grasp of fundamental calculus concepts",
  ],
  areas_for_improvement: [
    "Need more practice with series convergence tests",
    "Review implicit differentiation problems",
    "Spend more time on word problems",
  ],
  recommendations: [
    "Complete additional practice problems on series",
    "Review chapter 6 materials before the next quiz",
    "Consider joining study groups for collaborative learning",
  ],
  study_streak: 7,
  total_study_time: 320,
  chapters_completed: 5,
  average_quiz_score: 88,
}

// [MOCK] Mock API functions
export const mockApi = {
  // Auth
  async login(email: string, password: string) {
    await mockDelay(800)
    console.log("[MOCK] Login called with:", email)
    return {
      token: "mock-jwt-token-12345",
      user: MOCK_USER,
    }
  },

  async register(data: any) {
    await mockDelay(1000)
    console.log("[MOCK] Register called with:", data)
    return {
      token: "mock-jwt-token-12345",
      user: { ...MOCK_USER, ...data },
    }
  },

  // Subjects
  async getSubjects() {
    await mockDelay(600)
    console.log("[MOCK] Getting subjects")
    return MOCK_SUBJECTS
  },

  async getSubject(id: string) {
    await mockDelay(400)
    console.log("[MOCK] Getting subject:", id)
    return MOCK_SUBJECTS.find((s) => s.id === id) || MOCK_SUBJECTS[0]
  },

  async createSubject(data: any) {
    await mockDelay(1200)
    console.log("[MOCK] Creating subject:", data)
    const newSubject = {
      id: `subj-${Date.now()}`,
      ...data,
      user_id: MOCK_USER.id,
      chapters_count: 0,
      completed_chapters: 0,
      progress: 0,
      created_at: new Date().toISOString(),
    }
    return newSubject
  },

  async deleteSubject(id: string) {
    await mockDelay(500)
    console.log("[MOCK] Deleting subject:", id)
    return { success: true }
  },

  async generatePlan(subjectId: string, data: any) {
    await mockDelay(2000)
    console.log("[MOCK] Generating plan for subject:", subjectId, data)
    return { success: true, message: "Study plan generated successfully" }
  },

  // Chapters
  async getChapters(subjectId: string) {
    await mockDelay(400)
    console.log("[MOCK] Getting chapters for subject:", subjectId)
    return MOCK_CHAPTERS[subjectId] || []
  },

  async getChapter(subjectId: string, chapterNumber: number) {
    await mockDelay(500)
    console.log("[MOCK] Getting chapter:", subjectId, chapterNumber)
    return MOCK_CHAPTER_DETAIL
  },

  // Quizzes
  async getQuizzes(subjectId: string) {
    await mockDelay(400)
    console.log("[MOCK] Getting quizzes for subject:", subjectId)
    return MOCK_QUIZZES[subjectId] || []
  },

  async getQuiz(quizId: string) {
    await mockDelay(500)
    console.log("[MOCK] Getting quiz:", quizId)
    return MOCK_QUIZ_DETAIL
  },

  async submitQuiz(quizId: string, answers: any) {
    await mockDelay(1000)
    console.log("[MOCK] Submitting quiz:", quizId, answers)
    return { result_id: "result-mock-123" }
  },

  async getQuizResult(quizId: string) {
    await mockDelay(400)
    console.log("[MOCK] Getting quiz result:", quizId)
    return MOCK_QUIZ_RESULT
  },

  // Analytics
  async getStats() {
    await mockDelay(300)
    console.log("[MOCK] Getting stats")
    return MOCK_STATS
  },

  async getAnalytics() {
    await mockDelay(600)
    console.log("[MOCK] Getting analytics")
    return MOCK_ANALYTICS_DATA
  },

  async getFeedback(subjectId: string) {
    await mockDelay(500)
    console.log("[MOCK] Getting feedback for subject:", subjectId)
    return MOCK_FEEDBACK
  },

  // Chat
  async sendChatMessage(subjectId: string, message: string) {
    await mockDelay(1500)
    console.log("[MOCK] Sending chat message:", subjectId, message)
    return {
      response:
        "This is a mock AI response. In the real app, this would be an intelligent answer based on the chapter content and your question.",
    }
  },
}
