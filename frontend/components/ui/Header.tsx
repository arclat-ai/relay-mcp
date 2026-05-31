"use client"

import Link from 'next/link'
import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { LayoutDashboard, Upload, FileText, UserCircle, LogOut, ChevronDown, Sun, Moon } from 'lucide-react'

export default function Header() {
  const [authed, setAuthed] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  const menuRef = useRef<HTMLDivElement>(null)
  const router = useRouter()

  useEffect(() => {
    setAuthed(!!localStorage.getItem('token'))
    const stored = localStorage.getItem('theme') as 'dark' | 'light' | null
    if (stored) {
      setTheme(stored)
      document.documentElement.setAttribute('data-theme', stored)
    }
  }, [])

  function toggleTheme() {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    localStorage.setItem('theme', next)
    if (next === 'light') {
      document.documentElement.setAttribute('data-theme', 'light')
    } else {
      document.documentElement.removeAttribute('data-theme')
    }
  }

  useEffect(() => {
    function handleOutsideClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleOutsideClick)
    return () => document.removeEventListener('mousedown', handleOutsideClick)
  }, [])

  function signOut() {
    localStorage.removeItem('token')
    document.cookie = 'sb-access-token=; path=/; max-age=0; samesite=lax'
    setAuthed(false)
    setMenuOpen(false)
    router.push('/')
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-black/30 backdrop-blur-2xl">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-6 py-4 sm:px-10 lg:px-12">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 text-sm font-semibold text-white shadow-[0_10px_30px_rgba(125,214,245,0.28)]" style={{background: 'linear-gradient(135deg, var(--accent-600), #1a6e8a)'}}>A</div>
          <div>
            <div className="font-heading text-lg font-semibold tracking-tight">Arclat</div>
            <div className="text-xs uppercase tracking-[0.28em] text-[var(--muted)]">AI latency optimizer</div>
          </div>
        </Link>

        <nav className="hidden items-center gap-1 text-sm text-[var(--muted)] md:flex">
          <Link href="/dashboard" className="flex items-center gap-1.5 rounded-full px-4 py-2 hover:bg-white/5 hover:text-[var(--text)]">
            <LayoutDashboard size={14} />
            Dashboard
          </Link>
          <Link href="/upload" className="flex items-center gap-1.5 rounded-full px-4 py-2 hover:bg-white/5 hover:text-[var(--text)]">
            <Upload size={14} />
            Upload
          </Link>
          <Link href="/share" className="flex items-center gap-1.5 rounded-full px-4 py-2 hover:bg-white/5 hover:text-[var(--text)]">
            <FileText size={14} />
            Reports
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="flex items-center justify-center rounded-full border border-white/10 p-2 text-[var(--muted)] hover:bg-white/5 hover:text-[var(--text)] transition-colors"
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          {authed ? (
            <div ref={menuRef} className="relative">
              <button
                onClick={() => setMenuOpen((o) => !o)}
                className="flex items-center gap-2 rounded-full border border-white/10 px-3 py-2 text-sm text-[var(--muted)] hover:bg-white/5 hover:text-[var(--text)] transition-colors"
              >
                <UserCircle size={18} />
                <ChevronDown size={13} className={`transition-transform ${menuOpen ? 'rotate-180' : ''}`} />
              </button>
              {menuOpen && (
                <div className="absolute right-0 mt-2 w-40 overflow-hidden rounded-2xl border border-white/10 bg-[#0e1116] shadow-[0_20px_60px_rgba(0,0,0,0.5)]">
                  <button
                    onClick={signOut}
                    className="flex w-full items-center gap-2 px-4 py-3 text-sm text-[var(--muted)] hover:bg-white/5 hover:text-[var(--text)] transition-colors"
                  >
                    <LogOut size={14} />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link href="/auth/login" className="rounded-full border border-white/10 px-4 py-2 text-sm text-[var(--muted)] hover:bg-white/5 hover:text-[var(--text)]">Sign in</Link>
              <Link href="/auth/register" className="rounded-full px-4 py-2 text-sm font-semibold text-white shadow-[0_10px_30px_rgba(125,214,245,0.22)]" style={{background: 'linear-gradient(90deg, var(--accent-600), #1a6e8a)'}}>Get started</Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
