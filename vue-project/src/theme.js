export const themes = {
  classic: {
    name: 'Classic Amber (Default)',
    obsidian: '#0D0D12',
    champagne: '#C9A84C',
    ivory: '#FAF8F5',
    slate: '#2A2A35',
    panel: '#1A1A24',
    'dark-input': '#14141A'
  },
  midnight: {
    name: 'Midnight Blue',
    obsidian: '#080C14',
    champagne: '#3B82F6',
    ivory: '#F8FAFC',
    slate: '#1E293B',
    panel: '#111827',
    'dark-input': '#0F172A'
  },
  cyberpunk: {
    name: 'Cyberpunk Neon',
    obsidian: '#1A0826',
    champagne: '#F43F5E',
    ivory: '#FDF4FF',
    slate: '#3B0764',
    panel: '#2E1065',
    'dark-input': '#240046'
  },
  forest: {
    name: 'Forest Emerald',
    obsidian: '#05140B',
    champagne: '#10B981',
    ivory: '#F0FDF4',
    slate: '#064E3B',
    panel: '#022C22',
    'dark-input': '#062013'
  },
  matrix: {
    name: 'Matrix Terminal',
    obsidian: '#000000',
    champagne: '#22C55E',
    ivory: '#A7F3D0',
    slate: '#166534',
    panel: '#14532D',
    'dark-input': '#052E16'
  },
  rose: {
    name: 'Rose Quartz',
    obsidian: '#1C0A10',
    champagne: '#EC4899',
    ivory: '#FFF1F2',
    slate: '#4C0519',
    panel: '#881337',
    'dark-input': '#310411'
  },
  slate: {
    name: 'Slate Minimalist',
    obsidian: '#0F172A',
    champagne: '#64748B',
    ivory: '#F8FAFC',
    slate: '#334155',
    panel: '#1E293B',
    'dark-input': '#0F172A'
  },
  monochrome: {
    name: 'Monochrome Dark',
    obsidian: '#000000',
    champagne: '#FFFFFF',
    ivory: '#F3F4F6',
    slate: '#374151',
    panel: '#1F2937',
    'dark-input': '#111827'
  }
}

export function applyTheme(colors) {
  if (!colors) return
  Object.entries(colors).forEach(([key, val]) => {
    if (key === 'name') return
    document.documentElement.style.setProperty(`--color-theme-${key}`, val)
  })
}

export function initTheme() {
  try {
    const saved = localStorage.getItem('customTheme')
    if (saved) {
      const parsed = JSON.parse(saved)
      applyTheme(parsed)
      return parsed
    }
  } catch (e) {
    console.error('Failed to parse saved customTheme:', e)
  }
  return null
}
