<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="help-overlay" @click.self="close">
        <div class="help-dialog">
          <button class="help-close-btn" @click="close" title="关闭">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>

          <div class="help-header">
            <div class="help-header-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <circle cx="12" cy="12" r="10"/>
                <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
            </div>
            <h2>使用说明</h2>
            <p>{{ subtitle }}</p>
          </div>

          <div class="help-body">
            <slot />
          </div>

          <div class="help-actions">
            <button class="help-start-btn" @click="close">
              知道了
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  subtitle: { type: String, default: '' }
})

import { computed } from 'vue'
import { useHelpGuide } from '../composables/useHelpGuide.js'

const { isOpen, close } = useHelpGuide()
</script>

<style scoped>
.help-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(6px);
  padding: 20px;
}

.help-dialog {
  position: relative;
  width: 100%;
  max-width: 680px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  background: var(--card-bg, #fff);
  border-radius: 24px;
  border: 1px solid var(--panel-border, rgba(0,0,0,0.08));
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.help-close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 2;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: 1px solid var(--panel-border, rgba(0,0,0,0.08));
  background: var(--card-bg, #fff);
  color: var(--text-secondary, #64748b);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}
.help-close-btn:hover {
  background: rgba(0,0,0,0.05);
  color: var(--text-color);
}
.help-close-btn svg { width: 18px; height: 18px; }

.help-header {
  padding: 32px 32px 0;
  text-align: center;
}
.help-header-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(15,118,110,0.12), rgba(15,118,110,0.04));
  color: var(--accent, #0f766e);
  margin-bottom: 14px;
}
.help-header-icon svg { width: 26px; height: 26px; }
.help-header h2 {
  margin: 0 0 6px;
  font-family: "Alegreya", "Source Han Serif SC", serif;
  font-size: 26px;
  font-weight: 700;
  color: var(--heading-color);
  letter-spacing: -0.01em;
}
.help-header p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.help-body {
  padding: 24px 32px;
  overflow-y: auto;
  flex: 1;
}

.help-body :deep(h3) {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 700;
  color: var(--heading-color);
}
.help-body :deep(h3 svg) {
  width: 18px;
  height: 18px;
  color: var(--accent);
  flex-shrink: 0;
}
.help-body :deep(p) {
  margin: 0 0 8px;
  font-size: 13px;
  line-height: 1.75;
  color: var(--text-secondary);
}
.help-body :deep(p:last-child) { margin-bottom: 0; }
.help-body :deep(ul) {
  margin: 0;
  padding: 0 0 0 18px;
}
.help-body :deep(li) {
  font-size: 13px;
  line-height: 1.75;
  color: var(--text-secondary);
  margin-bottom: 4px;
}
.help-body :deep(li strong) { color: var(--text-color); }
.help-body :deep(.help-section) { margin-bottom: 20px; }
.help-body :deep(.help-section:last-child) { margin-bottom: 0; }
.help-body :deep(.help-tip) {
  padding: 12px 16px;
  border-radius: 12px;
  background: var(--accent-soft, rgba(15,118,110,0.06));
  border: 1px solid rgba(15,118,110,0.12);
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-top: 8px;
}

.help-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 16px 32px 24px;
  border-top: 1px solid var(--panel-border, rgba(0,0,0,0.06));
  gap: 12px;
}

.help-start-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #0d9488, #14b8a6);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 20px rgba(13, 148, 136, 0.3);
}
.help-start-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 28px rgba(13, 148, 136, 0.4);
}
.help-start-btn svg { width: 16px; height: 16px; }

.modal-enter-active, .modal-leave-active { transition: opacity 0.3s ease; }
.modal-enter-active .help-dialog, .modal-leave-active .help-dialog {
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease;
}
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .help-dialog { opacity: 0; transform: scale(0.92) translateY(24px); }
.modal-leave-to .help-dialog { opacity: 0; transform: scale(0.92) translateY(24px); }

@media (max-width: 560px) {
  .help-dialog { max-width: 100%; border-radius: 20px; }
  .help-header { padding: 24px 20px 0; }
  .help-body { padding: 20px; }
  .help-actions { padding: 14px 20px 20px; }
  .help-start-btn { width: 100%; justify-content: center; }
}
</style>
