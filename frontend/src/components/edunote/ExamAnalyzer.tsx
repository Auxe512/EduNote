"use client";
import { useState } from "react";

interface ExamTopic { topic: string; count: number; description: string; }

export function ExamAnalyzer({ notebookId }: { notebookId: string }) {
  const [sourceId, setSourceId] = useState("");
  const [topics, setTopics] = useState<ExamTopic[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadTopics() {
    const res = await fetch(`/api/edunote/exam/topics/${notebookId}`);
    const data = await res.json();
    setTopics(data);
  }

  async function analyze() {
    if (!sourceId.trim()) { setError("請先填入 Source ID"); return; }
    setLoading(true); setError("");
    try {
      const res = await fetch("/api/edunote/exam/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notebook_id: notebookId, source_id: sourceId }),
      });
      if (!res.ok) throw new Error(await res.text());
      await loadTopics();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">★ 考點分析器</h2>
      <div className="flex gap-2">
        <input
          className="border rounded px-3 py-2 flex-1"
          placeholder="貼上歷年試題的 Source ID"
          value={sourceId}
          onChange={e => setSourceId(e.target.value)}
        />
        <button onClick={analyze} disabled={loading}
          className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600 disabled:opacity-50">
          {loading ? "分析中..." : "分析考點"}
        </button>
        <button onClick={loadTopics} className="border px-4 py-2 rounded">載入已有考點</button>
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {topics.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-semibold">考點主題（出現頻率）</h3>
          {topics.map(t => (
            <div key={t.topic} className="flex items-center gap-3 p-2 bg-orange-50 rounded">
              <span className="font-medium w-40">{t.topic}</span>
              <div className="flex-1 bg-gray-200 h-2 rounded">
                <div className="bg-orange-400 h-2 rounded" style={{ width: `${Math.min(t.count * 10, 100)}%` }} />
              </div>
              <span className="text-sm text-gray-600">出現 {t.count} 次</span>
              {t.count >= 5 && <span className="text-orange-500">🔥</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
