<template>
  <header class="app-header">
    <div class="header-left">
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
        <span>{{ uiStore.darkMode ? '亮色' : '暗色' }}</span>
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  margin-bottom: 18px;
  padding: 18px 28px;
  border: 1px solid var(--header-border, rgba(255, 255, 255, 0.55));
  border-radius: 26px;
  background: var(--header-bg, linear-gradient(135deg, rgba(255, 247, 234, 0.92), rgba(233, 243, 245, 0.88)));
  box-shadow: 0 20px 45px var(--header-shadow, rgba(31, 64, 76, 0.12));
  backdrop-filter: blur(18px);
}
.header-left { flex: 1; }
.eyebrow { margin: 0 0 4px; font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--accent, #0f766e); }
.app-header h1 { margin: 0; font-family: "Alegreya", "Source Han Serif SC", "Noto Serif SC", serif; font-size: clamp(22px, 2.8vw, 36px); line-height: 1.05; color: var(--heading-color, inherit); }
.header-nav { display: flex; gap: 8px; align-items: center; }
.nav-link {
  display: flex; align-items: center; gap: 6px; padding: 10px 18px; border-radius: 999px;
  border: 1px solid var(--nav-border, rgba(18, 48, 59, 0.1));
  background: var(--nav-bg, rgba(255, 255, 255, 0.68));
  color: var(--text-color, #12303b); text-decoration: none; font-size: 14px; cursor: pointer;
  transition: all 0.2s ease; font-family: inherit;
}
.nav-link:hover { transform: translateY(-1px); border-color: rgba(15, 118, 110, 0.26); box-shadow: 0 10px 18px rgba(18, 48, 59, 0.08); }
.nav-link--active {
  border-color: rgba(15, 118, 110, 0.42);
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.14), var(--nav-active-bg, rgba(255, 248, 240, 0.9)));
  color: var(--accent, #0f5f5a); font-weight: 700;
}
.nav-icon { width: 16px; height: 16px; }
.theme-btn { border-color: var(--nav-border, rgba(18, 48, 59, 0.1)); }
@media (max-width: 720px) {
  .app-header { flex-direction: column; padding: 16px 20px; }
  .header-nav { width: 100%; justify-content: center; flex-wrap: wrap; }
}
</style>
