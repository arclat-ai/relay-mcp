'use client'
import { useState } from 'react'
import LogUploader from '../../components/upload/LogUploader'
import { Loader2, AlertCircle } from 'lucide-react'

export default function UploadPage() {
  const [tab, setTab] = useState<'logs' | 'text'>('logs')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<any>(null)
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  async function submitDescription() {
    if (!description.trim()) return
    setLoading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('input_type', 'description')
      form.append('input_raw', description)
      const res = await fetch(`${apiBase}/audits/quick`, { method: 'POST', body: form })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Audit failed')
      setResult(data)
    } catch (err: any) {
      setError(err.message ?? 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-1 px-6 py-6 sm:px-10 lg:px-12">
      <div className="grid w-full gap-8 lg:grid-cols-[0.88fr_1.12fr]">
        <aside className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl lg:p-8">
          <p className="text-xs uppercase tracking-[0.3em] text-accent">Submit pipeline</p>
          <h1 className="mt-4 font-heading text-3xl font-semibold text-white sm:text-4xl">Turn logs into a ranked latency report.</h1>
          <p className="mt-4 max-w-md text-sm leading-7 text-textSecondary">
            Upload JSON logs or describe the pipeline in plain language. Arclat will map slow steps, identify repeated work, and show the next fix.
          </p>

          <div className="mt-8 space-y-4">
            {[
              'Chronological execution analysis',
              'Bottlenecks ranked by time lost',
              'Concrete before/after recommendations',
            ].map((item) => (
              <div key={item} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white">
                <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-accent" />
                {item}
              </div>
            ))}
          </div>

          <div className="mt-8 rounded-2xl border border-white/10 bg-black/20 p-4">
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-textSecondary">Expected JSON shape</p>
            <pre className="overflow-x-auto text-[11px] leading-6 text-textSecondary">{`{
  "spans": [
    {
      "id": "span-1",
      "name": "tool_call",
      "span_type": "tool",
      "start_ms": 0,
      "end_ms": 640,
      "metadata": {}
    }
  ]
}`}</pre>
          </div>
        </aside>

        <section className="rounded-[2rem] border border-white/10 bg-[#0d1014]/90 p-4 shadow-[0_40px_120px_rgba(0,0,0,0.35)] backdrop-blur-xl sm:p-6 lg:p-8">
          <div className="flex flex-wrap gap-3 rounded-full border border-white/10 bg-black/20 p-1">
            <button
              className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${tab === 'logs' ? 'bg-accent text-[#06111a]' : 'text-textSecondary hover:text-white'}`}
              onClick={() => { setTab('logs'); setResult(null); setError('') }}
            >
              Upload logs (JSON)
            </button>
            <button
              className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${tab === 'text' ? 'bg-accent text-[#06111a]' : 'text-textSecondary hover:text-white'}`}
              onClick={() => { setTab('text'); setResult(null); setError('') }}
            >
              Describe your pipeline
            </button>
          </div>

          <div className="mt-6 rounded-[1.75rem] border border-white/10 bg-black/25 p-5 sm:p-6">
            {tab === 'logs' ? (
              <LogUploader />
            ) : result ? (
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                    <p className="text-xs uppercase tracking-[0.25em] text-textSecondary">Bottlenecks</p>
                    <p className="mt-2 font-heading text-2xl font-semibold text-white">{result.summary.total_bottlenecks}</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                    <p className="text-xs uppercase tracking-[0.25em] text-textSecondary">Est. improvement</p>
                    <p className="mt-2 font-heading text-2xl font-semibold text-accent">{result.summary.estimated_improvement_pct}%</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                    <p className="text-xs uppercase tracking-[0.25em] text-textSecondary">Top issue</p>
                    <p className="mt-2 text-sm font-semibold text-white leading-snug">{result.summary.top_issue}</p>
                  </div>
                </div>
                <p className="text-xs text-textSecondary">Description-based audits are limited — upload JSON logs for ranked bottlenecks with code diffs.</p>
                <button
                  onClick={() => { setResult(null); setDescription('') }}
                  className="rounded-full border border-white/10 px-5 py-2.5 text-sm text-textSecondary hover:bg-white/5 hover:text-white transition-colors"
                >
                  Try again
                </button>
              </div>
            ) : (
              <div>
                <label className="mb-3 block text-sm font-medium text-white">Pipeline summary</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="h-56 w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-textPrimary outline-none transition-colors placeholder:text-textSecondary focus:border-accent"
                  placeholder="Describe your pipeline steps sequentially. Example: I initialize a langchain loop taking 600ms, then I make a sync query to the DB..."
                />
                {error && (
                  <div className="mt-3 flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-xs text-red-400">
                    <AlertCircle size={14} className="shrink-0" />
                    {error}
                  </div>
                )}
                <div className="mt-4 flex items-center justify-between gap-4">
                  <p className="text-xs text-textSecondary">The clearer the sequence, the better the bottleneck ranking.</p>
                  <button
                    onClick={submitDescription}
                    disabled={loading || !description.trim()}
                    className="flex items-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-semibold text-[#06111a] transition-transform hover:-translate-y-0.5 disabled:opacity-60 disabled:translate-y-0"
                  >
                    {loading && <Loader2 size={14} className="animate-spin" />}
                    {loading ? 'Auditing…' : 'Submit description'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  )
}
