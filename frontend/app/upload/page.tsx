'use client'
import { useState } from 'react'
import LogUploader from '../../components/upload/LogUploader'

export default function UploadPage() {
  const [tab, setTab] = useState<'logs' | 'text'>('logs')

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
                <span className="h-2.5 w-2.5 rounded-full bg-accent" />
                {item}
              </div>
            ))}
          </div>
        </aside>

        <section className="rounded-[2rem] border border-white/10 bg-[#0d1014]/90 p-4 shadow-[0_40px_120px_rgba(0,0,0,0.35)] backdrop-blur-xl sm:p-6 lg:p-8">
          <div className="flex flex-wrap gap-3 rounded-full border border-white/10 bg-black/20 p-1">
            <button
              className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${tab === 'logs' ? 'bg-accent text-black' : 'text-textSecondary hover:text-white'}`}
              onClick={() => setTab('logs')}
            >
              Upload logs (JSON)
            </button>
            <button
              className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${tab === 'text' ? 'bg-accent text-black' : 'text-textSecondary hover:text-white'}`}
              onClick={() => setTab('text')}
            >
              Describe your pipeline
            </button>
          </div>

          <div className="mt-6 rounded-[1.75rem] border border-white/10 bg-black/25 p-5 sm:p-6">
            {tab === 'logs' ? (
              <LogUploader />
            ) : (
              <div>
                <label className="mb-3 block text-sm font-medium text-white">Pipeline summary</label>
                <textarea
                  className="h-56 w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-textPrimary outline-none transition-colors placeholder:text-textSecondary focus:border-accent"
                  placeholder="Describe your pipeline steps sequentially. Example: I initialize a langchain loop taking 600ms, then I make a sync query to the DB..."
                />
                <div className="mt-4 flex items-center justify-between gap-4">
                  <p className="text-xs text-textSecondary">The clearer the sequence, the better the bottleneck ranking.</p>
                  <button className="rounded-full bg-accent px-5 py-3 text-sm font-semibold text-black transition-transform hover:-translate-y-0.5">
                    Submit description
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
