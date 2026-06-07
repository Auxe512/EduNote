'use client'

import { useParams } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import { ExamAnalyzer } from '@/components/edunote/ExamAnalyzer'
import { EduNoteNav } from '@/components/edunote/EduNoteNav'

export default function ExamPage() {
  const params = useParams()
  const rawId = params?.id ? decodeURIComponent(params.id as string) : ''

  return (
    <AppShell>
      <div className="flex h-full">
        <aside className="w-56 border-r p-4 shrink-0 overflow-y-auto">
          <EduNoteNav notebookRawId={rawId} />
        </aside>
        <main className="flex-1 overflow-y-auto bg-white text-gray-900">
          <ExamAnalyzer notebookId={`notebook:${rawId}`} />
        </main>
      </div>
    </AppShell>
  )
}
