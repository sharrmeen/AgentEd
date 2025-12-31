import { Suspense } from "react"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { LoadingSpinner } from "@/components/loading-spinner"
import { StudySessionContent } from "@/components/study-session-content"

export default function StudySessionPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Navbar />
        <Suspense
          fallback={
            <div className="flex min-h-[60vh] items-center justify-center">
              <LoadingSpinner size="lg" />
            </div>
          }
        >
          <StudySessionContent />
        </Suspense>
      </div>
    </AuthGuard>
  )
}
