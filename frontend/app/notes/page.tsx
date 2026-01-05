"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/loading-spinner"
import { useToast } from "@/hooks/use-toast"
import { FileText, Download, Trash2, BookOpen, Calendar } from "lucide-react"
import { api } from "@/lib/api"

interface Note {
  id: string
  subject_id: string
  subject: string
  chapter: string
  source_file: string
  file_path: string
  file_type: string
  created_at: string
  updated_at: string
}

interface NotesListResponse {
  notes: Note[]
  total: number
}

export default function NotesPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [notes, setNotes] = useState<Note[]>([])
  const [isDeleting, setIsDeleting] = useState<string | null>(null)

  useEffect(() => {
    fetchAllNotes()
  }, [])

  const fetchAllNotes = async () => {
    try {
      setIsLoading(true)
      const response = await api.get<NotesListResponse>("/api/v1/notes/user/all")
      setNotes(response.notes || [])
    } catch (error) {
      toast({
        title: "Error loading notes",
        description: error instanceof Error ? error.message : "Failed to load notes",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (noteId: string) => {
    if (!confirm("Are you sure you want to delete this note?")) return

    try {
      setIsDeleting(noteId)
      await api.delete(`/api/v1/notes/${noteId}`)
      setNotes(notes.filter(n => n.id !== noteId))
      toast({
        title: "Note deleted",
        description: "Your note has been removed",
      })
    } catch (error) {
      toast({
        title: "Error deleting note",
        description: error instanceof Error ? error.message : "Failed to delete note",
        variant: "destructive",
      })
    } finally {
      setIsDeleting(null)
    }
  }

  const handleDownload = (note: Note) => {
    // Download file from file_path
    const link = document.createElement('a')
    link.href = note.file_path
    link.download = note.source_file
    link.click()
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  // Group notes by subject
  const groupedBySubject = notes.reduce((acc, note) => {
    if (!acc[note.subject]) {
      acc[note.subject] = []
    }
    acc[note.subject].push(note)
    return acc
  }, {} as Record<string, Note[]>)

  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Navbar />

        <main className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                  <FileText className="h-8 w-8 text-primary" />
                  My Study Materials
                </h1>
                <p className="text-muted-foreground mt-1">
                  Access all your uploaded notes and study materials
                </p>
              </div>
              <Button onClick={() => router.push("/subjects")}>
                Upload More Notes
              </Button>
            </div>
          </div>

          {isLoading ? (
            <div className="flex min-h-[400px] items-center justify-center">
              <div className="text-center space-y-4">
                <LoadingSpinner size="lg" />
                <p className="text-muted-foreground">Loading your notes...</p>
              </div>
            </div>
          ) : notes.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                <h2 className="text-lg font-semibold">No study materials yet</h2>
                <p className="text-sm text-muted-foreground mb-4">
                  Upload notes to your subjects to get started
                </p>
                <Button onClick={() => router.push("/subjects")}>
                  Go to Subjects
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-8">
              {/* Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Total Materials</p>
                        <p className="text-3xl font-bold">{notes.length}</p>
                      </div>
                      <FileText className="h-8 w-8 text-primary opacity-50" />
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Subjects</p>
                        <p className="text-3xl font-bold">{Object.keys(groupedBySubject).length}</p>
                      </div>
                      <BookOpen className="h-8 w-8 text-blue-500 opacity-50" />
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Recently Added</p>
                        <p className="text-sm font-semibold">
                          {notes.length > 0
                            ? new Date(notes[0].created_at).toLocaleDateString()
                            : "N/A"}
                        </p>
                      </div>
                      <Calendar className="h-8 w-8 text-green-500 opacity-50" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Notes by Subject */}
              {Object.entries(groupedBySubject).map(([subject, subjectNotes]) => (
                <div key={subject}>
                  <h2 className="text-xl font-semibold mb-4">{subject}</h2>
                  <div className="grid grid-cols-1 gap-4">
                    {subjectNotes.map((note) => (
                      <Card key={note.id} className="hover:shadow-lg transition-shadow">
                        <CardContent className="p-6">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex items-start gap-4 flex-1 min-w-0">
                              <FileText className="h-6 w-6 text-primary mt-1 flex-shrink-0" />
                              <div className="min-w-0 flex-1">
                                <p className="font-semibold truncate">{note.source_file}</p>
                                <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                                  <span className="px-2 py-1 bg-muted rounded text-xs">
                                    {note.file_type.toUpperCase()}
                                  </span>
                                  <span>{note.chapter}</span>
                                </div>
                                <p className="text-xs text-muted-foreground mt-2">
                                  Added {formatDate(note.created_at)}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleDownload(note)}
                                title="Download note"
                              >
                                <Download className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleDelete(note.id)}
                                disabled={isDeleting === note.id}
                                title="Delete note"
                                className="text-destructive hover:text-destructive"
                              >
                                {isDeleting === note.id ? (
                                  <LoadingSpinner size="sm" />
                                ) : (
                                  <Trash2 className="h-4 w-4" />
                                )}
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  )
}
