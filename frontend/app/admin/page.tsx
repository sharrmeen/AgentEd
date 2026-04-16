"use client"

import { useEffect, useState } from "react"
import { AuthGuard } from "@/components/auth-guard"
import { Navbar } from "@/components/navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/loading-spinner"
import { api } from "@/lib/api"
import { ShieldCheck, Users, UserPlus, GraduationCap } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface MeResponse {
  id: string
  name: string
  username: string
  role: string
  class_id?: string | null
  email?: string | null
}

interface AdminUser {
  id: string
  name: string
  username: string
  email?: string | null
  role: "admin" | "teacher" | "student"
  class_id?: string | null
  must_change_password: boolean
  is_active: boolean
  created_at: string
  last_login?: string | null
}

interface AdminUsersResponse {
  users: AdminUser[]
  total: number
  skip: number
  limit: number
}

interface ClassItem {
  id: string
  name: string
  section?: string | null
  teacher_id?: string | null
  teacher_name?: string | null
  student_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

interface ClassListResponse {
  classes: ClassItem[]
  total: number
}

interface ClassStudentItem {
  id: string
  name: string
  username: string
  email?: string | null
  class_id?: string | null
}

interface ClassStudentsResponse {
  class_id: string
  students: ClassStudentItem[]
  total: number
}

interface CreateUserPayload {
  name: string
  username: string
  password: string
  role: "student" | "teacher"
  class_id?: string | null
  email?: string | null
  must_change_password: boolean
}

export default function AdminPage() {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [me, setMe] = useState<MeResponse | null>(null)
  const [users, setUsers] = useState<AdminUser[]>([])
  const [classes, setClasses] = useState<ClassItem[]>([])
  const [teachers, setTeachers] = useState<AdminUser[]>([])
  const [search, setSearch] = useState("")

  const [createUserOpen, setCreateUserOpen] = useState(false)
  const [createClassOpen, setCreateClassOpen] = useState(false)
  const [editClassOpen, setEditClassOpen] = useState(false)
  const [bulkEnrollOpen, setBulkEnrollOpen] = useState(false)

  const [newUser, setNewUser] = useState<CreateUserPayload>({
    name: "",
    username: "",
    password: "",
    role: "student",
    class_id: null,
    email: "",
    must_change_password: true,
  })

  const [newClass, setNewClass] = useState({
    name: "",
    section: "",
    teacher_id: "",
  })

  const [editingClass, setEditingClass] = useState<ClassItem | null>(null)
  const [editClassForm, setEditClassForm] = useState({
    name: "",
    section: "",
    teacher_id: "",
    is_active: true,
  })

  const [enrollTargetClass, setEnrollTargetClass] = useState<ClassItem | null>(null)
  const [selectedStudentIds, setSelectedStudentIds] = useState<string[]>([])
  const [bulkEnrollSearch, setBulkEnrollSearch] = useState("")
  const [isSavingClass, setIsSavingClass] = useState(false)
  const [isSavingEnrollment, setIsSavingEnrollment] = useState(false)
  const [activeClassId, setActiveClassId] = useState<string | null>(null)
  const [activeClassStudents, setActiveClassStudents] = useState<ClassStudentItem[]>([])
  const [isLoadingClassStudents, setIsLoadingClassStudents] = useState(false)

  const [classSelectionByUser, setClassSelectionByUser] = useState<Record<string, string>>({})

  const loadData = async () => {
    const [meData, usersData, classesData, teachersData] = await Promise.all([
      api.get<MeResponse>("/api/v1/auth/me"),
      api.get<AdminUsersResponse>("/api/v1/auth/admin/users?limit=200"),
      api.get<ClassListResponse>("/api/v1/classes/admin?limit=200"),
      api.get<AdminUsersResponse>("/api/v1/auth/admin/users?role=teacher&limit=200"),
    ])

    setMe(meData)
    setUsers(usersData.users || [])
    setClasses(classesData.classes || [])
    setTeachers(teachersData.users || [])
  }

  useEffect(() => {
    const load = async () => {
      try {
        await loadData()
      } finally {
        setIsLoading(false)
      }
    }

    load()
  }, [])

  const handleCreateUser = async () => {
    if (!newUser.name || !newUser.username || !newUser.password) {
      toast({ title: "Missing fields", description: "Name, username and password are required.", variant: "destructive" })
      return
    }

    if (newUser.role === "student" && !newUser.class_id) {
      toast({ title: "Class required", description: "Please assign a class for students.", variant: "destructive" })
      return
    }

    try {
      await api.post("/api/v1/auth/admin/users", {
        ...newUser,
        class_id: newUser.role === "student" ? newUser.class_id : null,
        email: newUser.email || null,
      })

      toast({ title: "User created", description: `${newUser.name} was created successfully.` })
      setCreateUserOpen(false)
      setNewUser({
        name: "",
        username: "",
        password: "",
        role: "student",
        class_id: null,
        email: "",
        must_change_password: true,
      })
      await loadData()
    } catch (error) {
      toast({
        title: "Could not create user",
        description: error instanceof Error ? error.message : "Request failed",
        variant: "destructive",
      })
    }
  }

  const handleCreateClass = async () => {
    if (!newClass.name.trim()) {
      toast({ title: "Class name required", description: "Please enter a class name.", variant: "destructive" })
      return
    }

    try {
      await api.post("/api/v1/classes/admin", {
        name: newClass.name,
        section: newClass.section || null,
        teacher_id: newClass.teacher_id || null,
      })
      toast({ title: "Class created", description: `${newClass.name} is now available.` })
      setCreateClassOpen(false)
      setNewClass({ name: "", section: "", teacher_id: "" })
      await loadData()
    } catch (error) {
      toast({
        title: "Could not create class",
        description: error instanceof Error ? error.message : "Request failed",
        variant: "destructive",
      })
    }
  }

  const assignStudentClass = async (userId: string, explicitClassId?: string | null) => {
    const classId = explicitClassId !== undefined ? explicitClassId : (classSelectionByUser[userId] ?? "")
    try {
      await api.patch(`/api/v1/auth/admin/users/${userId}/class`, { class_id: classId || null })
      toast({ title: "Class updated", description: "Student class assignment saved." })
      await loadData()
      if (activeClassId) {
        await loadClassStudents(activeClassId)
      }
    } catch (error) {
      toast({
        title: "Could not assign class",
        description: error instanceof Error ? error.message : "Request failed",
        variant: "destructive",
      })
    }
  }

  const openEditClassDialog = (cls: ClassItem) => {
    setEditingClass(cls)
    setEditClassForm({
      name: cls.name,
      section: cls.section || "",
      teacher_id: cls.teacher_id || "",
      is_active: cls.is_active,
    })
    setEditClassOpen(true)
  }

  const handleUpdateClass = async () => {
    if (!editingClass) return
    if (!editClassForm.name.trim()) {
      toast({ title: "Class name required", description: "Please enter a class name.", variant: "destructive" })
      return
    }

    try {
      setIsSavingClass(true)
      await api.patch(`/api/v1/classes/admin/${editingClass.id}`, {
        name: editClassForm.name,
        section: editClassForm.section || null,
        teacher_id: editClassForm.teacher_id || null,
        is_active: editClassForm.is_active,
      })

      toast({ title: "Class updated", description: "Class details saved successfully." })
      setEditClassOpen(false)
      setEditingClass(null)
      await loadData()
    } catch (error) {
      toast({
        title: "Could not update class",
        description: error instanceof Error ? error.message : "Request failed",
        variant: "destructive",
      })
    } finally {
      setIsSavingClass(false)
    }
  }

  const openBulkEnrollDialog = async (cls: ClassItem) => {
    try {
      setEnrollTargetClass(cls)
      const response = await api.get<ClassStudentsResponse>(`/api/v1/classes/admin/${cls.id}/students`)
      setSelectedStudentIds((response.students || []).map((student) => student.id))
      setBulkEnrollSearch("")
      setBulkEnrollOpen(true)
    } catch (error) {
      toast({
        title: "Could not load class students",
        description: error instanceof Error ? error.message : "Request failed",
        variant: "destructive",
      })
    }
  }

  const toggleStudentSelection = (studentId: string, checked: boolean) => {
    setSelectedStudentIds((prev) => {
      if (checked) return Array.from(new Set([...prev, studentId]))
      return prev.filter((id) => id !== studentId)
    })
  }

  const handleSaveBulkEnrollment = async () => {
    if (!enrollTargetClass) return

    try {
      setIsSavingEnrollment(true)
      await api.post(`/api/v1/classes/admin/${enrollTargetClass.id}/students`, {
        student_ids: selectedStudentIds,
      })

      toast({
        title: "Enrollment updated",
        description: "Selected students were assigned to the class.",
      })
      setBulkEnrollOpen(false)
      setEnrollTargetClass(null)
      await loadData()
    } catch (error) {
      toast({
        title: "Could not update enrollment",
        description: error instanceof Error ? error.message : "Request failed",
        variant: "destructive",
      })
    } finally {
      setIsSavingEnrollment(false)
    }
  }

  const loadClassStudents = async (classId: string) => {
    try {
      setIsLoadingClassStudents(true)
      const response = await api.get<ClassStudentsResponse>(`/api/v1/classes/admin/${classId}/students`)
      setActiveClassStudents(response.students || [])
    } catch (error) {
      toast({
        title: "Could not load class details",
        description: error instanceof Error ? error.message : "Request failed",
        variant: "destructive",
      })
      setActiveClassStudents([])
    } finally {
      setIsLoadingClassStudents(false)
    }
  }

  const toggleClassDetails = async (classId: string) => {
    if (activeClassId === classId) {
      setActiveClassId(null)
      setActiveClassStudents([])
      return
    }

    setActiveClassId(classId)
    await loadClassStudents(classId)
  }

  const filteredUsers = users.filter((user) => {
    if (!search.trim()) return true
    const q = search.toLowerCase()
    return (
      user.name.toLowerCase().includes(q) ||
      user.username.toLowerCase().includes(q) ||
      (user.email || "").toLowerCase().includes(q)
    )
  })

  const studentUsers = users.filter((user) => user.role === "student")
  const filteredBulkStudents = studentUsers.filter((student) => {
    if (!bulkEnrollSearch.trim()) return true
    const q = bulkEnrollSearch.toLowerCase()
    return (
      student.name.toLowerCase().includes(q) ||
      student.username.toLowerCase().includes(q) ||
      (student.email || "").toLowerCase().includes(q)
    )
  })

  return (
    <AuthGuard allowedRoles={["admin"]}>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <div className="mb-8 flex items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold">Admin Console</h1>
              <p className="mt-2 text-muted-foreground">Manage users, classes, and platform operations.</p>
            </div>
            <ShieldCheck className="h-10 w-10 text-primary" />
          </div>

          {isLoading ? (
            <div className="flex min-h-[40vh] items-center justify-center">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Signed In As</CardTitle>
                  <CardDescription>{me?.name || "Admin"}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">Username: {me?.username}</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">User Management</CardTitle>
                  <CardDescription>Create teacher and student accounts</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <UserPlus className="h-4 w-4" />
                    <span className="text-sm">Admin endpoint ready</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Class Operations</CardTitle>
                  <CardDescription>Assign students and monitor classes</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <GraduationCap className="h-4 w-4" />
                    <span className="text-sm">Class workflows in progress</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Platform Visibility</CardTitle>
                  <CardDescription>Audit and system-level insights</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Users className="h-4 w-4" />
                    <span className="text-sm">{users.length} users in system</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Users</CardTitle>
              <CardDescription>Current users visible to admin.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 flex items-center gap-3">
                <Input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by name, username, or email"
                />
                <Dialog open={createUserOpen} onOpenChange={setCreateUserOpen}>
                  <DialogTrigger asChild>
                    <Button>
                      <UserPlus className="mr-2 h-4 w-4" />
                      Add User
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Create User</DialogTitle>
                      <DialogDescription>Create a teacher or student account.</DialogDescription>
                    </DialogHeader>

                    <div className="space-y-3">
                      <div>
                        <Label>Name</Label>
                        <Input value={newUser.name} onChange={(e) => setNewUser((p) => ({ ...p, name: e.target.value }))} />
                      </div>
                      <div>
                        <Label>Username</Label>
                        <Input value={newUser.username} onChange={(e) => setNewUser((p) => ({ ...p, username: e.target.value }))} />
                      </div>
                      <div>
                        <Label>Password</Label>
                        <Input type="password" value={newUser.password} onChange={(e) => setNewUser((p) => ({ ...p, password: e.target.value }))} />
                      </div>
                      <div>
                        <Label>Email (optional)</Label>
                        <Input value={newUser.email || ""} onChange={(e) => setNewUser((p) => ({ ...p, email: e.target.value }))} />
                      </div>
                      <div>
                        <Label>Role</Label>
                        <Select value={newUser.role} onValueChange={(value: "student" | "teacher") => setNewUser((p) => ({ ...p, role: value, class_id: value === "student" ? p.class_id : null }))}>
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="Select role" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="student">Student</SelectItem>
                            <SelectItem value="teacher">Teacher</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      {newUser.role === "student" && (
                        <div>
                          <Label>Class</Label>
                          <Select value={newUser.class_id || ""} onValueChange={(value) => setNewUser((p) => ({ ...p, class_id: value }))}>
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Assign class" />
                            </SelectTrigger>
                            <SelectContent>
                              {classes.map((cls) => (
                                <SelectItem key={cls.id} value={cls.id}>
                                  {cls.name}{cls.section ? ` - ${cls.section}` : ""}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )}
                    </div>

                    <DialogFooter>
                      <Button variant="outline" onClick={() => setCreateUserOpen(false)}>Cancel</Button>
                      <Button onClick={handleCreateUser}>Create</Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>

                <Dialog open={createClassOpen} onOpenChange={setCreateClassOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline">
                      <GraduationCap className="mr-2 h-4 w-4" />
                      Add Class
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Create Class</DialogTitle>
                      <DialogDescription>Add a new class and optionally assign a teacher.</DialogDescription>
                    </DialogHeader>

                    <div className="space-y-3">
                      <div>
                        <Label>Class Name</Label>
                        <Input value={newClass.name} onChange={(e) => setNewClass((p) => ({ ...p, name: e.target.value }))} />
                      </div>
                      <div>
                        <Label>Section (optional)</Label>
                        <Input value={newClass.section} onChange={(e) => setNewClass((p) => ({ ...p, section: e.target.value }))} />
                      </div>
                      <div>
                        <Label>Teacher (optional)</Label>
                        <Select value={newClass.teacher_id} onValueChange={(value) => setNewClass((p) => ({ ...p, teacher_id: value }))}>
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="Select teacher" />
                          </SelectTrigger>
                          <SelectContent>
                            {teachers.map((teacher) => (
                              <SelectItem key={teacher.id} value={teacher.id}>
                                {teacher.name} ({teacher.username})
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <DialogFooter>
                      <Button variant="outline" onClick={() => setCreateClassOpen(false)}>Cancel</Button>
                      <Button onClick={handleCreateClass}>Create Class</Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>

              <div className="space-y-2">
                {filteredUsers.map((user) => (
                  <div key={user.id} className="flex flex-wrap items-center justify-between gap-3 rounded-md border p-3">
                    <div>
                      <p className="font-medium">{user.name}</p>
                      <p className="text-xs text-muted-foreground">{user.username} {user.email ? `• ${user.email}` : ""}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="capitalize">
                        {user.role}
                      </Badge>
                      {user.class_id && <Badge variant="outline">Class {user.class_id}</Badge>}
                      {user.must_change_password && <Badge variant="destructive">Reset Pending</Badge>}

                      {user.role === "student" && (
                        <div className="flex items-center gap-2">
                          <Select
                            value={classSelectionByUser[user.id] ?? user.class_id ?? ""}
                            onValueChange={(value) =>
                              setClassSelectionByUser((prev) => ({
                                ...prev,
                                [user.id]: value,
                              }))
                            }
                          >
                            <SelectTrigger className="w-48">
                              <SelectValue placeholder="Assign class" />
                            </SelectTrigger>
                            <SelectContent>
                              {classes.map((cls) => (
                                <SelectItem key={cls.id} value={cls.id}>
                                  {cls.name}{cls.section ? ` - ${cls.section}` : ""}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <Button size="sm" onClick={() => assignStudentClass(user.id)}>
                            Save
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {!isLoading && filteredUsers.length === 0 && (
                  <p className="text-sm text-muted-foreground">No users match your search.</p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Classes</CardTitle>
              <CardDescription>Current class roster and assignments.</CardDescription>
            </CardHeader>
            <CardContent>
              {classes.length === 0 ? (
                <p className="text-sm text-muted-foreground">No classes yet. Create your first class.</p>
              ) : (
                <div className="space-y-2">
                  {classes.map((cls) => (
                    <div key={cls.id} className="flex flex-wrap items-center justify-between gap-3 rounded-md border p-3">
                      <div>
                        <p className="font-medium">{cls.name}{cls.section ? ` - ${cls.section}` : ""}</p>
                        <p className="text-xs text-muted-foreground">Teacher: {cls.teacher_name || "Not assigned"}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{cls.student_count} students</Badge>
                        {!cls.is_active && <Badge variant="destructive">Inactive</Badge>}
                        <Button size="sm" variant="ghost" onClick={() => toggleClassDetails(cls.id)}>
                          {activeClassId === cls.id ? "Hide Students" : "View Students"}
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => openEditClassDialog(cls)}>
                          Edit
                        </Button>
                        <Button size="sm" onClick={() => openBulkEnrollDialog(cls)}>
                          Bulk Enroll
                        </Button>
                      </div>

                      {activeClassId === cls.id && (
                        <div className="mt-3 w-full rounded-md border bg-muted/20 p-3">
                          {isLoadingClassStudents ? (
                            <div className="flex items-center justify-center py-4">
                              <LoadingSpinner size="sm" />
                            </div>
                          ) : activeClassStudents.length === 0 ? (
                            <p className="text-sm text-muted-foreground">No students assigned to this class.</p>
                          ) : (
                            <div className="space-y-2">
                              {activeClassStudents.map((student) => (
                                <div key={student.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border bg-background p-2">
                                  <div>
                                    <p className="text-sm font-medium">{student.name}</p>
                                    <p className="text-xs text-muted-foreground">{student.username} {student.email ? `• ${student.email}` : ""}</p>
                                  </div>
                                  <div className="flex flex-wrap items-center gap-2">
                                    <Select
                                      value={classSelectionByUser[student.id] ?? student.class_id ?? ""}
                                      onValueChange={(value) =>
                                        setClassSelectionByUser((prev) => ({
                                          ...prev,
                                          [student.id]: value,
                                        }))
                                      }
                                    >
                                      <SelectTrigger className="w-48">
                                        <SelectValue placeholder="Reassign class" />
                                      </SelectTrigger>
                                      <SelectContent>
                                        {classes.map((targetClass) => (
                                          <SelectItem key={targetClass.id} value={targetClass.id}>
                                            {targetClass.name}{targetClass.section ? ` - ${targetClass.section}` : ""}
                                          </SelectItem>
                                        ))}
                                      </SelectContent>
                                    </Select>
                                    <Button size="sm" variant="outline" onClick={() => assignStudentClass(student.id)}>
                                      Reassign
                                    </Button>
                                    <Button size="sm" variant="destructive" onClick={() => assignStudentClass(student.id, null)}>
                                      Remove
                                    </Button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Dialog open={editClassOpen} onOpenChange={setEditClassOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Edit Class</DialogTitle>
                <DialogDescription>Update class details and teacher assignment.</DialogDescription>
              </DialogHeader>

              <div className="space-y-3">
                <div>
                  <Label>Class Name</Label>
                  <Input value={editClassForm.name} onChange={(e) => setEditClassForm((p) => ({ ...p, name: e.target.value }))} />
                </div>
                <div>
                  <Label>Section</Label>
                  <Input value={editClassForm.section} onChange={(e) => setEditClassForm((p) => ({ ...p, section: e.target.value }))} />
                </div>
                <div>
                  <Label>Teacher</Label>
                  <Select
                    value={editClassForm.teacher_id || "__none__"}
                    onValueChange={(value) => setEditClassForm((p) => ({ ...p, teacher_id: value === "__none__" ? "" : value }))}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select teacher" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">Not assigned</SelectItem>
                      {teachers.map((teacher) => (
                        <SelectItem key={teacher.id} value={teacher.id}>
                          {teacher.name} ({teacher.username})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    id="edit-class-active"
                    type="checkbox"
                    checked={editClassForm.is_active}
                    onChange={(e) => setEditClassForm((p) => ({ ...p, is_active: e.target.checked }))}
                  />
                  <Label htmlFor="edit-class-active">Class is active</Label>
                </div>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setEditClassOpen(false)} disabled={isSavingClass}>Cancel</Button>
                <Button onClick={handleUpdateClass} disabled={isSavingClass}>{isSavingClass ? "Saving..." : "Save"}</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={bulkEnrollOpen} onOpenChange={setBulkEnrollOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Bulk Enroll Students</DialogTitle>
                <DialogDescription>
                  Select students to assign to {enrollTargetClass?.name || "this class"}.
                </DialogDescription>
              </DialogHeader>

              <div className="max-h-80 space-y-2 overflow-y-auto">
                <Input
                  value={bulkEnrollSearch}
                  onChange={(e) => setBulkEnrollSearch(e.target.value)}
                  placeholder="Search students by name, username, or email"
                />

                {filteredBulkStudents.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No student accounts available.</p>
                ) : (
                  filteredBulkStudents.map((student) => {
                    const checked = selectedStudentIds.includes(student.id)
                    return (
                      <label key={student.id} className="flex items-center justify-between rounded-md border p-2">
                        <div>
                          <p className="text-sm font-medium">{student.name}</p>
                          <p className="text-xs text-muted-foreground">{student.username} {student.class_id ? `• Class ${student.class_id}` : ""}</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(e) => toggleStudentSelection(student.id, e.target.checked)}
                        />
                      </label>
                    )
                  })
                )}
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setBulkEnrollOpen(false)} disabled={isSavingEnrollment}>Cancel</Button>
                <Button onClick={handleSaveBulkEnrollment} disabled={isSavingEnrollment}>
                  {isSavingEnrollment ? "Saving..." : "Save Enrollment"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </main>
      </div>
    </AuthGuard>
  )
}
