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
        teal: {
          500: 'var(--color-teal-500)',
          600: 'var(--color-teal-600)',
          soft: 'var(--color-teal-soft)',
        },
        surface: {
          page: 'var(--color-page-bg)',
          sidebar: 'var(--color-sidebar-bg)',
          card: 'var(--color-card-bg)',
          panel: 'var(--color-card-bg)',
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
        border: {
          DEFAULT: 'var(--color-border)',
          strong: 'var(--color-border-strong)',
        },
        scene: {
          home: 'var(--color-scene-home)',
          sleep: 'var(--color-scene-sleep)',
          energy: 'var(--color-scene-energy)',
          security: 'var(--color-scene-security)',
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
