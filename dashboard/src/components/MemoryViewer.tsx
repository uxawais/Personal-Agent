"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Memory = { id: number; category: string; key: string; content: string; importance: number };

export default function MemoryViewer() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/memories")
      .then(setMemories)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-400">Loading...</p>;

  return (
    <div className="max-w-4xl">
      <h2 className="text-2xl font-bold mb-6">Agent Memory</h2>
      {memories.length === 0 ? (
        <p className="text-gray-500">No memories stored yet. Chat with your agent to build memory.</p>
      ) : (
        <div className="space-y-3">
          {memories.map((m) => (
            <div key={m.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="bg-blue-600/20 text-blue-400 px-2 py-0.5 rounded text-xs">{m.category}</span>
                <span className="text-gray-400 text-sm">{m.key}</span>
                <span className="ml-auto text-xs text-gray-500">importance: {m.importance}</span>
              </div>
              <p className="text-gray-200">{m.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
