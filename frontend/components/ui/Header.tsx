"use client"

import Link from 'next/link'
import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { LayoutDashboard, FileText, UserCircle, LogOut, ChevronDown, Sun, Moon } from 'lucide-react'

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
    <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-[var(--bg)]">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-6 py-3.5 sm:px-10 lg:px-12">
        <Link href="/" className="flex items-center gap-2.5">
          <img src="/logo.svg" alt="Arclat" className="h-8 w-8 rounded-lg" />
          <span className="text-base font-semibold tracking-tight text-[var(--text)]">Arclat</span>
        </Link>

        <nav className="hidden items-center gap-0.5 text-sm text-[var(--muted)] md:flex">
          <Link href="/dashboard" className="flex items-center gap-1.5 rounded-lg px-3 py-2 hover:bg-white/5 hover:text-[var(--text)]">
            <LayoutDashboard size={14} />
            Dashboard
          </Link>
          <Link href="/share" className="flex items-center gap-1.5 rounded-lg px-3 py-2 hover:bg-white/5 hover:text-[var(--text)]">
            <FileText size={14} />
            Reports
          </Link>
        </nav>

        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="flex items-center justify-center rounded-lg border border-white/10 p-2 text-[var(--muted)] hover:bg-white/5 hover:text-[var(--text)]"
          >
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>
          {authed ? (
            <div ref={menuRef} className="relative">
              <button
                onClick={() => setMenuOpen((o) => !o)}
                className="flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm text-[var(--muted)] hover:bg-white/5 hover:text-[var(--text)]"
              >
                <UserCircle size={16} />
                <ChevronDown size={12} className={`transition-transform ${menuOpen ? 'rotate-180' : ''}`} />
              </button>
              {menuOpen && (
                <div className="absolute right-0 mt-1.5 w-36 overflow-hidden rounded-xl border border-white/10 bg-[var(--card)] shadow-xl">
                  <button
                    onClick={signOut}
                    className="flex w-full items-center gap-2 px-4 py-3 text-sm text-[var(--muted)] hover:bg-white/5 hover:text-[var(--text)]"
                  >
                    <LogOut size={13} />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link href="/auth/login" className="rounded-lg border border-white/10 px-4 py-2 text-sm text-[var(--muted)] hover:bg-white/5 hover:text-[var(--text)]">Sign in</Link>
              <Link href="/auth/register" className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-[#06111a] hover:opacity-90">Get started</Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
