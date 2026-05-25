<template>
  <div class="semantic-page">
    <div class="page-hero">
      <h2 class="page-title">语义搜索</h2>
      <p class="page-desc">用自然语言提问，AI 结合知识图谱关系给出精准答案</p>
    </div>

    <div class="search-box">
      <!-- #18 自动补全 -->
      <div class="search-row" ref="searchRowRef">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
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
          @focus="showHistory = true"
          @blur="hideHistory"
        />
        <span v-if="loading" class="spinner"></span>

        <div v-if="(suggestions.length || searchHistory.length) && showSuggestions" class="suggest-dropdown">
          <template v-if="suggestions.length">
            <div class="suggest-section-title">搜索建议</div>
            <button v-for="s in suggestions" :key="s.name" class="suggest-item" @mousedown.prevent="pickSuggestion(s.name)">
              <span class="suggest-type-icon">{{ typeIcon(s.type) }}</span>
              <span>{{ s.name }}</span>
              <span class="suggest-type-tag" :class="typeClass(s.type)">{{ typeLabel(s.type) }}</span>
            </button>
          </template>
          <template v-if="searchHistory.length && !suggestions.length">
            <div class="suggest-section-title">搜索历史</div>
            <button v-for="item in searchHistory" :key="item" class="suggest-item" @mousedown.prevent="pickSuggestion(item)">
              <svg class="suggest-history-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              <span>{{ item }}</span>
            </button>
          </template>
          <button v-if="searchHistory.length" class="suggest-clear" @mousedown.prevent="clearHistory">清除搜索历史</button>
        </div>
      </div>

      <div class="search-actions">
        <button class="action-btn action-btn--search" @click="doSearch">搜索</button>
        <button class="action-btn action-btn--ask" @click="doAsk">智能问答</button>
        <button class="action-btn action-btn--clear" @click="clearAll">清空</button>
      </div>

      <!-- #3 热门推荐 -->
      <div v-if="!results.length && !loading && !answer && !error" class="hot-tags">
        <span class="hot-tags-label">热门搜索：</span>
        <button v-for="hint in hotQueries" :key="hint" class="hot-tag" @click="query = hint; doSearch()">{{ hint }}</button>
      </div>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <!-- 智能问答结果 -->
    <div v-if="answer" class="answer-card">
      <h3 class="answer-title">AI 回答</h3>
      <p class="answer-text">{{ answer }}</p>
    </div>

    <div class="results-layout" v-if="results.length">
      <!-- #6 分面过滤侧栏 -->
      <aside class="facet-sidebar" v-if="facets.length">
        <h4 class="facet-title">筛选</h4>
        <div v-for="facet in facets" :key="facet.key" class="facet-group">
          <div class="facet-label">{{ facet.label }}</div>
          <button
            v-for="opt in facet.options"
            :key="opt.value"
            class="facet-option"
            :class="{ active: activeFilters[facet.key] === opt.value }"
            @click="toggleFilter(facet.key, opt.value)"
          >
            {{ opt.label }}
            <span class="facet-count">{{ opt.count }}</span>
          </button>
        </div>
        <button v-if="hasActiveFilters" class="facet-reset" @click="resetFilters">重置筛选</button>
      </aside>

      <div class="results-main">
        <div class="results-header">
          <h3 class="results-title">搜索结果（{{ filteredResults.length }} 条，耗时 {{ elapsed }}ms）</h3>
          <span v-if="intentLabel" class="intent-badge">{{ intentLabel }}</span>
        </div>

        <div class="result-cards">
          <div
            v-for="item in filteredResults"
            :key="item.id + (item.via || '')"
            class="result-card"
            :class="{ 'is-anchor': item.isAnchor, 'is-shared': item.shared }"
            @click="goToBird(item.id)"
          >
            <div class="result-card-header">
              <span class="result-name">
                <span class="type-icon">{{ typeIcon(item.type) }}</span>
                {{ item.name }}
              </span>
              <span v-if="item.score != null" class="result-score">{{ (item.score * 100).toFixed(0) }}%</span>
            </div>

            <div class="result-meta">
              <span class="type-tag" :class="typeClass(item.type)">{{ typeLabel(item.type) }}</span>
              <template v-if="item.englishName">{{ item.englishName }}</template>
              <template v-if="item.latinName"> · {{ item.latinName }}</template>
              <span v-if="item.degree > 3" class="degree-badge" title="关联实体数">+{{ item.degree }} 关联</span>
            </div>

            <!-- #12 关系路径 -->
            <div v-if="item.relation" class="result-path">
              <svg class="path-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              <span class="path-via">{{ item.viaName }}</span>
              <span class="path-arrow">→</span>
              <span class="path-relation">{{ item.relationLabel }}</span>
              <span class="path-arrow">→</span>
              <span class="path-target">{{ item.name }}</span>
              <span v-if="item.hop === 2" class="hop-badge">2跳</span>
            </div>

            <div v-if="item.shared" class="result-shared">共享于 {{ item.sharedBetween?.join('、') }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'

const router = useRouter()
const searchRowRef = ref(null)

const query = ref('')
const results = ref([])
const answer = ref('')
const loading = ref(false)
const error = ref('')
const elapsed = ref(0)
const intent = ref('')
const matchedEntities = ref([])

// #18 自动补全
const suggestions = ref([])
const showSuggestions = ref(false)
const showHistory = ref(false)

// #3 搜索历史
const searchHistory = ref(loadHistory())

// #6 分面
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

function typeIcon(t) { return ({ bird: '\uD83D\uDC26', location: '\uD83D\uDCCD', taxonomy: '\uD83D\uDCC1', habitat: '\uD83C\uDF3F', threat: '\u26A0', status: '\uD83C\uDD98' })[t] || '\u25CF' }
function typeLabel(t) { return ({ bird: '鸟', location: '地点', taxonomy: '分类', habitat: '栖息地', threat: '威胁', status: '保护等级' })[t] || t }
function typeClass(t) { return ({ bird: 'type-bird', location: 'type-loc', taxonomy: 'type-tax', habitat: 'type-hab', threat: 'type-threat', status: 'type-status' })[t] || '' }

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
function pickSuggestion(name) {
  query.value = name
  showSuggestions.value = false
  doSearch()
}
function hideHistory() { setTimeout(() => { showSuggestions.value = false; showHistory.value = false }, 200) }
function clearHistory() { searchHistory.value = []; saveHistory() }

async function doSearch() {
  const q = query.value.trim()
  if (!q) return
  loading.value = true; error.value = ''; answer.value = ''; results.value = []; elapsed.value = 0; intent.value = ''

  // save history
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
  } catch (e) { error.value = '搜索服务连接失败，请确认已启动 npm run search:server' }
  finally { loading.value = false }
}

async function doAsk() {
  const q = query.value.trim()
  if (!q) return
  loading.value = true; error.value = ''; answer.value = ''
  try {
    const resp = await fetch(`/api/ask?q=${encodeURIComponent(q)}`)
    const data = await resp.json()
    answer.value = data.answer || ''
    intent.value = data.intent || ''
  } catch (e) { error.value = '问答服务连接失败' }
  finally { loading.value = false }
}

function clearAll() {
  query.value = ''; results.value = []; answer.value = ''; error.value = ''
  elapsed.value = 0; intent.value = ''; suggestions.value = []
  activeFilters.value = {}
}

function goToBird(id) { if (id) router.push(`/bird/${id}`) }

// #6 分面逻辑
function buildFacets(results) {
  if (!results.length) return []
  const types = {}, statuses = {}
  for (const r of results) {
    const t = r.type || 'unknown'
    types[t] = (types[t] || 0) + 1
    if (r.statusFilter) statuses[r.statusFilter] = (statuses[r.statusFilter] || 0) + 1
  }
  const f = []
  if (Object.keys(types).length > 1) f.push({ key: 'type', label: '实体类型', options: Object.entries(types).map(([k, v]) => ({ value: k, label: typeLabel(k), count: v })) })
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
</script>

<style scoped>
.semantic-page { max-width: 1100px; margin: 0 auto; animation: pageIn 0.4s ease-out; }
.page-hero { text-align: center; margin-bottom: 24px; }
.page-title { font-family: "Alegreya", "Source Han Serif SC", serif; font-size: 32px; margin: 0 0 6px; color: var(--heading-color); }
.page-desc { color: var(--text-secondary); font-size: 15px; margin: 0; }

.search-box { margin-bottom: 20px; position: relative; }
.search-row { position: relative; display: flex; align-items: center; margin-bottom: 10px; }
.search-icon { position: absolute; left: 18px; width: 20px; height: 20px; color: rgba(18,48,59,0.4); pointer-events: none; z-index: 2; }
.search-input { width: 100%; padding: 16px 50px; border: 2px solid rgba(15,118,110,0.2); border-radius: 999px; background: var(--card-bg); color: var(--text-color); font-size: 16px; outline: none; transition: all 0.28s ease; }
.search-input:focus { border-color: var(--accent); box-shadow: 0 8px 32px rgba(15,118,110,0.14); }
.spinner { position: absolute; right: 18px; width: 18px; height: 18px; border: 2px solid rgba(15,118,110,0.2); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.6s linear infinite; z-index: 2; }

/* #18 autocomplete dropdown */
.suggest-dropdown { position: absolute; top: 100%; left: 0; right: 0; background: var(--card-bg); border: 1px solid var(--panel-border); border-radius: 16px; box-shadow: 0 12px 40px rgba(0,0,0,0.1); z-index: 30; margin-top: 6px; overflow: hidden; }
.suggest-section-title { font-size: 11px; color: var(--text-secondary); padding: 10px 16px 4px; text-transform: uppercase; letter-spacing: 0.06em; }
.suggest-item { display: flex; align-items: center; gap: 8px; width: 100%; padding: 10px 16px; border: none; background: transparent; color: var(--text-color); font-size: 14px; cursor: pointer; text-align: left; transition: background 0.12s; }
.suggest-item:hover { background: rgba(15,118,110,0.06); }
.suggest-type-icon { font-size: 13px; flex-shrink: 0; }
.suggest-type-tag { font-size: 10px; padding: 1px 6px; border-radius: 999px; font-weight: 600; margin-left: auto; flex-shrink: 0; }
.suggest-history-icon { width: 14px; height: 14px; color: var(--text-secondary); flex-shrink: 0; }
.suggest-clear { width: 100%; padding: 8px; border: none; background: transparent; color: var(--text-secondary); font-size: 12px; cursor: pointer; border-top: 1px solid rgba(0,0,0,0.05); }
.suggest-clear:hover { color: #dc2626; }

.search-actions { display: flex; gap: 8px; }
.action-btn { padding: 8px 20px; border-radius: 999px; border: 1px solid rgba(15,118,110,0.2); background: var(--card-bg); color: var(--text-color); font-size: 13px; cursor: pointer; transition: all 0.22s ease; }
.action-btn:hover { border-color: var(--accent); background: rgba(15,118,110,0.06); }
.action-btn--search { background: linear-gradient(135deg, rgba(15,118,110,0.08), rgba(15,118,110,0.02)); }
.action-btn--ask { background: linear-gradient(135deg, rgba(59,130,246,0.08), rgba(59,130,246,0.02)); border-color: rgba(59,130,246,0.25); }
.action-btn--clear { border-color: rgba(220,38,38,0.15); color: var(--text-secondary); }

/* #3 hot tags */
.hot-tags { display: flex; align-items: center; gap: 6px; margin-top: 12px; flex-wrap: wrap; }
.hot-tags-label { font-size: 12px; color: var(--text-secondary); }
.hot-tag { padding: 5px 14px; border-radius: 999px; border: 1px solid rgba(15,118,110,0.12); background: transparent; color: var(--text-color); font-size: 12px; cursor: pointer; transition: all 0.15s; }
.hot-tag:hover { border-color: var(--accent); background: rgba(15,118,110,0.06); }

.error-msg { padding: 12px 20px; border-radius: 16px; background: rgba(220,38,38,0.06); border: 1px solid rgba(220,38,38,0.2); color: #b91c1c; font-size: 13px; margin-bottom: 20px; }
.answer-card { padding: 20px 24px; border-radius: 20px; background: var(--card-bg); border: 1px solid var(--panel-border); margin-bottom: 24px; }
.answer-title { font-size: 12px; color: var(--accent); margin: 0 0 10px; text-transform: uppercase; letter-spacing: 0.06em; }
.answer-text { font-size: 15px; line-height: 1.8; color: var(--text-color); margin: 0; }

/* results layout */
.results-layout { display: flex; gap: 20px; align-items: flex-start; }

/* #6 facet sidebar */
.facet-sidebar { width: 180px; flex-shrink: 0; padding: 16px; border-radius: 16px; background: var(--card-bg); border: 1px solid var(--panel-border); }
.facet-title { font-size: 12px; color: var(--text-secondary); margin: 0 0 12px; text-transform: uppercase; letter-spacing: 0.06em; }
.facet-group { margin-bottom: 14px; }
.facet-label { font-size: 11px; color: var(--text-secondary); margin-bottom: 4px; }
.facet-option { display: flex; justify-content: space-between; width: 100%; padding: 4px 8px; border: none; border-radius: 8px; background: transparent; color: var(--text-color); font-size: 12px; cursor: pointer; text-align: left; transition: background 0.12s; }
.facet-option:hover { background: rgba(15,118,110,0.04); }
.facet-option.active { background: rgba(15,118,110,0.08); color: #0f766e; font-weight: 600; }
.facet-count { font-size: 10px; color: var(--text-secondary); }
.facet-reset { margin-top: 8px; width: 100%; padding: 6px; border: none; border-radius: 8px; background: transparent; color: var(--text-secondary); font-size: 11px; cursor: pointer; }
.facet-reset:hover { color: #dc2626; }

.results-main { flex: 1; min-width: 0; }
.results-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.results-title { font-size: 14px; color: var(--text-secondary); margin: 0; font-weight: 500; }
.intent-badge { font-size: 11px; padding: 2px 8px; border-radius: 999px; background: rgba(15,118,110,0.1); color: #0f766e; font-weight: 600; }

.result-cards { display: flex; flex-direction: column; gap: 8px; }
.result-card { padding: 14px 18px; border-radius: 14px; background: var(--card-bg); border: 1px solid var(--panel-border); cursor: pointer; transition: all 0.2s ease; }
.result-card:hover { border-color: var(--accent); transform: translateY(-1px); box-shadow: 0 6px 20px rgba(15,118,110,0.06); }
.result-card.is-anchor { border-color: rgba(15,118,110,0.28); background: linear-gradient(135deg, rgba(15,118,110,0.04), var(--card-bg)); }
.result-card.is-shared { border-color: rgba(139,92,246,0.3); background: rgba(139,92,246,0.03); }
.result-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px; }
.result-name { font-weight: 700; color: var(--heading-color); font-size: 14px; display: flex; align-items: center; gap: 5px; }
.type-icon { font-size: 13px; }
.result-score { font-size: 11px; font-weight: 600; color: var(--accent); background: rgba(15,118,110,0.08); padding: 1px 6px; border-radius: 999px; }
.result-meta { font-size: 11px; color: var(--text-secondary); display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
.type-tag { font-size: 10px; padding: 1px 6px; border-radius: 999px; font-weight: 600; }
.type-bird { background: rgba(15,118,110,0.1); color: #0f766e; }
.type-loc { background: rgba(59,130,246,0.1); color: #2563eb; }
.type-tax { background: rgba(139,92,246,0.1); color: #7c3aed; }
.type-hab { background: rgba(34,197,94,0.1); color: #16a34a; }
.type-threat { background: rgba(239,68,68,0.1); color: #dc2626; }
.type-status { background: rgba(245,158,11,0.1); color: #d97706; }
.degree-badge { font-size: 10px; color: var(--accent); background: rgba(15,118,110,0.06); padding: 1px 5px; border-radius: 999px; margin-left: auto; }

.result-path { margin-top: 6px; padding-top: 6px; border-top: 1px dashed rgba(15,118,110,0.08); font-size: 12px; color: var(--text-secondary); display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.path-icon { width: 12px; height: 12px; color: var(--accent); flex-shrink: 0; }
.path-via { font-weight: 500; color: var(--text-color); }
.path-arrow { color: var(--accent); font-size: 10px; }
.path-relation { background: rgba(15,118,110,0.06); padding: 1px 6px; border-radius: 999px; font-size: 11px; color: #0f766e; }
.path-target { font-weight: 600; color: var(--heading-color); }
.hop-badge { font-size: 10px; padding: 0 4px; border-radius: 999px; background: rgba(139,92,246,0.1); color: #7c3aed; }
.result-shared { margin-top: 4px; font-size: 11px; color: #7c3aed; }

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes pageIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 768px) {
  .results-layout { flex-direction: column; }
  .facet-sidebar { width: 100%; display: flex; flex-wrap: wrap; gap: 8px; padding: 10px; }
  .facet-group { margin-bottom: 0; margin-right: 12px; }
}
</style>
