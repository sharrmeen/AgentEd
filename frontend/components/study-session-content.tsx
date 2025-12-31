"use client"

import { useEffect, useState, useRef } from "react"
import { useRouter, useParams, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingSpinner } from "@/components/loading-spinner"
import { useToast } from "@/hooks/use-toast"
import { 
  ArrowLeft, 
  MessageCircle, 
  ClipboardCheck, 
  CheckCircle2, 
  BookOpen, 
  ChevronDown,
  Sparkles,
  Send,
  AlertCircle,
  Upload,
  FileText,
  X
} from "lucide-react"
import Link from "next/link"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { api } from "@/lib/api"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Progress } from "@/components/ui/progress"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"


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

interface BackendSubject {
  id: string
  subject_name: string
  syllabus_id: string | null
  status: string
  plan: {
    chapters: Array<{
      chapter_number: number
      title: string
      objectives: string[]
      estimated_hours: number
    }>
  } | null
  plan_summary: object | null
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
  timestamp?: Date
  confidence?: number
}

interface ChapterProgressResponse {
  completed_objectives: string[]
  total_objectives: number
  is_complete: boolean
  started_at: string | null
  completed_at: string | null
  deadline: string | null
  estimated_hours: number
}

interface ObjectiveCompleteResponse {
  chapter_completed: boolean
  replanned: boolean
  message: string
}

// Notes types
interface NoteItem {
  id: string
  subject_id: string
  subject: string
  chapter: string
  source_file: string
  file_path: string
  file_type: string
  created_at: string
}

interface NotesListResponse {
  notes: NoteItem[]
  total: number
}

interface NotesUploadResponse {
  note_id: string
  file_path: string
  ingestion_status: string
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
  const [isObjectivesOpen, setIsObjectivesOpen] = useState(true)
  const [isContentOpen, setIsContentOpen] = useState(true)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [chatId, setChatId] = useState<string | null>(null)
  const [completedObjectives, setCompletedObjectives] = useState<Set<string>>(new Set())
  const [isChapterComplete, setIsChapterComplete] = useState(false)
  const [isSavingProgress, setIsSavingProgress] = useState(false)
  const chapterNumber = searchParams.get("chapter")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  // Notes upload state
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [hasNotes, setHasNotes] = useState(false)
  const [chapterNotes, setChapterNotes] = useState<NoteItem[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [subjectName, setSubjectName] = useState<string>("")
  const fileInputRef = useRef<HTMLInputElement>(null)

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
      const chapterNum = Number(chapterNumber)

      // Fetch subject to get chapter details from the plan
      // Endpoint: GET /api/v1/subjects/{id}
      const subjectData = await api.get<BackendSubject>(`/api/v1/subjects/${params.id}`)
      setSubjectName(subjectData.subject_name)

      // Find the chapter in the plan
      const chapterData = subjectData.plan?.chapters?.find(
        (c) => c.chapter_number === chapterNum
      )

      let chapterTitle = `Chapter ${chapterNum}`
      if (chapterData) {
        chapterTitle = chapterData.title
        setChapter({
          chapter_number: chapterNum,
          title: chapterData.title,
          content: "", // Content can be generated on demand
          learning_objectives: chapterData.objectives || [],
        })
      } else {
        // Fallback: set basic chapter info even if not found in plan
        setChapter({
          chapter_number: chapterNum,
          title: chapterTitle,
          content: "",
          learning_objectives: [],
        })
      }

      // Check if notes exist for this chapter
      // Endpoint: GET /api/v1/notes/{subject_id}?chapter={chapter}
      try {
        const chapterIdentifier = `Chapter ${chapterNum}: ${chapterTitle}`
        const notesResponse = await api.get<NotesListResponse>(
          `/api/v1/notes/${params.id}?chapter=${encodeURIComponent(chapterIdentifier)}`
        )
        
        if (notesResponse.notes && notesResponse.notes.length > 0) {
          setHasNotes(true)
          setChapterNotes(notesResponse.notes)
        } else {
          // Try with just chapter number format
          const altNotesResponse = await api.get<NotesListResponse>(
            `/api/v1/notes/${params.id}?chapter=${encodeURIComponent(`Chapter ${chapterNum}`)}`
          )
          if (altNotesResponse.notes && altNotesResponse.notes.length > 0) {
            setHasNotes(true)
            setChapterNotes(altNotesResponse.notes)
          } else {
            setHasNotes(false)
            setShowUploadDialog(true) // Show upload dialog if no notes
          }
        }
      } catch {
        // No notes found, show upload dialog
        setHasNotes(false)
        setShowUploadDialog(true)
      }

      // Create or resume study session
      // Endpoint: POST /api/v1/sessions/ (returns existing if already created)
      try {
        const sessionData = await api.post<SessionResponse>("/api/v1/sessions/", {
          subject_id: params.id,
          chapter_number: chapterNum,
        })

        setSessionId(sessionData.id)
        setChatId(sessionData.chat_id)
      } catch (error) {
        // If creation fails, try to get existing session
        const errorMessage = error instanceof Error ? error.message : String(error)
        
        // Only try to fetch existing if it's a duplicate key error
        if (errorMessage.includes("E11000") || errorMessage.includes("duplicate")) {
          try {
            // Get all sessions for this subject
            const sessionsResponse = await api.get<{ sessions: SessionResponse[]; total: number }>(
              `/api/v1/sessions/subject/${params.id}`
            )
            
            // Find the session for this chapter
            const existingSession = sessionsResponse.sessions.find(
              (s) => s.chapter_number === chapterNum
            )
            
            if (existingSession) {
              setSessionId(existingSession.id)
              setChatId(existingSession.chat_id)
              toast({
                title: "Session resumed",
                description: "Continuing your study session for this chapter",
                variant: "default",
              })
            } else {
              throw new Error("Session not found after creation attempt")
            }
          } catch (fetchError) {
            toast({
              title: "Session error",
              description: fetchError instanceof Error ? fetchError.message : "Could not resume session",
              variant: "destructive",
            })
          }
        } else {
          toast({
            title: "Error creating session",
            description: errorMessage || "Could not create a study session",
            variant: "destructive",
          })
        }
      }

      // Fetch chapter progress (completed objectives)
      // Endpoint: GET /api/v1/planner/{subject_id}/chapter/{chapter_number}
      try {
        const progressData = await api.get<ChapterProgressResponse>(
          `/api/v1/planner/${params.id}/chapter/${chapterNum}`
        )
        
        if (progressData.completed_objectives && progressData.completed_objectives.length > 0) {
          setCompletedObjectives(new Set(progressData.completed_objectives))
        }
        setIsChapterComplete(progressData.is_complete)
      } catch (progressError) {
        // Progress not found is OK - user hasn't started this chapter yet
        console.log("No progress data found for chapter:", progressError)
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

    const newMessage: Message = { 
      role: "user", 
      content: userMessage,
      timestamp: new Date()
    }
    setMessages((prev) => [...prev, newMessage])
    setUserMessage("")
    setIsSending(true)

    try {
      // Endpoint: POST /api/v1/chat/{chat_id}/message
      const response = await api.post<ChatMessageResponse>(`/api/v1/chat/${chatId}/message`, {
        question: userMessage,
        intent_tag: "answer",
      })

      setMessages((prev) => [...prev, { 
        role: "assistant", 
        content: response.answer,
        timestamp: new Date(),
        confidence: response.confidence_score || undefined
      }])
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

  const toggleObjective = async (objective: string) => {
    // Prevent toggling if already completed (cannot uncomplete from frontend)
    if (completedObjectives.has(objective)) {
      return
    }
    
    setIsSavingProgress(true)
    
    try {
      // Endpoint: POST /api/v1/planner/objective/complete
      const response = await api.post<ObjectiveCompleteResponse>("/api/v1/planner/objective/complete", {
        subject_id: params.id as string,
        chapter_number: Number(chapterNumber),
        objective: objective,
      })
      
      // Update local state
      const newSet = new Set(completedObjectives)
      newSet.add(objective)
      setCompletedObjectives(newSet)
      
      if (response.chapter_completed) {
        setIsChapterComplete(true)
        toast({
          title: "🎉 Chapter Complete!",
          description: "Great job! You've completed all objectives for this chapter.",
          variant: "default",
        })
      } else {
        toast({
          title: "Progress saved",
          description: "Objective marked as complete",
          variant: "default",
        })
      }
    } catch (error) {
      toast({
        title: "Error saving progress",
        description: error instanceof Error ? error.message : "Could not save progress",
        variant: "destructive",
      })
    } finally {
      setIsSavingProgress(false)
    }
  }

  // File upload handlers
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file type
      const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/png', 'image/jpeg', 'image/jpg']
      if (!validTypes.includes(file.type)) {
        toast({
          title: "Invalid file type",
          description: "Please upload a PDF, DOCX, or image file (PNG, JPG)",
          variant: "destructive",
        })
        return
      }
      setSelectedFile(file)
    }
  }

  const handleUploadNotes = async () => {
    if (!selectedFile || !chapter) return

    setIsUploading(true)
    try {
      const chapterIdentifier = `Chapter ${chapter.chapter_number}: ${chapter.title}`
      
      // Create FormData for file upload
      const formData = new FormData()
      formData.append('file', selectedFile)
      
      // Upload notes
      const response = await fetch(
        `http://localhost:8000/api/v1/notes/${params.id}/upload?chapter=${encodeURIComponent(chapterIdentifier)}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
          body: formData,
        }
      )

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to upload notes')
      }

      const result: NotesUploadResponse = await response.json()
      
      toast({
        title: "Notes uploaded!",
        description: `${selectedFile.name} has been uploaded and processed for ${chapterIdentifier}`,
      })

      // Update state
      setHasNotes(true)
      setShowUploadDialog(false)
      setSelectedFile(null)
      
      // Refresh notes list
      const notesResponse = await api.get<NotesListResponse>(
        `/api/v1/notes/${params.id}?chapter=${encodeURIComponent(chapterIdentifier)}`
      )
      if (notesResponse.notes) {
        setChapterNotes(notesResponse.notes)
      }
    } catch (error) {
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Could not upload notes",
        variant: "destructive",
      })
    } finally {
      setIsUploading(false)
    }
  }

  const progressPercent = chapter 
    ? (completedObjectives.size / chapter.learning_objectives.length) * 100 
    : 0

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center space-y-4">
          <LoadingSpinner size="lg" />
          <p className="text-muted-foreground">Initializing study session...</p>
        </div>
      </div>
    )
  }

  if (!chapter) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="border-destructive/50">
          <CardContent className="py-12 text-center space-y-4">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive" />
            <p className="text-lg font-semibold">Chapter not found</p>
            <p className="text-sm text-muted-foreground">Unable to load the requested chapter</p>
            <Link href={`/subjects/${params.id}`}>
              <Button variant="outline">Back to Subject</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <main className="container mx-auto px-4 py-8">
      {/* Notes Upload Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5 text-primary" />
              Upload Notes for This Chapter
            </DialogTitle>
            <DialogDescription>
              Upload your study materials for this chapter. Supported formats: PDF, DOCX, PNG, JPG
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Pre-filled chapter info */}
            <div className="space-y-2">
              <Label htmlFor="subject">Subject</Label>
              <Input
                id="subject"
                value={subjectName}
                disabled
                className="bg-muted"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="chapterNumber">Chapter Number</Label>
                <Input
                  id="chapterNumber"
                  value={chapter?.chapter_number || ""}
                  disabled
                  className="bg-muted"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="chapterTitle">Chapter Title</Label>
                <Input
                  id="chapterTitle"
                  value={chapter?.title || ""}
                  disabled
                  className="bg-muted"
                />
              </div>
            </div>
            
            {/* File upload area */}
            <div className="space-y-2">
              <Label>Notes File</Label>
              <div 
                className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer ${
                  selectedFile ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'
                }`}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.png,.jpg,.jpeg"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                {selectedFile ? (
                  <div className="flex items-center justify-center gap-2">
                    <FileText className="h-8 w-8 text-primary" />
                    <div className="text-left">
                      <p className="font-medium">{selectedFile.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="ml-2"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedFile(null)
                      }}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Upload className="h-10 w-10 mx-auto text-muted-foreground" />
                    <p className="font-medium">Click to upload or drag and drop</p>
                    <p className="text-sm text-muted-foreground">PDF, DOCX, PNG, or JPG (max 10MB)</p>
                  </div>
                )}
              </div>
            </div>
            
            {/* Existing notes */}
            {chapterNotes.length > 0 && (
              <div className="space-y-2">
                <Label>Existing Notes</Label>
                <div className="space-y-2">
                  {chapterNotes.map((note) => (
                    <div key={note.id} className="flex items-center gap-2 p-2 bg-muted rounded-md">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">{note.source_file}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          <DialogFooter className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setShowUploadDialog(false)}
            >
              {hasNotes ? "Close" : "Skip for now"}
            </Button>
            <Button
              onClick={handleUploadNotes}
              disabled={!selectedFile || isUploading}
            >
              {isUploading ? (
                <>
                  <LoadingSpinner size="sm" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Notes
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Header Section */}
      <div className="mb-8">
        <Link href={`/subjects/${params.id}`} className="inline-block mb-4">
          <Button variant="ghost" className="gap-2 hover:bg-muted">
            <ArrowLeft className="h-4 w-4" />
            Back to Subject
          </Button>
        </Link>

        <div>
          <h1 className="text-4xl font-bold text-balance mb-2">
            Chapter {chapter.chapter_number}: {chapter.title}
          </h1>
          <p className="text-muted-foreground">Master the concepts with AI-powered guidance</p>
        </div>
      </div>

      {/* Progress Bar */}
      {chapter.learning_objectives.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Learning Progress</span>
            <span className="text-sm text-muted-foreground">{completedObjectives.size}/{chapter.learning_objectives.length}</span>
          </div>
          <Progress value={progressPercent} className="h-2" />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Chat Area */}
        <div className="lg:col-span-2">
          <Card className="flex flex-col h-[calc(100vh-320px)] border-2 border-primary/10">
            <CardHeader className="border-b bg-gradient-to-r from-primary/5 to-transparent">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <MessageCircle className="h-5 w-5 text-primary" />
                    AI Study Assistant
                  </CardTitle>
                  <CardDescription>Ask questions to deepen your understanding</CardDescription>
                </div>
                {chatId && (
                  <div className="flex items-center gap-1 px-3 py-1 rounded-full bg-green-100 dark:bg-green-900/30">
                    <div className="h-2 w-2 rounded-full bg-green-600 animate-pulse" />
                    <span className="text-xs text-green-700 dark:text-green-400">Active</span>
                  </div>
                )}
              </div>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col p-4 overflow-hidden">
              <ScrollArea className="flex-1 pr-4 mb-4">
                {messages.length === 0 ? (
                  <div className="flex h-full items-center justify-center text-center p-8">
                    <div className="space-y-4 max-w-sm">
                      <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                        <Sparkles className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <p className="font-semibold text-foreground">Ready to help you learn</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          {chatId 
                            ? "Ask any questions about this chapter and get instant, personalized help"
                            : "Initializing chat session..."}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {messages.map((message, idx) => (
                      <div
                        key={idx}
                        className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2`}
                      >
                        <div
                          className={`max-w-xs px-4 py-3 rounded-lg text-sm ${
                            message.role === "user"
                              ? "bg-primary text-primary-foreground rounded-br-none"
                              : "bg-muted text-foreground rounded-bl-none border border-border"
                          }`}
                        >
                          <p className="leading-relaxed">{message.content}</p>
                          {message.role === "assistant" && message.confidence && (
                            <p className="text-xs opacity-70 mt-1">
                              Confidence: {(message.confidence * 100).toFixed(0)}%
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                    {isSending && (
                      <div className="flex justify-start">
                        <div className="max-w-xs px-4 py-3 rounded-lg bg-muted text-foreground border border-border">
                          <div className="flex items-center gap-2">
                            <div className="flex gap-1">
                              <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce" />
                              <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce delay-100" />
                              <div className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce delay-200" />
                            </div>
                            <span className="text-sm text-muted-foreground">Thinking...</span>
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </ScrollArea>

              {/* Message Input Area */}
              <div className="space-y-3 border-t pt-4">
                <Textarea
                  placeholder="Ask something about this chapter..."
                  value={userMessage}
                  onChange={(e) => setUserMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault()
                      sendMessage()
                    }
                  }}
                  disabled={isSending || !chatId}
                  rows={3}
                  className="resize-none border-primary/20 focus:border-primary/50"
                />
                <Button 
                  onClick={sendMessage} 
                  disabled={isSending || !userMessage.trim() || !chatId}
                  className="w-full gap-2"
                  size="lg"
                >
                  <Send className="h-4 w-4" />
                  {isSending ? "Sending..." : "Send Question"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar - Chapter Info */}
        <div className="lg:col-span-1 space-y-6">
          {/* Learning Objectives Card */}
          <Card className={`border-primary/10 ${isChapterComplete ? "border-green-500/50 bg-green-50/10" : ""}`}>
            <CardContent className="p-0">
              <Collapsible open={isObjectivesOpen} onOpenChange={setIsObjectivesOpen}>
                <CollapsibleTrigger className="w-full">
                  <div className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors border-b">
                    <div className="flex items-center gap-2">
                      <BookOpen className="h-4 w-4 text-primary" />
                      <span className="font-semibold text-sm">Learning Objectives</span>
                      {isChapterComplete && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Complete</span>
                      )}
                    </div>
                    <ChevronDown 
                      className={`h-4 w-4 transition-transform duration-200 ${
                        isObjectivesOpen ? "rotate-180" : ""
                      }`} 
                    />
                  </div>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <div className="p-4 space-y-3">
                    {isSavingProgress && (
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                        <LoadingSpinner size="sm" />
                        <span>Saving progress...</span>
                      </div>
                    )}
                    {chapter.learning_objectives.length > 0 ? (
                      <ul className="space-y-2">
                        {chapter.learning_objectives.map((objective, idx) => (
                          <li 
                            key={idx} 
                            className={`flex items-start gap-2 p-2 rounded-md transition-colors ${
                              completedObjectives.has(objective) 
                                ? "bg-green-50/50 cursor-default" 
                                : "hover:bg-muted/50 cursor-pointer"
                            }`}
                            onClick={() => toggleObjective(objective)}
                          >
                            <div className={`flex-shrink-0 mt-0.5 h-5 w-5 rounded border-2 flex items-center justify-center transition-all ${
                              completedObjectives.has(objective)
                                ? "bg-green-600 border-green-600"
                                : "border-muted-foreground hover:border-primary"
                            }`}>
                              {completedObjectives.has(objective) && (
                                <CheckCircle2 className="h-4 w-4 text-white" />
                              )}
                            </div>
                            <span className={`text-sm ${
                              completedObjectives.has(objective) 
                                ? "line-through text-muted-foreground" 
                                : "text-foreground"
                            }`}>
                              {objective}
                            </span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-muted-foreground text-center py-4">
                        No learning objectives available
                      </p>
                    )}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            </CardContent>
          </Card>

          {/* Content Card */}
          <Card className="border-primary/10">
            <CardContent className="p-0">
              <Collapsible open={isContentOpen} onOpenChange={setIsContentOpen}>
                <CollapsibleTrigger className="w-full">
                  <div className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors border-b">
                    <span className="font-semibold text-sm">Content</span>
                    <ChevronDown 
                      className={`h-4 w-4 transition-transform duration-200 ${
                        isContentOpen ? "rotate-180" : ""
                      }`} 
                    />
                  </div>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <div className="p-4 max-h-64 overflow-y-auto">
                    <p className="text-sm text-muted-foreground">
                      {chapter.content || "Chapter content will be displayed here. Ask questions to explore this chapter."}
                    </p>
                  </div>
                </CollapsibleContent>
              </Collapsible>
            </CardContent>
          </Card>

          {/* Action Card */}
          <Card className="bg-gradient-to-br from-primary/5 to-transparent border-primary/20">
            <CardContent className="p-4 space-y-3">
              <p className="text-sm font-medium">Ready for assessment?</p>
              <Button 
                className="w-full gap-2 bg-primary hover:bg-primary/90"
                onClick={() => router.push(`/subjects/${params.id}/quizzes?chapter=${chapterNumber}`)}
              >
                <ClipboardCheck className="h-4 w-4" />
                Take Quiz
              </Button>
            </CardContent>
          </Card>

          {/* Upload Notes Card */}
          <Card className="border-primary/10">
            <CardContent className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">Study Materials</p>
                {hasNotes && (
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full dark:bg-green-900/30 dark:text-green-400">
                    {chapterNotes.length} file{chapterNotes.length !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
              {chapterNotes.length > 0 && (
                <div className="space-y-1">
                  {chapterNotes.slice(0, 2).map((note) => (
                    <div key={note.id} className="flex items-center gap-2 text-xs text-muted-foreground">
                      <FileText className="h-3 w-3" />
                      <span className="truncate">{note.source_file}</span>
                    </div>
                  ))}
                  {chapterNotes.length > 2 && (
                    <p className="text-xs text-muted-foreground">+{chapterNotes.length - 2} more</p>
                  )}
                </div>
              )}
              <Button 
                variant="outline"
                className="w-full gap-2"
                onClick={() => setShowUploadDialog(true)}
              >
                <Upload className="h-4 w-4" />
                {hasNotes ? "Upload More Notes" : "Upload Notes"}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  )
}
