import './globals.css'
import type { Metadata } from 'next'
import { Inter, Syne } from 'next/font/google'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const syne = Syne({ subsets: ['latin'], variable: '--font-syne' })

export const metadata: Metadata = {
  title: 'Arclat — AI Agent Latency Optimizer',
  description: "Your AI agent is slow. Here's why.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${syne.variable} font-body min-h-screen flex flex-col`}>
        {children}
      </body>
    </html>
  )
}
