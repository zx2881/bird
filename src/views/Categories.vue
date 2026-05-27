<template>
  <div class="categories-page">
    <div class="cat-hero">
      <h2 class="page-title">知识图谱浏览器</h2>
      <p class="page-desc">按分类层级、物种卡片或关系一览浏览全部知识图谱实体</p>
    </div>

    <div class="cat-search-bar">
      <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
      </svg>
      <input
        v-model="searchQuery"
        type="text"
        class="search-input"
        placeholder="搜索鸟类、地点、分类… 支持中文名、英文名、学名"
        @input="onSearchInput"
      />
      <span v-if="searchQuery" class="search-count">{{ totalResultCount }} 个结果</span>
    </div>

    <div class="tabs-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ 'tab-active': activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
        <span v-if="tab.count != null" class="tab-count">{{ tab.count }}</span>
      </button>
    </div>

    <div v-if="!store.loaded" class="empty-state">正在加载数据…</div>

    <template v-else>
      <Transition name="tab-fade" mode="out-in">
        <div v-if="activeTab === 'birds'" key="birds" class="bird-grid">
          <div v-for="bird in filteredBirds" :key="bird.id" class="bird-card scroll-reveal visible" @click="goToBird(bird)">
            <div class="bird-card-img">
              <div class="bird-card-img-bg" :style="{ background: statusGradient(bird.status) }"></div>
              <img :src="bird.imageUrl || `https://picsum.photos/seed/${bird.id}/300/200`" :alt="bird.name" loading="lazy" @error="onImgError" />
              <div class="bird-card-img-overlay"></div>
              <span v-if="bird.status" class="bird-card-status" :class="statusClass(bird.status)">
                <span class="status-dot"></span>{{ statusLabel(bird.status) }}
              </span>
            </div>
            <div class="bird-card-body">
              <h3 class="bird-card-name">{{ bird.name }}</h3>
              <p class="bird-card-english">{{ bird.englishName || bird.latinName || '' }}</p>
              <div class="bird-card-meta">
                <span v-if="bird.locations?.length" class="bird-card-meta-item">
                  <svg viewBox="0 0 16 16" width="10" height="10" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 1C5.2 1 3 3.2 3 6c0 3.5 5 8 5 8s5-4.5 5-8c0-2.8-2.2-5-5-5z"/><circle cx="8" cy="6" r="1.5"/></svg>
                  {{ bird.locations.length }} 分布
                </span>
                <span v-if="bird.habitats?.length" class="bird-card-meta-item">
                  <svg viewBox="0 0 16 16" width="10" height="10" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 14h12M4 14V8a4 4 0 018 0v6"/></svg>
                  {{ bird.habitats.length }} 栖息地
                </span>
                <span class="bird-card-meta-item">
                  <svg viewBox="0 0 16 16" width="10" height="10" fill="none" stroke="currentColor" stroke-width="2"><circle cx="8" cy="4" r="2"/><path d="M4 12c0-2.2 1.8-4 4-4s4 1.8 4 4"/></svg>
                  {{ store.getNodeDegree(bird.id) }} 关联
                </span>
              </div>
            </div>
          </div>
          <div v-if="!filteredBirds.length" class="empty-state">没有匹配的鸟类</div>
        </div>

        <div v-else-if="activeTab === 'locations'" key="locations" class="location-grid">
          <div v-for="loc in filteredLocations" :key="loc.id" class="location-card scroll-reveal visible" @click="goToLocation(loc)">
            <div class="location-card-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                <circle cx="12" cy="9" r="2.5"/>
              </svg>
            </div>
            <div class="location-card-info">
              <h3 class="location-card-name">{{ loc.name }}</h3>
              <span class="location-card-continent">{{ store.getContinent(loc.lat, loc.lng) }}</span>
            </div>
            <span v-if="loc.lat != null" class="location-card-coords">{{ loc.lat.toFixed(2) }}, {{ loc.lng.toFixed(2) }}</span>
          </div>
          <div v-if="!filteredLocations.length" class="empty-state">没有匹配的地点</div>
        </div>

        <div v-else-if="activeTab === 'relations'" key="relations" class="relations-list">
          <div v-for="(group, idx) in filteredRelations" :key="idx" class="relation-item" :class="{ 'relation-highlight': isHighlighted(group) }" :style="{ animationDelay: `${idx * 0.03}s` }">
            <span class="relation-source" @click="goToEntity(group.source)">
              <span class="relation-entity-icon" :class="`entity-${group.source.type}`"></span>
              {{ group.source.name }}
            </span>
            <span class="relation-arrow" :class="`relation-type-${(group.link.relation || '').replace(/_/g, '-')}`">
              <span class="relation-label">{{ group.link.label || group.link.relation }}</span>
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
              </svg>
            </span>
            <span class="relation-target" @click="goToEntity(group.target)">
              <span class="relation-entity-icon" :class="`entity-${group.target.type}`"></span>
              {{ group.target.name }}
            </span>
          </div>
          <div v-if="!filteredRelations.length" class="empty-state">没有匹配的关系</div>
        </div>

        <div v-else-if="activeTab === 'taxonomy'" key="taxonomy" class="taxonomy-section">
          <div class="taxonomy-intro">
            <div class="taxonomy-summary-badge">
              <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 5h14M3 10h14M3 15h10"/></svg>
              鸟类分类体系：<strong>{{ taxonomySummary }}</strong>
            </div>
            <p class="taxonomy-hint">点击目/科可筛选下方鸟类卡片</p>
          </div>
          <div class="taxonomy-grid">
            <div v-for="order in taxonomyOrders" :key="order.id" class="taxonomy-order-card" :class="{ 'order-selected': selectedTaxonId && order.families.some(f => f.id === selectedTaxonId) }" @click="selectTaxon(order)">
              <div class="tax-order-header">
                <h4>{{ order.name }}</h4>
                <span class="tax-count">{{ order.memberCount || 0 }} 种</span>
              </div>
              <div class="tax-families">
                <button
                  v-for="fam in order.families.slice(0, 8)"
                  :key="fam.id"
                  class="tax-family-tag"
                  :class="{ active: selectedTaxonId === fam.id }"
                  @click.stop="selectTaxon(fam)"
                >
                  {{ fam.name }}
                </button>
                <span v-if="order.families.length > 8" class="tax-family-more">+{{ order.families.length - 8 }}</span>
              </div>
            </div>
          </div>

          <div v-if="selectedTaxonId" class="tax-filtered-birds">
            <h3 class="section-title">「{{ selectedTaxonName }}」下的鸟类</h3>
            <div class="bird-grid">
              <div v-for="bird in taxonFilteredBirds" :key="bird.id" class="bird-card scroll-reveal visible" @click="goToBird(bird)">
                <div class="bird-card-img">
                  <div class="bird-card-img-bg" :style="{ background: statusGradient(bird.status) }"></div>
                  <img :src="bird.imageUrl || `https://picsum.photos/seed/${bird.id}/300/200`" :alt="bird.name" loading="lazy" @error="onImgError" />
                  <div class="bird-card-img-overlay"></div>
                  <span v-if="bird.status" class="bird-card-status" :class="statusClass(bird.status)">
                    <span class="status-dot"></span>{{ statusLabel(bird.status) }}
                  </span>
                </div>
                <div class="bird-card-body">
                  <h3 class="bird-card-name">{{ bird.name }}</h3>
                  <p class="bird-card-english">{{ bird.englishName || bird.latinName || '' }}</p>
                </div>
              </div>
            </div>
            <p v-if="!taxonFilteredBirds.length" class="empty-tip">该分类下未加载到鸟类数据，请在首页图谱中展开相关节点。</p>
          </div>
        </div>
      </Transition>
    </template>
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
const selectedTaxonId = ref('')
const searchTerm = computed(() => searchQuery.value.trim().toLowerCase())

const tabs = computed(() => [
  { key: 'birds', label: '鸟类', count: filteredBirds.value.length },
  { key: 'locations', label: '地点', count: filteredLocations.value.length },
  { key: 'relations', label: '关系', count: filteredRelations.value.length },
  { key: 'taxonomy', label: '分类树', count: null }
])

const taxonomySummary = computed(() => {
  const m = store.meta?.counts || {}
  return `${m.kingdoms || 1}界 · ${m.phyla || 1}门 · ${m.classes || 1}纲 · ${m.orders || 0}目 · ${m.families || 0}科 · ${m.genera || 0}属 · ${m.species || 0}种`
})

const taxonomyOrders = computed(() => {
  const orders = store.nodes.filter(n => n.type === 'taxonomy' && n.taxonomyLevel === 'order')
  return orders.map(order => {
    const familyIds = order.memberCount ? [] : []
    const families = []
    store.links.forEach(link => {
      if (link.relation === 'belongs_to_order' && store.getNodeById(link.target)?.id === order.id) {
        const fam = store.getNodeById(link.source)
        if (fam && fam.type === 'taxonomy' && fam.taxonomyLevel === 'family') {
          families.push(fam)
        }
      }
    })
    return { ...order, families }
  }).sort((a, b) => (b.memberCount || 0) - (a.memberCount || 0))
})

const selectedTaxonName = computed(() => store.getNodeById(selectedTaxonId.value)?.name || '')

const taxonFilteredBirds = computed(() => {
  if (!selectedTaxonId.value) return []
  const taxon = store.getNodeById(selectedTaxonId.value)
  if (!taxon) return []
  const level = taxon.taxonomyLevel
  const idField = level === 'order' ? 'orderId' : level === 'family' ? 'familyId' : null
  if (!idField) return []
  return store.birdNodes.filter(b => b[idField] === selectedTaxonId.value)
})

function selectTaxon(taxon) {
  selectedTaxonId.value = taxon.id
}

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

const filteredLocations = computed(() => {
  const q = searchTerm.value
  const locs = store.nodes.filter(n => n.type === 'location')
  if (!q) return locs
  return locs.filter(l => l.name.toLowerCase().includes(q))
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

const totalResultCount = computed(() => {
  if (!searchTerm.value) return store.birdNodes.length + store.nodes.filter(n => n.type === 'location').length
  return filteredBirds.value.length + filteredLocations.value.length + filteredRelations.value.length
})

const highlightedKeys = computed(() => {
  const q = searchTerm.value
  if (!q) return new Set()
  const set = new Set()
  filteredRelations.value.forEach(({ source, target, link }) => {
    if ((link.label || link.relation || '').toLowerCase().includes(q)) {
      set.add(`${source.id}->${target.id}->${link.relation}`)
    }
  })
  return set
})

function isHighlighted(group) {
  return highlightedKeys.value.has(`${group.source.id}->${group.target.id}->${group.link.relation}`)
}

function onSearchInput() { selectedTaxonId.value = '' }

function statusClass(s) { return { CR: 'status-cr', EN: 'status-en', VU: 'status-vu', NT: 'status-nt', LC: 'status-lc' }[s] || 'status-lc' }
function statusLabel(s) { return { CR: '极危', EN: '濒危', VU: '易危', NT: '近危', LC: '无危' }[s] || s }
function statusGradient(s) {
  const g = { CR: 'linear-gradient(135deg, #fecaca, #ef4444)', EN: 'linear-gradient(135deg, #fed7aa, #f97316)', VU: 'linear-gradient(135deg, #fef08a, #eab308)', NT: 'linear-gradient(135deg, #bbf7d0, #22c55e)', LC: 'linear-gradient(135deg, #bbf7d0, #16a34a)' }
  return g[s] || 'linear-gradient(135deg, #e2e8f0, #94a3b8)'
}
function onImgError(e) { e.target.style.display = 'none' }

function goToBird(bird) { router.push(`/bird/${bird.id}`) }
function goToLocation(loc) { router.push(`/location/${loc.id}`) }
function goToBirdById(id) { router.push(`/bird/${id}`) }
function goToEntity(entity) {
  if (!entity) return
  if (entity.type === 'bird') router.push(`/bird/${entity.id}`)
  else if (entity.type === 'location') router.push(`/location/${entity.id}`)
  else {
    store.loadNodeChunk(entity.id)
    router.push('/')
  }
}

onMounted(async () => {
  if (!store.loaded) await store.loadData()
  if (!store.previewLoaded) await store.loadGraphPreview()
})
</script>

<style scoped>
.categories-page { display: flex; flex-direction: column; gap: 22px; padding-bottom: 48px; }

.cat-hero { text-align: center; margin-bottom: 0; }
.page-title { margin: 0; font-size: 30px; font-weight: 800; font-family: "Alegreya","Source Han Serif SC",serif; color: var(--heading-color); letter-spacing: 0.02em; }
.page-desc { margin: 8px 0 0; font-size: 14px; color: var(--text-secondary); }

.cat-search-bar {
  position: relative;
  display: flex;
  align-items: center;
  max-width: 720px;
  margin: 0 auto;
  width: 100%;
}
.search-icon {
  position: absolute;
  left: 20px;
  width: 20px; height: 20px;
  color: var(--text-secondary);
  pointer-events: none;
  z-index: 2;
  opacity: 0.7;
}
.search-input {
  width: 100%;
  padding: 15px 130px 15px 54px;
  border: 2px solid rgba(15,118,110,0.12);
  border-radius: 999px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 15px;
  outline: none;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
}
.search-input::placeholder { color: var(--text-secondary); opacity: 0.7; }
.search-input:focus { border-color: var(--accent); box-shadow: 0 4px 24px rgba(15,118,110,0.12), 0 0 0 3px rgba(15,118,110,0.06); }
.search-count {
  position: absolute; right: 20px;
  font-size: 12px; font-weight: 600; color: var(--accent);
  background: var(--accent-soft);
  padding: 4px 14px; border-radius: 999px;
  white-space: nowrap;
}

.tabs-bar {
  display: flex; gap: 4px; padding: 5px;
  border-radius: 999px;
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  width: fit-content;
  margin: 0 auto;
}
.tab-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 24px; border: none; border-radius: 999px;
  background: transparent; color: var(--text-secondary);
  font-size: 14px; font-weight: 500; cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}
.tab-btn:hover { background: rgba(15,118,110,0.06); color: var(--text-color); }
.tab-active { background: var(--accent) !important; color: #fff !important; font-weight: 600; box-shadow: 0 2px 12px rgba(15,118,110,0.25); }
.tab-count {
  font-size: 11px; opacity: 0.85; font-weight: 400;
}
.tab-active .tab-count { opacity: 1; }

.tab-fade-enter-active { transition: opacity 0.22s ease, transform 0.22s ease; }
.tab-fade-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.tab-fade-enter-from { opacity: 0; transform: translateY(10px); }
.tab-fade-leave-to { opacity: 0; transform: translateY(-6px); }

.bird-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 22px;
}
.bird-card {
  border-radius: var(--radius-xl);
  overflow: hidden;
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4,0,0.2,1);
  animation: card-enter 0.4s ease backwards;
}
.bird-card:nth-child(1) { animation-delay: 0.02s; }
.bird-card:nth-child(2) { animation-delay: 0.05s; }
.bird-card:nth-child(3) { animation-delay: 0.08s; }
.bird-card:nth-child(4) { animation-delay: 0.11s; }
.bird-card:nth-child(5) { animation-delay: 0.14s; }
.bird-card:nth-child(6) { animation-delay: 0.17s; }
.bird-card:nth-child(n+7) { animation-delay: 0.2s; }
.bird-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 16px 40px rgba(0,0,0,0.1), 0 0 0 1px var(--accent);
  border-color: var(--accent);
}
.bird-card-img { position: relative; width: 100%; height: 180px; overflow: hidden; background: #e2e8f0; }
.bird-card-img-bg { position: absolute; inset: 0; opacity: 0.25; transition: opacity 0.3s ease; }
.bird-card-img img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s cubic-bezier(0.4,0,0.2,1); }
.bird-card:hover .bird-card-img img { transform: scale(1.1); }
.bird-card:hover .bird-card-img-bg { opacity: 0.4; }
.bird-card-img-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(180deg, transparent 50%, rgba(0,0,0,0.35) 100%);
  pointer-events: none; opacity: 0; transition: opacity 0.3s ease;
}
.bird-card:hover .bird-card-img-overlay { opacity: 1; }
.bird-card-status {
  position: absolute; top: 12px; right: 12px;
  display: flex; align-items: center; gap: 5px;
  padding: 5px 14px; border-radius: 999px;
  font-size: 11px; font-weight: 700; color: #fff;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
  backdrop-filter: blur(8px);
  background: rgba(0,0,0,0.35);
  transition: all 0.3s ease;
}
.bird-card:hover .bird-card-status { background: rgba(0,0,0,0.5); }
.status-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: currentColor; opacity: 0.9;
}
.status-cr { border: 1px solid rgba(239,68,68,0.5); }
.status-en { border: 1px solid rgba(249,115,22,0.5); }
.status-vu { border: 1px solid rgba(234,179,8,0.5); color: #92400e; }
.status-nt { border: 1px solid rgba(34,197,94,0.5); }
.status-lc { border: 1px solid rgba(22,163,74,0.5); }
.bird-card-body { padding: 18px 20px; }
.bird-card-name { margin: 0; font-size: 16px; font-weight: 700; color: var(--heading-color); line-height: 1.3; transition: color 0.2s ease; }
.bird-card:hover .bird-card-name { color: var(--accent); }
.bird-card-english { margin: 5px 0 0; font-size: 12px; color: var(--text-secondary); font-style: italic; }
.bird-card-meta { display: flex; gap: 8px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--panel-border); flex-wrap: wrap; }
.bird-card-meta-item {
  display: flex; align-items: center; gap: 4px;
  font-size: 11px; color: var(--text-secondary);
  background: var(--accent-soft); padding: 3px 10px; border-radius: 999px;
  transition: all 0.2s ease;
}
.bird-card:hover .bird-card-meta-item { background: rgba(15,118,110,0.15); }

.location-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.location-card {
  padding: 20px 18px;
  border-radius: var(--radius-lg);
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
.location-card:hover {
  transform: translateY(-5px) scale(1.03);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08), 0 0 0 1px var(--success);
  border-color: var(--success);
}
.location-card-icon {
  width: 48px; height: 48px; border-radius: 14px;
  background: rgba(22,163,74,0.1); color: var(--success);
  display: flex; align-items: center; justify-content: center;
  transition: all 0.3s ease;
}
.location-card:hover .location-card-icon {
  background: var(--success);
  color: #fff;
  transform: scale(1.1);
  box-shadow: 0 4px 16px rgba(22,163,74,0.3);
}
.location-card-icon svg { width: 22px; height: 22px; }
.location-card-info { display: flex; flex-direction: column; gap: 4px; }
.location-card-name { margin: 0; font-size: 15px; font-weight: 700; color: var(--heading-color); }
.location-card-continent {
  font-size: 11px; font-weight: 600; color: var(--success);
  background: rgba(22,163,74,0.08);
  padding: 2px 10px; border-radius: 999px;
}
.location-card-coords { font-size: 10px; color: var(--text-secondary); opacity: 0.55; font-family: monospace; }

.relations-list { display: flex; flex-direction: column; gap: 8px; }
.relation-item {
  display: flex; align-items: center; gap: 14px;
  padding: 16px 20px; border-radius: var(--radius-lg);
  background: var(--card-bg); border: 1px solid var(--panel-border);
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
  box-shadow: 0 1px 4px rgba(0,0,0,0.02);
  animation: relation-enter 0.35s ease backwards;
}
@keyframes relation-enter {
  from { opacity: 0; transform: translateX(-12px); }
  to { opacity: 1; transform: translateX(0); }
}
.relation-item:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.08); border-color: var(--accent); transform: translateX(4px); }
.relation-highlight {
  background: var(--accent-soft) !important; border-color: rgba(15,118,110,0.3) !important;
  box-shadow: 0 0 0 3px rgba(15,118,110,0.08) !important;
}
.relation-source, .relation-target {
  display: flex; align-items: center; gap: 6px;
  font-weight: 600; color: var(--accent); cursor: pointer;
  padding: 5px 10px; border-radius: 8px;
  transition: all 0.2s ease; font-size: 14px;
}
.relation-source:hover, .relation-target:hover { background: rgba(15,118,110,0.1); }
.relation-entity-icon {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.entity-bird { background: var(--accent); }
.entity-location { background: var(--success); }
.relation-arrow { display: flex; align-items: center; gap: 6px; color: var(--text-secondary); font-size: 13px; flex-shrink: 0; }
.relation-label { font-size: 12px; color: var(--text-secondary); font-weight: 500; }

.taxonomy-section { display: flex; flex-direction: column; gap: 20px; }
.taxonomy-intro {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  text-align: center;
}
.taxonomy-summary-badge {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 20px; border-radius: 999px;
  background: var(--accent-soft); color: var(--text-color); font-size: 14px;
  border: 1px solid rgba(15,118,110,0.15);
}
.taxonomy-summary-badge strong { color: var(--heading-color); }
.taxonomy-hint { margin: 0; font-size: 13px; color: var(--text-secondary); }
.taxonomy-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.taxonomy-order-card {
  padding: 18px 20px; border-radius: var(--radius-lg);
  background: var(--card-bg); border: 1px solid var(--panel-border);
  cursor: pointer; transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
.taxonomy-order-card:hover, .order-selected {
  border-color: var(--accent);
  box-shadow: 0 8px 28px rgba(0,0,0,0.08), 0 0 0 1px var(--accent);
  transform: translateY(-2px);
}
.tax-order-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.tax-order-header h4 { margin: 0; font-size: 16px; font-weight: 700; color: var(--heading-color); }
.tax-count { font-size: 12px; font-weight: 600; color: var(--accent); background: var(--accent-soft); padding: 3px 12px; border-radius: 999px; }
.tax-families { display: flex; flex-wrap: wrap; gap: 6px; }
.tax-family-tag {
  padding: 5px 12px; border-radius: 999px; border: 1px solid var(--panel-border);
  background: transparent; color: var(--text-color); font-size: 12px; font-weight: 500;
  cursor: pointer; transition: all 0.2s ease;
}
.tax-family-tag:hover { border-color: var(--accent); background: var(--accent-soft); color: var(--accent); }
.tax-family-tag.active { border-color: var(--accent); background: var(--accent); color: #fff; font-weight: 600; box-shadow: 0 2px 8px rgba(15,118,110,0.25); }
.tax-family-more { font-size: 12px; color: var(--text-secondary); padding: 5px 8px; font-weight: 500; }
.tax-filtered-birds { margin-top: 4px; }
.section-title { margin: 0 0 16px; font-size: 17px; font-weight: 700; color: var(--heading-color); padding-left: 4px; border-left: 3px solid var(--accent); padding: 2px 0 2px 14px; }

.empty-state { padding: 48px; text-align: center; color: var(--text-secondary); font-size: 15px; }
.empty-tip { padding: 24px; text-align: center; color: var(--text-secondary); font-size: 14px; }

@keyframes card-enter {
  from { opacity: 0; transform: translateY(16px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

@media (max-width: 720px) {
  .bird-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 14px; }
  .bird-card-img { height: 130px; }
  .bird-card-body { padding: 14px 16px; }
  .taxonomy-grid { grid-template-columns: 1fr; }
  .location-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }
  .tabs-bar { flex-wrap: wrap; justify-content: center; }
  .tab-btn { padding: 8px 16px; font-size: 13px; }
}
</style>
