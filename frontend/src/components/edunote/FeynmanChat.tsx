"use client";
import { useState, useRef, useEffect } from "react";
import apiClient from "@/lib/api/client";

interface Message {
  role: "user" | "ai";
  content: string;
}

const FEYNMAN_SYSTEM_PREFIX = `你是一個完全不懂這個主題的困惑學生。
請用繁體中文，以學生的視角提出困惑的問題，假裝你什麼都不懂。
當使用者解釋時，繼續追問更深的問題，直到你「真正理解」為止。
不要超出學生角色。`;

export function FeynmanChat({ notebookId }: { notebookId: string }) {
  const [topic, setTopic] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function startSession() {
    if (!topic.trim()) { setError("請輸入一個主題"); return; }
    setStarting(true); setError("");

    try {
      // Create a new chat session for this notebook
      const sessionRes = await apiClient.post("/chat/sessions", {
        notebook_id: `notebook:${notebookId}`,
        title: `費曼練習：${topic}`,
      });
      const newSessionId: string = sessionRes.data.id;
      setSessionId(newSessionId);

      // Send the opening message as the AI (we simulate it locally, then the real AI continues)
      const openingMsg = `你好！我聽說你要教我「${topic}」？我完全不懂，可以從頭解釋給我聽嗎？`;
      const initialMessages: Message[] = [{ role: "ai", content: openingMsg }];
      setMessages(initialMessages);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "無法建立對話");
    } finally {
      setStarting(false);
    }
  }

  async function sendMessage() {
    if (!input.trim() || !sessionId || loading) return;
    const userMsg = input.trim();
    setInput("");
    setLoading(true);
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);

    try {
      const feynmanContext = `${FEYNMAN_SYSTEM_PREFIX}\n\n主題：${topic}\n\n請繼續扮演困惑的學生，對使用者的解釋提出更多問題。`;

      const res = await apiClient.post("/chat/execute", {
        session_id: sessionId,
        message: userMsg,
        context: {
          sources: [],
          notes: [
            {
              id: "feynman-context",
              content: feynmanContext,
              title: "費曼模式指示",
            },
          ],
        },
      });

      const allMessages: Array<{ type: string; content: string }> = res.data.messages || [];
      const lastAi = [...allMessages].reverse().find(m => m.type === "ai");
      if (lastAi) {
        setMessages(prev => [...prev, { role: "ai", content: lastAi.content }]);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "傳送失敗");
      setMessages(prev => prev.slice(0, -1)); // remove optimistic user msg
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  if (!sessionId) {
    return (
      <div className="p-4 space-y-4 max-w-lg">
        <h2 className="text-xl font-bold">費曼學習法</h2>
        <p className="text-sm text-gray-600">
          選擇一個主題，AI 會扮演不懂的學生，讓你透過教導來加深理解。
        </p>
        <div className="flex gap-2">
          <input
            className="border rounded px-3 py-2 flex-1"
            placeholder="輸入你想練習教學的主題（如：牛頓第二定律）"
            value={topic}
            onChange={e => setTopic(e.target.value)}
            onKeyDown={e => e.key === "Enter" && startSession()}
          />
          <button
            onClick={startSession}
            disabled={starting}
            className="bg-indigo-500 text-white px-4 py-2 rounded hover:bg-indigo-600 disabled:opacity-50"
          >
            {starting ? "開始中..." : "開始教學"}
          </button>
        </div>
        {error && <p className="text-red-500 text-sm">{error}</p>}
      </div>
    );
  }

  return (
    <div className="p-4 flex flex-col max-w-2xl h-full" style={{ minHeight: "70vh" }}>
      <div className="flex items-center gap-2 mb-4">
        <h2 className="text-xl font-bold">費曼模式：{topic}</h2>
        <button
          onClick={() => { setSessionId(null); setMessages([]); setTopic(""); }}
          className="text-xs text-gray-400 hover:text-gray-600 ml-auto"
        >
          重新開始
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 mb-4 border rounded-lg p-3 bg-gray-50">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg text-sm ${
              m.role === "user"
                ? "bg-indigo-500 text-white"
                : "bg-white border text-gray-800"
            }`}>
              {m.role === "ai" && <span className="text-xs text-gray-400 block mb-1">困惑的學生</span>}
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border rounded-lg px-4 py-2 text-sm text-gray-400">
              思考中...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && <p className="text-red-500 text-xs mb-2">{error}</p>}

      <div className="flex gap-2">
        <textarea
          className="border rounded px-3 py-2 flex-1 resize-none text-sm"
          rows={2}
          placeholder="解釋給學生聽... (Enter 送出，Shift+Enter 換行)"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="bg-indigo-500 text-white px-4 rounded hover:bg-indigo-600 disabled:opacity-50"
        >
          送出
        </button>
      </div>
    </div>
  );
}
