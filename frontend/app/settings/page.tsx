"use client"

import { useEffect, useState } from "react"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { useToast } from "@/hooks/use-toast"
import { Moon, Bell, Trash2 } from "lucide-react"

export default function SettingsPage() {
  const { toast } = useToast()
  const [darkMode, setDarkMode] = useState(false)
  const [notifications, setNotifications] = useState(true)

  useEffect(() => {
    const isDark = document.documentElement.classList.contains("dark")
    setDarkMode(isDark)
  }, [])

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
                <CardTitle>Notifications</CardTitle>
                <CardDescription>Manage notification preferences</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bell className="h-4 w-4 text-muted-foreground" />
                    <Label htmlFor="notifications">Email Notifications</Label>
                  </div>
                  <Switch
                    id="notifications"
                    checked={notifications}
                    onCheckedChange={(checked) => {
                      setNotifications(checked)
                      toast({ title: "Settings updated", description: "Notification preferences saved" })
                    }}
                  />
                </div>
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
