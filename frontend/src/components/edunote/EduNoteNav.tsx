"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { QuickPrepButton } from "./QuickPrepButton";

interface EduNoteNavProps {
  notebookRawId: string;
}

const NAV_ITEMS = [
  { href: (id: string) => `/notebooks/${id}/exam`, label: "★ 考點分析", color: "text-orange-600" },
  { href: (id: string) => `/notebooks/${id}/quiz`, label: "✎ 測驗練習", color: "text-green-600" },
  { href: (id: string) => `/notebooks/${id}/flashcards`, label: "記憶卡片", color: "text-blue-600" },
  { href: (id: string) => `/notebooks/${id}/progress`, label: "學習進度", color: "text-purple-600" },
  { href: (id: string) => `/notebooks/${id}/feynman`, label: "費曼模式", color: "text-indigo-600" },
];

export function EduNoteNav({ notebookRawId }: EduNoteNavProps) {
  const pathname = usePathname();

  return (
    <div className="mt-3 border-t pt-3 flex flex-wrap items-center gap-2">
      <span className="text-xs font-semibold text-gray-400 uppercase mr-1">EduNote</span>
      <nav className="flex flex-wrap items-center gap-1.5">
        {NAV_ITEMS.map(item => {
          const href = item.href(notebookRawId);
          const isActive = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`px-3 py-1 rounded-full text-sm border transition-colors hover:bg-gray-100 ${item.color} ${isActive ? "bg-gray-100 font-semibold border-current" : "border-gray-200"}`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="ml-auto">
        <QuickPrepButton
          notebookId={`notebook:${notebookRawId}`}
          notebookRawId={notebookRawId}
        />
      </div>
    </div>
  );
}
