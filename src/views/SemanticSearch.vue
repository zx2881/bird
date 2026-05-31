<template>
  <div class="semantic-page">
    <button class="help-float-btn" @click="helpGuide.open('semantic-search')" title="使用说明">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    </button>

    <HelpModal subtitle="语义搜索 · 功能介绍">
      <div class="help-section">
        <h3>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
          搜索模式
        </h3>
        <ul>
          <li><strong>搜索：</strong>输入自然语言查询（如"鄱阳湖有什么濒危鸟类"），系统在知识图谱中匹配相关实体和关系路径并返回结果。支持搜索鸟类、地点、分类层级等不同类型实体。</li>
          <li><strong>智能问答：</strong>点击"智能问答"按钮，AI 基于知识图谱内容生成自然语言回答。</li>
          <li><strong>热门搜索：</strong>点击预设的热门查询快速体验语义搜索功能。</li>
        </ul>
      </div>
      <div class="help-section">
        <h3>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/></svg>
          结果筛选与详情
        </h3>
        <ul>
          <li><strong>筛选侧边栏：</strong>按实体类型（鸟类、地点、分类、栖息地、威胁、保护等级）筛选搜索结果。</li>
          <li><strong>结果卡片：</strong>每条结果展示实体名称、类型标签、学名/英文名、关联度和匹配关系路径。点击卡片跳转详情页。</li>
          <li><strong>共享实体：</strong>当同一实体通过多条路径匹配时，标记为"共享"并显示关联的查询实体。</li>
        </ul>
      </div>
      <div class="help-section">
        <h3>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          搜索历史
        </h3>
        <ul>
          <li>自动保存最近 20 条搜索历史，聚焦输入框时展示，支持一键复用和清除。</li>
          <li>输入时提供实时搜索建议，基于已有实体名称自动补全。</li>
        </ul>
      </div>
    </HelpModal>

    <div class="page-hero">
      <div class="hero-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <circle cx="11" cy="11" r="7" />
          <path d="M21 21l-4.5-4.5" />
          <path d="M9.5 11h3M11 9.5v3" />
        </svg>
      </div>
      <span class="semantic-kicker">Knowledge query desk</span>
      <h2 class="page-title">语义搜索</h2>
      <p class="page-desc">用自然语言探索鸟类知识图谱，AI 理解语义并返回精准答案</p>
    </div>

    <div class="search-box">
      <div class="search-row" ref="searchRowRef">
        <svg class="search-icon" :class="{ focused: isFocused }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8" />
          <path d="M21 21l-4.35-4.35" />
        </svg>
        <input
          v-model="query"
          type="text"
          class="search-input"
          placeholder="试试「鄱阳湖有什么濒危鸟类」或「丹顶鹤生活在哪里」…"
          @input="onQueryInput"
          @keydown.enter="doAsk"
          @focus="onFocus"
          @blur="onBlur"
          aria-label="语义搜索输入"
          autocomplete="off"
        />
        <div class="search-right">
          <span v-if="loading" class="spinner" />
          <button v-if="query && !loading" class="search-clear-btn" @click="query = ''" aria-label="清除搜索">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12" /></svg>
          </button>
        </div>

        <div v-if="(suggestions.length || searchHistory.length) && showSuggestions" class="suggest-dropdown">
          <template v-if="suggestions.length">
            <div class="suggest-section-title">搜索建议</div>
            <button
              v-for="s in suggestions"
              :key="s.name"
              class="suggest-item"
              @mousedown.prevent="pickSuggestion(s.name)"
            >
              <span class="suggest-type-icon">{{ typeIcon(s.type) }}</span>
              <span class="suggest-name">{{ s.name }}</span>
              <span class="suggest-type-tag" :class="typeClass(s.type)">{{ typeLabel(s.type) }}</span>
            </button>
          </template>
          <template v-if="searchHistory.length && !suggestions.length">
            <div class="suggest-section-title">
              <svg class="suggest-title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              搜索历史
            </div>
            <button
              v-for="item in searchHistory"
              :key="item"
              class="suggest-item"
              @mousedown.prevent="pickSuggestion(item)"
            >
              <svg class="suggest-history-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              <span class="suggest-name">{{ item }}</span>
            </button>
          </template>
          <button v-if="searchHistory.length" class="suggest-clear" @mousedown.prevent="clearHistory">清除搜索历史</button>
        </div>
      </div>

      <div class="search-actions">
        <button class="action-btn action-btn--search" @click="doSearch" :disabled="loading">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
          搜索
        </button>
        <button class="action-btn action-btn--ask" @click="doAsk" :disabled="loading">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9.663 17h4.674M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
          智能问答
        </button>
        <button class="action-btn action-btn--clear" @click="clearAll">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14"/></svg>
          清空
        </button>
      </div>

      <div v-if="!results.length && !loading && !answer && !error" class="hot-section">
        <div class="hot-label">
          <svg class="hot-label-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5a6 6 0 00-6-6c-3.3 0-6 2.7-6 6 0 2.7 1.8 5 4.5 5.8M12 13v6"/></svg>
          热门搜索
        </div>
        <div class="hot-tags">
          <button v-for="hint in hotQueries" :key="hint" class="hot-tag" @click="query = hint; doSearch()">{{ hint }}</button>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-msg">
      <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/></svg>
      {{ error }}
    </div>

    <div v-if="answer" class="answer-card">
      <div class="answer-header">
        <svg class="answer-ai-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9.663 17h4.674M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
        </svg>
        <h3 class="answer-title">AI 智能回答</h3>
      </div>
      <div class="answer-text">{{ answer }}</div>
    </div>

    <div class="results-layout" v-if="results.length">
      <aside class="facet-sidebar" v-if="facets.length">
        <div class="facet-header">
          <svg class="facet-header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/></svg>
          <h4 class="facet-title">筛选</h4>
        </div>
        <div v-for="facet in facets" :key="facet.key" class="facet-group">
          <div class="facet-label">{{ facet.label }} <span class="facet-count-total">{{ facet.options.reduce((a, o) => a + o.count, 0) }}</span></div>
          <button
            v-for="opt in facet.options"
            :key="opt.value"
            class="facet-option"
            :class="{ active: activeFilters[facet.key] === opt.value }"
            @click="toggleFilter(facet.key, opt.value)"
          >
            <span class="facet-dot" :class="typeClass(opt.value)" />
            <span class="facet-opt-label">{{ opt.label }}</span>
            <span class="facet-count">{{ opt.count }}</span>
          </button>
        </div>
        <button v-if="hasActiveFilters" class="facet-reset" @click="resetFilters">
          <svg class="facet-reset-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
          重置筛选
        </button>
      </aside>

      <div class="results-main">
        <div class="results-header">
          <div class="results-header-left">
            <h3 class="results-title">搜索结果</h3>
            <span class="results-meta-badge">{{ filteredResults.length }} 条 · {{ elapsed }}ms</span>
          </div>
          <span v-if="intentLabel" class="intent-badge">{{ intentLabel }}</span>
        </div>

        <div class="result-cards">
          <div
            v-for="(item, idx) in filteredResults"
            :key="item.id + (item.via || '')"
            class="result-card"
            :class="{ 'is-anchor': item.isAnchor, 'is-shared': item.shared }"
            :style="{ animationDelay: `${idx * 0.04}s` }"
            @click="goToBird(item.id)"
          >
            <div class="result-card-header">
              <div class="result-name-row">
                <span class="type-icon">{{ typeIcon(item.type) }}</span>
                <span class="result-name">{{ item.name }}</span>
                <span v-if="item.shared" class="shared-badge" title="共享实体">共享</span>
              </div>
              <div class="result-score-row">
                <span v-if="item.score != null" class="result-score">
                  <span class="score-bar" :style="{ width: `${(item.score * 100).toFixed(0)}%` }" />
                  <span class="score-text">{{ (item.score * 100).toFixed(0) }}%</span>
                </span>
              </div>
            </div>

            <div class="result-meta">
              <span class="type-tag" :class="typeClass(item.type)">{{ typeLabel(item.type) }}</span>
              <template v-if="item.englishName">
                <span class="meta-sep">·</span>
                <span class="meta-name">{{ item.englishName }}</span>
              </template>
              <template v-if="item.latinName">
                <span class="meta-latin">{{ item.latinName }}</span>
              </template>
              <span v-if="item.degree > 3" class="degree-badge" :title="`关联 ${item.degree} 个实体`">
                <svg class="degree-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>
                {{ item.degree }}
              </span>
            </div>

            <div v-if="item.relation" class="result-path">
              <svg class="path-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              <span class="path-via">{{ item.viaName }}</span>
              <svg class="path-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
              <span class="path-relation">{{ item.relationLabel }}</span>
              <svg class="path-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
              <span class="path-target">{{ item.name }}</span>
              <span v-if="item.hop === 2" class="hop-badge">{{ item.hop }}跳</span>
            </div>

            <div v-if="item.shared" class="result-shared">
              <svg class="shared-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4-4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>
              共享于 {{ item.sharedBetween?.join('、') }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!loading && !results.length && !error && !answer" class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
        <circle cx="11" cy="11" r="8" />
        <path d="M21 21l-4.5-4.5" />
        <path d="M9 11h4" />
      </svg>
      <p class="empty-title">输入问题开始探索</p>
      <p class="empty-desc">在上方搜索框中输入自然语言问题，AI 将结合知识图谱为你找到答案</p>
    </div>

    <div v-if="loading && !results.length && !answer" class="loading-skeleton">
      <div class="skeleton-card" v-for="n in 5" :key="n">
        <div class="skeleton-line skeleton-line--title" />
        <div class="skeleton-line skeleton-line--meta" />
        <div class="skeleton-line skeleton-line--path" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'
import { useGraphStore } from '../stores/graphStore.js'
import { useHelpGuide } from '../composables/useHelpGuide.js'
import HelpModal from '../components/HelpModal.vue'

const router = useRouter()
const store = useGraphStore()
const helpGuide = useHelpGuide()
const searchRowRef = ref(null)

const query = ref('')
const results = ref([])
const answer = ref('')
const loading = ref(false)
const error = ref('')
const elapsed = ref(0)
const intent = ref('')
const matchedEntities = ref([])
const isFocused = ref(false)

const suggestions = ref([])
const showSuggestions = ref(false)

const searchHistory = ref(loadHistory())

const activeFilters = ref({})
const facets = computed(() => buildFacets(results.value))
const filteredResults = computed(() => applyFilters(results.value, activeFilters.value))
const hasActiveFilters = computed(() => Object.values(activeFilters.value).some(v => v))

function loadHistory() {
  try { return JSON.parse(localStorage.getItem('bird_search_history') || '[]') } catch { return [] }
}
function saveHistory() { localStorage.setItem('bird_search_history', JSON.stringify(searchHistory.value)) }

const hotQueries = ['鄱阳湖有什么濒危鸟类', '中国的湿地涉禽', '丹顶鹤的威胁', '非洲大型鸟类', '鹤科有哪些']

const INTENT_LABELS = {
  ENTITY_LOOKUP: '实体查找', RELATION_ASK: '关系查询', COMPARE: '对比', FILTER: '筛选', GENERAL: '综合',
}
const intentLabel = computed(() => INTENT_LABELS[intent.value] || '')

function typeIcon(t) {
  return ({ bird: '\uD83D\uDC26', location: '\uD83D\uDCCD', taxonomy: '\uD83D\uDCC1', habitat: '\uD83C\uDF3F', threat: '\u26A0', status: '\uD83C\uDD98' })[t] || '\u25CF'
}
function typeLabel(t) {
  return ({ bird: '鸟类', location: '地点', taxonomy: '分类', habitat: '栖息地', threat: '威胁', status: '保护等级' })[t] || t
}
function typeClass(t) {
  return ({ bird: 'type-bird', location: 'type-loc', taxonomy: 'type-tax', habitat: 'type-hab', threat: 'type-threat', status: 'type-status' })[t] || ''
}

const fetchSuggestions = useDebounceFn(async () => {
  const q = query.value.trim()
  if (q.length < 2) { suggestions.value = []; return }
  try {
    const r = await fetch(`/api/suggest?q=${encodeURIComponent(q)}`)
    const d = await r.json()
    suggestions.value = d.suggestions || []
  } catch { suggestions.value = [] }
}, 200)

function onQueryInput() {
  showSuggestions.value = true
  fetchSuggestions()
}
function onFocus() {
  isFocused.value = true
  if (query.value.length >= 2) showSuggestions.value = true
}
function onBlur() {
  isFocused.value = false
  setTimeout(() => { showSuggestions.value = false }, 200)
}
function pickSuggestion(name) {
  query.value = name
  showSuggestions.value = false
  doSearch()
}
function clearHistory() { searchHistory.value = []; saveHistory() }

async function doSearch() {
  const q = query.value.trim()
  if (!q) return
  loading.value = true; error.value = ''; answer.value = ''; results.value = []; elapsed.value = 0; intent.value = ''
  showSuggestions.value = false

  if (!searchHistory.value.includes(q)) {
    searchHistory.value.unshift(q)
    if (searchHistory.value.length > 20) searchHistory.value.pop()
    saveHistory()
  }

  try {
    const t0 = performance.now()
    const resp = await fetch(`/api/search?q=${encodeURIComponent(q)}&top=20&hops=2`)
    const data = await resp.json()
    elapsed.value = Math.round(performance.now() - t0)
    results.value = data.results || []
    intent.value = data.intent || ''
    matchedEntities.value = data.matchedEntities || []
    if (!results.value.length) error.value = '没有找到相关结果，试试换个问法'
  } catch (e) {
    error.value = '搜索服务连接失败，请确认已启动 npm run search:server'
  } finally { loading.value = false }
}

async function doAsk() {
  const q = query.value.trim()
  if (!q) return
  loading.value = true; error.value = ''; answer.value = ''
  showSuggestions.value = false

  if (!searchHistory.value.includes(q)) {
    searchHistory.value.unshift(q)
    if (searchHistory.value.length > 20) searchHistory.value.pop()
    saveHistory()
  }

  try {
    const resp = await fetch(`/api/ask?q=${encodeURIComponent(q)}`)
    const data = await resp.json()
    answer.value = data.answer || ''
    intent.value = data.intent || ''
  } catch (e) {
    error.value = '问答服务连接失败，请确认已启动 npm run search:server'
  } finally { loading.value = false }
}

function clearAll() {
  query.value = ''; results.value = []; answer.value = ''; error.value = ''
  elapsed.value = 0; intent.value = ''; suggestions.value = []
  activeFilters.value = {}
}

function goToBird(id) {
  if (!id) return
  const idStr = String(id)
  if (idStr.startsWith('loc-')) {
    router.push(`/location/${id}`)
  } else {
    router.push(`/bird/${id}`)
  }
}

function buildFacets(results) {
  if (!results.length) return []
  const types = {}
  for (const r of results) {
    const t = r.type || 'unknown'
    types[t] = (types[t] || 0) + 1
  }
  const f = []
  if (Object.keys(types).length > 1) {
    f.push({
      key: 'type',
      label: '实体类型',
      options: Object.entries(types).map(([k, v]) => ({ value: k, label: typeLabel(k), count: v })),
    })
  }
  return f
}
function toggleFilter(key, value) {
  if (activeFilters.value[key] === value) activeFilters.value[key] = ''
  else activeFilters.value[key] = value
}
function resetFilters() { activeFilters.value = {} }
function applyFilters(results, filters) {
  return results.filter(r => {
    for (const [k, v] of Object.entries(filters)) {
      if (!v) continue
      if (k === 'type' && r.type !== v) return false
    }
    return true
  })
}

onMounted(() => {
  setTimeout(() => helpGuide.checkFirstVisit('semantic-search'), 800)
})
</script>

<style scoped>
.semantic-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 4px;
  position: relative;
}
.semantic-page::before {
  content: "";
  position: absolute;
  inset: 112px auto auto 2%;
  width: 170px;
  height: 68px;
  opacity: 0.13;
  pointer-events: none;
  color: var(--accent);
  background:
    radial-gradient(circle at 12% 60%, currentColor 0 2px, transparent 2.5px),
    radial-gradient(circle at 44% 36%, currentColor 0 2px, transparent 2.5px),
    radial-gradient(circle at 80% 56%, currentColor 0 2px, transparent 2.5px),
    linear-gradient(14deg, transparent 0 20%, currentColor 20.5% 21.5%, transparent 22% 100%);
}

/* ── Hero ── */
.page-hero {
  position: relative;
  text-align: center;
  margin-bottom: 28px;
  padding: 28px 24px 26px;
  border-radius: 30px;
  border: 1px solid var(--panel-border);
  background:
    radial-gradient(circle at 18% 22%, var(--leaf-soft), transparent 30%),
    radial-gradient(circle at 84% 18%, var(--sky-soft), transparent 30%),
    linear-gradient(135deg, color-mix(in srgb, var(--card-bg) 86%, transparent), color-mix(in srgb, var(--accent) 9%, transparent));
  box-shadow: var(--shadow);
  overflow: hidden;
}
.hero-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(15,118,110,0.12), rgba(15,118,110,0.04));
  color: var(--accent);
  margin-bottom: 12px;
}
.hero-icon svg { width: 24px; height: 24px; }
.semantic-kicker {
  display: block;
  margin-bottom: 8px;
  color: var(--accent);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}
.page-title {
  font-family: "Alegreya Sans", "Source Han Sans SC", sans-serif;
  font-size: 34px;
  font-weight: 900;
  margin: 0 0 8px;
  color: var(--heading-color);
  letter-spacing: -0.02em;
}
.page-desc {
  color: var(--text-secondary);
  font-size: 15px;
  margin: 0;
  line-height: 1.6;
}

/* ── Search Box ── */
.search-box {
  margin-bottom: 24px;
  position: relative;
  padding: 22px;
  border: 1px solid var(--panel-border);
  border-radius: 24px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.32), transparent 42%),
    var(--card-bg);
  box-shadow: var(--shadow);
}
.search-row {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.search-icon {
  position: absolute;
  left: 20px;
  width: 20px;
  height: 20px;
  color: var(--text-secondary);
  pointer-events: none;
  z-index: 2;
  transition: color 0.25s ease, transform 0.25s ease;
}
.search-icon.focused {
  color: var(--accent);
  transform: scale(1.08);
}
.search-input {
  width: 100%;
  padding: 20px 60px 20px 56px;
  border: 1px solid var(--panel-border);
  border-radius: 18px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 16px;
  line-height: 1.5;
  outline: none;
  transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.5), 0 18px 48px rgba(15,118,110,0.08);
  backdrop-filter: blur(8px);
}
.search-input::placeholder { color: var(--text-secondary); opacity: 0.6; }
.search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 8px 32px rgba(15,118,110,0.1), 0 0 0 4px rgba(15,118,110,0.04);
}
.search-right {
  position: absolute;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 4px;
  z-index: 2;
}
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(15,118,110,0.15);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
.search-clear-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  background: rgba(18,48,59,0.06);
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  transition: all 0.15s;
}
.search-clear-btn:hover { background: rgba(18,48,59,0.12); color: var(--text-color); }
.search-clear-btn svg { width: 14px; height: 14px; }

/* ── Suggest Dropdown ── */
.suggest-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
  border-radius: 14px;
  box-shadow: 0 16px 48px rgba(0,0,0,0.1);
  z-index: 30;
  overflow: hidden;
  backdrop-filter: blur(16px);
  animation: dropdownIn 0.18s ease-out;
}
.suggest-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-secondary);
  padding: 12px 16px 6px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
}
.suggest-title-icon { width: 13px; height: 13px; flex-shrink: 0; }
.suggest-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  border: none;
  background: transparent;
  color: var(--text-color);
  font-size: 14px;
  cursor: pointer;
  text-align: left;
  transition: background 0.12s;
}
.suggest-item:hover { background: rgba(15,118,110,0.06); }
.suggest-type-icon { font-size: 15px; flex-shrink: 0; }
.suggest-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.suggest-type-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
  flex-shrink: 0;
  margin-left: auto;
}
.suggest-history-icon {
  width: 14px;
  height: 14px;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.suggest-clear {
  width: 100%;
  padding: 10px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  border-top: 1px solid var(--panel-border);
  transition: color 0.15s;
}
.suggest-clear:hover { color: var(--danger); }

/* ── Search Actions ── */
.search-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
}
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 12px 24px;
  border-radius: 999px;
  border: 1px solid var(--panel-border);
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}
.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.action-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.action-btn:active:not(:disabled) {
  transform: translateY(0);
}
.btn-icon { width: 15px; height: 15px; flex-shrink: 0; }
.action-btn--search {
  background: linear-gradient(135deg, rgba(15,118,110,0.1), rgba(15,118,110,0.02));
  border-color: rgba(15,118,110,0.2);
  color: var(--accent);
}
.action-btn--search:hover:not(:disabled) {
  border-color: rgba(15,118,110,0.4);
  background: linear-gradient(135deg, rgba(15,118,110,0.14), rgba(15,118,110,0.04));
}
.action-btn--ask {
  background: linear-gradient(135deg, rgba(139,92,246,0.08), rgba(139,92,246,0.02));
  border-color: rgba(139,92,246,0.25);
  color: #7c3aed;
}
.action-btn--ask:hover:not(:disabled) {
  border-color: rgba(139,92,246,0.4);
  background: linear-gradient(135deg, rgba(139,92,246,0.12), rgba(139,92,246,0.04));
}
.action-btn--clear {
  border-color: transparent;
  color: var(--text-secondary);
}
.action-btn--clear:hover:not(:disabled) {
  border-color: rgba(220,38,38,0.2);
  color: var(--danger);
}

/* ── Hot Queries ── */
.hot-section {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 6px;
}
.hot-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
  white-space: nowrap;
  padding-top: 6px;
}
.hot-label-icon { width: 14px; height: 14px; color: #ea580c; }
.hot-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.hot-tag {
  border-radius: 999px;
  box-shadow: 0 10px 24px rgba(2, 8, 23, 0.08);
}
.hot-tag {
  padding: 6px 15px;
  border-radius: 12px;
  border: 1px solid var(--panel-border);
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.18s ease;
}
.hot-tag:hover {
  border-color: var(--accent);
  background: rgba(15,118,110,0.06);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(15,118,110,0.06);
}

/* ── Error ── */
.error-msg {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 20px;
  border-radius: 16px;
  background: rgba(220,38,38,0.05);
  border: 1px solid rgba(220,38,38,0.15);
  color: var(--danger);
  font-size: 13px;
  margin-bottom: 20px;
}
.error-icon { width: 18px; height: 18px; flex-shrink: 0; }

/* ── Answer Card ── */
.answer-card {
  padding: 22px 26px;
  border-radius: 20px;
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.03);
  animation: cardIn 0.35s ease-out;
}
.answer-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}
.answer-ai-icon {
  width: 20px;
  height: 20px;
  color: #7c3aed;
}
.answer-title {
  font-size: 13px;
  color: #7c3aed;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
}
.answer-text {
  font-size: 15px;
  line-height: 1.85;
  color: var(--text-color);
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

/* ── Results Layout ── */
.results-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

/* ── Facet Sidebar ── */
.facet-sidebar {
  width: 190px;
  flex-shrink: 0;
  padding: 16px;
  border-radius: 18px;
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
  position: sticky;
  top: 20px;
}
.facet-header {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 16px;
}
.facet-header-icon { width: 15px; height: 15px; color: var(--text-secondary); }
.facet-title {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
}
.facet-group { margin-bottom: 16px; }
.facet-label {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.facet-count-total {
  font-size: 10px;
  font-weight: 400;
  color: var(--text-secondary);
  background: rgba(18,48,59,0.04);
  padding: 1px 6px;
  border-radius: 999px;
}
.facet-option {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 6px 10px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--text-color);
  font-size: 12px;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
  margin-bottom: 2px;
}
.facet-option:hover { background: rgba(15,118,110,0.04); }
.facet-option.active {
  background: rgba(15,118,110,0.08);
  color: var(--accent);
  font-weight: 600;
}
.facet-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.facet-dot.type-bird { background: #0f766e; }
.facet-dot.type-loc { background: #2563eb; }
.facet-dot.type-tax { background: #7c3aed; }
.facet-dot.type-hab { background: #16a34a; }
.facet-dot.type-threat { background: #dc2626; }
.facet-dot.type-status { background: #d97706; }
.facet-opt-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.facet-count {
  font-size: 10px;
  color: var(--text-secondary);
  font-weight: 400;
}
.facet-option.active .facet-count { color: var(--accent); }
.facet-reset {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 6px;
  width: 100%;
  padding: 8px;
  border: 1px solid var(--panel-border);
  border-radius: 10px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
  justify-content: center;
}
.facet-reset:hover {
  border-color: rgba(220,38,38,0.3);
  color: var(--danger);
}
.facet-reset-icon { width: 13px; height: 13px; }

/* ── Results Main ── */
.results-main { flex: 1; min-width: 0; }
.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.results-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.results-title {
  font-size: 15px;
  color: var(--heading-color);
  margin: 0;
  font-weight: 600;
}
.results-meta-badge {
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(18,48,59,0.04);
  padding: 3px 10px;
  border-radius: 999px;
}
.intent-badge {
  font-size: 11px;
  padding: 3px 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(15,118,110,0.12), rgba(15,118,110,0.04));
  color: var(--accent);
  font-weight: 600;
  border: 1px solid rgba(15,118,110,0.15);
}

/* ── Result Cards ── */
.result-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.result-card {
  padding: 16px 20px;
  border-radius: 16px;
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  animation: cardIn 0.35s ease-out both;
  position: relative;
  overflow: hidden;
}
.result-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: transparent;
  border-radius: 0 2px 2px 0;
  transition: background 0.25s;
}
.result-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(15,118,110,0.08);
}
.result-card:hover::before { background: var(--accent); }
.result-card:active { transform: translateY(0); }

.result-card.is-anchor {
  border-color: rgba(15,118,110,0.22);
  background: linear-gradient(135deg, rgba(15,118,110,0.04), var(--card-bg));
}
.result-card.is-anchor::before { background: rgba(15,118,110,0.4); }
.result-card.is-shared {
  border-color: rgba(139,92,246,0.25);
  background: linear-gradient(135deg, rgba(139,92,246,0.03), var(--card-bg));
}
.result-card.is-shared::before { background: #7c3aed; }

.result-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
}
.result-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  flex: 1;
}
.result-name {
  font-weight: 700;
  color: var(--heading-color);
  font-size: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.type-icon { font-size: 16px; flex-shrink: 0; line-height: 1; }
.shared-badge {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(139,92,246,0.1);
  color: #7c3aed;
  font-weight: 600;
  flex-shrink: 0;
}
.result-score-row { flex-shrink: 0; }
.result-score {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(15,118,110,0.06);
  min-width: 60px;
}
.score-bar {
  display: none;
}
.score-text { white-space: nowrap; }

.result-meta {
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  margin-bottom: 2px;
}
.type-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
}
.type-bird { background: rgba(15,118,110,0.1); color: #0f766e; }
.type-loc { background: rgba(59,130,246,0.1); color: #2563eb; }
.type-tax { background: rgba(139,92,246,0.1); color: #7c3aed; }
.type-hab { background: rgba(34,197,94,0.1); color: #16a34a; }
.type-threat { background: rgba(239,68,68,0.1); color: #dc2626; }
.type-status { background: rgba(245,158,11,0.1); color: #d97706; }
.meta-sep { color: var(--text-secondary); opacity: 0.5; }
.meta-name { font-style: italic; opacity: 0.8; }
.meta-latin {
  font-style: italic;
  opacity: 0.65;
  font-size: 11px;
}
.meta-latin::before { content: '· '; }
.degree-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: var(--accent);
  background: rgba(15,118,110,0.06);
  padding: 2px 8px;
  border-radius: 999px;
  margin-left: auto;
}
.degree-icon { width: 12px; height: 12px; }

/* ── Result Path ── */
.result-path {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--panel-border);
  font-size: 12px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
}
.path-icon { width: 14px; height: 14px; color: var(--accent); flex-shrink: 0; }
.path-via {
  font-weight: 500;
  color: var(--text-color);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.path-chevron {
  width: 12px;
  height: 12px;
  color: var(--accent);
  flex-shrink: 0;
  opacity: 0.6;
}
.path-relation {
  background: rgba(15,118,110,0.08);
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  color: var(--accent);
  font-weight: 500;
  white-space: nowrap;
}
.path-target {
  font-weight: 600;
  color: var(--heading-color);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.hop-badge {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(139,92,246,0.1);
  color: #7c3aed;
  font-weight: 600;
}
.result-shared {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed rgba(139,92,246,0.12);
  font-size: 11px;
  color: #7c3aed;
  display: flex;
  align-items: center;
  gap: 4px;
}
.shared-icon { width: 13px; height: 13px; flex-shrink: 0; }

/* ── Empty State ── */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
  animation: pageIn 0.4s ease-out;
}
.empty-icon {
  width: 64px;
  height: 64px;
  color: var(--text-secondary);
  opacity: 0.4;
  margin-bottom: 16px;
}
.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
  margin: 0 0 8px;
}
.empty-desc {
  font-size: 14px;
  margin: 0;
  max-width: 360px;
  margin: 0 auto;
  line-height: 1.6;
}

/* ── Loading Skeleton ── */
.loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: 10px;
  animation: pageIn 0.3s ease-out;
}
.skeleton-card {
  padding: 18px 20px;
  border-radius: 16px;
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
}
.skeleton-line {
  height: 14px;
  border-radius: 7px;
  background: linear-gradient(90deg, rgba(18,48,59,0.04), rgba(18,48,59,0.08), rgba(18,48,59,0.04));
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  margin-bottom: 8px;
}
.skeleton-line--title { width: 40%; height: 16px; }
.skeleton-line--meta  { width: 65%; height: 12px; }
.skeleton-line--path  { width: 80%; height: 12px; margin-bottom: 0; }

/* ── Keyframes ── */
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pageIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@keyframes cardIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes dropdownIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .semantic-page { padding: 0; }
  .page-hero { margin-bottom: 20px; }
  .page-title { font-size: 26px; }
  .page-desc { font-size: 14px; }

  .search-input {
    padding: 16px 48px 16px 46px;
    font-size: 15px;
    border-radius: 16px;
  }
  .search-icon { left: 16px; }
  .search-actions { gap: 6px; }
  .action-btn {
    padding: 9px 14px;
    font-size: 12px;
    border-radius: 12px;
  }
  .action-btn .btn-icon { width: 14px; height: 14px; }

  .hot-section { flex-direction: column; gap: 8px; }
  .hot-label { padding-top: 0; }

  .results-layout { flex-direction: column; }
  .facet-sidebar {
    width: 100%;
    position: static;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    padding: 14px;
    border-radius: 14px;
  }
  .facet-header { width: 100%; margin-bottom: 0; }
  .facet-group {
    margin-bottom: 0;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .facet-label { margin-bottom: 0; margin-right: 4px; }
  .facet-option { width: auto; margin-bottom: 0; }
  .facet-reset { width: auto; margin-top: 0; }

  .result-card { padding: 14px 16px; border-radius: 14px; }
  .result-card-header { flex-wrap: wrap; }
  .answer-card { padding: 16px 18px; border-radius: 16px; }
}

@media (max-width: 480px) {
  .page-title { font-size: 22px; }
  .hero-icon { width: 40px; height: 40px; border-radius: 12px; }
  .hero-icon svg { width: 20px; height: 20px; }
  .search-input { padding: 14px 44px 14px 40px; font-size: 14px; }
  .search-icon { left: 14px; width: 17px; height: 17px; }
  .search-clear-btn { width: 20px; height: 20px; }
  .search-clear-btn svg { width: 12px; height: 12px; }
  .action-btn {
    padding: 8px 12px;
    font-size: 11px;
    gap: 4px;
  }
  .action-btn .btn-icon { width: 13px; height: 13px; }
  .hot-tag { font-size: 12px; padding: 5px 12px; }
}

.help-float-btn {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 100;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.9), rgba(124, 58, 237, 0.9));
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.35);
  backdrop-filter: blur(8px);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.help-float-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 24px rgba(139, 92, 246, 0.5);
  border-color: rgba(139, 92, 246, 0.5);
}
.help-float-btn svg {
  width: 22px;
  height: 22px;
}
</style>
