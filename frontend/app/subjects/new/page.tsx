"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"
import { LoadingSpinner } from "@/components/loading-spinner"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import { api } from "@/lib/api"

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

export default function NewSubjectPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    description: "",
  })
  const [errors, setErrors] = useState<{ name?: string; description?: string }>({})

  const validateForm = () => {
    const newErrors: { name?: string; description?: string } = {}

    if (!formData.name.trim()) {
      newErrors.name = "Subject name is required"
    } else if (formData.name.length > 100) {
      newErrors.name = "Subject name must be less than 100 characters"
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

      toast({
        title: "Subject created!",
        description: "Your subject has been created successfully",
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
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto max-w-2xl px-4 py-8">
          <div className="mb-6">
            <Link href="/dashboard">
              <Button variant="ghost" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Dashboard
              </Button>
            </Link>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Create New Subject</CardTitle>
              <CardDescription>Add a new subject to start your learning journey</CardDescription>
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

                <div className="flex gap-3 pt-4">
                  <Button type="submit" disabled={isLoading} className="flex-1">
                    {isLoading ? (
                      <>
                        <LoadingSpinner size="sm" />
                        <span className="ml-2">Creating...</span>
                      </>
                    ) : (
                      "Create Subject"
                    )}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => router.push("/dashboard")}
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
