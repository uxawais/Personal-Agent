"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import ChatPanel from "@/components/ChatPanel";
import SessionList from "@/components/SessionList";
import StatusCard from "@/components/StatusCard";
import PersonalityEditor from "@/components/PersonalityEditor";
import MemoryViewer from "@/components/MemoryViewer";
import ConversationLogs from "@/components/ConversationLogs";

type Tab = "chat" | "status" | "personality" | "memory" | "logs";

export default function Home() {
  const [tab, setTab] = useState<Tab>("chat");
  const [status, setStatus] = useState<any>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    apiFetch("/status").then(setStatus).catch(console.error);
  }, []);

  useEffect(() => {
    if (sessionId === null) setSessionId(crypto.randomUUID());
  }, [sessionId]);

  function startNewChat() {
    setSessionId(crypto.randomUUID());
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "chat", label: "Chat" },
    { id: "status", label: "Status" },
    { id: "personality", label: "Personality" },
    { id: "memory", label: "Memory" },
    { id: "logs", label: "Logs" },
  ];

  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-xl font-bold">Chorus Agent</h1>
          <p className="text-sm text-gray-400 mt-1">Dashboard</p>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`w-full text-left px-4 py-2 rounded-lg transition ${
                tab === t.id ? "bg-blue-600 text-white" : "text-gray-300 hover:bg-gray-800"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-800 text-xs text-gray-500">
          {status ? (
            <span className="text-green-400">● Connected</span>
          ) : (
            <span className="text-red-400">● Disconnected</span>
          )}
        </div>
      </aside>

      <main className="flex-1 overflow-auto p-8">
        {tab === "chat" && (
          <div className="flex h-full">
            <SessionList activeId={sessionId} onSelect={setSessionId} onNew={startNewChat} />
            <div className="flex-1 pl-8">
              {sessionId ? (
                <ChatPanel sessionId={sessionId} />
              ) : (
                <p className="text-gray-500">Start a new chat</p>
              )}
            </div>
          </div>
        )}
        {tab === "status" && <StatusCard status={status} />}
        {tab === "personality" && <PersonalityEditor />}
        {tab === "memory" && <MemoryViewer />}
        {tab === "logs" && <ConversationLogs />}
      </main>
    </div>
  );
}
