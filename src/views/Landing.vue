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
      <div class="hero-showcase" data-reveal="2" aria-hidden="true">
        <div class="showcase-card migration-card">
          <div class="showcase-topline">
            <span>Migration signal</span>
            <strong>LIVE</strong>
          </div>
          <div class="migration-window">
            <span class="route route-a"></span>
            <span class="route route-b"></span>
            <span class="route route-c"></span>
            <i class="node node-a"></i>
            <i class="node node-b"></i>
            <i class="node node-c"></i>
            <i class="node node-d"></i>
          </div>
        </div>
        <div class="showcase-card taxonomy-card">
          <span class="showcase-kicker">Taxonomy stack</span>
          <strong>31 目</strong>
          <p>物种、地点、栖息地、威胁因素被组织成可探索的关系网络。</p>
        </div>
        <div class="showcase-card specimen-card">
          <span class="specimen-wing"></span>
          <div>
            <strong>10,772</strong>
            <p>species indexed</p>
          </div>
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

    <section class="conservation" ref="conservationRef">
      <div class="section-header" data-reveal>
        <h2 class="section-title">为什么鸟类保护至关重要</h2>
        <p class="section-sub">鸟类不仅是自然之美的象征，更是地球生态健康的晴雨表</p>
      </div>
      <div class="conservation-grid">
        <div class="conservation-stat-card" data-reveal="1">
          <div class="conservation-stat-glow" aria-hidden="true"></div>
          <span class="conservation-stat-number">1,481</span>
          <span class="conservation-stat-label">种全球受威胁鸟类</span>
          <p class="conservation-stat-desc">约占已知鸟类的 13%，被 IUCN 列为 CR/EN/VU 等级</p>
        </div>
        <div class="conservation-stat-card" data-reveal="2">
          <div class="conservation-stat-glow" aria-hidden="true"></div>
          <span class="conservation-stat-number">68%</span>
          <span class="conservation-stat-label">种群数量下降</span>
          <p class="conservation-stat-desc">过去 50 年间，全球超过 2/3 的鸟类种群呈下降趋势</p>
        </div>
        <div class="conservation-stat-card" data-reveal="3">
          <div class="conservation-stat-glow" aria-hidden="true"></div>
          <span class="conservation-stat-number">1,200+</span>
          <span class="conservation-stat-label">已灭绝鸟类物种</span>
          <p class="conservation-stat-desc">自 1500 年以来，人类活动导致的鸟类灭绝速度是自然速率的 100 倍</p>
        </div>
      </div>

      <div class="conservation-topics" data-reveal="4">
        <div class="conservation-topic">
          <div class="topic-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M2 22L12 12M22 2L12 12"/>
              <path d="M12 12l-3.5 3.5M12 12l-7 7"/>
              <circle cx="8" cy="8" r="2"/>
              <path d="M14 2h8v8"/>
            </svg>
          </div>
          <div class="topic-content">
            <h4>栖息地丧失</h4>
            <p>森林砍伐、湿地填埋、草原开垦使鸟类失去赖以生存的家园。全球每年消失的森林面积相当于一个葡萄牙，湿地退化速度是森林的三倍。候鸟迁徙路线上的停歇地正以惊人的速度缩减。</p>
          </div>
        </div>
        <div class="conservation-topic">
          <div class="topic-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
            </svg>
          </div>
          <div class="topic-content">
            <h4>气候变化</h4>
            <p>全球变暖导致鸟类物候紊乱——迁徙时间错位、繁殖季节提前、食物链断裂。温度每升高 1°C，约有 100 种鸟类的适宜栖息范围将显著缩小。极地和高山鸟类受到的冲击尤为严重。</p>
          </div>
        </div>
        <div class="conservation-topic">
          <div class="topic-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
          </div>
          <div class="topic-content">
            <h4>非法捕猎与贸易</h4>
            <p>每年数以百万计的鸟类被非法捕捉用于宠物贸易、食物和传统医药。东南亚地区的鸣禽贸易每年涉及超过 1,000 万只鸟，许多物种因过度捕捉而濒临野外灭绝。</p>
          </div>
        </div>
        <div class="conservation-topic">
          <div class="topic-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4-4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
            </svg>
          </div>
          <div class="topic-content">
            <h4>环境污染</h4>
            <p>农药、重金属和塑料污染直接毒害鸟类或通过食物链富集。每年有超过 100 万只海鸟因误食塑料而死亡。杀虫剂的使用使昆虫数量锐减，以昆虫为食的鸟类面临严重的食物短缺。</p>
          </div>
        </div>
      </div>

      <div class="conservation-cta" data-reveal="5">
        <div class="conservation-cta-bg" aria-hidden="true"></div>
        <div class="conservation-cta-content">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z"/>
            <path d="M8 12l3 3 5-5"/>
          </svg>
          <div>
            <h4>我们能做什么</h4>
            <p>支持保护地建设与湿地修复，参与公民科学项目（如 eBird），减少塑料使用，选择可持续农产品，传播鸟类保护知识——每个人的行动都能为鸟类带来希望。</p>
          </div>
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
const conservationRef = ref(null)
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
  background:
    radial-gradient(circle at 14% 18%, rgba(20, 184, 166, 0.18), transparent 29%),
    radial-gradient(circle at 84% 20%, rgba(56, 189, 248, 0.15), transparent 27%),
    linear-gradient(115deg, rgba(132, 204, 22, 0.08), transparent 34%),
    #050b13;
  color: var(--text-color, #e2e8f0);
}

/* ═══════════════════════════════════════════
   Hero
   ═══════════════════════════════════════════ */
.hero {
  position: relative;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: clamp(32px, 5vw, 82px);
  padding: clamp(42px, 7vw, 92px);
  overflow: hidden;
}

.hero::after {
  content: "";
  position: absolute;
  right: clamp(24px, 7vw, 120px);
  top: clamp(80px, 16vh, 180px);
  z-index: 1;
  width: clamp(180px, 24vw, 340px);
  height: clamp(80px, 12vw, 150px);
  opacity: 0.16;
  pointer-events: none;
  color: #5eead4;
  background:
    radial-gradient(circle at 8% 60%, currentColor 0 2px, transparent 2.7px),
    radial-gradient(circle at 34% 36%, currentColor 0 2px, transparent 2.7px),
    radial-gradient(circle at 62% 48%, currentColor 0 2px, transparent 2.7px),
    radial-gradient(circle at 92% 30%, currentColor 0 2px, transparent 2.7px),
    linear-gradient(14deg, transparent 0 18%, currentColor 18.3% 19.2%, transparent 19.6% 100%),
    linear-gradient(-12deg, transparent 0 52%, currentColor 52.3% 53.2%, transparent 53.6% 100%);
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
  background: rgba(132, 204, 22, 0.035);
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
  text-align: left;
  max-width: 700px;
  padding: 0;
  margin-right: 0;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 22px;
  border-radius: 12px;
  background: rgba(94, 234, 212, 0.055);
  border: 1px solid rgba(94, 234, 212, 0.16);
  font-size: 13px;
  color: #9cffd8;
  font-weight: 500;
  letter-spacing: 0.02em;
  margin-bottom: 36px;
  backdrop-filter: blur(8px);
}
.hero-badge svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.hero-title {
  font-family: "Alegreya Sans", "Source Han Sans SC", "Noto Sans SC", sans-serif;
  font-size: clamp(48px, 7vw, 94px);
  font-weight: 900;
  line-height: 0.96;
  margin: 0 0 20px;
  color: #f1f5f9;
  letter-spacing: 0;
}

.gradient-text {
  color: #5eead4;
  text-decoration: none;
  text-shadow: 0 0 44px rgba(94, 234, 212, 0.28);
}

.hero-subtitle {
  font-size: clamp(15px, 1.4vw, 18px);
  color: rgba(226, 232, 240, 0.68);
  line-height: 1.7;
  margin: 0 0 40px;
  max-width: 560px;
  font-weight: 400;
}

.hero-actions {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.cta-primary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 16px 38px;
  border-radius: 12px;
  background: var(--accent, #0d9488);
  color: oklch(0.99 0.01 170);
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
  border-radius: 12px;
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
  background:
    linear-gradient(90deg, rgba(94, 234, 212, 0.04), rgba(56, 189, 248, 0.025)),
    rgba(255, 255, 255, 0.015);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(6px);
}

.hero-showcase {
  position: relative;
  z-index: 2;
  flex: 0 1 470px;
  min-height: 560px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr auto;
  gap: 18px;
  perspective: 1200px;
}

.showcase-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(148, 211, 197, 0.2);
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.09), rgba(255, 255, 255, 0.018)),
    rgba(7, 17, 31, 0.72);
  box-shadow: 0 34px 90px rgba(0, 0, 0, 0.34), inset 0 1px 0 rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
}

.migration-card {
  grid-column: 1 / -1;
  min-height: 370px;
  border-radius: 28px;
  transform: rotateY(-8deg) rotateX(4deg);
}

.showcase-topline {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  padding: 18px 20px 0;
  color: rgba(226, 232, 240, 0.62);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.showcase-topline strong {
  color: #9cffd8;
}

.migration-window {
  position: absolute;
  inset: 56px 24px 24px;
  border-radius: 22px;
  background:
    linear-gradient(rgba(148, 211, 197, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 211, 197, 0.08) 1px, transparent 1px),
    radial-gradient(circle at 32% 38%, rgba(94, 234, 212, 0.2), transparent 18%),
    radial-gradient(circle at 74% 28%, rgba(56, 189, 248, 0.18), transparent 20%),
    rgba(3, 7, 18, 0.7);
  background-size: auto, 48px 48px, auto, auto, auto;
  border: 1px solid rgba(148, 211, 197, 0.14);
}

.route {
  position: absolute;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, #5eead4, transparent);
  filter: drop-shadow(0 0 12px rgba(94, 234, 212, 0.44));
  transform-origin: left center;
}

.route-a { left: 12%; top: 58%; width: 68%; transform: rotate(-24deg); }
.route-b { left: 18%; top: 38%; width: 56%; transform: rotate(16deg); opacity: 0.78; }
.route-c { left: 34%; top: 72%; width: 42%; transform: rotate(-8deg); opacity: 0.64; }

.node {
  position: absolute;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #9cffd8;
  box-shadow: 0 0 0 8px rgba(94, 234, 212, 0.08), 0 0 22px rgba(94, 234, 212, 0.6);
}

.node-a { left: 14%; top: 56%; }
.node-b { left: 38%; top: 34%; background: #93c5fd; }
.node-c { left: 70%; top: 22%; }
.node-d { left: 78%; top: 68%; background: #facc15; }

.taxonomy-card {
  min-height: 172px;
  padding: 22px;
  border-radius: 24px;
}

.showcase-kicker {
  display: block;
  color: rgba(226, 232, 240, 0.48);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: 14px;
}

.taxonomy-card strong,
.specimen-card strong {
  display: block;
  color: #f8fafc;
  font-size: clamp(30px, 3vw, 38px);
  line-height: 1;
  white-space: nowrap;
}

.taxonomy-card p,
.specimen-card p {
  margin: 10px 0 0;
  color: rgba(226, 232, 240, 0.58);
  font-size: 13px;
  line-height: 1.55;
}

.specimen-card {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 172px;
  padding: 22px;
  border-radius: 24px;
  background:
    radial-gradient(circle at 18% 20%, rgba(250, 204, 21, 0.12), transparent 34%),
    rgba(7, 17, 31, 0.72);
}

.specimen-wing {
  flex: 0 0 auto;
  width: 62px;
  height: 54px;
  border: 3px solid #9cffd8;
  border-left-color: transparent;
  border-bottom-color: transparent;
  border-radius: 60% 82% 45% 76%;
  transform: rotate(-18deg);
  opacity: 0.72;
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
  font-family: inherit;
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
  font-family: inherit;
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
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.026);
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
  transform: translateY(-2px);
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
   Conservation
   ═══════════════════════════════════════════ */
.conservation {
  padding: 100px 24px 80px;
  max-width: 1100px;
  margin: 0 auto;
  text-align: center;
}

.conservation-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
  margin-top: 48px;
  margin-bottom: 56px;
}

.conservation-stat-card {
  position: relative;
  padding: 38px 24px 32px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.022);
  border: 1px solid rgba(255, 255, 255, 0.06);
  overflow: hidden;
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1),
    border-color 0.35s ease, box-shadow 0.35s ease;
}
.conservation-stat-card:hover {
  transform: translateY(-4px);
  border-color: rgba(220, 38, 38, 0.25);
  box-shadow: 0 20px 56px rgba(0, 0, 0, 0.3);
}
.conservation-stat-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 0%, rgba(220, 38, 38, 0.07), transparent 65%);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.4s ease;
}
.conservation-stat-card:hover .conservation-stat-glow {
  opacity: 1;
}
.conservation-stat-number {
  display: block;
  font-family: "Alegreya", "Source Han Serif SC", serif;
  font-size: 48px;
  font-weight: 800;
  background: linear-gradient(135deg, #f87171, #dc2626);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.1;
  margin-bottom: 8px;
}
.conservation-stat-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--heading-color, #f1f5f9);
  margin-bottom: 10px;
}
.conservation-stat-desc {
  font-size: 13px;
  line-height: 1.65;
  color: rgba(226, 232, 240, 0.45);
  margin: 0;
}

.conservation-topics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18px;
  margin-bottom: 48px;
}
.conservation-topic {
  display: flex;
  gap: 16px;
  padding: 24px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.018);
  border: 1px solid rgba(255, 255, 255, 0.05);
  text-align: left;
  transition: all 0.3s ease;
}
.conservation-topic:hover {
  border-color: rgba(94, 234, 212, 0.15);
  background: rgba(255, 255, 255, 0.028);
}
.topic-icon {
  width: 44px;
  height: 44px;
  border-radius: 13px;
  background: rgba(94, 234, 212, 0.1);
  color: #5eead4;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.topic-icon svg {
  width: 22px;
  height: 22px;
}
.topic-content h4 {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 600;
  color: var(--heading-color, #f1f5f9);
}
.topic-content p {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(226, 232, 240, 0.45);
}

.conservation-cta {
  position: relative;
  padding: 36px 40px;
  border-radius: 24px;
  background: rgba(94, 234, 212, 0.03);
  border: 1px solid rgba(94, 234, 212, 0.1);
  overflow: hidden;
}
.conservation-cta-bg {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 30% 50%, rgba(94, 234, 212, 0.06), transparent 60%);
  pointer-events: none;
}
.conservation-cta-content {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  text-align: left;
}
.conservation-cta-content svg {
  width: 28px;
  height: 28px;
  color: #5eead4;
  flex-shrink: 0;
  margin-top: 2px;
}
.conservation-cta-content h4 {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 700;
  color: var(--heading-color, #f1f5f9);
}
.conservation-cta-content p {
  margin: 0;
  font-size: 14px;
  line-height: 1.75;
  color: rgba(226, 232, 240, 0.52);
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
  .hero {
    flex-direction: column;
    justify-content: center;
    padding: 82px 22px 54px;
  }

  .hero-content {
    margin-right: 0;
    text-align: center;
  }

  .hero-showcase {
    width: min(100%, 560px);
    min-height: 430px;
  }

  .migration-card {
    transform: none;
    min-height: 270px;
  }

  .hero-subtitle {
    margin-left: auto;
    margin-right: auto;
  }

  .hero-actions {
    justify-content: center;
  }

  .feature-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .feature-card {
    padding: 28px 24px 26px;
  }

  .conversation-grid,
  .conservation-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .conservation-topics {
    grid-template-columns: 1fr;
    gap: 14px;
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
    font-size: 42px;
  }

  .hero-showcase {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .migration-card,
  .taxonomy-card,
  .specimen-card {
    min-height: 180px;
    border-radius: 18px;
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
    justify-content: center;
    width: 100%;
    padding: 14px 22px;
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

  .conservation-stat-card {
    padding: 28px 20px 24px;
  }

  .conservation-stat-number {
    font-size: 36px;
  }

  .conservation-topic {
    padding: 18px;
  }

  .conservation-cta {
    padding: 24px 20px;
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
