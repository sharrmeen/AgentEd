"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingSpinner } from "@/components/loading-spinner"
import { api } from "@/lib/api"
import { BookOpen, ClipboardList, Plus, Users } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

interface Subject {
  id: string
  subject_name: string
}

interface SubjectListResponse {
  subjects: Subject[]
  total: number
}

interface TeacherClassItem {
  id: string
  name: string
  section?: string | null
  student_count: number
}

interface TeacherClassesResponse {
  classes: TeacherClassItem[]
  total: number
}

interface TeacherClassStudent {
  id: string
  name: string
  username: string
  email?: string | null
}

interface TeacherClassStudentsResponse {
  class_id: string
  students: TeacherClassStudent[]
  total: number
}

interface TeacherProgressStudent {
  student_id: string
  student_name: string
  username: string
  quizzes_completed: number
  average_score: number
}

interface TeacherClassProgressResponse {
  class_id: string
  class_name: string
  student_progress: TeacherProgressStudent[]
}

export default function TeacherPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [classes, setClasses] = useState<TeacherClassItem[]>([])
  const [selectedClassId, setSelectedClassId] = useState("")
  const [classStudents, setClassStudents] = useState<TeacherClassStudent[]>([])
  const [classProgress, setClassProgress] = useState<TeacherProgressStudent[]>([])

  useEffect(() => {
    const load = async () => {
      try {
        const [subjectsResponse, classesResponse] = await Promise.all([
          api.get<SubjectListResponse>("/api/v1/subjects/"),
          api.get<TeacherClassesResponse>("/api/v1/classes/teacher/me"),
        ])

        setSubjects(subjectsResponse.subjects || [])
        setClasses(classesResponse.classes || [])

        const firstClass = classesResponse.classes?.[0]
        if (firstClass) {
          setSelectedClassId(firstClass.id)
        }
      } finally {
        setIsLoading(false)
      }
    }

    load()
  }, [])

  useEffect(() => {
    const loadClassDetails = async () => {
      if (!selectedClassId) {
        setClassStudents([])
        setClassProgress([])
        return
      }

      try {
        const [studentsResponse, progressResponse] = await Promise.all([
          api.get<TeacherClassStudentsResponse>(`/api/v1/classes/teacher/me/${selectedClassId}/students`),
          api.get<TeacherClassProgressResponse>(`/api/v1/classes/teacher/me/${selectedClassId}/progress`),
        ])

        setClassStudents(studentsResponse.students || [])
        setClassProgress(progressResponse.student_progress || [])
      } catch {
        setClassStudents([])
        setClassProgress([])
      }
    }

    loadClassDetails()
  }, [selectedClassId])

  const totalStudents = classes.reduce((sum, cls) => sum + (cls.student_count || 0), 0)

  return (
    <AuthGuard allowedRoles={["teacher"]}>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <div className="mb-8 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-3xl font-bold">Teacher Console</h1>
              <p className="mt-2 text-muted-foreground">Manage subjects and monitor your classes.</p>
            </div>
            <Button onClick={() => router.push("/subjects/new")} className="gap-2 self-start md:self-auto">
              <Plus className="h-4 w-4" />
              Add Subject
            </Button>
          </div>

          {isLoading ? (
            <div className="flex min-h-[40vh] items-center justify-center">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Total Subjects</CardTitle>
                    <CardDescription>Subjects managed by you</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold">{subjects.length}</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Classes</CardTitle>
                    <CardDescription>Total classes assigned</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold">{classes.length}</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Students</CardTitle>
                    <CardDescription>Total students in your classes</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold">{totalStudents}</p>
                  </CardContent>
                </Card>
              </div>

              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>My Classes</CardTitle>
                  <CardDescription>Select a class to view roster and student progress.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {classes.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No classes assigned yet.</p>
                  ) : (
                    <>
                      <Select value={selectedClassId} onValueChange={setSelectedClassId}>
                        <SelectTrigger className="w-full md:w-80">
                          <SelectValue placeholder="Select class" />
                        </SelectTrigger>
                        <SelectContent>
                          {classes.map((cls) => (
                            <SelectItem key={cls.id} value={cls.id}>
                              {cls.name}{cls.section ? ` - ${cls.section}` : ""}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>

                      <div className="grid gap-4 md:grid-cols-2">
                        <Card>
                          <CardHeader>
                            <CardTitle className="text-base">Class Roster</CardTitle>
                          </CardHeader>
                          <CardContent>
                            {classStudents.length === 0 ? (
                              <p className="text-sm text-muted-foreground">No students in this class.</p>
                            ) : (
                              <div className="space-y-2">
                                {classStudents.map((student) => (
                                  <div key={student.id} className="flex items-center justify-between rounded-md border p-2">
                                    <div>
                                      <p className="text-sm font-medium">{student.name}</p>
                                      <p className="text-xs text-muted-foreground">{student.username}</p>
                                    </div>
                                    <Badge variant="outline">
                                      <Users className="mr-1 h-3 w-3" />
                                      Student
                                    </Badge>
                                  </div>
                                ))}
                              </div>
                            )}
                          </CardContent>
                        </Card>

                        <Card>
                          <CardHeader>
                            <CardTitle className="text-base">Class Progress</CardTitle>
                          </CardHeader>
                          <CardContent>
                            {classProgress.length === 0 ? (
                              <p className="text-sm text-muted-foreground">No progress data yet.</p>
                            ) : (
                              <div className="space-y-2">
                                {classProgress.map((item) => (
                                  <div key={item.student_id} className="rounded-md border p-2">
                                    <p className="text-sm font-medium">{item.student_name}</p>
                                    <p className="text-xs text-muted-foreground">
                                      {item.username} • Quizzes: {item.quizzes_completed} • Avg: {Math.round(item.average_score)}%
                                    </p>
                                  </div>
                                ))}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>

              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>My Subjects</CardTitle>
                  <CardDescription>Quick visibility for subjects and planning workflows.</CardDescription>
                </CardHeader>
                <CardContent>
                  {subjects.length === 0 ? (
                    <div className="space-y-3">
                      <p className="text-sm text-muted-foreground">No subjects yet. Add your first subject to get started.</p>
                      <Button variant="outline" onClick={() => router.push("/subjects/new")} className="gap-2">
                        <Plus className="h-4 w-4" />
                        Add Subject
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {subjects.map((subject) => (
                        <div key={subject.id} className="flex items-center justify-between rounded-md border p-3">
                          <div className="flex items-center gap-2">
                            <BookOpen className="h-4 w-4 text-primary" />
                            <span>{subject.subject_name}</span>
                          </div>
                          <ClipboardList className="h-4 w-4 text-muted-foreground" />
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </main>
      </div>
    </AuthGuard>
  )
}
