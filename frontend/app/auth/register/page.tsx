"use client"

import { useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function RegisterPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  function setAuthCookie(token: string) {
    document.cookie = `sb-access-token=${encodeURIComponent(token)}; path=/; max-age=86400; samesite=lax`
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await fetch(`${apiBase}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.detail ?? 'Registration failed. Please try again.')
        return
      }
      localStorage.setItem('token', data.token)
      setAuthCookie(data.token)
      router.push('/dashboard')
    } catch {
      setError('Unable to reach the server. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl items-center px-6 py-10 sm:px-10 lg:px-12">
      <div className="grid w-full gap-6 lg:grid-cols-[0.95fr_1.05fr]">

        {/* Brand panel */}
        <aside className="relative overflow-hidden rounded-[2.25rem] border border-white/10 bg-white/5 p-8 shadow-[0_40px_120px_rgba(0,0,0,0.35)] backdrop-blur-xl sm:p-10 lg:p-12">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(125,214,245,0.14),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(255,255,255,0.06),transparent_28%)]" />
          <div className="relative">
            <p className="text-xs uppercase tracking-[0.3em] text-accent">Create account</p>
            <h2 className="mt-3 font-heading text-4xl font-semibold text-white">Register</h2>
            <p className="mt-4 max-w-lg text-sm leading-7 text-textSecondary">
              Set up your workspace to get audited reports, saved histories, and a cleaner path from log upload to optimization.
            </p>
            <div className="mt-10 space-y-4">
              {['Saved pipeline reports', 'Shareable audit links', 'Repeatable performance checks'].map((item) => (
                <div key={item} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-4 text-sm text-white">
                  <span className="h-2 w-2 shrink-0 rounded-full bg-accent" />
                  {item}
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* Form panel */}
        <section className="rounded-[2.25rem] border border-white/10 bg-[#0d1014]/90 p-8 shadow-[0_40px_120px_rgba(0,0,0,0.35)] backdrop-blur-xl sm:p-10">
          <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">Sign up</p>

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
                autoComplete="new-password"
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
              className="mt-2 w-full rounded-2xl bg-accent py-3 text-sm font-semibold text-[#06111a] transition hover:bg-[var(--accent-600)] disabled:opacity-50"
            >
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-textSecondary">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-accent hover:underline">
              Sign in
            </Link>
          </p>
        </section>
      </div>
    </main>
  )
}
