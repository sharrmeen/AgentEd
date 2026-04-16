"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { useToast } from "@/hooks/use-toast"
import { auth, TokenResponse } from "@/lib/auth"
import { api } from "@/lib/api"
import { LoadingSpinner } from "@/components/loading-spinner"
import { Eye, EyeOff, GraduationCap } from "lucide-react"

export default function LoginPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [mustChangePassword, setMustChangePassword] = useState(false)
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    rememberMe: false,
  })
  const [resetData, setResetData] = useState({
    email: "",
    new_password: "",
    confirm_password: "",
    current_password: "",
  })
  const [errors, setErrors] = useState<{ username?: string; password?: string }>({})
  const [resetErrors, setResetErrors] = useState<{ email?: string; new_password?: string; confirm_password?: string }>({})

  const validateForm = () => {
    const newErrors: { username?: string; password?: string } = {}

    if (!formData.username) {
      newErrors.username = "Username is required"
    }

    if (!formData.password) {
      newErrors.password = "Password is required"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const validateResetForm = () => {
    const newErrors: { email?: string; new_password?: string; confirm_password?: string } = {}

    if (!resetData.email) {
      newErrors.email = "Email is required"
    } else if (!/\S+@\S+\.\S+/.test(resetData.email)) {
      newErrors.email = "Enter a valid email"
    }

    if (!resetData.new_password) {
      newErrors.new_password = "New password is required"
    } else if (resetData.new_password.length < 6) {
      newErrors.new_password = "Password must be at least 6 characters"
    }

    if (!resetData.confirm_password) {
      newErrors.confirm_password = "Please confirm new password"
    } else if (resetData.new_password !== resetData.confirm_password) {
      newErrors.confirm_password = "Passwords do not match"
    }

    setResetErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    setIsLoading(true)

    try {
      const response = await api.post<TokenResponse>("/api/v1/auth/login", {
        username: formData.username,
        password: formData.password,
      })

      auth.handleAuthResponse(response)

      if (response.must_change_password) {
        setMustChangePassword(true)
        setResetData((prev) => ({
          ...prev,
          current_password: formData.password,
        }))
        toast({
          title: "Password reset required",
          description: "Please set your email and choose a new password.",
        })
        return
      }

      toast({
        title: "Welcome back!",
        description: `Logged in as ${response.name}`,
      })

      router.push(auth.getDefaultRoute())
    } catch (error) {
      toast({
        title: "Login failed",
        description: error instanceof Error ? error.message : "Invalid credentials",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleFirstLoginReset = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateResetForm()) return

    setIsLoading(true)

    try {
      await api.post<{ success: boolean; message: string }>("/api/v1/auth/change-password", {
        email: resetData.email,
        current_password: resetData.current_password,
        new_password: resetData.new_password,
      })

      toast({
        title: "Password updated",
        description: "Your account is now active.",
      })

      setMustChangePassword(false)
      router.push(auth.getDefaultRoute())
    } catch (error) {
      toast({
        title: "Password update failed",
        description: error instanceof Error ? error.message : "Could not update password",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-linear-to-br from-primary/5 via-background to-secondary/5 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <GraduationCap className="h-7 w-7" />
          </div>
          <CardTitle className="text-2xl font-bold">Welcome to AgentED</CardTitle>
          <CardDescription>
            {mustChangePassword ? "First login setup" : "Sign in with username and password"}
          </CardDescription>
        </CardHeader>
        {mustChangePassword ? (
          <form onSubmit={handleFirstLoginReset}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="reset-email">Email</Label>
                <Input
                  id="reset-email"
                  type="email"
                  placeholder="you@example.com"
                  value={resetData.email}
                  onChange={(e) => {
                    setResetData({ ...resetData, email: e.target.value })
                    setResetErrors({ ...resetErrors, email: undefined })
                  }}
                  disabled={isLoading}
                  className={resetErrors.email ? "border-destructive" : ""}
                />
                {resetErrors.email && <p className="text-sm text-destructive">{resetErrors.email}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-password">New Password</Label>
                <div className="relative">
                  <Input
                    id="new-password"
                    type={showNewPassword ? "text" : "password"}
                    placeholder="Choose a new password"
                    value={resetData.new_password}
                    onChange={(e) => {
                      setResetData({ ...resetData, new_password: e.target.value })
                      setResetErrors({ ...resetErrors, new_password: undefined })
                    }}
                    disabled={isLoading}
                    className={resetErrors.new_password ? "border-destructive pr-10" : "pr-10"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {resetErrors.new_password && <p className="text-sm text-destructive">{resetErrors.new_password}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirm-password">Confirm New Password</Label>
                <Input
                  id="confirm-password"
                  type="password"
                  placeholder="Confirm your new password"
                  value={resetData.confirm_password}
                  onChange={(e) => {
                    setResetData({ ...resetData, confirm_password: e.target.value })
                    setResetErrors({ ...resetErrors, confirm_password: undefined })
                  }}
                  disabled={isLoading}
                  className={resetErrors.confirm_password ? "border-destructive" : ""}
                />
                {resetErrors.confirm_password && (
                  <p className="text-sm text-destructive">{resetErrors.confirm_password}</p>
                )}
              </div>
            </CardContent>
            <CardFooter className="flex flex-col space-y-4">
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span className="ml-2">Updating...</span>
                  </>
                ) : (
                  "Complete Setup"
                )}
              </Button>
            </CardFooter>
          </form>
        ) : (
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="GR number or employee ID"
                  value={formData.username}
                  onChange={(e) => {
                    setFormData({ ...formData, username: e.target.value })
                    setErrors({ ...errors, username: undefined })
                  }}
                  disabled={isLoading}
                  className={errors.username ? "border-destructive" : ""}
                />
                {errors.username && <p className="text-sm text-destructive">{errors.username}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={(e) => {
                      setFormData({ ...formData, password: e.target.value })
                      setErrors({ ...errors, password: undefined })
                    }}
                    disabled={isLoading}
                    className={errors.password ? "border-destructive pr-10" : "pr-10"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {errors.password && <p className="text-sm text-destructive">{errors.password}</p>}
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="remember"
                    checked={formData.rememberMe}
                    onCheckedChange={(checked) => setFormData({ ...formData, rememberMe: checked as boolean })}
                  />
                  <Label htmlFor="remember" className="text-sm font-normal">
                    Remember me
                  </Label>
                </div>
                <Link href="/forgot-password" className="text-sm text-primary hover:underline">
                  Forgot password?
                </Link>
              </div>
            </CardContent>
            <CardFooter className="flex flex-col space-y-4">
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span className="ml-2">Signing in...</span>
                  </>
                ) : (
                  "Sign in"
                )}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                Accounts are created by admin. Contact admin for username and password.
              </p>
            </CardFooter>
          </form>
        )}
      </Card>
    </div>
  )
}
