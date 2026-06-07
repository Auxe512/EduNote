"use client";
import { useState } from "react";

interface Props {
  onSubmit: (name: string) => void;
}

export function StudentIdSetup({ onSubmit }: Props) {
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) { setError("請輸入你的名字"); return; }
    onSubmit(name.trim());
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-8 w-full max-w-sm space-y-4">
        <h2 className="text-xl font-bold">👋 歡迎使用 EduNote</h2>
        <p className="text-sm text-gray-600">
          請輸入你的名字，系統會為你獨立記錄學習進度與測驗結果。
        </p>
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="text"
            placeholder="例如：王小明"
            value={name}
            onChange={e => { setName(e.target.value); setError(""); }}
            className="w-full border rounded-lg px-4 py-2 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            autoFocus
          />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            type="submit"
            className="w-full bg-indigo-500 text-white py-2 rounded-lg hover:bg-indigo-600 font-medium"
          >
            開始學習
          </button>
        </form>
      </div>
    </div>
  );
}
