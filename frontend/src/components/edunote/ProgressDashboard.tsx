"use client";
import { useState, useEffect } from "react";

interface Progress {
  completion_rate: number;
  read_notes: number;
  total_notes: number;
  avg_quiz_score: number | null;
  quiz_count: number;
  streak_days: number;
  weak_topics: { topic: string; error_rate: number }[];
}

export function ProgressDashboard({ notebookId, userId }: { notebookId: string; userId: string }) {
  const [data, setData] = useState<Progress | null>(null);

  useEffect(() => {
    fetch(`/api/edunote/progress/${notebookId}/${userId}`)
      .then(r => r.json())
      .then(setData);
  }, [notebookId, userId]);

  if (!data) return <div className="p-4">載入進度中...</div>;

  return (
    <div className="p-4 space-y-6 max-w-2xl">
      <h2 className="text-xl font-bold">學習進度</h2>
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-yellow-50 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-yellow-600">{data.completion_rate}%</div>
          <div className="text-sm text-gray-500 mt-1">章節完成率</div>
          <div className="mt-2 bg-gray-200 h-2 rounded">
            <div className="bg-yellow-400 h-2 rounded" style={{ width: `${data.completion_rate}%` }} />
          </div>
        </div>
        <div className="bg-green-50 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-green-600">
            {data.avg_quiz_score !== null ? `${data.avg_quiz_score}分` : "—"}
          </div>
          <div className="text-sm text-gray-500 mt-1">測驗平均分</div>
          <div className="text-xs text-gray-400 mt-1">共 {data.quiz_count} 次</div>
        </div>
        <div className="bg-orange-50 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-orange-600">🔥 {data.streak_days}</div>
          <div className="text-sm text-gray-500 mt-1">連續學習天數</div>
        </div>
      </div>
      {data.weak_topics.length > 0 && (
        <div>
          <h3 className="font-semibold mb-2">需加強的主題</h3>
          <div className="space-y-2">
            {data.weak_topics.map(t => (
              <div key={t.topic} className="flex justify-between items-center p-2 bg-red-50 rounded">
                <span className="text-sm">{t.topic}</span>
                <span className="text-sm text-red-600">答錯率 {Math.round(t.error_rate * 100)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
      <div>
        <h3 className="font-semibold mb-2">筆記閱讀進度</h3>
        <p className="text-sm text-gray-600">已讀 {data.read_notes} / {data.total_notes} 篇</p>
      </div>
    </div>
  );
}
