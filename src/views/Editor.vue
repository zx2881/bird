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
    <div class="editor-canvas-wrap">
      <VueFlow
        v-model:nodes="flowNodes"
        v-model:edges="flowEdges"
        :default-edge-options="defaultEdgeOptions"
        :node-types="nodeTypes"
        :fit-view-on-init="true"
        :min-zoom="0.1"
        :max-zoom="4"
        class="vue-flow-editor"
        @connect="onConnect"
      >
        <template #node-bird="nodeProps">
          <div class="custom-node bird-node" :style="nodeStyle(nodeProps)">
            <div class="node-label">{{ nodeProps.data.label }}</div>
          </div>
        </template>
        <template #node-default="nodeProps">
          <div class="custom-node default-node" :style="nodeStyle(nodeProps)">
            <div class="node-label">{{ nodeProps.data.label }}</div>
          </div>
        </template>
        <Panel position="top-right" class="editor-minimap-panel">
          <MiniMap :node-color="getNodeColor" :mask-color="'rgba(0,0,0,0.1)'" :pannable="true" :zoomable="true" />
          <Controls />
        </Panel>
        <div class="vue-flow-bg"></div>
      </VueFlow>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { VueFlow, useVueFlow, Panel, MarkerType } from '@vue-flow/core'
import { MiniMap } from '@vue-flow/minimap'
import { Controls } from '@vue-flow/controls'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/minimap/dist/style.css'
import '@vue-flow/controls/dist/style.css'
import { useGraphStore } from '../stores/graphStore.js'

const store = useGraphStore()
const typeColors = {
  bird: '#7f8fa6', location: '#6f9e98', habitat: '#8da56b',
  status: '#b59a62', threat: '#9f727a', taxonomy: '#8b84ab'
}

const flowNodes = ref([])
const flowEdges = ref([])

const defaultEdgeOptions = {
  type: 'smoothstep', animated: true,
  markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(148,163,184,0.5)' },
  style: { stroke: 'rgba(148,163,184,0.4)', strokeWidth: 2 }
}

const { undo, redo, canUndo, canRedo, fitView, addEdges, addNodes } = useVueFlow({ id: 'editor' })

function loadFromStore() {
  const nodeMap = new Map()
  flowNodes.value = store.nodes.map((n, i) => {
    const pos = { x: 150 + (i % 10) * 200, y: 100 + Math.floor(i / 10) * 150 }
    nodeMap.set(n.id, pos)
    return {
      id: n.id, type: n.type === 'bird' ? 'bird' : 'default',
      position: pos,
      data: { label: n.name, type: n.type, original: n }
    }
  })
  flowEdges.value = store.links.map(l => ({
    id: l.key, source: l.source, target: l.target,
    label: l.relation,
    data: { relation: l.relation }
  }))
  setTimeout(() => fitView({ padding: 0.2, duration: 300 }), 100)
}

function onConnect(connection) {
  const { source, target } = connection
  const key = `${source}__custom__${target}__${Date.now()}`
  addEdges([{
    id: key, source, target,
    label: 'custom', animated: true,
    style: { stroke: 'rgba(148,163,184,0.4)', strokeWidth: 2 }
  }])
}

function nodeStyle(props) {
  const color = typeColors[props.data.type] || '#8b949e'
  return { background: color, border: `2px solid ${color}` }
}

function getNodeColor(node) {
  return typeColors[node.data?.type] || '#8b949e'
}

function saveToJSON() {
  const nodes = flowNodes.value.map(n => ({
    id: n.id, name: n.data.label, type: n.data.type
  }))
  const links = flowEdges.value.map(e => ({
    source: e.source, target: e.target, relation: e.data?.relation || 'custom',
    key: e.id
  }))
  const data = { meta: { exported_at: new Date().toISOString(), source: 'editor' }, nodes, links }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = `bird-graph-edited-${Date.now()}.json`; a.click()
  URL.revokeObjectURL(url)
}

function resetView() { fitView({ padding: 0.2, duration: 300 }) }

function init() {
  if (store.loaded && store.nodes.length) loadFromStore()
}
init()
</script>

<style scoped>
.editor-page { display: flex; flex-direction: column; gap: 10px; height: calc(100vh - 160px); }
.editor-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-radius: 16px; background: var(--panel-bg); border: 1px solid var(--panel-border); flex-wrap: wrap; gap: 8px; }
.editor-toolbar-left, .editor-toolbar-right { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.editor-btn { padding: 8px 14px; border-radius: 10px; border: 1px solid var(--panel-border); background: var(--nav-bg); color: var(--text-color); font-size: 13px; cursor: pointer; transition: all 0.2s; }
.editor-btn:hover { background: var(--accent-soft); border-color: var(--accent); }
.editor-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.editor-status { font-size: 12px; color: var(--text-secondary); }
.editor-canvas-wrap { flex: 1; border-radius: 16px; overflow: hidden; border: 1px solid var(--panel-border); }
.vue-flow-editor { width: 100%; height: 100%; background: var(--bg-gradient); }
.custom-node { padding: 10px 16px; border-radius: 999px; color: #fff; font-size: 13px; font-weight: 600; text-align: center; min-width: 60px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); cursor: grab; }
.custom-node:active { cursor: grabbing; }
.node-label { white-space: nowrap; }
.editor-minimap-panel { display: flex; flex-direction: column; gap: 8px; }
.vue-flow-bg { pointer-events: none; position: absolute; inset: 0; z-index: -1; }
</style>
