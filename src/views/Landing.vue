<template>
  <div class="landing-page">
    <section class="hero">
      <canvas ref="graphCanvas" class="hero-canvas" aria-hidden="true"></canvas>
      <div class="hero-glow hero-glow-1" aria-hidden="true"></div>
      <div class="hero-glow hero-glow-2" aria-hidden="true"></div>
      <div class="hero-glow hero-glow-3" aria-hidden="true"></div>
      <div class="hero-content">
        <div class="hero-badge" data-reveal>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <circle cx="7" cy="8" r="2.5"/>
            <circle cx="17" cy="9" r="2"/>
            <circle cx="12" cy="15" r="2.5"/>
            <line x1="7" y1="8" x2="10" y2="14"/>
            <line x1="12" y1="15" x2="10" y2="14"/>
            <line x1="17" y1="9" x2="12" y2="15"/>
          </svg>
          <span>Bird Biodiversity Knowledge Graph</span>
        </div>
        <h1 class="hero-title" data-reveal="1">
          探索全球<br/>
          <span class="gradient-text">鸟类多样性</span>
        </h1>
        <p class="hero-subtitle" data-reveal="2">
          融合 10,772 个物种、3,370 个地点与 75,212 条知识关系的<br/>大型鸟类知识图谱
        </p>
        <div class="hero-actions" data-reveal="3">
          <router-link to="/home" class="cta-primary">
            进入知识图谱
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </router-link>
          <a href="#features" class="cta-secondary" @click.prevent="scrollTo('features')">了解更多</a>
        </div>
      </div>
      <div class="hero-bottom-fade" aria-hidden="true"></div>
    </section>

    <section class="stats-strip" ref="statsRef">
      <div class="stats-container">
        <div class="stat-item" data-reveal>
          <span class="stat-value">{{ animatedStats.species }}</span>
          <span class="stat-label">鸟类物种</span>
        </div>
        <div class="stat-divider" aria-hidden="true"></div>
        <div class="stat-item" data-reveal="1">
          <span class="stat-value">{{ animatedStats.locations }}</span>
          <span class="stat-label">分布地点</span>
        </div>
        <div class="stat-divider" aria-hidden="true"></div>
        <div class="stat-item" data-reveal="2">
          <span class="stat-value">{{ animatedStats.relations }}</span>
          <span class="stat-label">知识关系</span>
        </div>
        <div class="stat-divider" aria-hidden="true"></div>
        <div class="stat-item" data-reveal="3">
          <span class="stat-value">{{ animatedStats.orders }}</span>
          <span class="stat-label">目级分类</span>
        </div>
        <div class="stat-divider" aria-hidden="true"></div>
        <div class="stat-item" data-reveal="4">
          <span class="stat-value">{{ animatedStats.continents }}</span>
          <span class="stat-label">大洲覆盖</span>
        </div>
      </div>
    </section>

    <section id="features" class="features">
      <div class="section-header" data-reveal>
        <h2 class="section-title">探索方式</h2>
        <p class="section-sub">四种视角，全方位理解全球鸟类多样性</p>
      </div>
      <div class="feature-grid">
        <div
          v-for="(feat, i) in features"
          :key="i"
          class="feature-card"
          :data-reveal="i + 1"
        >
          <div class="feature-glow" aria-hidden="true"></div>
          <div class="feature-icon-wrap" :class="'fc-' + i">
            <svg v-if="i === 0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="7" cy="6" r="3.5"/>
              <circle cx="17" cy="5" r="3"/>
              <circle cx="12" cy="16" r="3.5"/>
              <line x1="7" y1="6" x2="12" y2="16"/>
              <line x1="17" y1="5" x2="12" y2="16"/>
              <line x1="7" y1="6" x2="17" y2="5"/>
            </svg>
            <svg v-else-if="i === 1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="10" cy="10" r="7"/>
              <path d="M16 16l6 6"/>
              <path d="M7 10h6M10 7v6"/>
            </svg>
            <svg v-else-if="i === 2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 20V12M10 20V8M16 4v16M22 20v-8"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="7" height="7" rx="1.5"/>
              <rect x="14" y="3" width="7" height="7" rx="1.5"/>
              <rect x="3" y="14" width="7" height="7" rx="1.5"/>
              <rect x="14" y="14" width="7" height="7" rx="1.5"/>
            </svg>
          </div>
          <h3>{{ feat.title }}</h3>
          <p>{{ feat.desc }}</p>
        </div>
      </div>
    </section>

    <div class="section-divider" aria-hidden="true">
      <svg viewBox="0 0 1440 80" preserveAspectRatio="none" fill="none">
        <path d="M0 80 L0 40 Q180 0 360 40 Q540 80 720 40 Q900 0 1080 40 Q1260 80 1440 40 L1440 80 Z" fill="currentColor"/>
      </svg>
    </div>

    <section class="about">
      <div class="about-bg" aria-hidden="true"></div>
      <div class="about-content" data-reveal>
        <h2 class="section-title">关于这个项目</h2>
        <p>
          全球鸟类多样性知识探索平台是一个开源的鸟类生物多样性知识图谱项目。
          数据来源于鸟类学文献、IUCN 红色名录、Wikipedia 以及开放地理数据，
          通过自动化数据管道整合为结构化的知识网络。
        </p>
        <p>
          图谱以 <strong>10,772 种鸟类</strong> 为核心节点，连接分布地点、栖息地类型、保护等级、
          威胁因素和完整的七级分类体系（界—门—纲—目—科—属—种），
          支持渐进式加载、语义搜索和三维可视化。
        </p>
        <div class="about-cta">
          <router-link to="/home" class="cta-primary">
            开始探索
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </router-link>
        </div>
      </div>
    </section>

    <footer class="landing-footer">
      <div class="footer-decoration" aria-hidden="true"></div>
      <p>Global Avian Biodiversity Graph &copy; 2026 &middot; 数据来源：Wikipedia, IUCN, eBird, BirdLife International</p>
      <p class="footer-data-note"><strong>10,772</strong> 物种 &middot; <strong>3,370</strong> 地点 &middot; <strong>75,212</strong> 关系 &middot; <strong>31</strong> 目 &middot; <strong>7</strong> 大洲</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'

const graphCanvas = ref(null)
const statsRef = ref(null)
const reducedMotion = ref(false)

const animatedStats = reactive({
  species: '0',
  locations: '0',
  relations: '0',
  orders: '0',
  continents: '0',
})

const features = [
  {
    title: '3D 知识图谱',
    desc: '在三维空间中自由探索鸟类与地点、栖息地、威胁因素的关联网络，支持拖拽、缩放、聚焦和按需展开。',
  },
  {
    title: '语义搜索',
    desc: '用自然语言提问，如「鄱阳湖有什么濒危鸟类」「丹顶鹤生活在哪」，AI 理解语义并返回图谱中的精准答案。',
  },
  {
    title: '数据概览',
    desc: '通过交互式图表了解全球鸟类按大洲、栖息地类型、濒危等级和分类体系的分布统计，一目了然。',
  },
  {
    title: '分类浏览',
    desc: '按目、科、属的层级体系浏览鸟类物种卡片，查看详细的分布、栖息地、保护等级与威胁因素信息。',
  },
]

let rafId = null
let revealObserver = null
let statsObserver = null
let nodes = []
let canvasW = 0
let canvasH = 0

const NODE_COUNT = 62
const CONNECTION_DIST = 135

function createNodes(w, h) {
  const arr = []
  for (let i = 0; i < NODE_COUNT; i++) {
    arr.push({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.28,
      vy: (Math.random() - 0.5) * 0.28,
      r: Math.random() * 1.6 + 1.2,
      alpha: Math.random() * 0.3 + 0.14,
    })
  }
  for (let i = 0; i < 8; i++) {
    arr[i].r = Math.random() * 2 + 2.6
    arr[i].alpha = Math.random() * 0.25 + 0.45
  }
  nodes = arr
}

function setCanvasSize() {
  const canvas = graphCanvas.value
  if (!canvas) return
  const rect = canvas.parentElement.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1
  canvasW = rect.width
  canvasH = rect.height
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  canvas.style.width = rect.width + 'px'
  canvas.style.height = rect.height + 'px'
}

function draw() {
  const canvas = graphCanvas.value
  if (!canvas || reducedMotion.value) return
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const dx = nodes[i].x - nodes[j].x
      const dy = nodes[i].y - nodes[j].y
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < CONNECTION_DIST) {
        const alpha = (1 - dist / CONNECTION_DIST) * 0.1
        ctx.strokeStyle = `rgba(94,234,212,${alpha})`
        ctx.lineWidth = 0.5
        ctx.beginPath()
        ctx.moveTo(nodes[i].x * dpr, nodes[i].y * dpr)
        ctx.lineTo(nodes[j].x * dpr, nodes[j].y * dpr)
        ctx.stroke()
      }
    }
  }

  for (const node of nodes) {
    ctx.beginPath()
    ctx.arc(node.x * dpr, node.y * dpr, node.r * dpr, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(94,234,212,${node.alpha})`
    ctx.fill()
  }
}

function updateNodes() {
  for (const node of nodes) {
    node.x += node.vx
    node.y += node.vy
    if (node.x < -20) node.x = canvasW + 20
    if (node.x > canvasW + 20) node.x = -20
    if (node.y < -20) node.y = canvasH + 20
    if (node.y > canvasH + 20) node.y = -20
  }
}

function animate() {
  if (reducedMotion.value) return
  updateNodes()
  draw()
  rafId = requestAnimationFrame(animate)
}

function handleResize() {
  setCanvasSize()
  createNodes(canvasW, canvasH)
}

function animateValue(key, target, duration, delay) {
  return new Promise((resolve) => {
    if (reducedMotion.value) {
      animatedStats[key] = target.toLocaleString()
      resolve()
      return
    }
    const start = performance.now()
    function tick(now) {
      const elapsed = now - start - delay
      if (elapsed < 0) { requestAnimationFrame(tick); return }
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      animatedStats[key] = Math.floor(eased * target).toLocaleString()
      if (progress < 1) {
        requestAnimationFrame(tick)
      } else {
        animatedStats[key] = target.toLocaleString()
        resolve()
      }
    }
    requestAnimationFrame(tick)
  })
}

async function startCountUp() {
  if (reducedMotion.value) {
    animatedStats.species = '10,772'
    animatedStats.locations = '3,370'
    animatedStats.relations = '75,212'
    animatedStats.orders = '31'
    animatedStats.continents = '7'
    return
  }
  await Promise.all([
    animateValue('species', 10772, 1900, 0),
    animateValue('locations', 3370, 1900, 100),
    animateValue('relations', 75212, 1900, 200),
    animateValue('orders', 31, 1600, 300),
    animateValue('continents', 7, 1400, 400),
  ])
}

function scrollTo(id) {
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: reducedMotion.value ? 'auto' : 'smooth' })
  }
}

function revealAll() {
  document.querySelectorAll('[data-reveal]').forEach((el) => el.classList.add('revealed'))
}

onMounted(() => {
  const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
  reducedMotion.value = mq.matches

  if (reducedMotion.value) {
    revealAll()
    startCountUp()
    return
  }

  setCanvasSize()
  createNodes(canvasW, canvasH)
  animate()
  window.addEventListener('resize', handleResize)

  revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const el = entry.target
          const delay = parseInt(el.getAttribute('data-reveal')) || 0
          setTimeout(() => el.classList.add('revealed'), delay * 100)
          revealObserver.unobserve(el)
        }
      })
    },
    { threshold: 0.1, rootMargin: '0px 0px -30px 0px' },
  )

  document.querySelectorAll('[data-reveal]').forEach((el) => revealObserver.observe(el))

  if (statsRef.value) {
    statsObserver = new IntersectionObserver(
      (entries) => {
        if (entries[0] && entries[0].isIntersecting) {
          startCountUp()
          statsObserver.unobserve(entries[0].target)
        }
      },
      { threshold: 0.35 },
    )
    statsObserver.observe(statsRef.value)
  }
})

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId)
  window.removeEventListener('resize', handleResize)
  if (revealObserver) revealObserver.disconnect()
  if (statsObserver) statsObserver.disconnect()
})
</script>

<style scoped>
.landing-page {
  min-height: 100vh;
  background: #060b14;
  color: var(--text-color, #e2e8f0);
}

/* ═══════════════════════════════════════════
   Hero
   ═══════════════════════════════════════════ */
.hero {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.hero-canvas {
  position: absolute;
  inset: 0;
  z-index: 1;
}

.hero-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(140px);
  pointer-events: none;
  z-index: 0;
  opacity: 0.7;
}
.hero-glow-1 {
  width: 700px;
  height: 700px;
  background: rgba(94, 234, 212, 0.06);
  top: -280px;
  left: 5%;
  animation: glowPulse1 8s ease-in-out infinite;
}
.hero-glow-2 {
  width: 550px;
  height: 550px;
  background: rgba(56, 189, 248, 0.05);
  bottom: -100px;
  right: -5%;
  animation: glowPulse2 10s ease-in-out infinite;
}
.hero-glow-3 {
  width: 450px;
  height: 450px;
  background: rgba(168, 85, 247, 0.04);
  top: 35%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: glowPulse3 12s ease-in-out infinite;
}

@keyframes glowPulse1 {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.7; }
  50% { transform: translate(40px, -20px) scale(1.1); opacity: 0.5; }
}
@keyframes glowPulse2 {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.6; }
  50% { transform: translate(-30px, 30px) scale(1.15); opacity: 0.4; }
}
@keyframes glowPulse3 {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.5; }
  50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.3; }
}

.hero-content {
  position: relative;
  z-index: 2;
  text-align: center;
  max-width: 820px;
  padding: 0 28px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 22px;
  border-radius: 999px;
  background: rgba(94, 234, 212, 0.07);
  border: 1px solid rgba(94, 234, 212, 0.16);
  font-size: 13px;
  color: var(--accent, #5eead4);
  font-weight: 500;
  letter-spacing: 0.02em;
  margin-bottom: 36px;
  backdrop-filter: blur(12px);
}
.hero-badge svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.hero-title {
  font-family: "Alegreya", "Source Han Serif SC", "Noto Serif SC", serif;
  font-size: clamp(40px, 5.5vw, 64px);
  font-weight: 800;
  line-height: 1.08;
  margin: 0 0 20px;
  color: var(--heading-color, #f1f5f9);
  letter-spacing: -0.025em;
}

.gradient-text {
  background: linear-gradient(135deg, #5eead4 0%, #38bdf8 45%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: clamp(15px, 1.4vw, 18px);
  color: rgba(226, 232, 240, 0.55);
  line-height: 1.7;
  margin: 0 auto 40px;
  max-width: 560px;
  font-weight: 400;
}

.hero-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
}

.cta-primary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 16px 38px;
  border-radius: 999px;
  background: linear-gradient(135deg, #0d9488, #14b8a6);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  text-decoration: none;
  letter-spacing: 0.01em;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 28px rgba(13, 148, 136, 0.35);
}
.cta-primary:hover {
  transform: scale(1.02);
  box-shadow: 0 8px 44px rgba(13, 148, 136, 0.5);
}
.cta-primary svg {
  width: 18px;
  height: 18px;
}

.cta-secondary {
  display: inline-flex;
  align-items: center;
  padding: 16px 36px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  color: rgba(226, 232, 240, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 16px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.cta-secondary:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
  color: #e2e8f0;
}

.hero-bottom-fade {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 160px;
  background: linear-gradient(180deg, transparent 0%, #060b14 100%);
  z-index: 1;
  pointer-events: none;
}

/* ═══════════════════════════════════════════
   Stats Strip
   ═══════════════════════════════════════════ */
.stats-strip {
  position: relative;
  z-index: 2;
  padding: 44px 24px;
  background: rgba(255, 255, 255, 0.015);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(8px);
}

.stats-container {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0;
  max-width: 960px;
  margin: 0 auto;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 36px;
  min-width: 120px;
}

.stat-value {
  font-family: "Alegreya", "Source Han Serif SC", serif;
  font-size: 34px;
  font-weight: 800;
  color: var(--accent, #5eead4);
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-size: 12px;
  color: rgba(226, 232, 240, 0.4);
  margin-top: 6px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 500;
}

.stat-divider {
  width: 1px;
  height: 44px;
  background: rgba(255, 255, 255, 0.07);
}

/* ═══════════════════════════════════════════
   Features
   ═══════════════════════════════════════════ */
.features {
  padding: 100px 24px 80px;
  max-width: 1100px;
  margin: 0 auto;
  text-align: center;
}

.section-header {
  margin-bottom: 60px;
}

.section-title {
  font-family: "Alegreya", "Source Han Serif SC", serif;
  font-size: clamp(28px, 4vw, 38px);
  font-weight: 700;
  color: var(--heading-color, #f1f5f9);
  margin: 0 0 10px;
  letter-spacing: -0.015em;
}

.section-sub {
  font-size: 15px;
  color: rgba(226, 232, 240, 0.45);
  margin: 0;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 22px;
}

.feature-card {
  position: relative;
  padding: 38px 30px 34px;
  border-radius: var(--radius-lg, 20px);
  background: rgba(255, 255, 255, 0.022);
  border: 1px solid rgba(255, 255, 255, 0.06);
  text-align: left;
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1),
    background 0.35s cubic-bezier(0.16, 1, 0.3, 1),
    border-color 0.35s cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
  cursor: default;
}

.feature-card:hover {
  transform: translateY(-4px);
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(94, 234, 212, 0.2);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.35),
    0 0 0 1px rgba(94, 234, 212, 0.06);
}

.feature-glow {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: radial-gradient(circle at 50% 0%, rgba(94, 234, 212, 0.08), transparent 65%);
  opacity: 0;
  transition: opacity 0.4s ease;
  pointer-events: none;
}
.feature-card:hover .feature-glow {
  opacity: 1;
}

.feature-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}
.feature-icon-wrap svg {
  width: 22px;
  height: 22px;
}

.fc-0 {
  background: rgba(20, 184, 166, 0.14);
  color: #14b8a6;
}
.fc-1 {
  background: rgba(168, 85, 247, 0.14);
  color: #a78bfa;
}
.fc-2 {
  background: rgba(59, 130, 246, 0.14);
  color: #60a5fa;
}
.fc-3 {
  background: rgba(251, 191, 36, 0.14);
  color: #fbbf24;
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--heading-color, #f1f5f9);
  margin: 0 0 10px;
  letter-spacing: -0.01em;
}

.feature-card p {
  font-size: 14px;
  line-height: 1.72;
  color: rgba(226, 232, 240, 0.48);
  margin: 0;
}

/* ═══════════════════════════════════════════
   Section Divider (Stripe-style wave)
   ═══════════════════════════════════════════ */
.section-divider {
  width: 100%;
  overflow: hidden;
  line-height: 0;
  color: rgba(255, 255, 255, 0.015);
}
.section-divider svg {
  width: 100%;
  height: 80px;
}

/* ═══════════════════════════════════════════
   About
   ═══════════════════════════════════════════ */
.about {
  position: relative;
  padding: 100px 24px;
  overflow: hidden;
}

.about-bg {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 30%, rgba(94, 234, 212, 0.04) 0%, transparent 60%),
    radial-gradient(ellipse at 20% 80%, rgba(56, 189, 248, 0.03) 0%, transparent 50%);
  pointer-events: none;
}

.about-content {
  position: relative;
  max-width: 700px;
  margin: 0 auto;
  text-align: center;
}

.about-content p {
  font-size: 15px;
  line-height: 1.9;
  color: rgba(226, 232, 240, 0.55);
  margin: 0 0 18px;
}

.about-content strong {
  color: var(--heading-color, #f1f5f9);
  font-weight: 600;
}

.about-cta {
  margin-top: 36px;
}

/* ═══════════════════════════════════════════
   Footer
   ═══════════════════════════════════════════ */
.landing-footer {
  position: relative;
  text-align: center;
  padding: 36px 24px 40px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 12px;
  color: rgba(226, 232, 240, 0.28);
  background: rgba(0, 0, 0, 0.15);
}

.landing-footer p {
  margin: 0;
  line-height: 1.8;
}

.landing-footer strong {
  color: rgba(226, 232, 240, 0.45);
  font-weight: 500;
}

.footer-data-note {
  margin-top: 8px !important;
  font-size: 11px;
  color: rgba(226, 232, 240, 0.2);
}

/* ═══════════════════════════════════════════
   Scroll Reveal
   ═══════════════════════════════════════════ */
[data-reveal] {
  opacity: 0;
  transform: translateY(28px);
  transition: opacity 0.75s cubic-bezier(0.16, 1, 0.3, 1),
    transform 0.75s cubic-bezier(0.16, 1, 0.3, 1);
}

[data-reveal].revealed {
  opacity: 1;
  transform: translateY(0);
}

/* ═══════════════════════════════════════════
   Responsive
   ═══════════════════════════════════════════ */
@media (max-width: 860px) {
  .feature-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .feature-card {
    padding: 28px 24px 26px;
  }

  .stats-container {
    gap: 0;
  }

  .stat-item {
    padding: 10px 22px;
    min-width: 90px;
  }

  .stat-value {
    font-size: 26px;
  }
}

@media (max-width: 560px) {
  .hero-title {
    font-size: 32px;
  }

  .hero-badge {
    font-size: 11px;
    padding: 7px 16px;
    gap: 7px;
  }
  .hero-badge svg {
    width: 15px;
    height: 15px;
  }

  .hero-subtitle {
    font-size: 14px;
  }

  .cta-primary,
  .cta-secondary {
    padding: 14px 28px;
    font-size: 15px;
  }

  .stat-item {
    padding: 8px 14px;
    min-width: 70px;
  }

  .stat-value {
    font-size: 22px;
  }

  .stat-label {
    font-size: 10px;
  }

  .stat-divider {
    height: 32px;
  }

  .feature-card {
    padding: 24px 20px 22px;
  }

  .feature-card h3 {
    font-size: 16px;
  }

  .feature-card p {
    font-size: 13px;
  }

  .section-divider svg {
    height: 40px;
  }
}

/* ═══════════════════════════════════════════
   Reduced Motion
   ═══════════════════════════════════════════ */
@media (prefers-reduced-motion: reduce) {
  .hero-glow-1,
  .hero-glow-2,
  .hero-glow-3 {
    animation: none;
  }

  [data-reveal] {
    opacity: 1;
    transform: none;
    transition: none;
  }

  .feature-card {
    transition: none;
  }

  .cta-primary,
  .cta-secondary {
    transition: none;
  }
}
</style>
