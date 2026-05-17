import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#171717',
          foreground: '#fafafa',
          50: '#f5f5f5',
          100: '#e5e5e5',
          200: '#d4d4d4',
          300: '#a3a3a3',
          400: '#737373',
          500: '#171717',
          600: '#171717',
          700: '#0a0a0a',
          800: '#0a0a0a',
          900: '#0a0a0a',
        },
        success: '#22c55e',
        warning: '#f59e0b',
        destructive: '#ef4444',
        processing: '#171717',
        background: '#fafafa',
        surface: {
          DEFAULT: '#ffffff',
          dim: '#e5e5e5',
          container: {
            lowest: '#ffffff',
            low: '#fafafa',
            DEFAULT: '#f5f5f5',
            high: '#e5e5e5',
            highest: '#d4d4d4',
          },
        },
        muted: {
          DEFAULT: '#f5f5f5',
          foreground: '#737373',
        },
        accent: {
          DEFAULT: '#f5f5f5',
          foreground: '#171717',
        },
        border: '#e5e5e5',
        input: '#e5e5e5',
        ring: '#171717',
        foreground: '#171717',
        'hit-high': '#22c55e',
        'hit-medium': '#171717',
        'hit-low': '#f59e0b',
        'report-purple': '#7c3aed',
        'report-teal': '#14b8a6',
      },
      borderRadius: {
        lg: '0.5rem',
        md: '0.375rem',
        sm: '0.25rem',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        heading: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        'h1': ['20px', { lineHeight: '28px', fontWeight: '600' }],
        'h2': ['15px', { lineHeight: '22px', fontWeight: '600' }],
        'body': ['14px', { lineHeight: '20px' }],
        'body-small': ['13px', { lineHeight: '18px' }],
        'meta': ['12px', { lineHeight: '16px' }],
      },
      spacing: {
        'sidebar': '220px',
        'sidebar-collapsed': '56px',
        'topbar': '48px',
      },
    },
  },
  plugins: [],
}

export default config
