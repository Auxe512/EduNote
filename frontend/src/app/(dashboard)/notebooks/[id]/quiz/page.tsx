'use client'

import { useParams } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import { QuizPlayer } from '@/components/edunote/QuizPlayer'
import { EduNoteNav } from '@/components/edunote/EduNoteNav'
import { StudentIdSetup } from '@/components/edunote/StudentIdSetup'
import { useStudentId } from '@/lib/hooks/use-student-id'

export default function QuizPage() {
  const params = useParams()
  const rawId = params?.id ? decodeURIComponent(params.id as string) : ''
  const { userId, isReady, setStudentName } = useStudentId()

  return (
    <AppShell>
      {isReady && !userId && <StudentIdSetup onSubmit={setStudentName} />}
      <div className="flex h-full">
        <aside className="w-56 border-r p-4 shrink-0 overflow-y-auto">
          <EduNoteNav notebookRawId={rawId} />
        </aside>
        <main className="flex-1 overflow-y-auto bg-white text-gray-900">
          {userId && (
            <QuizPlayer notebookId={`notebook:${rawId}`} userId={userId} />
          )}
        </main>
      </div>
    </AppShell>
  )
}
