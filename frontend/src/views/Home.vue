<template>
  <div class="bento-container">
    <!-- Bento Grid 网格布局主体 -->
    <div class="bento-grid">
      <!-- 卡片 1: 个人身份与 WELCOME HERO (大号 span-8) -->
      <div class="bento-card hero-card">
        <div class="hero-bg-glow"></div>
        <div class="hero-content">
          <div class="pill-badge">
            <span class="pulse-dot"></span>
            <span>Spatial Lab System v2.0</span>
          </div>
          <h1 class="hero-title">
            你好，<span class="name-gradient">{{ userInfo?.name || '同学' }}</span>
          </h1>
          <p class="hero-subtitle">
            欢迎使用智能实验室预约系统 <span class="dot-sep">•</span> 当前身份：<span
              class="role-highlight"
              >{{ roleLabel }}</span
            >
          </p>
        </div>
        <div class="hero-action">
          <el-button
            type="primary"
            class="spatial-btn-primary"
            @click="$router.push('/manager/ai-chat')"
          >
            <el-icon class="btn-icon"><Sparkles /></el-icon>
            打开 AI 助手
          </el-button>
        </div>
      </div>

      <!-- 卡片 2: 天气与实验室环境卡片 (span-4)，点击跳转 AI 助手 -->
      <div
        class="bento-card weather-hub-card"
        @click="$router.push('/manager/ai-chat')"
        title="点击向 AI 助手查询环境详情"
      >
        <div class="card-header-sm">
          <span class="card-tag">LAB ENVIRONMENT</span>
          <span class="live-pill weather-pill">{{ weather.temp }} {{ weather.condition }}</span>
        </div>
        <div class="weather-content-wrap">
          <div class="weather-main-info">
            <div class="weather-icon-inner">{{ weather.icon }}</div>
            <div class="weather-temp-box">
              <span class="temp-val">{{ weather.temp }}</span>
              <span class="temp-sub">环境：{{ weather.condition }}</span>
            </div>
          </div>
          <div class="weather-details">
            <span>湿度：{{ weather.humidity }}</span>
            <span>风速：{{ weather.wind }}</span>
          </div>
        </div>
        <div class="agent-info">
          <div class="agent-title">实验室微气候监控</div>
        </div>
        <div class="card-arrow-link">AI 预约实验室 ➔</div>
      </div>

      <!-- 卡片 3, 4, 5: 核心数据指标小组件 (各自 span-4) -->
      <div
        v-for="(item, idx) in statCards"
        :key="item.label"
        class="bento-card stat-metric-card"
        :class="`metric-${idx}`"
      >
        <div class="metric-top">
          <span class="metric-label">{{ item.label }}</span>
          <div class="metric-icon-dot"></div>
        </div>
        <div class="metric-num-wrap">
          <span class="metric-value">{{ item.value }}</span>
          <span class="metric-unit" v-if="idx === 0">间</span>
          <span class="metric-unit" v-else-if="idx === 1">项</span>
        </div>
        <div class="metric-trend-bar">
          <div class="trend-fill" :style="{ width: idx === 2 ? '100%' : '65%' }"></div>
        </div>
      </div>

      <!-- 卡片 6: 系统能力与机制矩阵 (Bento Span-8) -->
      <div class="bento-card features-grid-card">
        <div class="card-header-main">
          <div class="header-title-group">
            <span class="section-badge">CAPABILITIES</span>
            <h3 class="section-heading">系统能做什么</h3>
          </div>
        </div>
        <div class="features-list">
          <div v-for="(feat, fIdx) in features" :key="feat.title" class="feature-item">
            <div class="feature-num">0{{ fIdx + 1 }}</div>
            <div class="feature-body">
              <div class="feature-title">{{ feat.title }}</div>
              <div class="feature-desc">{{ feat.desc }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 卡片 7: 快捷导航与状态路由 (Bento Span-4) -->
      <div class="bento-card shortcuts-card">
        <div class="card-header-main">
          <span class="section-badge">NAVIGATION</span>
          <h3 class="section-heading">快捷入口</h3>
        </div>
        <div class="shortcuts-grid">
          <button
            v-for="item in shortcuts"
            :key="item.path"
            class="spatial-nav-chip"
            @click="$router.push(item.path)"
          >
            <span class="chip-text">{{ item.label }}</span>
            <span class="chip-icon">↗</span>
          </button>
        </div>
      </div>

      <!-- 卡片 8: 空间健康度/硬件负载 (Bento Span-12 底部常驻条) -->
      <div class="bento-card system-health-bar">
        <div class="health-item">
          <span class="health-dot green"></span>
          <span class="health-label">API 状态：</span>
          <span class="health-val">正常 (200 OK)</span>
        </div>
        <div class="health-divider"></div>
        <div class="health-item">
          <span class="health-dot blue"></span>
          <span class="health-label">冲突检测引擎：</span>
          <span class="health-val">已就绪</span>
        </div>
        <div class="health-divider"></div>
        <div class="health-item">
          <span class="health-dot purple"></span>
          <span class="health-label">RAG 知识库：</span>
          <span class="health-val">索引同步中</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useUser } from '@/utils/user'
import { getLabPageList } from '@/api/lab'
import { getReservationPageList } from '@/api/reservation'

const { userInfo } = useUser()

const labTotal = ref('-')
const reservationTotal = ref('-')

const roleLabel = computed(() => (userInfo.value?.role === 'admin' ? '管理员' : '学生'))

const statCards = computed(() => [
  { label: '开放实验室', value: labTotal.value },
  { label: '关联预约数', value: reservationTotal.value },
  { label: 'AI Agent 引擎', value: '已接入' }
])

const features = [
  {
    title: '业务预约流程',
    desc: '实验室与设备直观浏览，快速提交预约及多状态审核闭环。'
  },
  {
    title: 'RAG 规则检索',
    desc: '基于知识库精准问答，实时解答开放时段与实验室规章制度。'
  },
  {
    title: '智能 Agent 编排',
    desc: 'Tool Calling + LangGraph 流式过程透明化，多轮确认后自动落库。'
  }
]

const shortcuts = computed(() => {
  const list = [
    { label: 'AI 智能助手', path: '/manager/ai-chat' },
    { label: '实验室列表', path: '/manager/lablist' },
    { label: '我的预约', path: '/manager/my-reservation' }
  ]
  if (userInfo.value?.role === 'admin') {
    list.push(
      { label: '预约审核', path: '/manager/audit-reservation' },
      { label: '实验室管理', path: '/manager/lab' },
      { label: '设备管理', path: '/manager/equipment' },
      { label: '用户管理', path: '/manager/user' }
    )
  }
  return list
})

onMounted(async () => {
  try {
    const labRes = await getLabPageList({ page: 1, page_size: 1, status: 1 })
    if (labRes.code === 200) labTotal.value = labRes.data?.total ?? 0
  } catch {
    labTotal.value = '-'
  }
  try {
    const resRes = await getReservationPageList({ page: 1, page_size: 1 })
    if (resRes.code === 200) reservationTotal.value = resRes.data?.total ?? 0
  } catch {
    reservationTotal.value = '-'
  }
})

// 定义真实的响应式天气状态
const weather = ref({
  temp: '--',
  condition: '加载中...',
  humidity: '--',
  wind: '--',
  icon: '🌤️'
})

// 异步获取真实天气数据
async function fetchRealWeather(cityName = 'Shenzhen') {
  try {
    // 使用 encodeURIComponent 确保中文或带空格的城市名能被正确解析
    const encodedCity = encodeURIComponent(cityName)
    const response = await fetch(`https://wttr.in/${encodedCity}?format=j1`)
    const data = await response.json()

    const current = data.current_condition[0]
    const tempC = current.temp_C
    const desc = current.weatherDesc[0].value
    const humidity = current.humidity
    const windSpeed = current.windspeedKmph

    weather.value = {
      temp: `${tempC}°C`,
      condition: translateCondition(desc),
      humidity: `${humidity}%`,
      wind: `${windSpeed}km/h`,
      icon: getWeatherIcon(desc)
    }
  } catch (error) {
    // 网络不通或异常时的降级显示
    weather.value = {
      temp: '22°C',
      condition: '晴间多云',
      humidity: '45%',
      wind: '2m/s',
      icon: '🌤️'
    }
  }
}

// 辅助函数：根据天气描述匹配图标
function getWeatherIcon(desc) {
  const d = desc.toLowerCase()
  if (d.includes('rain')) return '🌧️'
  if (d.includes('cloud')) return '☁️'
  if (d.includes('snow')) return '❄️'
  return '☀️'
}

// 简单的英文天气描述转中文（可按需增减）
function translateCondition(desc) {
  const map = {
    Sunny: '晴',
    Clear: '晴',
    'Partly cloudy': '多云',
    Cloudy: '阴',
    Overcast: '阴',
    'Light rain': '小雨',
    'Moderate rain': '中雨'
  }
  for (const [en, cn] of Object.entries(map)) {
    if (desc.toLowerCase().includes(en.toLowerCase())) return cn
  }
  return desc // 默认返回原英文或统一样式
}

// 在 onMounted 中与实验室、预约数据一起加载
onMounted(async () => {
  // 1. 获取天气
  fetchRealWeather()

  // 2. 原有的实验室与预约统计请求...
  try {
    const labRes = await getLabPageList({ page: 1, page_size: 1, status: 1 })
    if (labRes.code === 200) labTotal.value = labRes.data?.total ?? 0
  } catch {
    labTotal.value = '-'
  }
  try {
    const resRes = await getReservationPageList({ page: 1, page_size: 1 })
    if (resRes.code === 200) reservationTotal.value = resRes.data?.total ?? 0
  } catch {
    reservationTotal.value = '-'
  }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.bento-container {
  padding: 12px 4px;
  font-family:
    'Inter',
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    Roboto,
    sans-serif;
  color: #0f172a;
  background-color: #f8fafc;
  min-height: 100vh;
}

/* Bento 12列响应式网格 */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 16px;
  max-width: 1280px;
  margin: 0 auto;
}

/* 通用圆角与发光卡片样式 */
.bento-card {
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 20px;
  padding: 24px;
  position: relative;
  overflow: hidden;
  box-shadow:
    0 1px 3px rgba(15, 23, 42, 0.03),
    0 4px 12px rgba(15, 23, 42, 0.015);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.bento-card:hover {
  transform: translateY(-2px);
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow:
    0 12px 28px -6px rgba(99, 102, 241, 0.08),
    0 4px 12px -2px rgba(15, 23, 42, 0.04);
}

/* 卡片 1: Hero Welcome */
.hero-card {
  grid-column: span 8;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 200px;
  background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
}

.hero-bg-glow {
  position: absolute;
  top: -40px;
  right: -40px;
  width: 220px;
  height: 220px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.12) 0%, rgba(255, 255, 255, 0) 70%);
  border-radius: 50%;
  pointer-events: none;
}

.pill-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.08);
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  color: #4f46e5;
  margin-bottom: 12px;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  background: #6366f1;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.hero-title {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 0;
  color: #0f172a;
}

.name-gradient {
  background: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-subtitle {
  margin-top: 8px;
  font-size: 14px;
  color: #64748b;
}

.dot-sep {
  margin: 0 4px;
  color: #cbd5e1;
}

.role-highlight {
  font-weight: 600;
  color: #334155;
}

.hero-action {
  margin-top: 20px;
}

.spatial-btn-primary {
  background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.25);
  transition: all 0.2s ease;
}

.spatial-btn-primary:hover {
  box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35);
  transform: scale(1.02);
}

/* 卡片 2: 天气与实验室环境卡片样式 */
.weather-hub-card {
  grid-column: span 4;
  background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
  color: #ffffff;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.weather-hub-card:hover {
  border-color: #38bdf8;
}

.card-header-sm {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-tag {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #94a3b8;
}

.weather-pill {
  font-size: 11px;
  font-weight: 700;
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  padding: 2px 8px;
  border-radius: 10px;
}

.weather-content-wrap {
  margin: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.weather-main-info {
  display: flex;
  align-items: center;
  gap: 14px;
}

.weather-icon-inner {
  font-size: 32px;
}

.weather-temp-box {
  display: flex;
  flex-direction: column;
}

.temp-val {
  font-size: 24px;
  font-weight: 800;
  color: #f8fafc;
  letter-spacing: -0.02em;
}

.temp-sub {
  font-size: 11px;
  color: #38bdf8;
}

.weather-details {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.05);
  padding: 6px 10px;
  border-radius: 8px;
}

.agent-info {
  margin-top: 4px;
}

.agent-title {
  font-size: 15px;
  font-weight: 700;
  color: #f8fafc;
}

.agent-desc {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
  line-height: 1.4;
}

.card-arrow-link {
  font-size: 12px;
  font-weight: 600;
  color: #38bdf8;
  margin-top: 10px;
}

/* 卡片 3, 4, 5: Metric Cards */
.stat-metric-card {
  grid-column: span 4;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 120px;
}

.metric-label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.metric-icon-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e2e8f0;
}

.metric-num-wrap {
  margin-top: 8px;
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.metric-value {
  font-size: 32px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.03em;
}

.metric-unit {
  font-size: 12px;
  color: #94a3b8;
}

.metric-trend-bar {
  width: 100%;
  height: 4px;
  background: #f1f5f9;
  border-radius: 2px;
  margin-top: 16px;
  overflow: hidden;
}

.trend-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1 0%, #3b82f6 100%);
  border-radius: 2px;
}

/* 卡片 6: Features Grid */
.features-grid-card {
  grid-column: span 8;
}

.section-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #6366f1;
  display: block;
  margin-bottom: 2px;
}

.section-heading {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f1f5f9;
}

.feature-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.feature-num {
  font-size: 12px;
  font-weight: 800;
  color: #818cf8;
  background: #eef2ff;
  padding: 4px 8px;
  border-radius: 8px;
}

.feature-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.feature-desc {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
  line-height: 1.5;
}

/* 卡片 7: Shortcuts */
.shortcuts-card {
  grid-column: span 4;
}

.shortcuts-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.spatial-nav-chip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  color: #334155;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.spatial-nav-chip:hover {
  background: #eef2ff;
  border-color: #c7d2fe;
  color: #4338ca;
  transform: translateX(2px);
}

.chip-icon {
  font-size: 12px;
  color: #94a3b8;
}

/* 卡片 8: Health Bar */
.system-health-bar {
  grid-column: span 12;
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 14px 24px;
  background: #ffffff;
  border-radius: 14px;
  font-size: 12px;
}

.health-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.health-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.health-dot.green {
  background: #22c55e;
}
.health-dot.blue {
  background: #3b82f6;
}
.health-dot.purple {
  background: #a855f7;
}

.health-label {
  color: #64748b;
  font-weight: 500;
}

.health-val {
  color: #0f172a;
  font-weight: 600;
}

.health-divider {
  width: 1px;
  height: 16px;
  background: #e2e8f0;
}

/* 响应式调整 */
@media (max-width: 992px) {
  .hero-card {
    grid-column: span 12;
  }
  .weather-hub-card {
    grid-column: span 12;
  }
  .stat-metric-card {
    grid-column: span 4;
  }
  .features-grid-card {
    grid-column: span 12;
  }
  .shortcuts-card {
    grid-column: span 12;
  }
}

@media (max-width: 640px) {
  .stat-metric-card {
    grid-column: span 12;
  }
  .system-health-bar {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  .health-divider {
    display: none;
  }
}
</style>
