"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Log = {
  id: number;
  conversation_id: string;
  channel: string;
  user_id: string;
  role: string;
  content: string;
  model_used: string | null;
  tokens_used: number;
  created_at: string | null;
};

export default function ConversationLogs() {
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/conversations")
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-400">Loading...</p>;

  return (
    <div className="max-w-5xl">
      <h2 className="text-2xl font-bold mb-6">Conversation Logs</h2>
      {logs.length === 0 ? (
        <p className="text-gray-500">No conversations yet.</p>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-800">
              <tr>
                <th className="text-left px-4 py-3 text-gray-400">Time</th>
                <th className="text-left px-4 py-3 text-gray-400">Channel</th>
                <th className="text-left px-4 py-3 text-gray-400">Role</th>
                <th className="text-left px-4 py-3 text-gray-400">Content</th>
                <th className="text-left px-4 py-3 text-gray-400">Model</th>
                <th className="text-left px-4 py-3 text-gray-400">Tokens</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-t border-gray-800">
                  <td className="px-4 py-3 text-gray-400 whitespace-nowrap">
                    {log.created_at ? new Date(log.created_at).toLocaleString() : "-"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="bg-gray-800 px-2 py-0.5 rounded text-xs">{log.channel}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={log.role === "user" ? "text-blue-400" : "text-green-400"}>{log.role}</span>
                  </td>
                  <td className="px-4 py-3 max-w-md truncate">{log.content}</td>
                  <td className="px-4 py-3 text-gray-400">{log.model_used || "-"}</td>
                  <td className="px-4 py-3 text-gray-400">{log.tokens_used || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
