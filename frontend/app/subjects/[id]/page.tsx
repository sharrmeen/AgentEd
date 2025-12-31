"use client"

import type React from "react"

import { useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { LoadingSpinner } from "@/components/loading-spinner"
import { useToast } from "@/hooks/use-toast"
import { ArrowLeft, Upload, Sparkles, CheckCircle2, Circle, Play } from "lucide-react"
import Link from "next/link"
import { Progress } from "@/components/ui/progress"
import { api } from "@/lib/api"

// Backend response types
interface BackendSubject {
  id: string
  subject_name: string
  syllabus_id: string | null
  status: string
  plan: {
    chapters?: Array<{
      chapter_number: number
      title: string
      objectives: string[]
      estimated_hours: number
      deadline: string
    }>
  } | null
  plan_summary: object | null
  created_at: string
  updated_at: string
}

interface PlannerState {
  id: string
  subject_id: string
  total_chapters: number
  target_days: number
  daily_hours: number
  estimated_total_hours: number
  current_chapter: number
  completed_chapters: number[]
  completion_percent: number
  chapter_progress: Record<string, {
    completed_objectives: string[]
    started_at: string | null
    completed_at: string | null
  }>
  study_pace: string
  created_at: string
  updated_at: string
}

// Frontend display types
interface Subject {
  id: string
  name: string
  description: string
  syllabus_uploaded: boolean
  study_plan_generated: boolean
  created_at: string
}

interface Chapter {
  chapter_number: number
  title: string
  estimated_hours: number
  learning_objectives: string[]
  completed_objectives: number
}

export default function SubjectDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [subject, setSubject] = useState<Subject | null>(null)
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [activeTab, setActiveTab] = useState<"overview" | "study-plan">("overview")

  useEffect(() => {
    if (params.id) {
      fetchSubjectData()
    }
  }, [params.id])

  const fetchSubjectData = async () => {
    try {
      setIsLoading(true)
      
      // Fetch subject details
      const backendSubject = await api.get<BackendSubject>(`/api/v1/subjects/${params.id}`)
      
      // Transform to frontend format
      const transformedSubject: Subject = {
        id: backendSubject.id,
        name: backendSubject.subject_name,
        description: "",
        syllabus_uploaded: !!backendSubject.syllabus_id,
        study_plan_generated: backendSubject.status === "planned" || (!!backendSubject.plan && !!backendSubject.plan.chapters),
        created_at: backendSubject.created_at,
      }
      setSubject(transformedSubject)

      // If plan exists, fetch planner state for progress info
      if (transformedSubject.study_plan_generated && backendSubject.plan?.chapters) {
        try {
          const plannerState = await api.get<PlannerState>(`/api/v1/planner/${params.id}`)
          
          // Transform chapters with progress info
          const transformedChapters: Chapter[] = backendSubject.plan.chapters.map((ch) => {
            const chapterKey = ch.chapter_number.toString()
            const progress = plannerState.chapter_progress?.[chapterKey]
            const completedCount = progress?.completed_objectives?.length || 0
            
            return {
              chapter_number: ch.chapter_number,
              title: ch.title,
              estimated_hours: ch.estimated_hours,
              learning_objectives: ch.objectives || [],
              completed_objectives: completedCount,
            }
          })
          setChapters(transformedChapters)
        } catch {
          // If planner state doesn't exist, just show chapters without progress
          const transformedChapters: Chapter[] = backendSubject.plan.chapters.map((ch) => ({
            chapter_number: ch.chapter_number,
            title: ch.title,
            estimated_hours: ch.estimated_hours,
            learning_objectives: ch.objectives || [],
            completed_objectives: 0,
          }))
          setChapters(transformedChapters)
        }
      }
    } catch (error) {
      toast({
        title: "Error loading subject",
        description: error instanceof Error ? error.message : "Failed to load subject data",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const maxSize = 10 * 1024 * 1024
    if (file.size > maxSize) {
      toast({
        title: "File too large",
        description: "Please upload a file smaller than 10MB",
        variant: "destructive",
      })
      return
    }

    setIsUploading(true)

    try {
      await api.uploadFile(`/api/v1/syllabus/${params.id}/upload`, file)
      
      toast({
        title: "Syllabus uploaded!",
        description: "Your syllabus has been processed successfully",
      })
      fetchSubjectData()
    } catch (error) {
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Failed to upload syllabus",
        variant: "destructive",
      })
    } finally {
      setIsUploading(false)
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

  if (!subject) {
    return (
      <AuthGuard>
        <div className="min-h-screen bg-background">
          <Navbar />
          <div className="container mx-auto px-4 py-8">
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">Subject not found</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </AuthGuard>
    )
  }

  const totalObjectives = chapters.reduce((sum, ch) => sum + ch.learning_objectives.length, 0)
  const completedObjectives = chapters.reduce((sum, ch) => sum + ch.completed_objectives, 0)
  const overallProgress = totalObjectives > 0 ? Math.round((completedObjectives / totalObjectives) * 100) : 0

  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <div className="mb-6">
            <Link href="/dashboard">
              <Button variant="ghost" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Dashboard
              </Button>
            </Link>
          </div>

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-balance">{subject.name}</h1>
            <p className="mt-2 text-muted-foreground">{subject.description || "No description provided"}</p>
          </div>

          <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "overview" | "study-plan")} className="space-y-6">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="study-plan">Study Plan</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Upload className="h-5 w-5" />
                      Syllabus
                    </CardTitle>
                    <CardDescription>Upload your course syllabus to get started</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {subject.syllabus_uploaded ? (
                      <div className="flex items-center gap-2 text-accent">
                        <CheckCircle2 className="h-5 w-5" />
                        <span className="font-medium">Syllabus uploaded</span>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <p className="text-sm text-muted-foreground">Supported formats: PDF, DOCX, TXT (max 10MB)</p>
                        <label htmlFor="syllabus-upload">
                          <Button disabled={isUploading} className="w-full gap-2" asChild>
                            <span>
                              {isUploading ? (
                                <>
                                  <LoadingSpinner size="sm" />
                                  Processing...
                                </>
                              ) : (
                                <>
                                  <Upload className="h-4 w-4" />
                                  Upload Syllabus
                                </>
                              )}
                            </span>
                          </Button>
                        </label>
                        <input
                          id="syllabus-upload"
                          type="file"
                          accept=".pdf,.docx,.txt,image/*"
                          onChange={handleFileUpload}
                          className="hidden"
                          disabled={isUploading}
                        />
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Sparkles className="h-5 w-5" />
                      Study Plan
                    </CardTitle>
                    <CardDescription>AI-generated learning roadmap</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {subject.study_plan_generated ? (
                      <div className="space-y-3">
                        <div className="flex items-center gap-2 text-accent">
                          <CheckCircle2 className="h-5 w-5" />
                          <span className="font-medium">Plan generated</span>
                        </div>
                        <Button
                          variant="outline"
                          className="w-full bg-transparent"
                          onClick={() => setActiveTab("study-plan")}
                        >
                          View Study Plan
                        </Button>
                      </div>
                    ) : subject.syllabus_uploaded ? (
                      <div className="space-y-3">
                        <p className="text-sm text-muted-foreground">Generate a personalized study plan</p>
                        <Button
                          className="w-full gap-2"
                          onClick={() => router.push(`/subjects/${params.id}/generate-plan`)}
                        >
                          <Sparkles className="h-4 w-4" />
                          Generate Plan
                        </Button>
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">Upload syllabus first to generate a study plan</p>
                    )}
                  </CardContent>
                </Card>
              </div>

              {subject.study_plan_generated && (
                <Card>
                  <CardHeader>
                    <CardTitle>Quick Stats</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Overall Progress</span>
                        <span className="font-medium">{overallProgress}%</span>
                      </div>
                      <Progress value={overallProgress} className="mt-2 h-2" />
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-2xl font-bold">{chapters.length}</div>
                        <div className="text-xs text-muted-foreground">Chapters</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold">{completedObjectives}</div>
                        <div className="text-xs text-muted-foreground">Completed Objectives</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold">{totalObjectives}</div>
                        <div className="text-xs text-muted-foreground">Total Objectives</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="study-plan" className="space-y-6">
              {!subject.study_plan_generated ? (
                <Card>
                  <CardContent className="py-12 text-center">
                    <Sparkles className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                    <h3 className="mb-2 text-lg font-semibold">No study plan yet</h3>
                    <p className="mb-4 text-sm text-muted-foreground">
                      {subject.syllabus_uploaded
                        ? "Generate a study plan to see your learning chapters"
                        : "Upload a syllabus first to generate a study plan"}
                    </p>
                    {subject.syllabus_uploaded && (
                      <Button className="gap-2" onClick={() => router.push(`/subjects/${params.id}/generate-plan`)}>
                        <Sparkles className="h-4 w-4" />
                        Generate Study Plan
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-4">
                  {chapters.map((chapter) => {
                    const chapterProgress =
                      chapter.learning_objectives.length > 0
                        ? Math.round((chapter.completed_objectives / chapter.learning_objectives.length) * 100)
                        : 0

                    return (
                      <Card key={chapter.chapter_number}>
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <CardTitle className="text-lg">
                                Chapter {chapter.chapter_number}: {chapter.title}
                              </CardTitle>
                              <CardDescription className="mt-1">
                                Estimated: {chapter.estimated_hours} hours
                              </CardDescription>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              className="gap-2 bg-transparent"
                              onClick={() =>
                                router.push(`/subjects/${params.id}/study?chapter=${chapter.chapter_number}`)
                              }
                            >
                              <Play className="h-4 w-4" />
                              Study
                            </Button>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div>
                            <div className="flex items-center justify-between text-sm mb-2">
                              <span className="text-muted-foreground">Progress</span>
                              <span className="font-medium">{chapterProgress}%</span>
                            </div>
                            <Progress value={chapterProgress} className="h-2" />
                          </div>
                          <div>
                            <p className="mb-2 text-sm font-medium">Learning Objectives:</p>
                            <ul className="space-y-2">
                              {chapter.learning_objectives.map((objective, idx) => (
                                <li key={idx} className="flex items-start gap-2 text-sm">
                                  <Circle className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground" />
                                  <span>{objective}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </CardContent>
                      </Card>
                    )
                  })}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </AuthGuard>
  )
}
