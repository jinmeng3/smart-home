/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: 'var(--color-primary-50)',
          100: 'var(--color-primary-100)',
          200: 'var(--color-primary-200)',
          300: 'var(--color-primary-300)',
          400: 'var(--color-primary-400)',
          500: 'var(--color-primary-500)',
          600: 'var(--color-primary-600)',
          700: 'var(--color-primary-700)',
          800: 'var(--color-primary-800)',
        },
        surface: {
          page: 'var(--color-page-background)',
          sidebar: 'var(--color-sidebar-background)',
          panel: 'var(--color-panel-background)',
          subtle: 'var(--color-surface-subtle)',
          hover: 'var(--color-surface-hover)',
          active: 'var(--color-surface-active)',
          action: 'var(--color-action-subtle)',
        },
        content: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          tertiary: 'var(--color-text-tertiary)',
          muted: 'var(--color-text-muted)',
          disabled: 'var(--color-text-disabled)',
          inverse: 'var(--color-text-on-primary)',
        },
        semantic: {
          success: 'var(--color-success)',
          warning: 'var(--color-warning)',
          danger: 'var(--color-danger)',
          info: 'var(--color-info)',
        },
        ai: {
          DEFAULT: 'var(--color-ai)',
          soft: 'var(--color-ai-soft)',
          border: 'var(--color-ai-border)',
        },
      },
      boxShadow: {
        soft: 'var(--shadow-card)',
      },
    },
  },
  plugins: [],
}
