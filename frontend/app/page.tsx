import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex-1 flex flex-col items-center justify-center p-8 text-center sm:p-20">
      <h1 className="text-5xl font-heading font-bold mb-6">
        Your AI agent is slow. <span className="text-accent">Here's why.</span>
      </h1>
      <p className="text-xl text-textSecondary mb-10 max-w-2xl">
        Arclat audits your agent pipeline and tells you exactly where you're losing time — with ranked bottlenecks and specific fixes.
      </p>
      
      <Link href="/upload" className="bg-accent text-black font-bold py-3 px-8 rounded hover:opacity-90 transition-opacity text-lg">
        Audit your pipeline free
      </Link>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-20 max-w-5xl text-left">
        <div className="bg-surface p-6 rounded-lg border border-border">
          <h3 className="text-accent font-bold text-xl mb-3">Instant audit</h3>
          <p className="text-textSecondary">Upload logs or describe your pipeline. No integration required.</p>
        </div>
        <div className="bg-surface p-6 rounded-lg border border-border">
          <h3 className="text-accent font-bold text-xl mb-3">Ranked bottlenecks</h3>
          <p className="text-textSecondary">Sorted by time lost, highest impact first. Don't waste time on trivial fixes.</p>
        </div>
        <div className="bg-surface p-6 rounded-lg border border-border">
          <h3 className="text-accent font-bold text-xl mb-3">Specific fixes</h3>
          <p className="text-textSecondary">Before/after code examples, not generic advice.</p>
        </div>
      </div>
      
      <footer className="mt-auto pt-20 pb-4 text-textSecondary text-sm">
        Built by Arclat &middot; arclat.com
      </footer>
    </main>
  )
}
