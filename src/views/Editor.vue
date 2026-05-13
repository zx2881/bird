<template>
  <div class="editor-page">
    <div class="editor-toolbar">
      <div class="editor-toolbar-left">
        <button class="editor-btn" @click="saveToJSON" title="保存为 JSON">💾 保存</button>
        <button class="editor-btn" @click="undo" :disabled="!canUndo">↩ 撤销</button>
        <button class="editor-btn" @click="redo" :disabled="!canRedo">↪ 重做</button>
        <button class="editor-btn" @click="resetView">⟲ 重置视图</button>
      </div>
      <div class="editor-toolbar-right">
        <span class="editor-status">{{ store.nodeCount }} 节点 · {{ store.linkCount }} 关系</span>
        <button class="editor-btn" @click="loadFromStore">从图谱加载</button>
      </div>
    </div>
    <div v-if="ready" class="editor-canvas-wrap">
      <VueFlow
        id="editor"
        v-model:nodes="flowNodes"
        v-model:edges="flowEdges"
        :default-edge-options="defaultEdgeOptions"
        :fit-view-on-init="true"
        :min-zoom="0.1"
        :max-zoom="4"
        class="vue-flow-editor"
        @connect="onConnect"
      >
        <template #node-bird="nodeProps">
          <div class="custom-node" :style="nodeStyle(nodeProps.data.type)">
            <div class="node-label">{{ nodeProps.data.label }}</div>
          </div>
        </template>
        <template #node-default="nodeProps">
          <div class="custom-node default-node" :style="nodeStyle(nodeProps.data.type)">
            <div class="node-label">{{ nodeProps.data.label }}</div>
          </div>
        </template>
        <Panel position="top-right">
          <MiniMap :node-color="getNodeColor" :pannable="true" :zoomable="true" />
          <Controls />
        </Panel>
      </VueFlow>
    </div>
    <div v-else class="editor-loading">加载中…</div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { VueFlow, useVueFlow, Panel, MarkerType } from '@vue-flow/core'
import { MiniMap } from '@vue-flow/minimap'
import { Controls } from '@vue-flow/controls'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/minimap/dist/style.css'
import '@vue-flow/controls/dist/style.css'
import { useGraphStore } from '../stores/graphStore.js'

const store = useGraphStore()
const ready = ref(false)
const flowNodes = ref([])
const flowEdges = ref([])

const typeColors = {
  bird: '#5a6b7f', location: '#4d7a74', habitat: '#6b8a4e',
  status: '#937a48', threat: '#7a555d', taxonomy: '#6e6791'
}

const defaultEdgeOptions = {
  type: 'smoothstep', animated: true,
  markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(148,163,184,0.5)' },
  style: { stroke: 'rgba(148,163,184,0.4)', strokeWidth: 2 }
}

const { undo, redo, canUndo, canRedo, fitView, addEdges } = useVueFlow({ id: 'editor' })

function loadFromStore() {
  if (!store.nodes.length) return
  flowNodes.value = store.nodes.map((n, i) => ({
    id: n.id, type: n.type === 'bird' ? 'bird' : 'default',
    position: { x: 150 + (i % 10) * 200, y: 100 + Math.floor(i / 10) * 150 },
    data: { label: n.name, type: n.type }
  }))
  flowEdges.value = store.links.map(l => ({
    id: l.key, source: l.source, target: l.target,
    label: l.relation, data: { relation: l.relation }
  }))
  nextTick(() => fitView({ padding: 0.2, duration: 300 }))
}

function onConnect(connection) {
  const key = `${connection.source}__custom__${connection.target}__${Date.now()}`
  addEdges([{ id: key, source: connection.source, target: connection.target, label: '关联', animated: true }])
}

function nodeStyle(type) {
  const color = typeColors[type] || '#8b949e'
  return { background: color, border: `2px solid ${color}` }
}

function getNodeColor(node) { return typeColors[node.data?.type] || '#8b949e' }

function saveToJSON() {
  const data = {
    meta: { exported_at: new Date().toISOString(), source: 'editor' },
    nodes: flowNodes.value.map(n => ({ id: n.id, name: n.data.label, type: n.data.type })),
    links: flowEdges.value.map(e => ({ source: e.source, target: e.target, relation: e.data?.relation || 'custom', key: e.id }))
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = `bird-graph-edited-${Date.now()}.json`; a.click()
  URL.revokeObjectURL(url)
}

function resetView() { fitView({ padding: 0.2, duration: 300 }) }

onMounted(async () => {
  if (!store.loaded) await store.loadData()
  ready.value = true
  await nextTick()
  loadFromStore()
})
</script>

<style scoped>
.editor-page { display: flex; flex-direction: column; gap: 10px; height: calc(100vh - 160px); }
.editor-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-radius: 16px; background: var(--panel-bg); border: 1px solid var(--panel-border); flex-wrap: wrap; gap: 8px; }
.editor-toolbar-left, .editor-toolbar-right { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.editor-btn { padding: 8px 14px; border-radius: 10px; border: 1px solid var(--panel-border); background: var(--nav-bg); color: var(--text-color); font-size: 13px; cursor: pointer; transition: all 0.2s; font-family: inherit; }
.editor-btn:hover { background: var(--accent-soft); border-color: var(--accent); }
.editor-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.editor-status { font-size: 12px; color: var(--text-secondary); }
.editor-canvas-wrap { flex: 1; border-radius: 16px; overflow: hidden; border: 1px solid var(--panel-border); }
.vue-flow-editor { width: 100%; height: 100%; background: var(--bg-gradient); }
.editor-loading { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-secondary); font-size: 15px; }
.custom-node { padding: 10px 16px; border-radius: 999px; color: #fff; font-size: 13px; font-weight: 600; text-align: center; min-width: 60px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); cursor: grab; }
.custom-node:active { cursor: grabbing; }
.node-label { white-space: nowrap; }
</style>
