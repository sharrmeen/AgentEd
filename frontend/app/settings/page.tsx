"use client"

import { useEffect, useState } from "react"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { useToast } from "@/hooks/use-toast"
import { Moon, Bell, Trash2, Mail, Clock, Flame, BarChart3, Send } from "lucide-react"
import { api } from "@/lib/api"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { LoadingSpinner } from "@/components/loading-spinner"

interface NotificationPreferences {
  email_enabled: boolean
  study_reminders: boolean
  reminder_hour: number
  streak_alerts: boolean
  weekly_summary: boolean
  quiz_results: boolean
}

export default function SettingsPage() {
  const { toast } = useToast()
  const [darkMode, setDarkMode] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isSendingTest, setIsSendingTest] = useState(false)
  const [notificationPrefs, setNotificationPrefs] = useState<NotificationPreferences>({
    email_enabled: true,
    study_reminders: true,
    reminder_hour: 9,
    streak_alerts: true,
    weekly_summary: true,
    quiz_results: true,
  })

  useEffect(() => {
    const isDark = document.documentElement.classList.contains("dark")
    setDarkMode(isDark)
    fetchNotificationPreferences()
  }, [])

  const fetchNotificationPreferences = async () => {
    try {
      const prefs = await api.get<NotificationPreferences>("/api/v1/notifications/preferences")
      setNotificationPrefs(prefs)
    } catch (error) {
      console.log("Could not fetch notification preferences, using defaults")
    } finally {
      setIsLoading(false)
    }
  }

  const updateNotificationPrefs = async (updates: Partial<NotificationPreferences>) => {
    const newPrefs = { ...notificationPrefs, ...updates }
    setNotificationPrefs(newPrefs)
    setIsSaving(true)
    
    try {
      await api.put("/api/v1/notifications/preferences", newPrefs)
      toast({ 
        title: "Settings updated", 
        description: "Notification preferences saved" 
      })
    } catch (error) {
      toast({ 
        title: "Error", 
        description: "Failed to save notification preferences",
        variant: "destructive"
      })
      // Revert on error
      setNotificationPrefs(notificationPrefs)
    } finally {
      setIsSaving(false)
    }
  }

  const sendTestEmail = async () => {
    setIsSendingTest(true)
    try {
      await api.post("/api/v1/notifications/test", {
        email_type: "study_reminder"
      })
      toast({
        title: "Test email sent!",
        description: "Check your inbox for the test reminder email"
      })
    } catch (error) {
      toast({
        title: "Failed to send test email",
        description: "Make sure email is configured on the server",
        variant: "destructive"
      })
    } finally {
      setIsSendingTest(false)
    }
  }

  const toggleDarkMode = (checked: boolean) => {
    const html = document.documentElement
    if (checked) {
      html.classList.add("dark")
      localStorage.setItem("theme", "dark")
    } else {
      html.classList.remove("dark")
      localStorage.setItem("theme", "light")
    }
    setDarkMode(checked)
    toast({ title: "Theme updated", description: `Switched to ${checked ? "dark" : "light"} mode` })
  }

  const handleDeleteAccount = () => {
    toast({
      title: "Account deletion",
      description: "This feature is not yet implemented",
      variant: "destructive",
    })
  }

  // Generate hour options for reminder time
  const hourOptions = Array.from({ length: 24 }, (_, i) => {
    const hour = i
    const label = hour === 0 ? "12:00 AM" : 
                  hour < 12 ? `${hour}:00 AM` : 
                  hour === 12 ? "12:00 PM" : 
                  `${hour - 12}:00 PM`
    return { value: hour, label }
  })

  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto max-w-2xl px-4 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-balance">Settings</h1>
            <p className="mt-2 text-muted-foreground">Manage your preferences and account</p>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Appearance</CardTitle>
                <CardDescription>Customize how AgentED looks</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Moon className="h-4 w-4 text-muted-foreground" />
                    <Label htmlFor="dark-mode">Dark Mode</Label>
                  </div>
                  <Switch id="dark-mode" checked={darkMode} onCheckedChange={toggleDarkMode} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Email Notifications</CardTitle>
                <CardDescription>Manage your email notification preferences</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {isLoading ? (
                  <div className="flex justify-center py-4">
                    <LoadingSpinner />
                  </div>
                ) : (
                  <>
                    {/* Master toggle */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <Label htmlFor="email-enabled">Email Notifications</Label>
                          <p className="text-xs text-muted-foreground">Receive emails from AgentED</p>
                        </div>
                      </div>
                      <Switch
                        id="email-enabled"
                        checked={notificationPrefs.email_enabled}
                        onCheckedChange={(checked) => updateNotificationPrefs({ email_enabled: checked })}
                        disabled={isSaving}
                      />
                    </div>

                    {notificationPrefs.email_enabled && (
                      <>
                        <div className="border-t pt-4 space-y-4">
                          {/* Study Reminders */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Bell className="h-4 w-4 text-muted-foreground" />
                              <div>
                                <Label htmlFor="study-reminders">Daily Study Reminders</Label>
                                <p className="text-xs text-muted-foreground">Get reminded to study every day</p>
                              </div>
                            </div>
                            <Switch
                              id="study-reminders"
                              checked={notificationPrefs.study_reminders}
                              onCheckedChange={(checked) => updateNotificationPrefs({ study_reminders: checked })}
                              disabled={isSaving}
                            />
                          </div>

                          {/* Reminder Time */}
                          {notificationPrefs.study_reminders && (
                            <div className="flex items-center justify-between ml-6">
                              <div className="flex items-center gap-2">
                                <Clock className="h-4 w-4 text-muted-foreground" />
                                <Label>Reminder Time (UTC)</Label>
                              </div>
                              <Select
                                value={notificationPrefs.reminder_hour.toString()}
                                onValueChange={(value) => updateNotificationPrefs({ reminder_hour: parseInt(value) })}
                                disabled={isSaving}
                              >
                                <SelectTrigger className="w-[140px]">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {hourOptions.map((option) => (
                                    <SelectItem key={option.value} value={option.value.toString()}>
                                      {option.label}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                          )}

                          {/* Streak Alerts */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Flame className="h-4 w-4 text-muted-foreground" />
                              <div>
                                <Label htmlFor="streak-alerts">Streak Alerts</Label>
                                <p className="text-xs text-muted-foreground">Alert when your streak is at risk</p>
                              </div>
                            </div>
                            <Switch
                              id="streak-alerts"
                              checked={notificationPrefs.streak_alerts}
                              onCheckedChange={(checked) => updateNotificationPrefs({ streak_alerts: checked })}
                              disabled={isSaving}
                            />
                          </div>

                          {/* Weekly Summary */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <BarChart3 className="h-4 w-4 text-muted-foreground" />
                              <div>
                                <Label htmlFor="weekly-summary">Weekly Summary</Label>
                                <p className="text-xs text-muted-foreground">Receive weekly progress reports</p>
                              </div>
                            </div>
                            <Switch
                              id="weekly-summary"
                              checked={notificationPrefs.weekly_summary}
                              onCheckedChange={(checked) => updateNotificationPrefs({ weekly_summary: checked })}
                              disabled={isSaving}
                            />
                          </div>
                        </div>

                        {/* Test Email Button */}
                        <div className="border-t pt-4">
                          <Button 
                            variant="outline" 
                            onClick={sendTestEmail}
                            disabled={isSendingTest}
                            className="gap-2"
                          >
                            {isSendingTest ? (
                              <>
                                <LoadingSpinner size="sm" />
                                Sending...
                              </>
                            ) : (
                              <>
                                <Send className="h-4 w-4" />
                                Send Test Email
                              </>
                            )}
                          </Button>
                          <p className="text-xs text-muted-foreground mt-2">
                            Send a test email to verify your notification setup
                          </p>
                        </div>
                      </>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            <Card className="border-destructive">
              <CardHeader>
                <CardTitle className="text-destructive">Danger Zone</CardTitle>
                <CardDescription>Irreversible actions</CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="destructive" onClick={handleDeleteAccount} className="gap-2">
                  <Trash2 className="h-4 w-4" />
                  Delete Account
                </Button>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </AuthGuard>
  )
}
