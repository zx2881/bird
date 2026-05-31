import { ref } from 'vue'

const activePage = ref('')
const isOpen = ref(false)

export function useHelpGuide() {
  function open(pageId) {
    activePage.value = pageId
    isOpen.value = true
  }

  function close() {
    isOpen.value = false
  }

  function checkFirstVisit(pageId) {
    const key = `bird-help-shown-${pageId}`
    if (!localStorage.getItem(key)) {
      localStorage.setItem(key, 'true')
      open(pageId)
    }
  }

  return { isOpen, activePage, open, close, checkFirstVisit }
}
