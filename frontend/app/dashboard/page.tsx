"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingSpinner } from "@/components/loading-spinner"
import { auth } from "@/lib/auth"
import { api } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"
import { BookOpen, Clock, Trophy, TrendingUp, Plus, MoreVertical, Trash2, Edit } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Progress } from "@/components/ui/progress"

// Backend response types
interface BackendSubject {
  id: string
  subject_name: string
  syllabus_id: string | null
  status: string
  plan: object | null
  plan_summary: object | null
  created_at: string
  updated_at: string
}

interface SubjectsResponse {
  subjects: BackendSubject[]
  total: number
}

interface LearningProfile {
  total_study_hours: number
  total_quizzes_completed: number
  streak_days: number
  subjects: Record<string, { average_score: number }>
}

// Frontend display type
interface Subject {
  id: string
  name: string
  description: string
  created_at: string
  syllabus_uploaded: boolean
  study_plan_generated: boolean
}

interface Stats {
  total_study_hours: number
  quizzes_completed: number
  current_streak: number
  average_score: number
}

// Transform backend subject to frontend format
function transformSubject(backendSubject: BackendSubject): Subject {
  return {
    id: backendSubject.id,
    name: backendSubject.subject_name,
    description: "",
    created_at: backendSubject.created_at,
    syllabus_uploaded: !!backendSubject.syllabus_id,
    study_plan_generated: backendSubject.status === "planned" || !!backendSubject.plan,
  }
}

export default function DashboardPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const user = auth.getUser()

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true)
      
      // Fetch subjects and learning profile in parallel
      const [subjectsResponse, profileResponse] = await Promise.all([
        api.get<SubjectsResponse>("/api/v1/subjects/"),
        api.get<LearningProfile>("/api/v1/auth/profile/learning").catch(() => null),
      ])

      // Transform backend subjects to frontend format
      const transformedSubjects = subjectsResponse.subjects.map(transformSubject)
      setSubjects(transformedSubjects)

      // Calculate stats from learning profile
      if (profileResponse) {
        const subjectScores = Object.values(profileResponse.subjects || {})
        const avgScore = subjectScores.length > 0 
          ? subjectScores.reduce((sum, s) => sum + (s.average_score || 0), 0) / subjectScores.length 
          : 0

        setStats({
          total_study_hours: profileResponse.total_study_hours || 0,
          quizzes_completed: profileResponse.total_quizzes_completed || 0,
          current_streak: profileResponse.streak_days || 0,
          average_score: Math.round(avgScore),
        })
      } else {
        setStats({
          total_study_hours: 0,
          quizzes_completed: 0,
          current_streak: 0,
          average_score: 0,
        })
      }
    } catch (error) {
      toast({
        title: "Error loading dashboard",
        description: error instanceof Error ? error.message : "Failed to load data",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const deleteSubject = async (id: string) => {
    try {
      await api.delete(`/api/v1/subjects/${id}`)

      toast({ title: "Subject deleted successfully" })
      fetchDashboardData()
    } catch (error) {
      toast({
        title: "Error deleting subject",
        description: error instanceof Error ? error.message : "Failed to delete",
        variant: "destructive",
      })
    }
  }

  const getProgressPercentage = (subject: Subject) => {
    if (!subject.syllabus_uploaded) return 0
    if (!subject.study_plan_generated) return 33
    return 66
  }

  const getTimeSince = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return "Today"
    if (diffDays === 1) return "Yesterday"
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
    return `${Math.floor(diffDays / 30)} months ago`
  }

  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          {isLoading ? (
            <div className="flex min-h-[60vh] items-center justify-center">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <div className="space-y-8">
              <div>
                <h1 className="text-3xl font-bold text-balance">Welcome back, {user?.name}!</h1>
                <p className="mt-2 text-muted-foreground">Here's your learning progress overview</p>
              </div>

              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Study Hours</CardTitle>
                    <Clock className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats?.total_study_hours || 0}h</div>
                    <p className="text-xs text-muted-foreground">Total time invested</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Quizzes</CardTitle>
                    <BookOpen className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats?.quizzes_completed || 0}</div>
                    <p className="text-xs text-muted-foreground">Completed so far</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Current Streak</CardTitle>
                    <Trophy className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats?.current_streak || 0} days</div>
                    <p className="text-xs text-muted-foreground">Keep it going!</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Avg Score</CardTitle>
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats?.average_score || 0}%</div>
                    <p className="text-xs text-muted-foreground">Quiz performance</p>
                  </CardContent>
                </Card>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold">Your Subjects</h2>
                  <p className="text-sm text-muted-foreground">Manage your learning subjects</p>
                </div>
                <Button onClick={() => router.push("/subjects/new")} className="gap-2">
                  <Plus className="h-4 w-4" />
                  New Subject
                </Button>
              </div>

              {subjects.length === 0 ? (
                <Card className="border-dashed">
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <BookOpen className="mb-4 h-12 w-12 text-muted-foreground" />
                    <h3 className="mb-2 text-lg font-semibold">No subjects yet</h3>
                    <p className="mb-4 text-center text-sm text-muted-foreground">
                      Get started by creating your first subject to begin learning
                    </p>
                    <Button onClick={() => router.push("/subjects/new")} className="gap-2">
                      <Plus className="h-4 w-4" />
                      Create Your First Subject
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {subjects.map((subject) => (
                    <Card key={subject.id} className="group hover:shadow-md transition-shadow">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle
                              className="text-lg hover:text-primary cursor-pointer"
                              onClick={() => router.push(`/subjects/${subject.id}`)}
                            >
                              {subject.name}
                            </CardTitle>
                            <CardDescription className="mt-1 line-clamp-2">
                              {subject.description || "No description"}
                            </CardDescription>
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => router.push(`/subjects/${subject.id}`)}>
                                <Edit className="mr-2 h-4 w-4" />
                                View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => deleteSubject(subject.id)} className="text-destructive">
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Progress</span>
                            <span className="font-medium">{getProgressPercentage(subject)}%</span>
                          </div>
                          <Progress value={getProgressPercentage(subject)} className="h-2" />
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <span>Last active: {getTimeSince(subject.created_at)}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  )
}
