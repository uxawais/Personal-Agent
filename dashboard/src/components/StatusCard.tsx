"use client";

export default function StatusCard({ status }: { status: any }) {
  if (!status) return <p className="text-gray-400">Loading...</p>;

  return (
    <div className="max-w-3xl">
      <h2 className="text-2xl font-bold mb-6">Agent Status</h2>

      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h3 className="text-sm text-gray-400 mb-2">Status</h3>
          <p className="text-2xl font-bold text-green-400 capitalize">{status.status}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h3 className="text-sm text-gray-400 mb-2">Model Providers</h3>
          <p className="text-2xl font-bold">{status.model_providers?.length || 0}</p>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
        <h3 className="font-semibold mb-4">Channels</h3>
        <div className="space-y-2">
          {Object.entries(status.channels || {}).map(([name, active]) => (
            <div key={name} className="flex items-center justify-between">
              <span className="capitalize">{name}</span>
              <span className={active ? "text-green-400" : "text-red-400"}>
                {active ? "● Active" : "○ Inactive"}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="font-semibold mb-4">Available Tools</h3>
        <div className="flex flex-wrap gap-2">
          {(status.tools || []).map((tool: string) => (
            <span key={tool} className="bg-gray-800 px-3 py-1 rounded-full text-sm">
              {tool}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
