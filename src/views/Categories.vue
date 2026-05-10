<template>
  <div class="categories-page">
    <div class="categories-search">
      <div class="search-wrapper">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
        </svg>
        <input v-model="searchQuery" type="text" class="search-input" placeholder="搜索鸟类名称、学名或关系关键词…" />
      </div>
    </div>
    <div class="tabs-bar">
      <button class="tab-btn" :class="{ 'tab-active': activeTab === 'birds' }" @click="activeTab = 'birds'">鸟类一览</button>
      <button class="tab-btn" :class="{ 'tab-active': activeTab === 'relations' }" @click="activeTab = 'relations'">关系一览</button>
    </div>
    <div v-if="activeTab === 'birds'" class="bird-grid">
      <div v-for="bird in filteredBirds" :key="bird.id" class="bird-card" @click="goToBird(bird)">
        <div class="bird-card-img">
          <img :src="`https://picsum.photos/seed/${bird.id}/300/200`" :alt="bird.name" loading="lazy" />
          <span v-if="bird.status" class="bird-card-status" :class="statusClass(bird.status)">{{ bird.status }}</span>
        </div>
        <div class="bird-card-body">
          <h3 class="bird-card-name">{{ bird.name }}</h3>
          <p class="bird-card-english">{{ bird.englishName }}</p>
        </div>
      </div>
      <div v-if="!filteredBirds.length" class="empty-state">没有匹配的鸟类</div>
    </div>
    <div v-if="activeTab === 'relations'" class="relations-list">
      <div v-for="(group, idx) in filteredRelations" :key="idx" class="relation-item" :class="{ 'relation-highlight': isHighlighted(group) }">
        <span class="relation-source" @click="goToBirdById(group.source.id)">{{ group.source.name }}</span>
        <span class="relation-arrow">
          <span class="relation-label">{{ group.link.label || group.link.relation }}</span>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
          </svg>
        </span>
        <span class="relation-target" @click="goToBirdById(group.target.id)">{{ group.target.name }}</span>
      </div>
      <div v-if="!filteredRelations.length" class="empty-state">没有匹配的关系</div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGraphStore } from '../stores/graphStore.js'

const router = useRouter()
const store = useGraphStore()

const searchQuery = ref('')
const activeTab = ref('birds')
const searchTerm = computed(() => searchQuery.value.trim().toLowerCase())

const allRelations = computed(() => {
  const results = []; const seen = new Set()
  store.links.forEach(link => {
    const source = store.getNodeById(link.source)
    const target = store.getNodeById(link.target)
    if (!source || !target) return
    if (source.type !== 'bird' && target.type !== 'bird') return
    const key = `${source.id}->${target.id}->${link.relation}`
    if (seen.has(key)) return
    seen.add(key)
    results.push({ source, target, link })
  })
  return results
})

const filteredBirds = computed(() => {
  const q = searchTerm.value
  if (!q) return store.birdNodes
  return store.birdNodes.filter(bird => {
    const fields = [bird.name, bird.englishName, bird.latinName].filter(Boolean)
    return fields.some(f => f.toLowerCase().includes(q))
  })
})

const filteredRelations = computed(() => {
  const q = searchTerm.value
  if (!q) return allRelations.value
  return allRelations.value.filter(({ source, target, link }) => {
    const ms = [source.name, source.englishName].filter(Boolean).some(f => f.toLowerCase().includes(q))
    const mt = [target.name, target.englishName].filter(Boolean).some(f => f.toLowerCase().includes(q))
    const mr = (link.label || link.relation || '').toLowerCase().includes(q)
    return ms || mt || mr
  })
})

const highlightedKeys = computed(() => {
  const q = searchTerm.value
  if (!q) return new Set()
  const set = new Set()
  filteredRelations.value.forEach(({ source, target, link }) => {
    const key = `${source.id}->${target.id}->${link.relation}`
    if ((link.label || link.relation || '').toLowerCase().includes(q)) set.add(key)
  })
  return set
})

function isHighlighted(group) {
  return highlightedKeys.value.has(`${group.source.id}->${group.target.id}->${group.link.relation}`)
}
function statusClass(status) {
  return { CR: 'status-cr', EN: 'status-en', VU: 'status-vu', NT: 'status-nt', LC: 'status-lc' }[status] || 'status-lc'
}
function goToBird(bird) { router.push(`/bird/${bird.id}`) }
function goToBirdById(id) { router.push(`/bird/${id}`) }

onMounted(async () => {
  if (!store.loaded) await store.loadData()
})
</script>

<style scoped>
.categories-page { display: flex; flex-direction: column; gap: 18px; }
.categories-search { display: flex; justify-content: center; }
.search-wrapper { position: relative; width: 100%; max-width: 600px; }
.search-icon { position: absolute; left: 18px; top: 50%; transform: translateY(-50%); width: 20px; height: 20px; color: rgba(18, 48, 59, 0.4); pointer-events: none; }
.search-input { width: 100%; padding: 14px 20px 14px 52px; border: 2px solid rgba(15, 118, 110, 0.2); border-radius: 999px; background: rgba(255, 255, 255, 0.9); font-size: 15px; outline: none; transition: all 0.3s ease; box-shadow: 0 4px 20px rgba(31, 64, 76, 0.08); }
.search-input:focus { border-color: #0f766e; box-shadow: 0 8px 32px rgba(15, 118, 110, 0.15); }
.tabs-bar { display: flex; gap: 4px; padding: 4px; border-radius: 999px; background: rgba(255, 255, 255, 0.7); border: 1px solid rgba(18, 48, 59, 0.08); width: fit-content; }
.tab-btn { padding: 10px 24px; border: none; border-radius: 999px; background: transparent; color: var(--text-secondary); font-size: 14px; cursor: pointer; transition: all 0.2s ease; }
.tab-btn:hover { background: rgba(15, 118, 110, 0.08); }
.tab-active { background: #0f766e !important; color: #fff !important; font-weight: 600; }
.bird-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 18px; }
.bird-card { border-radius: 20px; overflow: hidden; background: var(--card-bg); border: 1px solid var(--panel-border); box-shadow: 0 10px 30px rgba(31, 64, 76, 0.08); cursor: pointer; transition: all 0.25s ease; }
.bird-card:hover { transform: translateY(-4px); box-shadow: var(--shadow); }
.bird-card-img { position: relative; width: 100%; height: 160px; overflow: hidden; background: #e2e8f0; }
.bird-card-img img { width: 100%; height: 100%; object-fit: cover; }
.bird-card-status { position: absolute; top: 10px; right: 10px; padding: 4px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; color: #fff; }
.status-cr { background: #dc2626; } .status-en { background: #b45309; } .status-vu { background: #ea580c; } .status-nt { background: #ca8a04; } .status-lc { background: #16a34a; }
.bird-card-body { padding: 14px 16px; }
.bird-card-name { margin: 0; font-size: 16px; color: var(--heading-color); }
.bird-card-english { margin: 4px 0 0; font-size: 12px; color: var(--text-secondary); }
.relations-list { display: flex; flex-direction: column; gap: 8px; }
.relation-item { display: flex; align-items: center; gap: 12px; padding: 14px 18px; border-radius: 16px; background: var(--card-bg); border: 1px solid var(--panel-border); transition: all 0.2s ease; }
.relation-item:hover { background: var(--card-bg); box-shadow: 0 4px 12px rgba(31, 64, 76, 0.08); }
.relation-highlight { background: rgba(15, 118, 110, 0.08) !important; border-color: rgba(15, 118, 110, 0.25); }
.relation-source, .relation-target { font-weight: 600; color: var(--accent); cursor: pointer; padding: 4px 8px; border-radius: 8px; transition: background 0.15s ease; }
.relation-source:hover, .relation-target:hover { background: rgba(15, 118, 110, 0.1); }
.relation-arrow { display: flex; align-items: center; gap: 6px; color: var(--text-secondary); font-size: 13px; flex-shrink: 0; }
.relation-label { font-size: 12px; color: var(--text-secondary); }
.empty-state { padding: 40px; text-align: center; color: var(--text-secondary); font-size: 15px; }
@media (max-width: 720px) {
  .bird-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; }
  .bird-card-img { height: 120px; }
}
</style>
