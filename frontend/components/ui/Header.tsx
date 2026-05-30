"use client"

import Link from 'next/link'

export default function Header() {
  return (
    <header className="w-full border-b bg-black/10 backdrop-blur-md">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-6 py-4">
        <Link href="/" className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg flex items-center justify-center text-white font-semibold" style={{background: 'linear-gradient(135deg, var(--accent), var(--accent-600))'}}>A</div>
          <div>
            <div className="text-lg font-semibold">Arclat</div>
            <div className="text-xs text-[var(--muted)]">AI latency optimizer</div>
          </div>
        </Link>

        <nav className="hidden items-center gap-6 text-sm text-[var(--muted)] md:flex">
          <Link href="/dashboard" className="hover:text-[var(--text)]">Dashboard</Link>
          <Link href="/upload" className="hover:text-[var(--text)]">Upload</Link>
          <Link href="/share" className="hover:text-[var(--text)]">Reports</Link>
        </nav>

        <div className="flex items-center gap-3">
          <Link href="/auth/login" className="rounded-md border border-white/10 px-3 py-1 text-sm text-[var(--muted)] hover:text-[var(--text)]">Sign in</Link>
          <Link href="/auth/register" className="rounded-md px-3 py-1 text-sm font-semibold text-white" style={{background: 'linear-gradient(90deg, var(--accent), var(--accent-600))'}}>Get started</Link>
        </div>
      </div>
    </header>
  )
}
