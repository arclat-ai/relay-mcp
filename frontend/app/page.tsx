import Link from 'next/link'

export default function Home() {
  return (
    <main className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-[-10rem] h-[28rem] w-[28rem] -translate-x-1/2 rounded-full bg-accent/15 blur-3xl" />
        <div className="absolute right-[-10rem] top-32 h-[24rem] w-[24rem] rounded-full bg-white/6 blur-3xl" />
        <div className="absolute inset-0 opacity-[0.05] [background-image:linear-gradient(rgba(255,255,255,0.7)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.7)_1px,transparent_1px)] [background-size:64px_64px]" />
      </div>

      <div className="relative mx-auto flex w-full max-w-7xl flex-col gap-12 px-6 py-10 sm:px-10 lg:px-12 lg:py-14">
        <section className="grid items-center gap-12 pt-4 lg:grid-cols-[1.08fr_0.92fr] lg:gap-14 lg:pt-10">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-accent">
              <span className="h-2 w-2 rounded-full bg-accent" />
              Find latency you can actually remove
            </div>
            <h1 className="mt-6 font-heading text-5xl font-semibold leading-[0.94] tracking-tight text-[var(--text)] sm:text-6xl lg:text-7xl">
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
              <div className="rounded-3xl border border-white/10 bg-white/5 p-4 backdrop-blur-xl">
                <div className="text-2xl font-heading font-semibold text-[var(--text)]">1 file</div>
                <p className="mt-1 text-sm text-textSecondary">Upload logs or describe the pipeline.</p>
              </div>
              <div className="rounded-3xl border border-white/10 bg-white/5 p-4 backdrop-blur-xl">
                <div className="text-2xl font-heading font-semibold text-[var(--text)]">Ranked</div>
                <p className="mt-1 text-sm text-textSecondary">Time lost sorted by impact, not guesswork.</p>
              </div>
              <div className="rounded-3xl border border-white/10 bg-white/5 p-4 backdrop-blur-xl">
                <div className="text-2xl font-heading font-semibold text-[var(--text)]">Actionable</div>
                <p className="mt-1 text-sm text-textSecondary">Before/after changes you can ship quickly.</p>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-x-8 top-8 h-44 rounded-full bg-accent/15 blur-3xl" />
            <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[#0e1116]/92 p-5 shadow-[0_40px_120px_rgba(0,0,0,0.45)] backdrop-blur-xl sm:p-6">
              <div className="flex items-start justify-between gap-4 border-b border-white/10 pb-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">Latency map</p>
                  <p className="mt-2 text-2xl font-semibold text-[var(--text)]">Pipeline audit snapshot</p>
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
                      <div className="h-full rounded-full bg-gradient-to-r from-accent via-accent to-white/70" style={{ width: item.percent }} />
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

              <div className="mt-5 rounded-2xl border border-accent/15 bg-accent/8 p-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.25em] text-textSecondary">Projected lift</p>
                    <p className="mt-1 text-base font-semibold text-[var(--text)]">Most time is lost before the model even responds.</p>
                  </div>
                  <div className="rounded-full border border-accent/20 bg-accent/10 px-3 py-1 text-sm font-semibold text-accent">
                    -28%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
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
            <article key={feature.title} className="group rounded-[1.75rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl transition-transform hover:-translate-y-1">
              <div className="mb-5 h-11 w-11 rounded-2xl border border-accent/20 bg-gradient-to-br from-accent/20 to-white/5" />
              <h2 className="font-heading text-xl font-semibold text-[var(--text)]">{feature.title}</h2>
              <p className="mt-3 text-sm leading-7 text-textSecondary">{feature.description}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-4 rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl sm:grid-cols-3 sm:p-8">
          {[
            ['32%', 'average latency removed'],
            ['4 signals', 'tracked across each audit'],
            ['1-click', 'shareable report output'],
          ].map(([value, label]) => (
            <div key={label} className="rounded-2xl border border-white/10 bg-black/20 p-5">
              <p className="font-heading text-3xl font-semibold text-[var(--text)]">{value}</p>
              <p className="mt-2 text-sm text-textSecondary">{label}</p>
            </div>
          ))}
        </section>
      </div>
    </main>
  )
}
