"use client"

import { useEffect, useState } from "react"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingSpinner } from "@/components/loading-spinner"
import { useToast } from "@/hooks/use-toast"
import { Clock, Trophy, TrendingUp, BookOpen } from "lucide-react"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Area, AreaChart, Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { api } from "@/lib/api"

// Backend response types
interface SubjectProfile {
  subject_id: string
  subject_name: string
  total_quizzes_taken: number
  average_score: number
  highest_score: number
  strengths: string[]
  weak_areas: string[]
}

interface LearningProfile {
  subjects: Record<string, SubjectProfile>
  total_study_hours: number
  total_quizzes_completed: number
  total_objectives_completed: number
  learning_style: string | null
  difficulty_preference: string | null
  streak_days: number
  last_active: string | null
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

// Frontend display types
interface AnalyticsData {
  total_study_hours: number
  quizzes_completed: number
  current_streak: number
  average_score: number
  quiz_scores: Array<{ date: string; score: number }>
  subject_progress: Array<{ name: string; progress: number }>
  study_time_per_subject: Array<{ name: string; hours: number }>
}

const chartConfig = {
  score: {
    label: "Score",
    color: "hsl(var(--chart-1))",
  },
  progress: {
    label: "Progress",
    color: "hsl(var(--chart-2))",
  },
  hours: {
    label: "Hours",
    color: "hsl(var(--chart-3))",
  },
}

export default function AnalyticsPage() {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
    try {
      setIsLoading(true)
      
      // Fetch learning profile for overall stats
      const profileData = await api.get<LearningProfile>("/api/v1/auth/profile/learning")
      
      // Fetch recent quiz results for the chart
      let quizScores: Array<{ date: string; score: number }> = []
      try {
        const resultsData = await api.get<QuizResultsResponse>("/api/v1/quiz/results")
        quizScores = resultsData.results
          .slice(0, 10) // Last 10 results
          .reverse() // Oldest first for chart
          .map((r) => ({
            date: new Date(r.completed_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            score: Math.round(r.percentage),
          }))
      } catch {
        // No quiz results yet
      }

      // Transform subject profiles to chart data
      const subjectProfiles = Object.values(profileData.subjects)
      const subjectProgress = subjectProfiles.map((s) => ({
        name: s.subject_name.length > 15 ? s.subject_name.substring(0, 15) + "..." : s.subject_name,
        progress: Math.round(s.average_score),
      }))

      // Calculate average score across all subjects
      const avgScore = subjectProfiles.length > 0
        ? subjectProfiles.reduce((sum, s) => sum + s.average_score, 0) / subjectProfiles.length
        : 0

      const analyticsData: AnalyticsData = {
        total_study_hours: Math.round(profileData.total_study_hours * 10) / 10,
        quizzes_completed: profileData.total_quizzes_completed,
        current_streak: profileData.streak_days,
        average_score: Math.round(avgScore),
        quiz_scores: quizScores,
        subject_progress: subjectProgress,
        study_time_per_subject: [], // Would need separate tracking
      }

      setAnalytics(analyticsData)
    } catch (error) {
      toast({
        title: "Error loading analytics",
        description: error instanceof Error ? error.message : "Failed to load analytics",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-balance">Learning Analytics</h1>
            <p className="mt-2 text-muted-foreground">Track your progress and performance</p>
          </div>

          {isLoading ? (
            <div className="flex min-h-[60vh] items-center justify-center">
              <LoadingSpinner size="lg" />
            </div>
          ) : analytics ? (
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Study Hours</CardTitle>
                    <Clock className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.total_study_hours}h</div>
                    <p className="text-xs text-muted-foreground">Total time invested</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Quizzes</CardTitle>
                    <BookOpen className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.quizzes_completed}</div>
                    <p className="text-xs text-muted-foreground">Completed so far</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Current Streak</CardTitle>
                    <Trophy className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.current_streak} days</div>
                    <p className="text-xs text-muted-foreground">Keep it going!</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Avg Score</CardTitle>
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.average_score}%</div>
                    <p className="text-xs text-muted-foreground">Quiz performance</p>
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Quiz Score Trends</CardTitle>
                    <CardDescription>Your performance over time</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {analytics.quiz_scores.length > 0 ? (
                      <ChartContainer config={chartConfig} className="h-[300px]">
                        <AreaChart data={analytics.quiz_scores}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <ChartTooltip content={<ChartTooltipContent />} />
                          <Area
                            type="monotone"
                            dataKey="score"
                            stroke="var(--color-score)"
                            fill="var(--color-score)"
                            fillOpacity={0.2}
                          />
                        </AreaChart>
                      </ChartContainer>
                    ) : (
                      <div className="flex h-[300px] items-center justify-center text-muted-foreground">
                        No quiz data available yet
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Subject Progress</CardTitle>
                    <CardDescription>Completion percentage by subject</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {analytics.subject_progress.length > 0 ? (
                      <ChartContainer config={chartConfig} className="h-[300px]">
                        <BarChart data={analytics.subject_progress}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <ChartTooltip content={<ChartTooltipContent />} />
                          <Bar dataKey="progress" fill="var(--color-progress)" radius={[8, 8, 0, 0]} />
                        </BarChart>
                      </ChartContainer>
                    ) : (
                      <div className="flex h-[300px] items-center justify-center text-muted-foreground">
                        No subject data available yet
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Time Spent Per Subject</CardTitle>
                  <CardDescription>Study hours breakdown</CardDescription>
                </CardHeader>
                <CardContent>
                  {analytics.study_time_per_subject.length > 0 ? (
                    <ChartContainer config={chartConfig} className="h-[300px]">
                      <BarChart data={analytics.study_time_per_subject} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" />
                        <YAxis dataKey="name" type="category" />
                        <ChartTooltip content={<ChartTooltipContent />} />
                        <Bar dataKey="hours" fill="var(--color-hours)" radius={[0, 8, 8, 0]} />
                      </BarChart>
                    </ChartContainer>
                  ) : (
                    <div className="flex h-[300px] items-center justify-center text-muted-foreground">
                      No study time data available yet
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">No analytics data available</p>
              </CardContent>
            </Card>
          )}
        </main>
      </div>
    </AuthGuard>
  )
}
