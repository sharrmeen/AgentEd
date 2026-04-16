"use client"

import type React from "react"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"
import { LoadingSpinner } from "@/components/loading-spinner"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import { api } from "@/lib/api"
import { auth } from "@/lib/auth"

// Backend response type
interface CreateSubjectResponse {
  id: string
  subject_name: string
  syllabus_id: string | null
  status: string
  plan: object | null
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

export default function NewSubjectPage() {
  const router = useRouter()
  const { toast } = useToast()
  const user = auth.getUser()
  const isTeacher = user?.role === "teacher"
  const backHref = auth.getDefaultRoute()
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    description: "",
  })
  const [selectedSyllabus, setSelectedSyllabus] = useState<File | null>(null)
  const [teacherClassId, setTeacherClassId] = useState("")
  const [teacherClasses, setTeacherClasses] = useState<Array<{ id: string; name: string; section?: string | null }>>([])
  const [errors, setErrors] = useState<{ name?: string; syllabus?: string }>({})

  useEffect(() => {
    if (!isTeacher) return
    fetchTeacherClasses()
  }, [isTeacher])

  const fetchTeacherClasses = async () => {
    try {
      const response = await api.get<ClassListResponse>("/api/v1/classes/teacher/me")
      setTeacherClasses(response.classes || [])
      if (response.classes?.length) {
        setTeacherClassId(response.classes[0].id)
      }
    } catch {
      // Class list is optional for syllabus upload.
    }
  }

  const validateForm = () => {
    const newErrors: { name?: string; syllabus?: string } = {}

    if (!formData.name.trim()) {
      newErrors.name = "Subject name is required"
    } else if (formData.name.length > 100) {
      newErrors.name = "Subject name must be less than 100 characters"
    }

    if (isTeacher && !selectedSyllabus) {
      newErrors.syllabus = "Syllabus file is required for teacher subject creation"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    setIsLoading(true)

    try {
      // Backend expects subject_name, not name
      const response = await api.post<CreateSubjectResponse>("/api/v1/subjects/", {
        subject_name: formData.name.trim(),
      })

      if (isTeacher && selectedSyllabus) {
        const params: Record<string, string> = {}
        if (teacherClassId) {
          params.class_id = teacherClassId
        }
        await api.uploadFile(`/api/v1/syllabus/${response.id}/upload`, selectedSyllabus, params)
      }

      toast({
        title: isTeacher ? "Subject and syllabus created!" : "Subject created!",
        description: isTeacher
          ? "Your subject was created and syllabus uploaded successfully"
          : "Your subject has been created successfully",
      })

      router.push(`/subjects/${response.id}`)
    } catch (error) {
      toast({
        title: "Error creating subject",
        description: error instanceof Error ? error.message : "Failed to create subject",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthGuard allowedRoles={["student", "teacher"]}>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto max-w-2xl px-4 py-8">
          <div className="mb-6">
            <Link href={backHref}>
              <Button variant="ghost" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back
              </Button>
            </Link>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Create New Subject</CardTitle>
              <CardDescription>
                {isTeacher
                  ? "Create a subject and upload syllabus in one step"
                  : "Add a new subject to start your learning journey"}
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">
                    Subject Name <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="name"
                    type="text"
                    placeholder="e.g., Advanced Mathematics, Biology 101"
                    value={formData.name}
                    onChange={(e) => {
                      setFormData({ ...formData, name: e.target.value })
                      setErrors({ ...errors, name: undefined })
                    }}
                    disabled={isLoading}
                    className={errors.name ? "border-destructive" : ""}
                  />
                  {errors.name && <p className="text-sm text-destructive">{errors.name}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description (Optional)</Label>
                  <Textarea
                    id="description"
                    placeholder="Describe what you'll learn in this subject..."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    disabled={isLoading}
                    rows={4}
                  />
                </div>

                {isTeacher && (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="teacher-class">Class (Optional)</Label>
                      <Select value={teacherClassId} onValueChange={setTeacherClassId}>
                        <SelectTrigger id="teacher-class">
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
                      <Label htmlFor="syllabus-file">
                        Syllabus File <span className="text-destructive">*</span>
                      </Label>
                      <Input
                        id="syllabus-file"
                        type="file"
                        accept=".pdf,.docx,.txt,image/*"
                        onChange={(e) => {
                          setSelectedSyllabus(e.target.files?.[0] || null)
                          setErrors({ ...errors, syllabus: undefined })
                        }}
                        disabled={isLoading}
                      />
                      {errors.syllabus && <p className="text-sm text-destructive">{errors.syllabus}</p>}
                    </div>
                  </>
                )}

                <div className="flex gap-3 pt-4">
                  <Button type="submit" disabled={isLoading} className="flex-1">
                    {isLoading ? (
                      <>
                        <LoadingSpinner size="sm" />
                        <span className="ml-2">Creating...</span>
                      </>
                    ) : (
                      isTeacher ? "Create Subject & Upload Syllabus" : "Create Subject"
                    )}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => router.push(backHref)}
                    disabled={isLoading}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </form>
          </Card>
        </main>
      </div>
    </AuthGuard>
  )
}
