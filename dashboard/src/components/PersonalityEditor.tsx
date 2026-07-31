"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Personality = {
  name: string;
  role: string;
  tone: string;
  system_prompt: string;
  max_tokens: number;
  temperature: number;
};

export default function PersonalityEditor() {
  const [config, setConfig] = useState<Personality | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    apiFetch("/personality").then(setConfig).catch(console.error);
  }, []);

  async function save() {
    if (!config) return;
    await apiFetch("/personality", { method: "PUT", body: JSON.stringify(config) });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  if (!config) return <p className="text-gray-400">Loading...</p>;

  return (
    <div className="max-w-3xl">
      <h2 className="text-2xl font-bold mb-6">Personality Configuration</h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Name</label>
          <input
            value={config.name}
            onChange={(e) => setConfig({ ...config, name: e.target.value })}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-4 py-2"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Role</label>
          <input
            value={config.role}
            onChange={(e) => setConfig({ ...config, role: e.target.value })}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-4 py-2"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Tone</label>
          <input
            value={config.tone}
            onChange={(e) => setConfig({ ...config, tone: e.target.value })}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-4 py-2"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">System Prompt</label>
          <textarea
            value={config.system_prompt}
            onChange={(e) => setConfig({ ...config, system_prompt: e.target.value })}
            rows={8}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg px-4 py-2 font-mono text-sm"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Max Tokens</label>
            <input
              type="number"
              value={config.max_tokens}
              onChange={(e) => setConfig({ ...config, max_tokens: Number(e.target.value) })}
              className="w-full bg-gray-900 border border-gray-800 rounded-lg px-4 py-2"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Temperature ({config.temperature})</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={config.temperature}
              onChange={(e) => setConfig({ ...config, temperature: Number(e.target.value) })}
              className="w-full"
            />
          </div>
        </div>
        <button
          onClick={save}
          className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg font-medium"
        >
          {saved ? "Saved!" : "Save Changes"}
        </button>
      </div>
    </div>
  );
}
