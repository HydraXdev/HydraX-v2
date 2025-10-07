import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0a0e17',
        secondary: '#1a1f2e',
        tertiary: '#2a3142',
        mint: '#00e0a4',
        cyan: '#7df9ff',
        amber: '#ffb020',
        danger: '#ff5470',
        muted: '#6b7280',
        active: '#374151',
        overlay: '#111827',
      },
      fontFamily: {
        tactical: ['Barlow Condensed', 'sans-serif'],
        code: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'neon-glow': 'neon-glow 1.5s ease-in-out infinite alternate',
      },
    },
  },
  plugins: [],
}

export default config