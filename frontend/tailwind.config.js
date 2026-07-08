/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-body)', 'system-ui', 'sans-serif'],
        display: ['var(--font-display)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      colors: {
        // brand-blue scale (#3B82F6 light accent, #60A5FA dark accent)
        primary: {
          50:  '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        accent: {
          cyan:    '#0ea5e9', // brand-sky
          sky:     '#38bdf8',
          magenta: '#f43f5e',
          yellow:  '#facc15',
          orange:  '#fb923c',
        },
        // theme-aware tokens driven by CSS variables in globals.css
        ink:   'rgb(var(--ink) / <alpha-value>)',
        fake:  'rgb(var(--fake) / <alpha-value>)',
        real:  'rgb(var(--real) / <alpha-value>)',
        field: 'var(--col-field)',
        card:  'var(--col-card)',
        dark: {
          100: '#1a1b2e',
          200: '#16172b',
          300: '#12131f',
          400: '#0d0e18',
          500: '#080912',
        },
      },
      backgroundImage: {
        'gradient-radial':  'radial-gradient(var(--tw-gradient-stops))',
        'gradient-mesh':    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'gradient-aurora':  'linear-gradient(to right, #4facfe 0%, #00f2fe 100%)',
      },
      animation: {
        'float':    'float 6s ease-in-out infinite',
        'glow':     'glow 2s ease-in-out infinite alternate',
        'scan':     'scan 3s linear infinite',
        'pulse-slow':'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-20px)' },
        },
        glow: {
          from: { boxShadow: '0 0 20px rgba(108,110,246,0.3)' },
          to:   { boxShadow: '0 0 40px rgba(108,110,246,0.8)' },
        },
        scan: {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
