import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0a',
        surface: '#111111',
        border: '#222222',
        accent: '#46f5a5',
        textPrimary: '#ffffff',
        textSecondary: '#888888',
        error: '#FF4444',
        warning: '#FFAA00'
      },
      fontFamily: {
        heading: ['var(--font-syne)'],
        body: ['var(--font-inter)'],
      }
    },
  },
  plugins: [],
}
export default config
