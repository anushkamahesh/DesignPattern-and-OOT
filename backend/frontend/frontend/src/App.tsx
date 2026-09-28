import { useEffect, useState } from 'react'

const REQUIRED_SECTIONS = [
  { id: 'sensors', name: 'Sensors', description: 'Monitor temperature, humidity, light, and soil moisture.' },
  { id: 'config', name: 'Configuration', description: 'Configure greenhouse thresholds and system rules.' },
  { id: 'automation', name: 'Automation', description: 'Set up automated watering and climate triggers.' },
  { id: 'overview', name: 'Overview', description: 'High-level telemetry and status dashboard.' },
  { id: 'controls', name: 'Controls', description: 'Manual overrides for fans, pumps, and lighting.' },
  { id: 'events', name: 'Events', description: 'System alerts and historical event logs.' },
]

export default function App() {
  const [apiStatus, setApiStatus] = useState<'checking' | 'ok' | 'error'>('checking')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => {
        if (data?.status === 'ok') setApiStatus('ok')
        else setApiStatus('error')
      })
      .catch(() => setApiStatus('error'))
  }, [])

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      {/* Header Bar */}
      <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">🌱</span>
          <h1 className="text-xl font-bold tracking-tight text-emerald-400">Smart Greenhouse</h1>
        </div>
        
        <div className="flex items-center space-x-6">
          <span className="text-sm text-slate-400 font-medium">Home Dashboard</span>
          <div className="flex items-center space-x-2 text-sm font-medium bg-slate-800 px-3 py-1 rounded-full border border-slate-700">
            <span>API:</span>
            {apiStatus === 'checking' && (
              <span className="flex items-center text-amber-400">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse mr-1.5" /> Checking...
              </span>
            )}
            {apiStatus === 'ok' && (
              <span className="flex items-center text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 mr-1.5" /> OK
              </span>
            )}
            {apiStatus === 'error' && (
              <span className="flex items-center text-rose-400">
                <span className="w-2 h-2 rounded-full bg-rose-400 mr-1.5" /> Offline
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main Hero & Dashboard Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-12 flex flex-col items-center">
        <div className="text-center max-w-2xl mb-12">
          <h2 className="text-4xl font-extrabold text-white tracking-tight sm:text-5xl mb-4">
            Smart Greenhouse
          </h2>
          <p className="text-lg text-slate-400">
            Monitor and control your greenhouse environment in real-time.
          </p>
        </div>

        {/* 6 Stable Section Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full">
          {REQUIRED_SECTIONS.map((section) => (
            <div
              key={section.id}
              id={section.id}
              className="bg-slate-800/60 border border-slate-700/60 hover:border-slate-600 rounded-xl p-6 flex flex-col justify-between transition shadow-lg"
            >
              <div>
                <h3 className="text-xl font-semibold text-slate-100 mb-2">
                  {section.name}
                </h3>
                <p className="text-sm text-slate-400">
                  {section.description}
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-700/40 flex items-center justify-between">
                <span className="inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded bg-slate-700/80 text-amber-300">
                  Coming soon
                </span>
                <span className="text-xs font-mono text-slate-500">#{section.id}</span>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
