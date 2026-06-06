"use client";
import { useState, useEffect } from "react";

interface Card { id: string; front: string; back: string; topic: string; }

export function FlashcardDeck({ notebookId, userId }: { notebookId: string; userId: string }) {
  const [cards, setCards] = useState<Card[]>([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [stats, setStats] = useState({ correct: 0, wrong: 0 });
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => { loadCards(); }, []);

  async function loadCards() {
    const res = await fetch(`/api/edunote/flashcards/${notebookId}`);
    const data = await res.json();
    setCards(data);
  }

  async function generate() {
    setLoading(true);
    await fetch(`/api/edunote/flashcards/generate/${notebookId}`, { method: "POST" });
    await loadCards();
    setLoading(false);
  }

  async function review(correct: boolean) {
    const card = cards[index];
    await fetch(`/api/edunote/flashcards/${card.id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, is_correct: correct }),
    });
    setStats(s => ({ ...s, correct: s.correct + (correct ? 1 : 0), wrong: s.wrong + (correct ? 0 : 1) }));
    setFlipped(false);
    if (index + 1 >= cards.length) setDone(true);
    else setIndex(i => i + 1);
  }

  if (cards.length === 0) return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">記憶卡片</h2>
      <button onClick={generate} disabled={loading}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50">
        {loading ? "生成中..." : "生成記憶卡片"}
      </button>
    </div>
  );

  if (done) return (
    <div className="p-4 space-y-4 text-center">
      <h2 className="text-xl font-bold">複習完成！</h2>
      <p className="text-green-600 text-2xl">✓ 記住了：{stats.correct} 張</p>
      <p className="text-red-600 text-2xl">✗ 還不會：{stats.wrong} 張</p>
      <button onClick={() => { setIndex(0); setDone(false); setFlipped(false); setStats({ correct: 0, wrong: 0 }); }}
        className="bg-blue-500 text-white px-4 py-2 rounded">再來一次</button>
    </div>
  );

  const card = cards[index];
  return (
    <div className="p-4 space-y-4 max-w-lg">
      <div className="flex justify-between text-sm text-gray-500">
        <span>第 {index + 1} / {cards.length} 張</span>
        <span className="text-orange-500 text-xs">{card.topic}</span>
      </div>
      <div onClick={() => setFlipped(f => !f)}
        className="cursor-pointer border-2 rounded-xl p-8 min-h-40 flex items-center justify-center text-center bg-white hover:shadow-lg transition-shadow">
        {flipped
          ? <p className="text-lg text-green-700">{card.back}</p>
          : <p className="text-lg font-medium">{card.front}</p>}
      </div>
      {!flipped && <p className="text-center text-sm text-gray-400">點擊卡片翻面</p>}
      {flipped && (
        <div className="flex gap-3">
          <button onClick={() => review(false)} className="flex-1 py-3 bg-red-100 text-red-700 rounded-lg hover:bg-red-200">✗ 還不會</button>
          <button onClick={() => review(true)} className="flex-1 py-3 bg-green-100 text-green-700 rounded-lg hover:bg-green-200">✓ 記住了</button>
        </div>
      )}
    </div>
  );
}
