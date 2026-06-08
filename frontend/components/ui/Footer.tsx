"use client"

export default function Footer() {
  return (
    <footer className="w-full border-t border-white/10">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-6 py-5 text-sm text-[var(--muted)] sm:px-10 lg:px-12 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <span className="font-semibold tracking-tight text-[var(--text)]">Arclat</span>
          <span>&copy; {new Date().getFullYear()}</span>
        </div>
        <div className="flex gap-1">
          <a href="#" className="rounded-lg px-3 py-1.5 hover:bg-white/5 hover:text-[var(--text)]">Privacy</a>
          <a href="#" className="rounded-lg px-3 py-1.5 hover:bg-white/5 hover:text-[var(--text)]">Terms</a>
        </div>
      </div>
    </footer>
  )
}
