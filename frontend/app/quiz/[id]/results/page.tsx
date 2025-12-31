"use client"

import { useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingSpinner } from "@/components/loading-spinner"
import { useToast } from "@/hooks/use-toast"
import { ArrowLeft, Trophy, CheckCircle2, XCircle, RotateCcw } from "lucide-react"
import Link from "next/link"
import { api } from "@/lib/api"

// Backend response types
interface BackendQuizResult {
  id: string
  quiz_id: string
  subject_id: string
  score: number
  max_score: number
  percentage: number
  passed: boolean
  time_taken_seconds: number
  question_results: Array<{
    question_id: string
    question_number: number
    question_text: string
    user_answer: string
    correct_answer: string
    is_correct: boolean
    marks_obtained: number
    marks_possible: number
    explanation: string
    concepts: string[]
  }>
  strengths: string[]
  weak_areas: string[]
  completed_at: string | null
}

// Frontend display types
interface QuestionResult {
  question: string
  user_answer: string
  correct_answer: string
  is_correct: boolean
  explanation?: string
}

interface QuizResult {
  id: string
  quiz_id: string
  subject_id: string
  score: number
  total_questions: number
  correct_answers: number
  incorrect_answers: number
  performance_level: string
  questions: QuestionResult[]
}

function getPerformanceLevel(percentage: number): string {
  if (percentage >= 90) return "Excellent!"
  if (percentage >= 75) return "Good Performance"
  if (percentage >= 60) return "Satisfactory"
  if (percentage >= 40) return "Needs Improvement"
  return "Keep Practicing"
}

function transformResult(backend: BackendQuizResult): QuizResult {
  const correct = backend.question_results.filter((a) => a.is_correct).length
  const incorrect = backend.question_results.length - correct

  return {
    id: backend.id,
    quiz_id: backend.quiz_id,
    subject_id: backend.subject_id,
    score: Math.round(backend.percentage),
    total_questions: backend.question_results.length,
    correct_answers: correct,
    incorrect_answers: incorrect,
    performance_level: getPerformanceLevel(backend.percentage),
    questions: backend.question_results.map((a) => ({
      question: a.question_text,
      user_answer: a.user_answer,
      correct_answer: a.correct_answer,
      is_correct: a.is_correct,
      explanation: a.explanation,
    })),
  }
}

export default function QuizResultsPage() {
  const router = useRouter()
  const params = useParams()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [results, setResults] = useState<QuizResult | null>(null)

  useEffect(() => {
    if (params.id) {
      fetchResults()
    }
  }, [params.id])

  const fetchResults = async () => {
    try {
      setIsLoading(true)
      const data = await api.get<BackendQuizResult>(`/api/v1/quiz/${params.id}/result`)
      setResults(transformResult(data))
    } catch (error) {
      toast({
        title: "Error loading results",
        description: error instanceof Error ? error.message : "Failed to load results",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <AuthGuard>
        <div className="min-h-screen bg-background">
          <Navbar />
          <div className="flex min-h-[60vh] items-center justify-center">
            <LoadingSpinner size="lg" />
          </div>
        </div>
      </AuthGuard>
    )
  }

  if (!results) {
    return (
      <AuthGuard>
        <div className="min-h-screen bg-background">
          <Navbar />
          <div className="container mx-auto px-4 py-8">
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">Results not found</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </AuthGuard>
    )
  }

  const getPerformanceColor = (level: string) => {
    if (level.toLowerCase().includes("excellent")) return "text-accent"
    if (level.toLowerCase().includes("good")) return "text-primary"
    return "text-amber-500"
  }

  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto max-w-4xl px-4 py-8">
          <div className="mb-6">
            <Link href={`/subjects/${results.subject_id}`}>
              <Button variant="ghost" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Subject
              </Button>
            </Link>
          </div>

          <Card className="mb-6">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <Trophy className="h-8 w-8 text-primary" />
              </div>
              <CardTitle className="text-3xl">Quiz Complete!</CardTitle>
              <CardDescription>Here's how you performed</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center mb-6">
                <div className="text-5xl font-bold mb-2">{results.score}%</div>
                <div className={`text-lg font-medium ${getPerformanceColor(results.performance_level)}`}>
                  {results.performance_level}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold">{results.total_questions}</div>
                  <div className="text-xs text-muted-foreground">Total</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-accent">{results.correct_answers}</div>
                  <div className="text-xs text-muted-foreground">Correct</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-destructive">{results.incorrect_answers}</div>
                  <div className="text-xs text-muted-foreground">Incorrect</div>
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1 gap-2 bg-transparent"
                  onClick={() => router.push(`/quiz/${params.id}/take`)}
                >
                  <RotateCcw className="h-4 w-4" />
                  Retake Quiz
                </Button>
                <Button 
                  className="flex-1" 
                  onClick={() => router.push(`/subjects/${results.subject_id}/feedback?result_id=${results.id}`)}
                >
                  View Feedback
                </Button>
              </div>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <h2 className="text-2xl font-bold">Question Review</h2>
            {results.questions.map((question, idx) => (
              <Card key={idx}>
                <CardHeader>
                  <div className="flex items-start gap-3">
                    {question.is_correct ? (
                      <CheckCircle2 className="mt-1 h-5 w-5 flex-shrink-0 text-accent" />
                    ) : (
                      <XCircle className="mt-1 h-5 w-5 flex-shrink-0 text-destructive" />
                    )}
                    <div className="flex-1">
                      <CardTitle className="text-base">Question {idx + 1}</CardTitle>
                      <CardDescription className="mt-1">{question.question}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Your Answer:</p>
                    <p className={`text-sm ${question.is_correct ? "text-accent" : "text-destructive"}`}>
                      {question.user_answer || <span className="italic text-muted-foreground">No answer provided</span>}
                    </p>
                  </div>
                  {!question.is_correct && (
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Correct Answer:</p>
                      <p className="text-sm text-accent">{question.correct_answer}</p>
                    </div>
                  )}
                  {question.explanation && (
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Explanation:</p>
                      <p className="text-sm">{question.explanation}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </main>
      </div>
    </AuthGuard>
  )
}
