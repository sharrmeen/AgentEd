"use client"

import { useEffect, useState } from "react"
import { useRouter, useParams, useSearchParams } from "next/navigation"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingSpinner } from "@/components/loading-spinner"
import { useToast } from "@/hooks/use-toast"
import { ArrowLeft, TrendingUp, AlertCircle, Lightbulb, Target } from "lucide-react"
import Link from "next/link"
import { api } from "@/lib/api"

// Backend response types
interface BackendFeedback {
  id: string
  quiz_result_id: string
  quiz_id: string
  subject_id: string
  session_id: string | null
  assessment_type: string
  score: number
  max_score: number
  percentage: number
  performance_level: string
  performance_summary: string
  strengths: string[]
  strength_details: Array<{
    concept: string
    questions_on_concept: number
    correct_answers: number
    accuracy_percentage: number
    mastery_level: string
    needs_revision: boolean
    suggestion: string
  }>
  weak_areas: string[]
  weakness_details: Array<{
    concept: string
    questions_on_concept: number
    correct_answers: number
    accuracy_percentage: number
    mastery_level: string
    needs_revision: boolean
    suggestion: string
  }>
  revision_tips: string[]
  revision_items: Array<{
    concept: string
    reason: string
    priority: string
    source_file: string | null
    chapter_number: number | null
    section: string | null
    estimated_time: number | null
    recommended_approach: string | null
  }>
  estimated_revision_time: number
  recommended_resources: string[]
  recommended_chapters: number[]
  insights: Array<{
    insight_type: string
    title: string
    description: string
    action_items: string[]
  }>
  motivational_message: string
  encouragement: string
  next_steps: string[]
  created_at: string
}

interface FeedbackListResponse {
  feedback_reports: Array<{
    id: string
    quiz_result_id: string
    quiz_title: string
    percentage: number
    performance_level: string
    created_at: string
  }>
  total: number
}

// Frontend display type
interface Feedback {
  overall_score: number
  performance_level: string
  performance_summary: string
  strengths: string[]
  areas_to_review: Array<{ topic: string; suggestion: string }>
  revision_tips: string[]
  next_steps: string[]
}

function transformFeedback(backend: BackendFeedback): Feedback {
  console.log("Backend feedback data:", backend)
  
  return {
    overall_score: Math.round(backend.percentage || 0),
    performance_level: (backend.performance_level || "needs_improvement").replace("_", " ").replace(/\b\w/g, l => l.toUpperCase()),
    performance_summary: backend.performance_summary || "No summary available.",
    strengths: backend.strengths || [],
    areas_to_review: (backend.weakness_details || []).map((w) => ({
      topic: w.concept || "Unknown",
      suggestion: w.suggestion || "Review this topic.",
    })),
    revision_tips: backend.revision_tips || ["Keep practicing to improve!"],
    next_steps: backend.next_steps || ["Continue studying."],
  }
}

export default function FeedbackPage() {
  const router = useRouter()
  const params = useParams()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [feedback, setFeedback] = useState<Feedback | null>(null)

  useEffect(() => {
    if (params.id) {
      fetchFeedback()
    }
  }, [params.id])

  const fetchFeedback = async () => {
    try {
      setIsLoading(true)
      
      // Check if we have a specific quiz result ID
      const resultId = searchParams.get("result_id")
      
      if (resultId) {
        // Fetch specific feedback for a quiz result
        const data = await api.get<BackendFeedback>(`/api/v1/feedback/${resultId}`)
        setFeedback(transformFeedback(data))
      } else {
        // List all feedback for this subject and use the most recent one
        const listData = await api.get<FeedbackListResponse>(`/api/v1/feedback?subject_id=${params.id}`)
        
        if (listData.feedback_reports && listData.feedback_reports.length > 0) {
          // Get the most recent feedback's full details
          const latestFeedbackId = listData.feedback_reports[0].id
          const data = await api.get<BackendFeedback>(`/api/v1/feedback/${latestFeedbackId}`)
          setFeedback(transformFeedback(data))
        } else {
          setFeedback(null)
        }
      }
    } catch (error) {
      toast({
        title: "Error loading feedback",
        description: error instanceof Error ? error.message : "Failed to load feedback",
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

  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto max-w-4xl px-4 py-8">
          <div className="mb-6">
            <Link href={`/subjects/${params.id}`}>
              <Button variant="ghost" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Subject
              </Button>
            </Link>
          </div>

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-balance">Performance Feedback</h1>
            <p className="mt-2 text-muted-foreground">Personalized insights to improve your learning</p>
          </div>

          {feedback ? (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    Overall Performance
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-center">
                    <div className="text-4xl font-bold mb-2">{feedback.overall_score}%</div>
                    <div className="text-lg font-medium text-primary">{feedback.performance_level}</div>
                  </div>
                  <p className="text-sm text-muted-foreground text-center">{feedback.performance_summary}</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-accent">
                    <TrendingUp className="h-5 w-5" />
                    Strengths
                  </CardTitle>
                  <CardDescription>Areas where you excel</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {feedback.strengths.map((strength, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <div className="mt-1 h-1.5 w-1.5 rounded-full bg-accent flex-shrink-0" />
                        <span className="text-sm">{strength}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-amber-500">
                    <AlertCircle className="h-5 w-5" />
                    Areas to Review
                  </CardTitle>
                  <CardDescription>Topics that need more attention</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {feedback.areas_to_review.map((area, idx) => (
                    <div key={idx} className="space-y-1">
                      <p className="text-sm font-medium">{area.topic}</p>
                      <p className="text-sm text-muted-foreground">{area.suggestion}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Lightbulb className="h-5 w-5" />
                    Revision Tips
                  </CardTitle>
                  <CardDescription>Actionable suggestions to improve</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {feedback.revision_tips.map((tip, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <div className="mt-1 h-1.5 w-1.5 rounded-full bg-primary flex-shrink-0" />
                        <span className="text-sm">{tip}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    Next Steps
                  </CardTitle>
                  <CardDescription>Recommended actions for continued progress</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {feedback.next_steps.map((step, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <div className="mt-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold flex-shrink-0">
                          {idx + 1}
                        </div>
                        <span className="text-sm">{step}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">
                  No feedback available yet. Complete some quizzes to get feedback!
                </p>
              </CardContent>
            </Card>
          )}
        </main>
      </div>
    </AuthGuard>
  )
}
