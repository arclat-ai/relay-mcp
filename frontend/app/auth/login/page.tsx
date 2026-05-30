"use client"

import { useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await fetch(`${apiBase}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.detail ?? 'Login failed. Check your credentials.')
        return
      }
      localStorage.setItem('token', data.token)
      router.push('/dashboard')
    } catch {
      setError('Unable to reach the server. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl items-center px-6 py-10 sm:px-10 lg:px-12">
      <div className="grid w-full gap-6 lg:grid-cols-[1.05fr_0.95fr]">

        {/* Brand panel */}
        <section className="relative overflow-hidden rounded-[2.25rem] border border-white/10 bg-white/5 p-8 shadow-[0_40px_120px_rgba(0,0,0,0.35)] backdrop-blur-xl sm:p-10 lg:p-12">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(0,255,136,0.18),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(255,255,255,0.06),transparent_28%)]" />
          <div className="relative">
            <p className="text-xs uppercase tracking-[0.3em] text-accent">Welcome back</p>
            <h2 className="mt-3 font-heading text-4xl font-semibold text-white">Login</h2>
            <p className="mt-4 max-w-lg text-sm leading-7 text-textSecondary">
              Upload logs, rank bottlenecks by impact, and ship concrete fixes — all from one place.
            </p>
            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              {['Ranked bottlenecks', 'Concrete fixes', 'Fast pipeline audits'].map((item) => (
                <div key={item} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-5 text-sm text-white">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Form panel */}
        <aside className="rounded-[2.25rem] border border-white/10 bg-[#0d1014]/90 p-8 shadow-[0_40px_120px_rgba(0,0,0,0.35)] backdrop-blur-xl sm:p-10">
          <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">Sign in</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-xs uppercase tracking-widest text-textSecondary">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-[#444] outline-none transition focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]/30"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="password" className="block text-xs uppercase tracking-widest text-textSecondary">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-[#444] outline-none transition focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]/30"
              />
            </div>

            {error && (
              <p className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-xs text-red-400">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="mt-2 w-full rounded-2xl bg-accent py-3 text-sm font-semibold text-black transition hover:bg-[var(--accent-600)] disabled:opacity-50"
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-textSecondary">
            No account?{' '}
            <Link href="/auth/register" className="text-accent hover:underline">
              Create one
            </Link>
          </p>
        </aside>
      </div>
    </main>
  )
}
