'use client'

import { useParams } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import { QuizPlayer } from '@/components/edunote/QuizPlayer'
import { EduNoteNav } from '@/components/edunote/EduNoteNav'

export default function QuizPage() {
  const params = useParams()
  const rawId = params?.id ? decodeURIComponent(params.id as string) : ''

  return (
    <AppShell>
      <div className="flex h-full">
        <aside className="w-56 border-r p-4 shrink-0 overflow-y-auto">
          <EduNoteNav notebookRawId={rawId} />
        </aside>
        <main className="flex-1 overflow-y-auto">
          <QuizPlayer notebookId={`notebook:${rawId}`} userId="user:demo" />
        </main>
      </div>
    </AppShell>
  )
}
