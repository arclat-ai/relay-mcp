'use client'
import { useState, useRef } from 'react'
import { Upload, FileCheck, AlertCircle, Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'

type AuditResult = {
  bottlenecks: {
    type: string
    severity: string
    title: string
    description: string
    time_lost_ms: number
    location: string
    rank: number
    code_before: string
    code_after: string
    effort: string
    impact: string
  }[]
  summary: {
    total_bottlenecks: number
    estimated_improvement_pct: number
    top_issue: string
  }
}

export default function LogUploader() {
  const [dragActive, setDragActive] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<AuditResult | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) pickFile(dropped)
  }

  function pickFile(f: File) {
    setError('')
    setResult(null)
    setFile(f)
  }

  async function handleAudit() {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('input_type', 'logs')
      form.append('file', file)
      const res = await fetch(`${apiBase}/audits/quick`, { method: 'POST', body: form })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Audit failed')
      setResult(data)
    } catch (err: any) {
      setError(err.message ?? 'Something went wrong. Try again.')
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return <AuditResults result={result} onReset={() => { setResult(null); setFile(null) }} />
  }

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept=".json,application/json"
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) pickFile(f) }}
      />

      <div
        className={`cursor-pointer rounded-[1.75rem] border-2 border-dashed p-10 text-center transition-colors sm:p-12 ${dragActive ? 'border-accent bg-accent/10' : 'border-white/10 bg-white/5 hover:border-accent/40 hover:bg-white/[0.07]'}`}
        onClick={() => inputRef.current?.click()}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {!file ? (
          <>
            <div className="mb-5 flex justify-center text-accent/80">
              <Upload size={48} strokeWidth={1.5} />
            </div>
            <p className="mb-2 text-lg font-semibold text-white">Click to select a file, or drag and drop</p>
            <p className="text-sm text-textSecondary">JSON format, max 10 MB</p>
          </>
        ) : (
          <div onClick={(e) => e.stopPropagation()}>
            <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/15 text-accent">
              <FileCheck size={28} />
            </div>
            <p className="mb-1 font-semibold text-white">{file.name}</p>
            <p className="mb-6 text-sm text-textSecondary">{(file.size / 1024 / 1024).toFixed(2)} MB</p>

            {error && (
              <div className="mb-4 flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-xs text-red-400">
                <AlertCircle size={14} className="shrink-0" />
                {error}
              </div>
            )}

            <div className="flex justify-center gap-3">
              <button
                onClick={() => { setFile(null); setError('') }}
                className="rounded-full border border-white/10 px-5 py-2.5 text-sm text-textSecondary hover:bg-white/5 hover:text-white transition-colors"
              >
                Change file
              </button>
              <button
                onClick={handleAudit}
                disabled={loading}
                className="flex items-center gap-2 rounded-full bg-accent px-8 py-2.5 text-sm font-semibold text-[#06111a] transition-transform hover:-translate-y-0.5 disabled:opacity-60 disabled:translate-y-0"
              >
                {loading && <Loader2 size={14} className="animate-spin" />}
                {loading ? 'Auditing…' : 'Audit logs'}
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

function AuditResults({ result, onReset }: { result: AuditResult; onReset: () => void }) {
  const severityColor: Record<string, string> = {
    high: 'text-red-400 border-red-500/20 bg-red-500/10',
    medium: 'text-yellow-400 border-yellow-500/20 bg-yellow-500/10',
    low: 'text-accent border-accent/20 bg-accent/10',
  }

  return (
    <div className="space-y-6">
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

      {result.bottlenecks.length === 0 ? (
        <div className="rounded-2xl border border-white/10 bg-white/5 px-6 py-10 text-center text-sm text-textSecondary">
          No bottlenecks detected. Your logs look clean, or the format may not be supported yet.
        </div>
      ) : (
        <div className="space-y-4">
          {result.bottlenecks.map((b) => (
            <div key={b.rank} className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-black/30 text-sm font-bold text-[var(--muted)]">
                    #{b.rank}
                  </span>
                  <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${severityColor[b.severity?.toLowerCase()] ?? severityColor.low}`}>
                    {b.severity}
                  </span>
                </div>
                <span className="text-sm font-bold text-red-400">+{b.time_lost_ms} ms</span>
              </div>
              <h3 className="mt-3 text-base font-semibold text-white">{b.title}</h3>
              <p className="mt-1 text-sm leading-6 text-textSecondary">{b.description}</p>
              {b.location && (
                <p className="mt-2 font-mono text-xs text-textSecondary">
                  <span className="opacity-60">loc:</span> {b.location}
                </p>
              )}
              <div className="mt-3 flex gap-4 text-xs text-textSecondary">
                <span>Effort: <span className="text-white font-medium">{b.effort}</span></span>
                <span>Impact: <span className="text-accent font-medium">{b.impact}</span></span>
              </div>
              {(b.code_before || b.code_after) && (
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {b.code_before && (
                    <div>
                      <p className="mb-1 text-[10px] uppercase tracking-widest text-red-400/70">Before</p>
                      <pre className="overflow-x-auto rounded-xl border border-white/10 bg-black/40 p-3 text-xs text-textSecondary">{b.code_before}</pre>
                    </div>
                  )}
                  {b.code_after && (
                    <div>
                      <p className="mb-1 text-[10px] uppercase tracking-widest text-accent/70">After</p>
                      <pre className="overflow-x-auto rounded-xl border border-white/10 bg-black/40 p-3 text-xs text-textSecondary">{b.code_after}</pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <button
        onClick={onReset}
        className="rounded-full border border-white/10 px-5 py-2.5 text-sm text-textSecondary hover:bg-white/5 hover:text-white transition-colors"
      >
        Audit another file
      </button>
    </div>
  )
}
