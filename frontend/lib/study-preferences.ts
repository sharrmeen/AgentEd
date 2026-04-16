export type SubjectDifficulty = "easy" | "intermediate" | "difficult"

const PREFIX = "subject_difficulty_"

export function getSubjectDifficulty(subjectId: string): SubjectDifficulty | null {
  if (typeof window === "undefined") return null
  const value = localStorage.getItem(`${PREFIX}${subjectId}`)
  if (value === "easy" || value === "intermediate" || value === "difficult") {
    return value
  }
  return null
}

export function setSubjectDifficulty(subjectId: string, difficulty: SubjectDifficulty): void {
  if (typeof window === "undefined") return
  localStorage.setItem(`${PREFIX}${subjectId}`, difficulty)
}

export function toQuizDifficulty(difficulty: SubjectDifficulty): "easy" | "medium" | "hard" {
  if (difficulty === "easy") return "easy"
  if (difficulty === "difficult") return "hard"
  return "medium"
}
