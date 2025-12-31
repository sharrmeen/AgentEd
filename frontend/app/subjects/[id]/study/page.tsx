"use client"

import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { StudySessionContent } from "@/components/study-session-content"

export default function StudyPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Navbar />
        <StudySessionContent />
      </div>
    </AuthGuard>
  )
}
