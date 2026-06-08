"use client";
import { useState, useEffect } from "react";
import { useNotebookSources } from "@/lib/hooks/use-sources";

interface ExamTopic { topic: string; count: number; description: string; }

export function ExamAnalyzer({ notebookId }: { notebookId: string }) {
  const { sources, isLoading: sourcesLoading } = useNotebookSources(notebookId);
  const [sourceId, setSourceId] = useState("");
  const [topics, setTopics] = useState<ExamTopic[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [cached, setCached] = useState(false);

  useEffect(() => {
    if (notebookId) loadTopics();
  }, [notebookId]);

  async function loadTopics() {
    try {
      const res = await fetch(`/api/edunote/exam/topics/${notebookId}`);
      const data = await res.json();
      if (Array.isArray(data)) setTopics(data);
    } catch { /* ignore */ }
  }

  async function analyze() {
    if (!sourceId) { setError("請先選擇來源文件"); return; }
    setLoading(true); setError("");
    try {
      const res = await fetch("/api/edunote/exam/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notebook_id: notebookId, source_id: sourceId }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setCached(data.cached === true);
      await loadTopics();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  function sourceLabel(s: { title: string | null; asset: { file_path?: string; url?: string } | null }) {
    if (s.title) return s.title;
    if (s.asset?.file_path) return s.asset.file_path.split("/").pop() ?? s.asset.file_path;
    if (s.asset?.url) return s.asset.url;
    return "未命名來源";
  }

  return (
    <div className="p-4 space-y-4 text-gray-900 bg-white min-h-full">
      <h2 className="text-xl font-bold">★ 考點分析器</h2>
      <div className="flex gap-2">
        {sourcesLoading ? (
          <div className="flex-1 border rounded px-3 py-2 text-gray-400">載入來源中...</div>
        ) : sources.length === 0 ? (
          <div className="flex-1 border rounded px-3 py-2 text-gray-400">
            尚未有來源。請先在「來源」區上傳 PDF。
          </div>
        ) : (
          <select
            className="border rounded px-3 py-2 flex-1 bg-white text-gray-900"
            value={sourceId}
            onChange={e => setSourceId(e.target.value)}
          >
            <option value="">請選擇要分析的文件...</option>
            {sources.map(s => (
              <option key={s.id} value={s.id}>{sourceLabel(s)}</option>
            ))}
          </select>
        )}
        <button onClick={analyze} disabled={loading || !sourceId}
          className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600 disabled:opacity-50">
          {loading ? "分析中..." : "分析考點"}
        </button>
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {cached && <p className="text-blue-500 text-sm">此文件已分析過，顯示先前結果。</p>}
      {topics.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">考點主題（重要度）</h3>
            <button
              onClick={async () => {
                await fetch(`/api/edunote/exam/topics/${notebookId}`, { method: "DELETE" });
                setTopics([]);
                setSourceId("");
                setCached(false);
              }}
              className="text-xs text-red-400 hover:text-red-600"
            >
              清除全部考點
            </button>
          </div>
          {topics.map(t => (
            <div key={t.topic} className="flex items-center gap-3 p-2 bg-orange-50 rounded">
              <span className="font-medium w-40">{t.topic}</span>
              <div className="flex-1 bg-gray-200 h-2 rounded">
                <div className="bg-orange-400 h-2 rounded" style={{ width: `${Math.min(t.count * 10, 100)}%` }} />
              </div>
              <span className="text-sm text-gray-600">重要度 {t.count}</span>
              {t.count >= 5 && <span className="text-orange-500">🔥</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
