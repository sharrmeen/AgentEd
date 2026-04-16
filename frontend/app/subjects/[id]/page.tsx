"use client"

import type React from "react"

import { useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { LoadingSpinner } from "@/components/loading-spinner"
import { useToast } from "@/hooks/use-toast"
import { ArrowLeft, Upload, Sparkles, CheckCircle2, Circle, Play, BookOpen } from "lucide-react"
import Link from "next/link"
import { Progress } from "@/components/ui/progress"
import { api } from "@/lib/api"
import { auth } from "@/lib/auth"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { getSubjectDifficulty, setSubjectDifficulty, type SubjectDifficulty } from "@/lib/study-preferences"

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

interface ClassListResponse {
  classes: Array<{
    id: string
    name: string
    section?: string | null
  }>
}

interface SyllabusResponse {
  id: string
  subject_id: string
  raw_text: string
  source_file: string
  file_type: string
  created_at: string
  updated_at: string
}

interface TeacherNoteItem {
  id: string
  chapter: string
  source_file: string
  file_type: string
  created_at: string
}

interface TeacherNotesResponse {
  notes: TeacherNoteItem[]
  total: number
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
  completed_objectives_list: string[]
}

export default function SubjectDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { toast } = useToast()
  const user = auth.getUser()
  const role = user?.role || "student"
  const isTeacher = role === "teacher"
  const isStudent = role === "student"
  const homeHref = auth.getDefaultRoute()
  const subjectId = String(params.id)
  const [isLoading, setIsLoading] = useState(true)
  const [subject, setSubject] = useState<Subject | null>(null)
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [isNotesUploading, setIsNotesUploading] = useState(false)
  const [teacherClassId, setTeacherClassId] = useState<string>("")
  const [teacherChapter, setTeacherChapter] = useState("")
  const [teacherNotesFile, setTeacherNotesFile] = useState<File | null>(null)
  const [teacherClasses, setTeacherClasses] = useState<Array<{ id: string; name: string; section?: string | null }>>([])
  const [teacherNotes, setTeacherNotes] = useState<TeacherNoteItem[]>([])
  const [isLoadingTeacherNotes, setIsLoadingTeacherNotes] = useState(false)
  const [isLoadingSyllabus, setIsLoadingSyllabus] = useState(false)
  const [isSyllabusDialogOpen, setIsSyllabusDialogOpen] = useState(false)
  const [syllabusPreview, setSyllabusPreview] = useState("")
  const [difficultyModalOpen, setDifficultyModalOpen] = useState(false)
  const [selectedDifficulty, setSelectedDifficulty] = useState<SubjectDifficulty>("intermediate")
  const [activeTab, setActiveTab] = useState<"overview" | "study-plan">("overview")

  useEffect(() => {
    if (subjectId) {
      fetchSubjectData()
    }
  }, [subjectId])

  useEffect(() => {
    if (!subject || !isStudent) return
    const saved = getSubjectDifficulty(subject.id)
    if (saved) {
      setSelectedDifficulty(saved)
      return
    }
    setDifficultyModalOpen(true)
  }, [subject, isStudent])

  useEffect(() => {
    if (!isTeacher) return
    fetchTeacherClasses()
    fetchTeacherNotes()
  }, [isTeacher, subjectId])

  const fetchTeacherClasses = async () => {
    try {
      const response = await api.get<ClassListResponse>("/api/v1/classes/teacher/me")
      setTeacherClasses(response.classes || [])
      if (response.classes?.length) {
        setTeacherClassId(response.classes[0].id)
      }
    } catch {
      // Class list is optional for subject viewing.
    }
  }

  const fetchTeacherNotes = async () => {
    try {
      setIsLoadingTeacherNotes(true)
      const response = await api.get<TeacherNotesResponse>(`/api/v1/notes/${subjectId}`)
      setTeacherNotes(response.notes || [])
    } catch {
      setTeacherNotes([])
    } finally {
      setIsLoadingTeacherNotes(false)
    }
  }

  const fetchSubjectData = async () => {
    try {
      setIsLoading(true)
      
      // Fetch subject details
      const backendSubject = await api.get<BackendSubject>(`/api/v1/subjects/${subjectId}`)
      
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
          const plannerState = await api.get<PlannerState>(`/api/v1/planner/${subjectId}`)
          
          // Transform chapters with progress info
          const transformedChapters: Chapter[] = backendSubject.plan.chapters.map((ch) => {
            const chapterKey = ch.chapter_number.toString()
            const progress = plannerState.chapter_progress?.[chapterKey]
            const completedList = progress?.completed_objectives || []
            const completedCount = completedList.length
            
            return {
              chapter_number: ch.chapter_number,
              title: ch.title,
              estimated_hours: ch.estimated_hours,
              learning_objectives: ch.objectives || [],
              completed_objectives: completedCount,
              completed_objectives_list: completedList,
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
            completed_objectives_list: [],
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
      await api.uploadFile(`/api/v1/syllabus/${subjectId}/upload`, file)
      
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

  const handleSaveDifficulty = () => {
    if (!subject) return
    setSubjectDifficulty(subject.id, selectedDifficulty)
    setDifficultyModalOpen(false)
    toast({
      title: "Difficulty preference saved",
      description: `We'll generate content at ${selectedDifficulty} level for this subject.`,
    })
  }

  const handleTeacherNotesUpload = async () => {
    if (!teacherNotesFile || !teacherChapter.trim()) {
      toast({
        title: "Missing details",
        description: "Please select a file and chapter name before uploading notes.",
        variant: "destructive",
      })
      return
    }

    if (!teacherClassId) {
      toast({
        title: "Select a class",
        description: "Teacher notes need a class assignment.",
        variant: "destructive",
      })
      return
    }

    setIsNotesUploading(true)
    try {
      await api.uploadFile(`/api/v1/notes/${subjectId}/upload`, teacherNotesFile, {
        chapter: teacherChapter.trim(),
        class_id: teacherClassId,
      })
      setTeacherNotesFile(null)
      setTeacherChapter("")
      await fetchTeacherNotes()
      toast({
        title: "Notes uploaded",
        description: "Notes were stored and queued for vector ingestion.",
      })
    } catch (error) {
      toast({
        title: "Notes upload failed",
        description: error instanceof Error ? error.message : "Unable to upload notes",
        variant: "destructive",
      })
    } finally {
      setIsNotesUploading(false)
    }
  }

  const handleViewSyllabus = async () => {
    try {
      setIsLoadingSyllabus(true)
      const response = await api.get<SyllabusResponse>(`/api/v1/syllabus/${subjectId}`)
      setSyllabusPreview(response.raw_text || "")
      setIsSyllabusDialogOpen(true)
    } catch (error) {
      toast({
        title: "Unable to load syllabus",
        description: error instanceof Error ? error.message : "Failed to fetch syllabus",
        variant: "destructive",
      })
    } finally {
      setIsLoadingSyllabus(false)
    }
  }

  if (isLoading) {
    return (
      <AuthGuard allowedRoles={["student", "teacher"]}>
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
      <AuthGuard allowedRoles={["student", "teacher"]}>
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
    <AuthGuard allowedRoles={["student", "teacher"]}>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <div className="mb-6">
            <Link href={homeHref}>
              <Button variant="ghost" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back
              </Button>
            </Link>
          </div>

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-balance">{subject.name}</h1>
            {subject.description && (
              <p className="mt-2 text-muted-foreground">{subject.description}</p>
            )}
          </div>

          <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "overview" | "study-plan")} className="space-y-6">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="study-plan">Study Plan</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Upload className="h-5 w-5" />
                      Syllabus
                    </CardTitle>
                    <CardDescription>
                      {isTeacher ? "Upload and update your course syllabus" : "Teacher-provided syllabus status"}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {subject.syllabus_uploaded ? (
                      <div className="space-y-3">
                        <div className="flex items-center gap-2 text-accent">
                          <CheckCircle2 className="h-5 w-5" />
                          <span className="font-medium">Syllabus uploaded</span>
                        </div>
                        {isTeacher && (
                          <Button
                            variant="outline"
                            className="w-full bg-transparent"
                            onClick={handleViewSyllabus}
                            disabled={isLoadingSyllabus}
                          >
                            {isLoadingSyllabus ? <LoadingSpinner size="sm" /> : "View Syllabus"}
                          </Button>
                        )}
                      </div>
                    ) : !isTeacher ? (
                      <p className="text-sm text-muted-foreground">Your teacher will upload the syllabus for this subject.</p>
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
                      {isTeacher ? <Upload className="h-5 w-5" /> : <Sparkles className="h-5 w-5" />}
                      {isTeacher ? "Class Notes" : "Study Plan"}
                    </CardTitle>
                    <CardDescription>
                      {isTeacher ? "Upload chapter notes for student retrieval" : "AI-generated learning roadmap"}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {isTeacher ? (
                      <div className="space-y-3">
                        <div className="space-y-2">
                          <Label htmlFor="class-id">Class</Label>
                          <Select value={teacherClassId} onValueChange={setTeacherClassId}>
                            <SelectTrigger id="class-id">
                              <SelectValue placeholder="Select class" />
                            </SelectTrigger>
                            <SelectContent>
                              {teacherClasses.map((classItem) => (
                                <SelectItem key={classItem.id} value={classItem.id}>
                                  {classItem.name}{classItem.section ? ` - ${classItem.section}` : ""}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="teacher-chapter">Chapter</Label>
                          <Input
                            id="teacher-chapter"
                            value={teacherChapter}
                            onChange={(event) => setTeacherChapter(event.target.value)}
                            placeholder="e.g., Chapter 3: Thermodynamics"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="teacher-notes">Notes File</Label>
                          <Input
                            id="teacher-notes"
                            type="file"
                            accept=".pdf,.docx,image/*"
                            onChange={(event) => setTeacherNotesFile(event.target.files?.[0] || null)}
                          />
                        </div>
                        <Button
                          onClick={handleTeacherNotesUpload}
                          disabled={isNotesUploading || !teacherClasses.length}
                          className="w-full gap-2"
                        >
                          {isNotesUploading ? <LoadingSpinner size="sm" /> : <Upload className="h-4 w-4" />}
                          Upload Notes
                        </Button>
                        {!teacherClasses.length && (
                          <p className="text-xs text-muted-foreground">Assign at least one class to upload teacher notes.</p>
                        )}
                        <div className="space-y-2 border-t pt-3">
                          <p className="text-sm font-medium">Uploaded Notes</p>
                          {isLoadingTeacherNotes ? (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <LoadingSpinner size="sm" />
                              Loading notes...
                            </div>
                          ) : teacherNotes.length === 0 ? (
                            <p className="text-xs text-muted-foreground">No notes uploaded for this subject yet.</p>
                          ) : (
                            <div className="space-y-1">
                              {teacherNotes.slice(0, 5).map((note) => (
                                <div key={note.id} className="rounded-md border p-2 text-xs">
                                  <p className="font-medium">{note.source_file}</p>
                                  <p className="text-muted-foreground">{note.chapter}</p>
                                </div>
                              ))}
                              {teacherNotes.length > 5 && (
                                <p className="text-xs text-muted-foreground">+{teacherNotes.length - 5} more files</p>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    ) : subject.study_plan_generated ? (
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
                          onClick={() => router.push(`/subjects/${subjectId}/generate-plan`)}
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

                {!isTeacher && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <BookOpen className="h-5 w-5" />
                        Quizzes
                      </CardTitle>
                      <CardDescription>Test your knowledge</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <p className="text-sm text-muted-foreground">Create and practice quizzes based on the material</p>
                        <Button
                          className="w-full gap-2"
                          onClick={() => router.push(`/subjects/${subjectId}/quizzes`)}
                        >
                          <BookOpen className="h-4 w-4" />
                          Go to Quizzes
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}
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
                      <Button className="gap-2" onClick={() => router.push(`/subjects/${subjectId}/generate-plan`)}>
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
                        ? Math.min(100, Math.round((chapter.completed_objectives / chapter.learning_objectives.length) * 100))
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
                                router.push(`/subjects/${subjectId}/study?chapter=${chapter.chapter_number}`)
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
                              {chapter.learning_objectives.map((objective, idx) => {
                                const isCompleted = chapter.completed_objectives_list.includes(objective)
                                return (
                                  <li key={idx} className="flex items-start gap-2 text-sm">
                                    {isCompleted ? (
                                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                                    ) : (
                                      <Circle className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                                    )}
                                    <span className={isCompleted ? "text-muted-foreground" : ""}>{objective}</span>
                                  </li>
                                )
                              })}
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

          <Dialog open={difficultyModalOpen} onOpenChange={setDifficultyModalOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Select Difficulty</DialogTitle>
                <DialogDescription>
                  Choose your preferred learning difficulty for this subject. You can change this later from plan or quiz pages.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-2">
                <Label htmlFor="subject-difficulty">Difficulty</Label>
                <Select
                  value={selectedDifficulty}
                  onValueChange={(value) => setSelectedDifficulty(value as SubjectDifficulty)}
                >
                  <SelectTrigger id="subject-difficulty">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="easy">Easy</SelectItem>
                    <SelectItem value="intermediate">Intermediate</SelectItem>
                    <SelectItem value="difficult">Difficult</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <DialogFooter>
                <Button onClick={handleSaveDifficulty}>Save Preference</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={isSyllabusDialogOpen} onOpenChange={setIsSyllabusDialogOpen}>
            <DialogContent className="max-h-[80vh] overflow-hidden">
              <DialogHeader>
                <DialogTitle>Syllabus Preview</DialogTitle>
                <DialogDescription>Extracted syllabus text for this subject.</DialogDescription>
              </DialogHeader>
              <div className="max-h-[55vh] overflow-y-auto rounded-md border p-3">
                <pre className="whitespace-pre-wrap text-sm">{syllabusPreview || "No syllabus content available."}</pre>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsSyllabusDialogOpen(false)}>Close</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </main>
      </div>
    </AuthGuard>
  )
}
