import Link from 'next/link'

export default function Home() {
  return (
    <main className="relative flex-1 overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-24 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-accent/15 blur-3xl" />
        <div className="absolute right-[-8rem] top-32 h-96 w-96 rounded-full bg-white/5 blur-3xl" />
        <div className="absolute inset-0 opacity-[0.04] [background-image:linear-gradient(rgba(255,255,255,0.8)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.8)_1px,transparent_1px)] [background-size:56px_56px]" />
      </div>

      <div className="relative mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 py-6 sm:px-10 lg:px-12">
        <header className="flex items-center justify-between rounded-full border border-white/10 bg-white/5 px-5 py-3 shadow-2xl shadow-black/20 backdrop-blur-xl">
          <div>
            <p className="font-heading text-lg font-semibold tracking-tight">Arclat</p>
            <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">AI latency optimizer</p>
          </div>
          <div className="hidden items-center gap-6 text-sm text-textSecondary md:flex">
            <span>Audit logs</span>
            <span>Rank bottlenecks</span>
            <span>Ship fixes</span>
          </div>
          <Link href="/upload" className="rounded-full border border-accent/30 bg-accent px-4 py-2 text-sm font-semibold text-black transition-transform hover:-translate-y-0.5">
            Start audit
          </Link>
        </header>

        <section className="grid flex-1 items-center gap-14 py-12 lg:grid-cols-[1.1fr_0.9fr] lg:py-16">
          <div className="max-w-2xl">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-accent">
              <span className="h-2 w-2 rounded-full bg-accent" />
              Find latency you can actually remove
            </div>
            <h1 className="font-heading text-5xl font-semibold leading-[0.95] tracking-tight text-[var(--text)] sm:text-6xl lg:text-7xl">
              Your AI agent is slow.
              <span className="block text-accent">Here is where the time goes.</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-textSecondary sm:text-xl">
              Arclat audits your agent pipeline, ranks bottlenecks by impact, and gives concrete fixes instead of vague advice.
            </p>

            <div className="mt-8 flex flex-col gap-4 sm:flex-row">
              <Link href="/upload" className="inline-flex items-center justify-center rounded-full bg-accent px-6 py-3 text-base font-semibold text-black transition-transform hover:-translate-y-0.5">
                Audit your pipeline
              </Link>
              <Link href="/dashboard" className="inline-flex items-center justify-center rounded-full border border-white/15 bg-white/5 px-6 py-3 text-base font-semibold text-[var(--text)] backdrop-blur-sm transition-colors hover:bg-white/10">
                See sample report
              </Link>
            </div>

            <div className="mt-10 grid gap-4 sm:grid-cols-3">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm">
                <div className="text-2xl font-heading font-semibold text-[var(--text)]">1 file</div>
                <p className="mt-1 text-sm text-textSecondary">Upload logs or describe the pipeline.</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm">
                <div className="text-2xl font-heading font-semibold text-[var(--text)]">Ranked</div>
                <p className="mt-1 text-sm text-textSecondary">Time lost sorted by impact, not guesswork.</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm">
                <div className="text-2xl font-heading font-semibold text-[var(--text)]">Actionable</div>
                <p className="mt-1 text-sm text-textSecondary">Before/after changes you can ship quickly.</p>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-x-10 top-6 h-48 rounded-full bg-accent/15 blur-3xl" />
            <div className="relative rounded-[2rem] border border-white/10 bg-white/95 p-5 shadow-[0_40px_120px_rgba(15,23,42,0.12)] backdrop-blur-xl sm:p-6">
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div>
                  <p className="text-sm uppercase tracking-[0.25em] text-textSecondary">Latency map</p>
                  <p className="mt-1 text-xl font-semibold text-[var(--text)]">Pipeline audit snapshot</p>
                </div>
                <span className="rounded-full border border-accent/20 bg-accent/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-accent">
                  4 bottlenecks
                </span>
              </div>

              <div className="mt-5 space-y-4">
                {[
                  { label: 'Tool call serialization', value: '640 ms', percent: '92%' },
                  { label: 'DB round-trips', value: '310 ms', percent: '58%' },
                  { label: 'Cold start + prefetch', value: '180 ms', percent: '31%' },
                ].map((item) => (
                  <div key={item.label} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="flex items-center justify-between gap-4 text-sm">
                      <span className="font-medium text-[var(--text)]">{item.label}</span>
                      <span className="text-textSecondary">{item.value}</span>
                    </div>
                    <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
                      <div className="h-full rounded-full bg-gradient-to-r from-accent to-white/70" style={{ width: item.percent }} />
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-textSecondary">Recommendation</p>
                  <p className="mt-2 text-sm leading-6 text-[var(--text)]">Batch sequential tool calls and hoist repeated context fetches.</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-textSecondary">Expected gain</p>
                  <p className="mt-2 text-sm leading-6 text-[var(--text)]">Reduce response time by roughly 28% on this path.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-6 pb-10 lg:grid-cols-3">
          {[
            {
              title: 'Instant audit',
              description: 'Upload logs or describe your pipeline. No integration required to get a first pass.',
            },
            {
              title: 'Ranked bottlenecks',
              description: 'Every issue is sorted by time lost so the highest-value fix is obvious immediately.',
            },
            {
              title: 'Specific fixes',
              description: 'You get concrete changes, not generic performance slogans or vague tuning advice.',
            },
          ].map((feature) => (
            <article key={feature.title} className="rounded-[1.75rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl transition-transform hover:-translate-y-1">
              <div className="mb-5 h-11 w-11 rounded-2xl border border-accent/20 bg-accent/10" />
              <h2 className="font-heading text-xl font-semibold text-[var(--text)]">{feature.title}</h2>
              <p className="mt-3 text-sm leading-7 text-textSecondary">{feature.description}</p>
            </article>
          ))}
        </section>

        <footer className="pb-4 text-sm text-textSecondary">
          Built by Arclat · arclat.com
        </footer>
      </div>
    </main>
  )
}
