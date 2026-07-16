// Theme variable mappings:
// - obsidian: Main application background (dark base)
// - champagne: Accent color for primary actions, buttons, and highlights
// - ivory: Principal text and high-contrast foreground color
// - slate: Divider lines, borders, and muted secondary text
// - panel: Card, modal, and side panel backgrounds
// - dark-input: Input fields, textareas, and dropdown backgrounds
export const themes = {
  classic: {
    name: 'Classic Amber (Default)',
    background: '#0D0D12',
    accent: '#C9A84C',
    text: '#FAF8F5',
    border: '#2A2A35',
    panel: '#1A1A24',
    input: '#14141A'
  },
  midnight: {
    name: 'Midnight Blue',
    background: '#080C14',
    accent: '#3B82F6',
    text: '#F8FAFC',
    border: '#1E293B',
    panel: '#111827',
    input: '#0F172A'
  },
  pornhub: {
    name: 'Pornhub',
    background: '#000000',
    accent: '#ffa31a',
    text: '#ffffff',
    border: '#212121',
    panel: '#0e0e0e',
    input: '#151515'
  },
  dark: {
    name: 'Dark Mode',
    background: '#0c0b0c',
    accent: '#BB86FC',
    text: '#E0E0E0',
    border: '#282929',
    panel: '#1d1c1d',
    input: '#2C2C2C'
  },
  dark2:{
    name: 'Dark Mode 2',
    background: '#13151a',
    accent: '#4392fe',
    text: '#E0E0E0',
    border: '#282c38',
    panel: '#181c25',
    input: '#161820'
  },
}

export function applyTheme(colors) {
  if (!colors) return
  Object.entries(colors).forEach(([key, val]) => {
    if (key === 'name') return
    let mappedKey = key
    if (key === 'obsidian') mappedKey = 'background'
    else if (key === 'champagne') mappedKey = 'accent'
    else if (key === 'ivory') mappedKey = 'text'
    else if (key === 'slate') mappedKey = 'border'
    else if (key === 'dark-input') mappedKey = 'input'
    
    document.documentElement.style.setProperty(`--color-theme-${mappedKey}`, val)
  })
}

export function initTheme() {
  try {
    const saved = localStorage.getItem('customTheme')
    if (saved) {
      const parsed = JSON.parse(saved)
      const normalized = {}
      Object.entries(parsed).forEach(([key, val]) => {
        let k = key
        if (key === 'obsidian') k = 'background'
        else if (key === 'champagne') k = 'accent'
        else if (key === 'ivory') k = 'text'
        else if (key === 'slate') k = 'border'
        else if (key === 'dark-input') k = 'input'
        normalized[k] = val
      })
      applyTheme(normalized)
      return normalized
    }
  } catch (e) {
    console.error('Failed to parse saved customTheme:', e)
  }
  return null
}
