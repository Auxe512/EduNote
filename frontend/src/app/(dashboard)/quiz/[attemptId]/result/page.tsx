'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import apiClient from '@/lib/api/client'

interface Result {
  score: number;
  correct: number;
  total: number;
  weak_topics: { topic: string; error_rate: number }[];
  completed: boolean;
}

export default function ResultPage() {
  const params = useParams()
  const attemptId = params?.attemptId ? decodeURIComponent(params.attemptId as string) : ''
  const [result, setResult] = useState<Result | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!attemptId) return
    apiClient.get(`/edunote/quiz/attempt/${attemptId}/result`)
      .then(r => setResult(r.data))
      .catch(() => setError('無法載入結果'))
  }, [attemptId])

  if (error) return (
    <AppShell>
      <div className="p-4 text-red-500">{error}</div>
    </AppShell>
  )

  if (!result) return (
    <AppShell>
      <div className="p-4">載入結果中...</div>
    </AppShell>
  )

  if (!result.completed) return (
    <AppShell>
      <div className="p-4 text-yellow-600">測驗尚未完成，請先作答所有題目。</div>
    </AppShell>
  )

  return (
    <AppShell>
      <div className="p-6 max-w-lg space-y-4 bg-white text-gray-900 min-h-full">
        <h2 className="text-2xl font-bold">測驗結果</h2>
        <div className="text-5xl font-bold text-center py-4">{result.score}分</div>
        <p className="text-center text-gray-600">{result.correct} / {result.total} 題答對</p>
        {result.weak_topics?.length > 0 && (
          <div>
            <h3 className="font-semibold mb-2">需加強的主題：</h3>
            {result.weak_topics.map(t => (
              <div key={t.topic} className="flex justify-between p-2 bg-red-50 rounded mb-1">
                <span>{t.topic}</span>
                <span className="text-red-600">答錯率 {Math.round(t.error_rate * 100)}%</span>
              </div>
            ))}
          </div>
        )}
        <button
          onClick={() => window.history.back()}
          className="block w-full text-center bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
        >
          返回
        </button>
      </div>
    </AppShell>
  )
}
