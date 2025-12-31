"use client"

import type React from "react"

import { useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"
import { LoadingSpinner } from "@/components/loading-spinner"
import { ArrowLeft, Sparkles } from "lucide-react"
import Link from "next/link"
import { api } from "@/lib/api"

export default function GeneratePlanPage() {
  const router = useRouter()
  const params = useParams()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState({
    target_days: "30",
    daily_hours: "2",
    difficulty: "intermediate",
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      // Backend endpoint: POST /api/v1/planner/{subject_id}/generate
      await api.post(`/api/v1/planner/${params.id}/generate`, {
        target_days: Number.parseInt(formData.target_days),
        daily_hours: Number.parseFloat(formData.daily_hours),
        // Note: 'difficulty' is stored in preferences object
        preferences: {
          difficulty: formData.difficulty,
        },
      })

      toast({
        title: "Study plan generated!",
        description: "Your personalized learning plan is ready",
      })

      router.push(`/subjects/${params.id}`)
    } catch (error) {
      toast({
        title: "Error generating plan",
        description: error instanceof Error ? error.message : "Failed to generate study plan",
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
            <Link href={`/subjects/${params.id}`}>
              <Button variant="ghost" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Subject
              </Button>
            </Link>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Generate Study Plan
              </CardTitle>
              <CardDescription>Customize your learning schedule based on your availability</CardDescription>
            </CardHeader>
            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="target_days">Target Completion (Days)</Label>
                  <Input
                    id="target_days"
                    type="number"
                    min="1"
                    max="365"
                    value={formData.target_days}
                    onChange={(e) => setFormData({ ...formData, target_days: e.target.value })}
                    disabled={isLoading}
                  />
                  <p className="text-xs text-muted-foreground">How many days do you want to complete this subject?</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="daily_hours">Daily Study Hours</Label>
                  <Input
                    id="daily_hours"
                    type="number"
                    min="0.5"
                    max="8"
                    step="0.5"
                    value={formData.daily_hours}
                    onChange={(e) => setFormData({ ...formData, daily_hours: e.target.value })}
                    disabled={isLoading}
                  />
                  <p className="text-xs text-muted-foreground">How many hours can you study per day?</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="difficulty">Difficulty Level</Label>
                  <Select
                    value={formData.difficulty}
                    onValueChange={(value) => setFormData({ ...formData, difficulty: value })}
                    disabled={isLoading}
                  >
                    <SelectTrigger id="difficulty">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="beginner">Beginner</SelectItem>
                      <SelectItem value="intermediate">Intermediate</SelectItem>
                      <SelectItem value="advanced">Advanced</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">Your familiarity with the subject</p>
                </div>

                <div className="flex gap-3 pt-4">
                  <Button type="submit" disabled={isLoading} className="flex-1 gap-2">
                    {isLoading ? (
                      <>
                        <LoadingSpinner size="sm" />
                        <span>Generating...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        Generate Plan
                      </>
                    )}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => router.push(`/subjects/${params.id}`)}
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
