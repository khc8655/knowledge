import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0052cc',
          foreground: '#ffffff',
          50: '#e6f0ff',
          100: '#b3d1ff',
          200: '#80b3ff',
          300: '#4d94ff',
          400: '#1a75ff',
          500: '#0052cc',
          600: '#003d9b',
          700: '#002d73',
          800: '#001e4d',
          900: '#000f26',
        },
        success: '#36B37E',
        warning: '#FFAB00',
        destructive: '#FF5630',
        processing: '#0052CC',
        background: '#faf8ff',
        surface: {
          DEFAULT: '#ffffff',
          dim: '#d9d9e4',
          container: {
            lowest: '#ffffff',
            low: '#f3f3fd',
            DEFAULT: '#ededf8',
            high: '#e7e7f2',
            highest: '#e1e2ec',
          },
        },
        muted: {
          DEFAULT: '#f3f3fd',
          foreground: '#434654',
        },
        accent: {
          DEFAULT: '#f3f3fd',
          foreground: '#191b23',
        },
        border: '#c3c6d6',
        input: '#c3c6d6',
        ring: '#0052cc',
        foreground: '#191b23',
        'hit-high': '#36B37E',
        'hit-medium': '#0052CC',
        'hit-low': '#FFAB00',
        'report-purple': '#6554C0',
        'report-teal': '#00B8D9',
      },
      borderRadius: {
        lg: '0.75rem',
        md: '0.5rem',
        sm: '0.25rem',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        heading: ['Manrope', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'h1': ['24px', { lineHeight: '32px', fontWeight: '600' }],
        'h2': ['18px', { lineHeight: '24px', fontWeight: '600' }],
        'body': ['14px', { lineHeight: '20px' }],
        'body-small': ['13px', { lineHeight: '18px' }],
        'meta': ['12px', { lineHeight: '16px' }],
      },
      spacing: {
        'sidebar': '240px',
        'sidebar-collapsed': '64px',
        'topbar': '56px',
      },
    },
  },
  plugins: [],
}

export default config
