"use client"

import { useEffect, useState } from "react"
import { useRouter, useParams, useSearchParams } from "next/navigation"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingSpinner } from "@/components/loading-spinner"
import { useToast } from "@/hooks/use-toast"
import { ArrowLeft, ClipboardCheck, Play, CheckCircle2, Plus, BookOpen } from "lucide-react"
import Link from "next/link"
import { api } from "@/lib/api"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

// Backend response types
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

// Backend response for quiz list (different from full quiz)
interface BackendQuizListItem {
  id: string
  title: string
  chapter: string
  chapter_number: number | null
  quiz_type: string
  total_marks: number
  questions_count: number
  time_limit: number
  created_at: string
}

interface QuizzesResponse {
  quizzes: BackendQuizListItem[]
  total: number
}

interface QuizResultsResponse {
  results: Array<{
    id: string
    quiz_id: string
    quiz_title: string
    score: number
    max_score: number
    percentage: number
    passed: boolean
    completed_at: string
  }>
  total: number
}

// Chapter info from subject
interface ChapterInfo {
  chapter_number: number
  title: string
  objectives: string[]
}

interface SubjectResponse {
  id: string
  subject_name: string
  plan: {
    chapters: ChapterInfo[]
  } | null
}

// Frontend display type
interface Quiz {
  id: string
  title: string
  chapter: string
  chapter_number: number | null
  total_questions: number
  completed: boolean
  score?: number
  created_at: string
}

export default function QuizzesPage() {
  const router = useRouter()
  const params = useParams()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [quizzes, setQuizzes] = useState<Quiz[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [chapters, setChapters] = useState<ChapterInfo[]>([])
  const [selectedChapter, setSelectedChapter] = useState<string>("")
  
  // Get chapter from URL if coming from study session
  const chapterFromUrl = searchParams.get("chapter")

  useEffect(() => {
    if (params.id) {
      fetchSubjectAndQuizzes()
    }
  }, [params.id])

  useEffect(() => {
    // Pre-select chapter from URL query param if present
    if (chapterFromUrl && !selectedChapter) {
      setSelectedChapter(chapterFromUrl)
    }
  }, [chapterFromUrl])

  const fetchSubjectAndQuizzes = async () => {
    try {
      setIsLoading(true)
      
      // Fetch subject to get chapters
      try {
        const subjectResponse = await api.get<SubjectResponse>(`/api/v1/subjects/${params.id}`)
        if (subjectResponse.plan?.chapters) {
          setChapters(subjectResponse.plan.chapters)
          // Pre-select first chapter if none selected and no URL param
          if (!selectedChapter && !chapterFromUrl && subjectResponse.plan.chapters.length > 0) {
            setSelectedChapter(String(subjectResponse.plan.chapters[0].chapter_number))
          }
        }
      } catch {
        // Subject fetch failed, continue with quiz fetch
      }
      
      // Fetch quizzes for this subject
      const quizzesResponse = await api.get<QuizzesResponse>(`/api/v1/quiz?subject_id=${params.id}`)
      
      // Fetch quiz results to know which are completed
      let resultsMap: Record<string, { score: number; percentage: number }> = {}
      try {
        const resultsResponse = await api.get<QuizResultsResponse>(`/api/v1/quiz/${params.id}/results`)
        resultsMap = resultsResponse.results.reduce((acc, r) => {
          acc[r.quiz_id] = { score: r.score, percentage: r.percentage }
          return acc
        }, {} as Record<string, { score: number; percentage: number }>)
      } catch {
        // No results yet, that's fine
      }

      // Transform to frontend format
      const transformedQuizzes: Quiz[] = quizzesResponse.quizzes.map((q) => ({
        id: q.id,
        title: q.title,
        chapter: q.chapter,
        chapter_number: q.chapter_number,
        total_questions: q.questions_count,
        completed: !!resultsMap[q.id],
        score: resultsMap[q.id]?.percentage,
        created_at: q.created_at,
      }))

      setQuizzes(transformedQuizzes)
    } catch (error) {
      toast({
        title: "Error loading quizzes",
        description: error instanceof Error ? error.message : "Failed to load quizzes",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const generateQuiz = async () => {
    if (!selectedChapter) {
      toast({
        title: "Select a chapter",
        description: "Please select a chapter to generate a quiz for",
        variant: "destructive",
      })
      return
    }

    setIsGenerating(true)
    try {
      const chapterNum = parseInt(selectedChapter)
      const selectedChapterInfo = chapters.find(c => c.chapter_number === chapterNum)
      
      await api.post<BackendQuiz>("/api/v1/quiz", {
        subject_id: params.id,
        chapter_number: chapterNum,
        num_questions: 10,
        quiz_type: "practice",
        difficulty: "medium",
      })

      toast({
        title: "Quiz generated!",
        description: selectedChapterInfo 
          ? `Quiz for Chapter ${chapterNum}: ${selectedChapterInfo.title} has been created`
          : `Quiz for Chapter ${chapterNum} has been created`,
      })

      fetchSubjectAndQuizzes()
    } catch (error) {
      toast({
        title: "Error generating quiz",
        description: error instanceof Error ? error.message : "Failed to generate quiz",
        variant: "destructive",
      })
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <div className="mb-6">
            <Link href={`/subjects/${params.id}`}>
              <Button variant="ghost" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Subject
              </Button>
            </Link>
          </div>

          <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-balance">Quizzes</h1>
              <p className="mt-2 text-muted-foreground">Test your knowledge and track your progress</p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              {chapters.length > 0 && (
                <Select value={selectedChapter} onValueChange={setSelectedChapter}>
                  <SelectTrigger className="w-full sm:w-[200px]">
                    <BookOpen className="mr-2 h-4 w-4" />
                    <SelectValue placeholder="Select chapter" />
                  </SelectTrigger>
                  <SelectContent>
                    {chapters.map((chapter) => (
                      <SelectItem key={chapter.chapter_number} value={String(chapter.chapter_number)}>
                        Ch {chapter.chapter_number}: {chapter.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
              <Button onClick={generateQuiz} disabled={isGenerating || !selectedChapter} className="gap-2">
                {isGenerating ? (
                  <>
                    <LoadingSpinner size="sm" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4" />
                    Generate Quiz
                  </>
                )}
              </Button>
            </div>
          </div>

          {isLoading ? (
            <div className="flex min-h-[40vh] items-center justify-center">
              <LoadingSpinner size="lg" />
            </div>
          ) : quizzes.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <ClipboardCheck className="mb-4 h-12 w-12 text-muted-foreground" />
                <h3 className="mb-2 text-lg font-semibold">No quizzes available</h3>
                <p className="text-center text-sm text-muted-foreground">
                  Quizzes will be available once you generate a study plan
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {quizzes.map((quiz) => (
                <Card key={quiz.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">{quiz.title}</CardTitle>
                        <CardDescription className="mt-1">
                          {quiz.chapter || (quiz.chapter_number ? `Chapter ${quiz.chapter_number}` : "General")}
                        </CardDescription>
                      </div>
                      {quiz.completed && <CheckCircle2 className="h-5 w-5 text-accent" />}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Questions</span>
                      <span className="font-medium">{quiz.total_questions}</span>
                    </div>

                    {quiz.completed && quiz.score !== undefined && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Score</span>
                        <span className="font-bold text-lg">{quiz.score}%</span>
                      </div>
                    )}

                    <Button
                      className="w-full gap-2"
                      variant={quiz.completed ? "outline" : "default"}
                      onClick={() =>
                        quiz.completed ? router.push(`/quiz/${quiz.id}/results`) : router.push(`/quiz/${quiz.id}/take`)
                      }
                    >
                      {quiz.completed ? (
                        <>
                          <CheckCircle2 className="h-4 w-4" />
                          View Results
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4" />
                          Start Quiz
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  )
}
