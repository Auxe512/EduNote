'use client'

import { useParams } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import { FeynmanChat } from '@/components/edunote/FeynmanChat'
import { EduNoteNav } from '@/components/edunote/EduNoteNav'

export default function FeynmanPage() {
  const params = useParams()
  const rawId = params?.id ? decodeURIComponent(params.id as string) : ''

  return (
    <AppShell>
      <div className="flex h-full">
        <aside className="w-56 border-r p-4 shrink-0 overflow-y-auto">
          <EduNoteNav notebookRawId={rawId} />
        </aside>
        <main className="flex-1 overflow-y-auto">
          <FeynmanChat notebookId={rawId} />
        </main>
      </div>
    </AppShell>
  )
}
