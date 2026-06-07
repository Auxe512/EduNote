"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export function QuickPrepButton({ notebookId, notebookRawId }: { notebookId: string; notebookRawId: string }) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const router = useRouter();

  async function quickPrep() {
    setLoading(true);
    setStatus("備考中...");
    try {
      const res = await fetch(`/api/edunote/quickprep/${notebookId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ exam_source_id: null }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      // The endpoint returns 200 even when an individual step failed, putting the
      // failure in the body as { quiz: { error }, flashcards: { error } }. The quiz
      // is where we navigate, so a quiz error must block the redirect rather than
      // sending the student to an empty quiz with a false "完成！" message.
      const data = await res.json();
      const quizErr = data?.quiz?.error;
      if (quizErr) {
        setStatus(`測驗生成失敗：${quizErr}`);
        setLoading(false);
        return;
      }

      const cardErr = data?.flashcards?.error;
      setStatus(cardErr ? "測驗已生成（卡片略過），跳轉..." : "完成！跳轉至測驗...");
      setTimeout(() => router.push(`/notebooks/${notebookRawId}/quiz`), 1000);
    } catch {
      setStatus("發生錯誤，請重試");
    }
    setLoading(false);
  }

  return (
    <div>
      <button
        onClick={quickPrep}
        disabled={loading}
        className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white px-4 py-3 rounded-lg font-bold hover:opacity-90 disabled:opacity-50"
      >
        {loading ? "備考中..." : "一鍵備考"}
      </button>
      {status && <p className="text-xs text-gray-500 mt-1 text-center">{status}</p>}
    </div>
  );
}
