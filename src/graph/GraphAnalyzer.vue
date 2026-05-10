<template>
  <div class="analyzer-panel panel">
    <h3 class="analyzer-title">路径查询</h3>
    <div class="path-form">
      <select v-model="sourceId" class="path-select">
        <option value="" disabled>选择起点鸟类</option>
        <option v-for="b in store.birdNodes" :key="b.id" :value="b.id">{{ b.name }}</option>
      </select>
      <span class="path-arrow">→</span>
      <select v-model="targetId" class="path-select">
        <option value="" disabled>选择终点鸟类</option>
        <option v-for="b in store.birdNodes" :key="b.id" :value="b.id">{{ b.name }}</option>
      </select>
      <button class="path-btn" @click="findPath" :disabled="!sourceId || !targetId">查询</button>
    </div>
    <div v-if="pathResult.length" class="path-result">
      <div class="path-summary">找到 {{ pathResult.length - 1 }} 步路径</div>
      <div class="path-steps">
        <div v-for="(id, i) in pathResult" :key="i" class="path-step">
          <span class="step-node">{{ store.getNodeById(id)?.name || id }}</span>
          <span v-if="i < pathResult.length - 1" class="step-connector">→</span>
        </div>
      </div>
      <button class="path-clear-btn" @click="$emit('clear-path')">清除高亮</button>
    </div>
    <div v-if="pathError" class="path-error">{{ pathError }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useGraphStore } from '../stores/graphStore.js'

const store = useGraphStore()
const emit = defineEmits(['path-found', 'clear-path'])

const sourceId = ref('')
const targetId = ref('')
const pathResult = ref([])
const pathError = ref('')

function findPath() {
  pathError.value = ''
  if (!sourceId.value || !targetId.value) { pathError.value = '请选择起点和终点'; return }
  if (sourceId.value === targetId.value) { pathError.value = '起点和终点不能相同'; return }

  const visited = new Set()
  const parent = new Map()
  const queue = [sourceId.value]
  visited.add(sourceId.value)

  while (queue.length > 0) {
    const current = queue.shift()
    if (current === targetId.value) break
    const links = store.getIncidentLinks(current)
    for (const link of links) {
      const next = link.source === current ? link.target : link.source
      if (!visited.has(next)) {
        visited.add(next)
        parent.set(next, current)
        queue.push(next)
      }
    }
  }

  if (!parent.has(targetId.value)) {
    pathError.value = '未找到连接路径'
    pathResult.value = []
    return
  }

  const path = []
  let step = targetId.value
  while (step !== sourceId.value) {
    path.unshift(step)
    step = parent.get(step)
  }
  path.unshift(sourceId.value)
  pathResult.value = path
  emit('path-found', path)
}
</script>

<style scoped>
.analyzer-panel { padding: 16px; }
.analyzer-title { margin: 0 0 12px; font-size: 15px; color: var(--heading-color); }
.path-form { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.path-select { flex: 1; min-width: 120px; padding: 8px 12px; border-radius: 10px; border: 1px solid var(--panel-border); background: var(--nav-bg); color: var(--text-color); font-size: 13px; }
.path-arrow { color: var(--text-secondary); font-size: 18px; }
.path-btn { padding: 8px 16px; border-radius: 999px; border: none; background: var(--accent); color: #fff; font-size: 13px; cursor: pointer; font-weight: 600; transition: opacity 0.2s; }
.path-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.path-result { margin-top: 12px; }
.path-summary { font-size: 12px; color: var(--accent); margin-bottom: 8px; font-weight: 600; }
.path-steps { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.path-step { display: flex; align-items: center; gap: 6px; }
.step-node { padding: 4px 10px; border-radius: 999px; background: var(--accent-soft); color: var(--accent); font-size: 12px; font-weight: 500; }
.step-connector { color: var(--text-secondary); font-size: 14px; }
.path-clear-btn { margin-top: 8px; padding: 6px 14px; border-radius: 999px; border: 1px solid var(--panel-border); background: transparent; color: var(--text-secondary); font-size: 12px; cursor: pointer; }
.path-clear-btn:hover { background: var(--accent-soft); }
.path-error { margin-top: 8px; font-size: 12px; color: var(--danger); }
</style>
