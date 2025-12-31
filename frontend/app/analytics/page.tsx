"use client"

import { useEffect, useState } from "react"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingSpinner } from "@/components/loading-spinner"
import { useToast } from "@/hooks/use-toast"
import { Clock, Trophy, TrendingUp, BookOpen } from "lucide-react"
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend,
  Cell,
  RadialBarChart,
  RadialBar
} from "recharts"
import { api } from "@/lib/api"

// Backend response type from /api/v1/dashboard/analytics
interface AnalyticsResponse {
  stats: {
    total_study_hours: number
    quizzes_completed: number
    current_streak: number
    average_score: number
  }
  quiz_scores: Array<{ date: string; score: number; title: string }>
  subject_progress: Array<{ name: string; progress: number }>
  study_time_per_subject: Array<{ name: string; hours: number }>
}

// Frontend display types
interface AnalyticsData {
  total_study_hours: number
  quizzes_completed: number
  current_streak: number
  average_score: number
  quiz_scores: Array<{ date: string; score: number; title?: string }>
  subject_progress: Array<{ name: string; progress: number }>
  study_time_per_subject: Array<{ name: string; hours: number }>
}

// Color palette for charts
const COLORS = [
  '#6366f1', // indigo
  '#8b5cf6', // violet
  '#a855f7', // purple
  '#d946ef', // fuchsia
  '#ec4899', // pink
  '#f43f5e', // rose
  '#14b8a6', // teal
  '#10b981', // emerald
]

// Custom tooltip component for quiz scores
const QuizScoreTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-popover border border-border rounded-lg shadow-lg p-3 min-w-[120px]">
        <p className="text-sm font-medium text-foreground mb-1">{label}</p>
        <p className="text-lg font-bold text-primary">
          {payload[0].value}%
        </p>
        {payload[0].payload.title && (
          <p className="text-xs text-muted-foreground mt-1 truncate max-w-[150px]">
            {payload[0].payload.title}
          </p>
        )}
      </div>
    )
  }
  return null
}

// Custom tooltip for subject progress
const SubjectProgressTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-popover border border-border rounded-lg shadow-lg p-3 min-w-[120px]">
        <p className="text-sm font-medium text-foreground mb-1">{label}</p>
        <p className="text-lg font-bold" style={{ color: payload[0].fill }}>
          {payload[0].value}% Complete
        </p>
      </div>
    )
  }
  return null
}

// Custom tooltip for study time
const StudyTimeTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-popover border border-border rounded-lg shadow-lg p-3 min-w-[120px]">
        <p className="text-sm font-medium text-foreground mb-1">{label}</p>
        <p className="text-lg font-bold" style={{ color: payload[0].fill }}>
          {payload[0].value}h
        </p>
      </div>
    )
  }
  return null
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
      
      // Fetch all analytics data from the new endpoint
      const response = await api.get<AnalyticsResponse>("/api/v1/dashboard/analytics")
      
      const analyticsData: AnalyticsData = {
        total_study_hours: response.stats.total_study_hours,
        quizzes_completed: response.stats.quizzes_completed,
        current_streak: response.stats.current_streak,
        average_score: response.stats.average_score,
        quiz_scores: response.quiz_scores,
        subject_progress: response.subject_progress,
        study_time_per_subject: response.study_time_per_subject,
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
                <Card className="border-border/50 shadow-sm">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg font-semibold">Quiz Score Trends</CardTitle>
                    <CardDescription>Your performance over time</CardDescription>
                  </CardHeader>
                  <CardContent className="pt-4">
                    {analytics.quiz_scores.length > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart 
                          data={analytics.quiz_scores}
                          margin={{ top: 10, right: 30, left: 0, bottom: 10 }}
                        >
                          <defs>
                            <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                              <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid 
                            strokeDasharray="3 3" 
                            stroke="hsl(var(--border))" 
                            opacity={0.5}
                            vertical={false}
                          />
                          <XAxis 
                            dataKey="date" 
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                            tickLine={false}
                            axisLine={{ stroke: 'hsl(var(--border))' }}
                            dy={10}
                          />
                          <YAxis 
                            domain={[0, 100]}
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(value) => `${value}%`}
                            width={50}
                          />
                          <Tooltip content={<QuizScoreTooltip />} />
                          <Line
                            type="monotone"
                            dataKey="score"
                            stroke="#6366f1"
                            strokeWidth={3}
                            dot={{ 
                              r: 5, 
                              fill: '#6366f1', 
                              strokeWidth: 2, 
                              stroke: '#fff' 
                            }}
                            activeDot={{ 
                              r: 7, 
                              fill: '#6366f1', 
                              strokeWidth: 2, 
                              stroke: '#fff' 
                            }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex h-[300px] flex-col items-center justify-center text-muted-foreground">
                        <BookOpen className="h-12 w-12 mb-3 opacity-50" />
                        <p className="text-sm">No quiz data available yet</p>
                        <p className="text-xs mt-1">Complete some quizzes to see your trends</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="border-border/50 shadow-sm">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg font-semibold">Subject Progress</CardTitle>
                    <CardDescription>Completion percentage by subject</CardDescription>
                  </CardHeader>
                  <CardContent className="pt-4">
                    {analytics.subject_progress.length > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart 
                          data={analytics.subject_progress}
                          margin={{ top: 10, right: 30, left: 0, bottom: 10 }}
                        >
                          <CartesianGrid 
                            strokeDasharray="3 3" 
                            stroke="hsl(var(--border))" 
                            opacity={0.5}
                            vertical={false}
                          />
                          <XAxis 
                            dataKey="name" 
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                            tickLine={false}
                            axisLine={{ stroke: 'hsl(var(--border))' }}
                            interval={0}
                            angle={-20}
                            textAnchor="end"
                            height={60}
                          />
                          <YAxis 
                            domain={[0, 100]}
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(value) => `${value}%`}
                            width={50}
                          />
                          <Tooltip content={<SubjectProgressTooltip />} />
                          <Bar 
                            dataKey="progress" 
                            radius={[6, 6, 0, 0]}
                            maxBarSize={50}
                          >
                            {analytics.subject_progress.map((entry, index) => (
                              <Cell 
                                key={`cell-${index}`} 
                                fill={COLORS[index % COLORS.length]}
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex h-[300px] flex-col items-center justify-center text-muted-foreground">
                        <TrendingUp className="h-12 w-12 mb-3 opacity-50" />
                        <p className="text-sm">No subject data available yet</p>
                        <p className="text-xs mt-1">Add subjects and start studying</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              <Card className="border-border/50 shadow-sm">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg font-semibold">Time Spent Per Subject</CardTitle>
                  <CardDescription>Study hours breakdown</CardDescription>
                </CardHeader>
                <CardContent className="pt-4">
                  {analytics.study_time_per_subject.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart 
                        data={analytics.study_time_per_subject} 
                        layout="vertical"
                        margin={{ top: 10, right: 30, left: 20, bottom: 10 }}
                      >
                        <CartesianGrid 
                          strokeDasharray="3 3" 
                          stroke="hsl(var(--border))" 
                          opacity={0.5}
                          horizontal={false}
                        />
                        <XAxis 
                          type="number" 
                          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                          tickLine={false}
                          axisLine={{ stroke: 'hsl(var(--border))' }}
                          domain={[0, 'auto']}
                          tickFormatter={(value) => `${value}h`}
                        />
                        <YAxis 
                          dataKey="name" 
                          type="category"
                          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                          tickLine={false}
                          axisLine={false}
                          width={100}
                        />
                        <Tooltip content={<StudyTimeTooltip />} />
                        <Bar 
                          dataKey="hours" 
                          radius={[0, 6, 6, 0]}
                          maxBarSize={30}
                        >
                          {analytics.study_time_per_subject.map((entry, index) => (
                            <Cell 
                              key={`cell-${index}`} 
                              fill={COLORS[index % COLORS.length]}
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex h-[300px] flex-col items-center justify-center text-muted-foreground">
                      <Clock className="h-12 w-12 mb-3 opacity-50" />
                      <p className="text-sm">No study time data available yet</p>
                      <p className="text-xs mt-1">Start studying to track your time</p>
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
