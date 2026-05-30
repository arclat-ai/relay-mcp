"use client"

export default function Footer() {
  return (
    <footer className="w-full border-t border-white/06 bg-transparent">
      <div className="container py-6 text-sm text-[var(--muted)]">
        <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
          <div>Built by Arclat · arclat.com</div>
          <div className="flex gap-4">
            <a href="#" className="hover:text-[var(--text)]">Privacy</a>
            <a href="#" className="hover:text-[var(--text)]">Terms</a>
          </div>
        </div>
      </div>
    </footer>
  )
}
