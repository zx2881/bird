<template>
  <header class="app-header">
    <div class="header-left">
      <div class="brand-mark" aria-hidden="true">
        <span class="brand-wing"></span>
      </div>
      <p class="eyebrow">Global Avian Biodiversity Graph</p>
      <h1>全球鸟类多样性知识探索平台</h1>
    </div>
    <nav class="header-nav">
      <router-link to="/home" class="nav-link" exact-active-class="nav-link--active">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        <span>首页</span>
      </router-link>
      <router-link to="/overview" class="nav-link" active-class="nav-link--active">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 20V10M12 20V4M6 20v-6"/>
        </svg>
        <span>数据概览</span>
      </router-link>
      <router-link to="/categories" class="nav-link" active-class="nav-link--active">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="7" height="7"/>
          <rect x="14" y="3" width="7" height="7"/>
          <rect x="3" y="14" width="7" height="7"/>
          <rect x="14" y="14" width="7" height="7"/>
        </svg>
        <span>类别</span>
      </router-link>
      <router-link to="/semantic-search" class="nav-link" active-class="nav-link--active">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="M21 21l-4.35-4.35"/>
          <path d="M11 8v6M8 11h6"/>
        </svg>
        <span>语义搜索</span>
      </router-link>
      <button class="nav-link theme-btn" @click="uiStore.toggleDarkMode()" :title="uiStore.darkMode ? '切换亮色' : '切换暗色'">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path :d="uiStore.darkMode ? 'M12 3v1m0 16v1m-9-9h1m16 0h1M4.2 4.2l.7.7m14.1 14.1l.7.7M4.2 19.8l.7-.7m14.1-14.1l.7-.7M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10' : 'M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z'"/>
        </svg>
        <span class="theme-label">{{ uiStore.darkMode ? '亮色' : '暗色' }}</span>
      </button>
    </nav>
  </header>
</template>

<script setup>
import { useUIStore } from '../stores/uiStore.js'
const uiStore = useUIStore()
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 14px;
  z-index: 80;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  margin-bottom: 18px;
  padding: 12px 14px 12px 16px;
  border: 1px solid var(--header-border, rgba(255, 255, 255, 0.55));
  border-radius: 18px;
  background:
    linear-gradient(90deg, color-mix(in srgb, var(--accent) 10%, transparent) 0 34%, transparent 34.2% 100%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.30), transparent 48%),
    var(--header-bg, linear-gradient(135deg, rgba(255, 247, 234, 0.92), rgba(233, 243, 245, 0.88)));
  box-shadow: 0 18px 42px var(--header-shadow, rgba(31, 64, 76, 0.12));
  backdrop-filter: blur(14px);
  overflow: hidden;
}

.app-header::after {
  content: "";
  position: absolute;
  inset: auto 24px 10px auto;
  width: 120px;
  height: 30px;
  pointer-events: none;
  opacity: 0.14;
  background:
    radial-gradient(circle at 12% 70%, var(--accent) 0 2px, transparent 2.5px),
    radial-gradient(circle at 44% 38%, var(--accent-2, #0ea5e9) 0 2px, transparent 2.5px),
    radial-gradient(circle at 80% 62%, var(--accent) 0 2px, transparent 2.5px),
    linear-gradient(12deg, transparent 0 22%, var(--accent) 22.5% 24%, transparent 24.5% 100%);
}

:global([data-theme="dark"]) .app-header {
  border-color: rgba(94, 234, 212, 0.22);
  background: linear-gradient(135deg, rgba(2, 8, 23, 0.94), rgba(8, 18, 33, 0.88));
  box-shadow: 0 16px 42px rgba(0, 0, 0, 0.46), 0 0 22px rgba(34, 211, 238, 0.1);
}
.header-left {
  position: relative;
  flex: 1;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  column-gap: 12px;
  align-items: center;
}
.brand-mark {
  grid-row: 1 / span 2;
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  color: var(--accent);
  background:
    radial-gradient(circle at 32% 28%, rgba(255, 255, 255, 0.85), transparent 28%),
    linear-gradient(145deg, var(--accent-soft), rgba(14, 165, 233, 0.12));
  border: 1px solid color-mix(in srgb, var(--accent) 36%, transparent);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.55), 0 12px 30px color-mix(in srgb, var(--accent) 16%, transparent);
}
.brand-wing {
  width: 22px;
  height: 16px;
  border: 2px solid currentColor;
  border-left-color: transparent;
  border-bottom-color: transparent;
  border-radius: 60% 80% 45% 70%;
  transform: rotate(-18deg);
}
.eyebrow { margin: 0 0 3px; font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--accent, #0f766e); }
.app-header h1 { margin: 0; font-family: inherit; font-size: clamp(18px, 1.9vw, 26px); font-weight: 850; line-height: 1.08; color: var(--heading-color, inherit); text-shadow: 0 1px 0 rgba(255,255,255,0.18); }
.header-nav { display: flex; gap: 8px; align-items: center; }
.nav-link {
  display: flex; align-items: center; justify-content: center; gap: 7px; min-height: 42px; padding: 9px 13px; border-radius: 12px;
  border: 1px solid var(--nav-border, rgba(18, 48, 59, 0.1));
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.22), transparent),
    var(--nav-bg, rgba(255, 255, 255, 0.68));
  color: var(--text-color, #12303b); text-decoration: none; font-size: 13px; cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, color 0.18s ease; font-family: inherit;
  white-space: nowrap;
}
.nav-link:hover { transform: translateY(-1px); border-color: rgba(15, 118, 110, 0.26); box-shadow: 0 10px 18px rgba(18, 48, 59, 0.08); }
.nav-link--active {
  border-color: rgba(15, 118, 110, 0.42);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--accent) 28%, transparent), var(--nav-active-bg, rgba(255, 248, 240, 0.9)));
  color: var(--accent, #0f5f5a); font-weight: 700;
  box-shadow: 0 10px 24px color-mix(in srgb, var(--accent) 16%, transparent);
}
.nav-icon { width: 16px; height: 16px; }
.theme-btn {
  width: 42px;
  padding-inline: 0;
  border-color: var(--nav-border, rgba(18, 48, 59, 0.1));
}
.theme-label {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
@media (max-width: 720px) {
  .app-header { flex-direction: column; padding: 14px; top: 10px; }
  .header-left { width: 100%; }
  .header-nav { width: 100%; justify-content: center; flex-wrap: wrap; }
  .nav-link { flex: 1 1 auto; min-width: 96px; }
  .theme-btn { flex: 0 0 42px; min-width: 42px; }
}
</style>
