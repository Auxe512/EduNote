"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

interface Question { id: string; question: string; options: string[]; correct: string; }

export function QuizPlayer({ notebookId, userId }: { notebookId: string; userId: string }) {
  const router = useRouter();
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [current, setCurrent] = useState(0);
  const [chosen, setChosen] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ correct: boolean; answer: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  async function generateQuestions() {
    setGenerating(true);
    const res = await fetch(`/api/edunote/quiz/generate/${notebookId}`, { method: "POST" });
    const data = await res.json();
    setGenerating(false);
    return data;
  }

  async function startQuiz() {
    setLoading(true);
    // Check if questions exist, generate if not
    const bankRes = await fetch(`/api/edunote/quiz/questions/${notebookId}`);
    const bank = await bankRes.json();
    if (bank.length === 0) {
      await generateQuestions();
    }

    const res = await fetch(`/api/edunote/quiz/start/${notebookId}?user_id=${userId}`, { method: "POST" });
    if (!res.ok) { setLoading(false); return; }
    const data = await res.json();
    setAttemptId(data.attempt_id);

    // Fetch full question objects
    const allRes = await fetch(`/api/edunote/quiz/questions/${notebookId}`);
    const allQ: Question[] = await allRes.json();
    const sampled = data.question_ids
      .map((id: string) => allQ.find(q => String(q.id) === String(id)))
      .filter(Boolean) as Question[];
    setQuestions(sampled);
    setLoading(false);
  }

  async function submitAnswer(letter: string) {
    if (!attemptId || feedback) return;
    setChosen(letter);
    const res = await fetch(`/api/edunote/quiz/attempt/${attemptId}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: questions[current].id, chosen: letter }),
    });
    const data = await res.json();
    setFeedback({ correct: data.is_correct, answer: data.correct });
  }

  async function nextQuestion() {
    setFeedback(null); setChosen(null);
    if (current + 1 >= questions.length) {
      await fetch(`/api/edunote/quiz/attempt/${attemptId}/complete`, { method: "POST" });
      router.push(`/quiz/${attemptId}/result`);
    } else {
      setCurrent(c => c + 1);
    }
  }

  if (!attemptId) return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">✎ 測驗練習</h2>
      <button onClick={startQuiz} disabled={loading || generating}
        className="bg-green-500 text-white px-6 py-3 rounded-lg text-lg hover:bg-green-600 disabled:opacity-50">
        {loading ? "載入題目中..." : generating ? "生成題目中..." : "開始測驗（10 題）"}
      </button>
    </div>
  );

  if (questions.length === 0) return <div className="p-4">載入題目中...</div>;

  const q = questions[current];
  return (
    <div className="p-4 max-w-2xl space-y-4">
      <div className="text-sm text-gray-500">第 {current + 1} / {questions.length} 題</div>
      <p className="text-lg font-medium">{q.question}</p>
      <div className="space-y-2">
        {q.options.map((opt, i) => {
          const letter = ["A", "B", "C", "D"][i];
          const isChosen = chosen === letter;
          const isCorrect = feedback?.answer === letter;
          let cls = "w-full text-left p-3 rounded border ";
          if (feedback) {
            cls += isCorrect ? "bg-green-100 border-green-500" : isChosen ? "bg-red-100 border-red-400" : "opacity-50";
          } else {
            cls += "hover:bg-gray-50";
          }
          return (
            <button key={letter} onClick={() => submitAnswer(letter)} className={cls}>{opt}</button>
          );
        })}
      </div>
      {feedback && (
        <div className={`p-3 rounded ${feedback.correct ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
          {feedback.correct ? "✓ 正確！" : `✗ 答案是 ${feedback.answer}`}
        </div>
      )}
      {feedback && (
        <button onClick={nextQuestion} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
          {current + 1 >= questions.length ? "查看結果" : "下一題"}
        </button>
      )}
    </div>
  );
}
