import Link from 'next/link'
import { Zap, Code2, Terminal } from 'lucide-react'

const featureIcons = [Terminal, Code2, Zap]

const MCP_SNIPPET = `{
  "mcpServers": {
    "arclat": {
      "command": "uvx",
      "args": ["arclat-mcp"],
      "env": {
        "ARCLAT_API_KEY": "your_api_key_here"
      }
    }
  }
}`

export default function Home() {
  return (
    <main>
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-16 px-6 py-14 sm:px-10 lg:px-12 lg:py-20">

        {/* Hero */}
        <section className="grid items-start gap-12 lg:grid-cols-[1fr_0.9fr] lg:gap-16">
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-1.5 text-xs font-medium uppercase tracking-widest text-[var(--muted)]">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
              MCP · Claude Code
            </div>

            <h1 className="mt-7 text-5xl font-semibold leading-[1.05] tracking-tight text-[var(--text)] sm:text-6xl">
              Arclat audits your agent codebase for latency issues —
              <br />
              <span className="text-[var(--accent)]">from inside Claude Code.</span>
            </h1>

            <p className="mt-5 text-base leading-7 text-[var(--muted)]">
              No log files. No context switching. Arclat reads your actual code, ranks bottlenecks by impact, and applies fixes — all from a single Claude Code conversation.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/auth/register"
                className="inline-flex items-center justify-center rounded-lg bg-[var(--accent)] px-5 py-2.5 text-sm font-semibold text-[#06111a] hover:opacity-90"
              >
                Install free
              </Link>
              <Link
                href="/dashboard"
                className="inline-flex items-center justify-center rounded-lg border border-white/10 px-5 py-2.5 text-sm font-semibold text-[var(--text)] hover:bg-white/5"
              >
                View dashboard
              </Link>
            </div>

            <div className="mt-10 grid gap-3 sm:grid-cols-3">
              {[
                { value: '1 line', label: "Add to Claude Code config and you're running." },
                { value: 'Ranked', label: 'Bottlenecks sorted by time lost, not guesswork.' },
                { value: 'Auto-fix', label: 'Apply patches directly from Claude Code.' },
              ].map((item) => (
                <div key={item.value} className="rounded-lg border border-white/10 bg-white/5 p-4">
                  <div className="text-xl font-semibold text-[var(--text)]">{item.value}</div>
                  <p className="mt-1 text-xs text-[var(--muted)]">{item.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Install snippet card */}
          <div className="rounded-xl border border-white/10 bg-[var(--card)] p-5">
            <div className="flex items-start justify-between gap-4 border-b border-white/10 pb-4">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-[var(--muted)]">One-line install</p>
                <p className="mt-1.5 text-lg font-semibold text-[var(--text)]">Add to Claude Code config</p>
              </div>
              <span className="rounded-full border border-white/10 px-2.5 py-1 text-[10px] font-medium uppercase tracking-widest text-[var(--muted)]">
                ~/.claude/config
              </span>
            </div>

            <pre className="mt-4 overflow-x-auto rounded-lg border border-white/10 bg-black/30 p-4 text-xs leading-6 text-[var(--text)]">
              <code>{MCP_SNIPPET}</code>
            </pre>

            <div className="mt-4 rounded-lg border border-white/10 bg-[var(--accent)]/5 p-3.5">
              <p className="text-sm text-[var(--muted)]">Then say in Claude Code:</p>
              <p className="mt-1 text-sm font-medium text-[var(--text)]">&ldquo;Audit this codebase for latency issues&rdquo;</p>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg border border-white/10 p-3.5">
                <p className="text-[10px] uppercase tracking-widest text-[var(--muted)]">Free tier</p>
                <p className="mt-1.5 text-sm leading-6 text-[var(--text)]">20 audits/month. Findings included. No credit card.</p>
              </div>
              <div className="rounded-lg border border-white/10 p-3.5">
                <p className="text-[10px] uppercase tracking-widest text-[var(--muted)]">Pro — $19/mo</p>
                <p className="mt-1.5 text-sm leading-6 text-[var(--text)]">Unlimited audits + apply_fix tool + CI/CD GitHub Action.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="grid gap-4 lg:grid-cols-3">
          {[
            { title: 'Works inside Claude Code', description: 'No browser tab, no upload flow. Arclat lives in your existing workflow as an MCP server.' },
            { title: 'Reads your actual code', description: 'AST-based analysis on your .py files. Not logs, not guesses — the real source of truth.' },
            { title: 'One-line install', description: "Add the MCP config snippet, get your API key, and you're auditing in under 60 seconds." },
          ].map((feature, i) => {
            const Icon = featureIcons[i]
            return (
              <article key={feature.title} className="rounded-xl border border-white/10 p-5 hover:bg-white/5 transition-colors">
                <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg border border-white/10">
                  <Icon size={16} className="text-[var(--accent)]" />
                </div>
                <h2 className="text-base font-semibold text-[var(--text)]">{feature.title}</h2>
                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{feature.description}</p>
              </article>
            )
          })}
        </section>

        {/* Pricing */}
        <section className="grid gap-4 rounded-xl border border-white/10 p-6 sm:grid-cols-4">
          {[
            ['Free', '$0', '20 audits/month'],
            ['Pro', '$19/mo', 'Unlimited + apply_fix'],
            ['Team', '$49/mo', '5 seats + GitHub Action'],
            ['Enterprise', '$200+/mo', 'Custom + Slack + support'],
          ].map(([tier, price, desc]) => (
            <div key={tier} className="border-r border-white/10 last:border-r-0 pr-6 last:pr-0">
              <p className="text-xs uppercase tracking-widest text-[var(--muted)]">{tier}</p>
              <p className="mt-1.5 text-2xl font-semibold tracking-tight text-[var(--text)]">{price}</p>
              <p className="mt-1 text-xs text-[var(--muted)]">{desc}</p>
            </div>
          ))}
        </section>

      </div>
    </main>
  )
}
