/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        lab: {
          bg:      '#0f1117',
          panel:   '#1a1d27',
          border:  '#2a2d3e',
          accent:  '#4f8ef7',
          chip:    '#7c3aed',
          biopsy:  '#f59e0b',
          plasma:  '#10b981',
          danger:  '#ef4444',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
