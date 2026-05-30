"use client"

import Link from 'next/link'

export default function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-black/30 backdrop-blur-2xl">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-6 py-4 sm:px-10 lg:px-12">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 text-sm font-semibold text-black shadow-[0_10px_30px_rgba(70,245,165,0.24)]" style={{background: 'linear-gradient(135deg, var(--accent), var(--accent-600))'}}>A</div>
          <div>
            <div className="font-heading text-lg font-semibold tracking-tight">Arclat</div>
            <div className="text-xs uppercase tracking-[0.28em] text-[var(--muted)]">AI latency optimizer</div>
          </div>
        </Link>

        <nav className="hidden items-center gap-2 text-sm text-[var(--muted)] md:flex">
          <Link href="/dashboard" className="rounded-full px-4 py-2 hover:bg-white/5 hover:text-[var(--text)]">Dashboard</Link>
          <Link href="/upload" className="rounded-full px-4 py-2 hover:bg-white/5 hover:text-[var(--text)]">Upload</Link>
          <Link href="/share" className="rounded-full px-4 py-2 hover:bg-white/5 hover:text-[var(--text)]">Reports</Link>
        </nav>

        <div className="flex items-center gap-3">
          <Link href="/auth/login" className="rounded-full border border-white/10 px-4 py-2 text-sm text-[var(--muted)] hover:bg-white/5 hover:text-[var(--text)]">Sign in</Link>
          <Link href="/auth/register" className="rounded-full px-4 py-2 text-sm font-semibold text-black shadow-[0_10px_30px_rgba(70,245,165,0.18)]" style={{background: 'linear-gradient(90deg, var(--accent), var(--accent-600))'}}>Get started</Link>
        </div>
      </div>
    </header>
  )
}
