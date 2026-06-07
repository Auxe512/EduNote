import { useState, useEffect } from 'react'

const STORAGE_KEY = 'edunote:student_id'

export function useStudentId() {
  const [userId, setUserId] = useState<string | null>(null)
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    setUserId(stored)
    setIsReady(true)
  }, [])

  function setStudentName(name: string) {
    const trimmed = name.trim()
    if (!trimmed) return
    const id = `user:${trimmed.toLowerCase().replace(/\s+/g, '_')}`
    localStorage.setItem(STORAGE_KEY, id)
    setUserId(id)
  }

  function reset() {
    localStorage.removeItem(STORAGE_KEY)
    setUserId(null)
  }

  return { userId, isReady, setStudentName, reset }
}
