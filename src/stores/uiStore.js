import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useUIStore = defineStore('ui', () => {
  const darkMode = ref(false)

  function initTheme() {
    const saved = localStorage.getItem('bird-dark-mode')
    if (saved !== null) darkMode.value = saved === 'true'
    else darkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    applyTheme()
  }

  function toggleDarkMode() {
    darkMode.value = !darkMode.value
    applyTheme()
  }

  function applyTheme() {
    document.documentElement.setAttribute('data-theme', darkMode.value ? 'dark' : 'light')
    localStorage.setItem('bird-dark-mode', darkMode.value)
  }

  watch(darkMode, applyTheme)

  return { darkMode, initTheme, toggleDarkMode }
})
