import './globals.css'
import type { Metadata } from 'next'
import { Plus_Jakarta_Sans } from 'next/font/google'
import Header from '../components/ui/Header'
import Footer from '../components/ui/Footer'

const jakarta = Plus_Jakarta_Sans({ subsets: ['latin'], variable: '--font-jakarta' })

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
    <html lang="en" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className={`${jakarta.variable} font-body min-h-screen flex flex-col antialiased`}
      >
        <div className="flex min-h-screen flex-col">
          <Header />
          <div className="flex-1 w-full">
            {children}
          </div>
          <Footer />
        </div>
      </body>
    </html>
  )
}
