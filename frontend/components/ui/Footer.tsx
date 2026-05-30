"use client"

export default function Footer() {
  return (
    <footer className="w-full border-t border-white/10 bg-black/20">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-6 py-6 text-sm text-[var(--muted)] sm:px-10 lg:px-12 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="font-heading text-base font-semibold tracking-tight text-[var(--text)]">Arclat</div>
          <div>Built for faster agent pipelines.</div>
        </div>
        <div className="flex gap-4">
          <a href="#" className="rounded-full px-3 py-2 hover:bg-white/5 hover:text-[var(--text)]">Privacy</a>
          <a href="#" className="rounded-full px-3 py-2 hover:bg-white/5 hover:text-[var(--text)]">Terms</a>
        </div>
      </div>
    </footer>
  )
}
