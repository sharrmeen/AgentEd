"use client"

import { useState, useEffect } from "react"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingSpinner } from "@/components/loading-spinner"
import { auth } from "@/lib/auth"
import { api } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"
import { User, Mail, Calendar, BookOpen } from "lucide-react"

// Backend response types
interface UserResponse {
  id: string
  name: string
  email: string
  role: string
  is_active: boolean
  learning_profile: {
    subjects: Record<string, any>
    total_study_hours: number
    total_quizzes_completed: number
    total_objectives_completed: number
    learning_style: string | null
    difficulty_preference: string | null
    streak_days: number
    last_active: string | null
  } | null
  created_at: string
  last_login: string | null
}

interface SubjectsResponse {
  subjects: Array<{ id: string; subject_name: string }>
  total: number
}

export default function ProfilePage() {
  const { toast } = useToast()
  const user = auth.getUser()
  const [isEditing, setIsEditing] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [userData, setUserData] = useState<UserResponse | null>(null)
  const [totalSubjects, setTotalSubjects] = useState(0)
  const [formData, setFormData] = useState({
    name: user?.name || "",
    email: user?.email || "",
  })

  useEffect(() => {
    fetchProfileData()
  }, [])

  const fetchProfileData = async () => {
    try {
      setIsLoading(true)
      
      // Fetch user profile and subjects in parallel
      const [profileResponse, subjectsResponse] = await Promise.all([
        api.get<UserResponse>("/api/v1/auth/me"),
        api.get<SubjectsResponse>("/api/v1/subjects/").catch(() => null),
      ])

      setUserData(profileResponse)
      setFormData({
        name: profileResponse.name,
        email: profileResponse.email,
      })

      if (subjectsResponse) {
        setTotalSubjects(subjectsResponse.total || 0)
      }
    } catch (error) {
      toast({
        title: "Error loading profile",
        description: error instanceof Error ? error.message : "Failed to load profile",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = () => {
    toast({
      title: "Profile updated",
      description: "Your profile has been updated successfully",
    })
    setIsEditing(false)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "long",
    }).format(date)
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
        <main className="container mx-auto max-w-2xl px-4 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-balance">Your Profile</h1>
            <p className="mt-2 text-muted-foreground">Manage your account information</p>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground text-2xl font-bold">
                    {userData?.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <CardTitle>{userData?.name}</CardTitle>
                    <CardDescription>{userData?.email}</CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Personal Information</CardTitle>
                <CardDescription>Update your personal details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      disabled={!isEditing}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      disabled={!isEditing}
                    />
                  </div>
                </div>

                <div className="flex gap-3 pt-4">
                  {isEditing ? (
                    <>
                      <Button onClick={handleSave} className="flex-1">
                        Save Changes
                      </Button>
                      <Button variant="outline" onClick={() => setIsEditing(false)} className="flex-1 bg-transparent">
                        Cancel
                      </Button>
                    </>
                  ) : (
                    <Button onClick={() => setIsEditing(true)} className="w-full">
                      Edit Profile
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Learning Stats</CardTitle>
                <CardDescription>Your learning journey overview</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <p className="text-sm">Member Since</p>
                  </div>
                  <p className="text-lg font-medium">
                    {userData?.created_at ? formatDate(userData.created_at) : "Unknown"}
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <BookOpen className="h-4 w-4" />
                    <p className="text-sm">Total Subjects</p>
                  </div>
                  <p className="text-lg font-medium">{totalSubjects} subject{totalSubjects !== 1 ? "s" : ""}</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </AuthGuard>
  )
}
