export default function Dashboard() {
  return (
    <main className="mx-auto flex w-full max-w-7xl flex-1 px-6 py-6 sm:px-10 lg:px-12">
      <div className="w-full rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl sm:p-8">
        <div className="flex flex-col gap-4 border-b border-white/10 pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-accent">Dashboard</p>
            <h1 className="mt-3 font-heading text-3xl font-semibold text-white">Audited pipelines</h1>
            <p className="mt-2 text-sm text-textSecondary">A home for ranked reports and repeat audits.</p>
          </div>
          <div className="rounded-full border border-accent/20 bg-accent/10 px-4 py-2 text-sm font-semibold text-accent">
            3 reports ready
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          {[
            { title: 'Agent loop audit', meta: 'Updated 12m ago', score: '82 ms saved' },
            { title: 'RAG retrieval path', meta: 'Updated 1h ago', score: '64 ms saved' },
            { title: 'Tool orchestration', meta: 'Updated 3h ago', score: '128 ms saved' },
          ].map((report) => (
            <article key={report.title} className="rounded-[1.5rem] border border-white/10 bg-black/20 p-5">
              <p className="text-xs uppercase tracking-[0.25em] text-textSecondary">Report</p>
              <h2 className="mt-3 text-xl font-semibold text-white">{report.title}</h2>
              <p className="mt-2 text-sm text-textSecondary">{report.meta}</p>
              <div className="mt-6 flex items-center justify-between border-t border-white/10 pt-4">
                <span className="text-sm text-textSecondary">Projected gain</span>
                <span className="text-sm font-semibold text-accent">{report.score}</span>
              </div>
            </article>
          ))}
        </div>
      </div>
    </main>
  )
}
