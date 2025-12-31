"use client"

import { useEffect, useState, useRef } from "react"
import { useRouter, useParams, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingSpinner } from "@/components/loading-spinner"
import { useToast } from "@/hooks/use-toast"
import { ArrowLeft, MessageCircle, ClipboardCheck, CheckCircle2 } from "lucide-react"
import Link from "next/link"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { api } from "@/lib/api"

// Backend response types
interface SessionResponse {
  id: string
  subject_id: string
  chapter_number: number
  chapter_title: string
  chat_id: string | null
  notes_uploaded: boolean
  status: string
  last_active: string | null
  created_at: string
  ended_at: string | null
}

interface ChatMessageResponse {
  answer: string
  source: string
  cached: boolean
  confidence_score: number | null
  session_id: string | null
  chat_id: string | null
}

interface PlannerStateResponse {
  id: string
  subject_id: string
  total_chapters: number
  target_days: number
  daily_hours: number
  estimated_total_hours: number
  current_chapter: number
  chapter_progress: Record<
    string,
    {
      completed_objectives: string[]
      total_objectives: number
      is_complete: boolean
      started_at: string | null
      completed_at: string | null
      deadline: string | null
      estimated_hours: number
    }
  >
  chapter_deadlines: Array<{
    chapter_number: number
    title: string
    deadline: string | null
    is_complete: boolean
    completed_objectives: string[]
    total_objectives: number
    progress_percent: number
  }>
  overall_progress_percent: number
  is_complete: boolean
  created_at: string
  updated_at: string
}

// Frontend display types
interface Chapter {
  chapter_number: number
  title: string
  content: string
  learning_objectives: string[]
}

interface Message {
  role: "user" | "assistant"
  content: string
}

export function StudySessionContent() {
  const router = useRouter()
  const params = useParams()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [chapter, setChapter] = useState<Chapter | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [userMessage, setUserMessage] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [chatId, setChatId] = useState<string | null>(null)
  const chapterNumber = searchParams.get("chapter")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (params.id && chapterNumber) {
      initializeSession()
    }
  }, [params.id, chapterNumber])

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const initializeSession = async () => {
    try {
      setIsLoading(true)

      // 1. Fetch planner state to get chapter info
      const plannerData = await api.get<PlannerStateResponse>(`/api/v1/planner/${params.id}`)
      
      const chapterNum = Number(chapterNumber)
      const chapterDeadline = plannerData.chapter_deadlines.find(
        (c) => c.chapter_number === chapterNum
      )
      
      if (chapterDeadline) {
        const chapterProgress = plannerData.chapter_progress[String(chapterNum)]
        setChapter({
          chapter_number: chapterNum,
          title: chapterDeadline.title,
          content: "", // Content could be fetched from a separate endpoint if needed
          learning_objectives: chapterProgress?.completed_objectives || [],
        })
      }

      // 2. Create or resume study session
      try {
        const sessionData = await api.post<SessionResponse>("/api/v1/sessions/", {
          subject_id: params.id,
          chapter_number: chapterNum,
        })
        
        setSessionId(sessionData.id)
        setChatId(sessionData.chat_id)
      } catch {
        // Session might already exist, try to list active sessions
        const sessionsResponse = await api.get<{ sessions: SessionResponse[]; total: number }>(
          `/api/v1/sessions/?subject_id=${params.id}&status=active`
        )
        const existingSession = sessionsResponse.sessions.find(
          (s) => s.chapter_number === chapterNum
        )
        if (existingSession) {
          setSessionId(existingSession.id)
          setChatId(existingSession.chat_id)
        }
      }
    } catch (error) {
      toast({
        title: "Error loading chapter",
        description: error instanceof Error ? error.message : "Failed to load chapter",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const sendMessage = async () => {
    if (!userMessage.trim() || !chatId) return

    const newMessage: Message = { role: "user", content: userMessage }
    setMessages((prev) => [...prev, newMessage])
    setUserMessage("")
    setIsSending(true)

    try {
      const response = await api.post<ChatMessageResponse>(`/api/v1/chat/${chatId}/message`, {
        question: userMessage,
        intent_tag: "answer",
      })

      setMessages((prev) => [...prev, { role: "assistant", content: response.answer }])
    } catch (error) {
      toast({
        title: "Error sending message",
        description: error instanceof Error ? error.message : "Failed to send message",
        variant: "destructive",
      })
      // Remove the user message if sending failed
      setMessages((prev) => prev.slice(0, -1))
    } finally {
      setIsSending(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!chapter) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">Chapter not found</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <Link href={`/subjects/${params.id}`}>
          <Button variant="ghost" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Subject
          </Button>
        </Link>
      </div>

      <div className="mb-6">
        <h1 className="text-3xl font-bold text-balance">
          Chapter {chapter.chapter_number}: {chapter.title}
        </h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Learning Objectives</CardTitle>
              <CardDescription>What you'll learn in this chapter</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {chapter.learning_objectives.map((objective, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary" />
                    <span>{objective}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Content</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {chapter.content || "Content will be available soon..."}
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-3">
            <Button
              variant="outline"
              className="flex-1 gap-2 bg-transparent"
              onClick={() => router.push(`/subjects/${params.id}/quizzes`)}
            >
              <ClipboardCheck className="h-4 w-4" />
              Take Quiz
            </Button>
          </div>
        </div>

        <div className="lg:col-span-1">
          <Card className="sticky top-20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageCircle className="h-5 w-5" />
                Ask Questions
              </CardTitle>
              <CardDescription>Get help from AI assistant</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ScrollArea className="h-[400px] pr-4">
                {messages.length === 0 ? (
                  <div className="flex h-full items-center justify-center text-center">
                    <p className="text-sm text-muted-foreground">
                      {chatId 
                        ? "Ask any questions about this chapter and get instant help"
                        : "Setting up chat session..."}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {messages.map((message, idx) => (
                      <div
                        key={idx}
                        className={`rounded-lg p-3 text-sm ${
                          message.role === "user" ? "bg-primary text-primary-foreground ml-4" : "bg-muted mr-4"
                        }`}
                      >
                        {message.content}
                      </div>
                    ))}
                    {isSending && (
                      <div className="flex items-center gap-2 rounded-lg bg-muted p-3">
                        <LoadingSpinner size="sm" />
                        <span className="text-sm text-muted-foreground">Thinking...</span>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </ScrollArea>

              <div className="flex gap-2">
                <Textarea
                  placeholder="Ask a question..."
                  value={userMessage}
                  onChange={(e) => setUserMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault()
                      sendMessage()
                    }
                  }}
                  disabled={isSending}
                  rows={3}
                />
              </div>
              <Button onClick={sendMessage} disabled={isSending || !userMessage.trim() || !chatId} className="w-full">
                {isSending ? "Sending..." : "Send"}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  )
}
