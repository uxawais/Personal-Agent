"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Session = {
  conversation_id: string;
  last_message: string | null;
  last_at: string | null;
  message_count: number;
};

export default function SessionList({
  activeId,
  onSelect,
  onNew,
}: {
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}) {
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await apiFetch("/sessions");
        if (!cancelled) setSessions(data);
      } catch (e) {
        console.error(e);
      }
    }
    load();
    const interval = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="w-72 border-r border-gray-800 flex flex-col h-full">
      <div className="p-4 border-b border-gray-800">
        <button
          onClick={onNew}
          className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg font-medium"
        >
          + New Chat
        </button>
      </div>
      <div className="flex-1 overflow-auto p-2 space-y-1">
        {sessions.length === 0 && (
          <p className="text-gray-500 text-sm text-center mt-6">No sessions yet</p>
        )}
        {sessions.map((s) => (
          <button
            key={s.conversation_id}
            onClick={() => onSelect(s.conversation_id)}
            className={`w-full text-left px-3 py-2 rounded-lg transition ${
              activeId === s.conversation_id
                ? "bg-gray-800"
                : "hover:bg-gray-800/50"
            }`}
          >
            <p className="text-sm text-gray-200 truncate">
              {s.last_message || "Empty conversation"}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">
              {s.message_count} messages
              {s.last_at ? ` · ${new Date(s.last_at).toLocaleString()}` : ""}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}
