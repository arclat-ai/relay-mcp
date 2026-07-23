"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

interface UserProfile {
  email: string
  name: string | null
  company: string | null
  plan: string
  api_key: string
  created_at: string
  usage: {
    count: number
    limit: number | null
    month: string
    last_audit_at: string | null
  }
}

export default function Dashboard() {
  const router = useRouter()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) { router.push('/auth/login'); return }

    fetch(`${apiBase}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (r.status === 401) { router.push('/auth/login'); return null }
        return r.json()
      })
      .then((data) => { if (data) setProfile(data) })
      .catch(() => setError('Failed to load profile.'))
  }, [apiBase, router])

  function copyKey() {
    if (!profile) return
    navigator.clipboard.writeText(profile.api_key)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function logout() {
    localStorage.removeItem('token')
    document.cookie = 'sb-access-token=; max-age=0; path=/'
    router.push('/auth/login')
  }

  if (error) return (
    <main className="flex min-h-screen items-center justify-center">
      <p className="text-red-400">{error}</p>
    </main>
  )

  if (!profile) return (
    <main className="flex min-h-screen items-center justify-center">
      <p className="text-textSecondary text-sm">Loading…</p>
    </main>
  )

  const usagePercent = profile.usage.limit
    ? Math.min(100, Math.round((profile.usage.count / profile.usage.limit) * 100))
    : null

  return (
    <main className="mx-auto w-full max-w-4xl px-6 py-10 sm:px-10">

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-accent">Dashboard</p>
          <h1 className="mt-2 font-heading text-3xl font-semibold text-white">
            {profile.name ?? profile.email}
          </h1>
          <p className="mt-1 text-sm text-textSecondary capitalize">{profile.plan} plan</p>
        </div>
        <button
          onClick={logout}
          className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs text-textSecondary hover:text-white transition"
        >
          Log out
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">

        {/* API Key */}
        <section className="rounded-[1.75rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl sm:col-span-2">
          <p className="text-xs uppercase tracking-[0.3em] text-accent mb-3">Your API Key</p>
          <div className="flex items-center gap-3">
            <code className="flex-1 rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white font-mono break-all">
              {profile.api_key}
            </code>
            <button
              onClick={copyKey}
              className="shrink-0 rounded-xl border border-accent/20 bg-accent/10 px-4 py-3 text-sm font-semibold text-accent hover:bg-accent/20 transition"
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </section>

        {/* Usage */}
        <section className="rounded-[1.75rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
          <p className="text-xs uppercase tracking-[0.3em] text-accent mb-3">Usage - {profile.usage.month}</p>
          <p className="text-4xl font-semibold text-white">
            {profile.usage.count}
            {profile.usage.limit && (
              <span className="text-xl text-textSecondary"> / {profile.usage.limit}</span>
            )}
          </p>
          <p className="mt-1 text-sm text-textSecondary">audits this month</p>
          {usagePercent !== null && (
            <div className="mt-4 h-1.5 w-full rounded-full bg-white/10">
              <div
                className="h-1.5 rounded-full bg-accent transition-all"
                style={{ width: `${usagePercent}%` }}
              />
            </div>
          )}
        </section>

        {/* Getting started */}
        <section className="rounded-[1.75rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl sm:col-span-2">
          <p className="text-xs uppercase tracking-[0.3em] text-accent mb-4">How to use your API key</p>
          <ol className="space-y-5 text-sm text-textSecondary">
            <li>
              <span className="text-white font-semibold">1. Add Arclat to Claude Code</span>
              <p className="mt-1">Open <code className="text-accent">~/.claude/claude_code_config.json</code> and add:</p>
              <pre className="mt-2 rounded-xl border border-white/10 bg-black/40 p-4 text-xs text-white overflow-x-auto">{`{
  "mcpServers": {
    "arclat": {
      "command": "uvx",
      "args": ["arclat-mcp"],
      "env": {
        "ARCLAT_API_KEY": "${profile.api_key}"
      }
    }
  }
}`}</pre>
            </li>
            <li>
              <span className="text-white font-semibold">2. Open any AI agent project in Claude Code</span>
              <p className="mt-1">Works with any Python codebase using LangChain, LlamaIndex, CrewAI, OpenAI, or Anthropic SDKs.</p>
            </li>
            <li>
              <span className="text-white font-semibold">3. Ask Claude to audit it</span>
              <p className="mt-1">Type in Claude Code:</p>
              <pre className="mt-2 rounded-xl border border-white/10 bg-black/40 p-4 text-xs text-white">{`Audit this codebase for latency issues`}</pre>
              <p className="mt-2">Claude will call the Arclat MCP tool, read your code, and return ranked bottlenecks with fix recommendations.</p>
            </li>
          </ol>
          <p className="mt-5 text-xs text-textSecondary">Free plan: 20 audits/month &nbsp;·&nbsp; <a href="mailto:abdur@lythe.ai" className="text-accent hover:underline">Contact us to upgrade</a></p>
        </section>

      </div>
    </main>
  )
}
