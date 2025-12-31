"use client"

import { useEffect, useState, useRef } from "react"
import { useRouter, useParams } from "next/navigation"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingSpinner } from "@/components/loading-spinner"
import { useToast } from "@/hooks/use-toast"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { api } from "@/lib/api"

// Backend response type
interface BackendQuiz {
  id: string
  subject_id: string
  subject: string
  chapter: string
  chapter_number: number
  title: string
  description: string
  quiz_type: string
  questions: Array<{
    question_id: string
    question_number: number
    text: string
    question_type: string
    options: string[]
    difficulty: string
    marks: number
  }>
  total_marks: number
  time_limit: number
  pass_percentage: number
  created_at: string
}

// Frontend display types
interface Question {
  id: string
  question: string
  type: "mcq" | "short_answer" | "true_false"
  options?: string[]
}

interface Quiz {
  id: string
  title: string
  questions: Question[]
}

function transformQuiz(backend: BackendQuiz): Quiz {
  return {
    id: backend.id,
    title: backend.title,
    questions: backend.questions.map((q) => ({
      id: q.question_id,
      question: q.text,
      type: q.question_type === "multiple_choice" ? "mcq" : 
            q.question_type === "true_false" ? "true_false" : "short_answer",
      options: q.options,
    })),
  }
}

export default function TakeQuizPage() {
  const router = useRouter()
  const params = useParams()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const startedAtRef = useRef<string>(new Date().toISOString())

  useEffect(() => {
    if (params.id) {
      fetchQuiz()
    }
  }, [params.id])

  const fetchQuiz = async () => {
    try {
      setIsLoading(true)
      const data = await api.get<BackendQuiz>(`/api/v1/quiz/${params.id}`)
      setQuiz(transformQuiz(data))
      startedAtRef.current = new Date().toISOString()
    } catch (error) {
      toast({
        title: "Error loading quiz",
        description: error instanceof Error ? error.message : "Failed to load quiz",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!quiz) return

    const unanswered = quiz.questions.filter((q) => !answers[q.id])
    if (unanswered.length > 0) {
      toast({
        title: "Incomplete quiz",
        description: `Please answer all ${unanswered.length} remaining question(s)`,
        variant: "destructive",
      })
      return
    }

    setIsSubmitting(true)

    try {
      // Transform answers to backend format
      const answersList = quiz.questions.map((q) => ({
        question_id: q.id,
        selected_option: answers[q.id],
      }))

      await api.post(`/api/v1/quiz/${params.id}/submit`, {
        quiz_id: params.id,
        answers: answersList,
        started_at: startedAtRef.current,
      })

      toast({
        title: "Quiz submitted!",
        description: "View your results now",
      })

      router.push(`/quiz/${params.id}/results`)
    } catch (error) {
      toast({
        title: "Error submitting quiz",
        description: error instanceof Error ? error.message : "Failed to submit quiz",
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
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

  if (!quiz) {
    return (
      <AuthGuard>
        <div className="min-h-screen bg-background">
          <Navbar />
          <div className="container mx-auto px-4 py-8">
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">Quiz not found</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </AuthGuard>
    )
  }

  const currentQuestion = quiz.questions[currentQuestionIndex]
  const progress = ((currentQuestionIndex + 1) / quiz.questions.length) * 100
  const answeredCount = Object.keys(answers).length

  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto max-w-3xl px-4 py-8">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{quiz.title}</CardTitle>
                  <CardDescription>
                    Question {currentQuestionIndex + 1} of {quiz.questions.length}
                  </CardDescription>
                </div>
                <div className="text-sm text-muted-foreground">
                  {answeredCount}/{quiz.questions.length} answered
                </div>
              </div>
              <Progress value={progress} className="mt-4 h-2" />
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-lg font-medium mb-4">{currentQuestion.question}</h3>

                {currentQuestion.type === "mcq" && currentQuestion.options && (
                  <RadioGroup
                    value={answers[currentQuestion.id] || ""}
                    onValueChange={(value) => setAnswers({ ...answers, [currentQuestion.id]: value })}
                  >
                    <div className="space-y-3">
                      {currentQuestion.options.map((option, idx) => (
                        <div key={idx} className="flex items-center space-x-2">
                          <RadioGroupItem value={option} id={`option-${idx}`} />
                          <Label htmlFor={`option-${idx}`} className="flex-1 cursor-pointer">
                            {option}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </RadioGroup>
                )}

                {currentQuestion.type === "short_answer" && (
                  <Input
                    placeholder="Type your answer..."
                    value={answers[currentQuestion.id] || ""}
                    onChange={(e) => setAnswers({ ...answers, [currentQuestion.id]: e.target.value })}
                  />
                )}

                {currentQuestion.type === "true_false" && (
                  <RadioGroup
                    value={answers[currentQuestion.id] || ""}
                    onValueChange={(value) => setAnswers({ ...answers, [currentQuestion.id]: value })}
                  >
                    <div className="space-y-3">
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="true" id="true" />
                        <Label htmlFor="true" className="cursor-pointer">
                          True
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="false" id="false" />
                        <Label htmlFor="false" className="cursor-pointer">
                          False
                        </Label>
                      </div>
                    </div>
                  </RadioGroup>
                )}
              </div>

              <div className="flex items-center justify-between pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={() => setCurrentQuestionIndex((prev) => Math.max(0, prev - 1))}
                  disabled={currentQuestionIndex === 0}
                  className="gap-2 bg-transparent"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>

                {currentQuestionIndex === quiz.questions.length - 1 ? (
                  <Button onClick={handleSubmit} disabled={isSubmitting} className="gap-2">
                    {isSubmitting ? (
                      <>
                        <LoadingSpinner size="sm" />
                        Submitting...
                      </>
                    ) : (
                      "Submit Quiz"
                    )}
                  </Button>
                ) : (
                  <Button
                    onClick={() => setCurrentQuestionIndex((prev) => Math.min(quiz.questions.length - 1, prev + 1))}
                    className="gap-2"
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    </AuthGuard>
  )
}
