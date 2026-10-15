<template>
  <div class="spatial-chat-container">
    <!-- Bento 顶部状态与操作网格 -->
    <div class="bento-card chat-header-card">
      <div class="header-left">
        <div class="pill-badge">
          <span class="pulse-dot"></span>
          <span>AGENT_RUNTIME: ACTIVE</span>
        </div>
        <h2 class="chat-title">AI 智能预约助手</h2>
      </div>
      <div class="header-actions">
        <el-button class="spatial-btn-secondary" :disabled="loading" @click="startNewConversation">
          新对话
        </el-button>
        <el-button
          v-if="userInfo?.role === 'admin'"
          class="spatial-btn-secondary admin-btn"
          :loading="rebuilding"
          @click="handleRebuildIndex"
        >
          重建知识库
        </el-button>
      </div>
    </div>

    <!-- 主对话工作区 Bento 容器 -->
    <div class="bento-card chat-workspace-card">
      <div ref="listRef" class="message-list" aria-live="polite">
        <div
          v-for="(item, index) in messages"
          :key="index"
          class="message-row"
          :class="item.role === 'user' ? 'user-row' : 'assistant-row'"
        >
          <div
            class="message-bubble"
            :class="item.role === 'user' ? 'user-bubble' : 'assistant-bubble'"
          >
            <!-- 预约草案待确认标签 -->
            <div v-if="item.pending_confirmation" class="confirmation-label">
              ⚡ 检测到预约草案，请核对并确认：
            </div>

            <!-- Agent 实时状态指示 -->
            <div v-if="item.role === 'assistant' && item.status" class="assistant-status">
              <span class="status-spinner"></span> {{ item.status }}
            </div>

            <!-- Agent 工具调用步骤流 -->
            <div v-if="item.role === 'assistant' && item.steps?.length" class="assistant-steps">
              <div v-for="(step, stepIndex) in item.steps" :key="stepIndex" class="step-item">
                <span class="step-bullet">▸</span> {{ step }}
              </div>
            </div>

            <!-- 消息正文 -->
            <div class="message-text">{{ item.content }}</div>

            <!-- 确认 / 取消预约交互按钮 -->
            <div
              v-if="item.role === 'assistant' && item.pending_confirmation"
              class="confirmation-actions"
            >
              <el-button
                type="primary"
                size="small"
                class="spatial-btn-primary"
                :disabled="loading"
                @click="sendConfirmation('确认预约')"
              >
                确认预约
              </el-button>
              <el-button
                size="small"
                class="spatial-btn-secondary"
                :disabled="loading"
                @click="sendConfirmation('取消预约')"
              >
                放弃预约
              </el-button>
            </div>
          </div>

          <!-- RAG 参考资料来源 -->
          <div v-if="item.sources?.length" class="sources-tag">
            📚 参考资料：{{ item.sources.map((source) => source.source).join('、') }}
          </div>
        </div>
      </div>

      <!-- 输入控制台 (Composer) -->
      <div class="composer-zone">
        <div class="composer-box">
          <el-input
            v-model="input"
            type="textarea"
            :rows="2"
            maxlength="8000"
            show-word-limit
            placeholder="问问实验室预约规则，或描述你的预约需求（例如：帮我预约明天下午人工智能实验室）……"
            :disabled="loading"
            class="spatial-textarea"
            @keydown.enter.exact.prevent="handleSend"
            @keydown.enter.shift.stop
          />
          <el-button
            type="primary"
            class="spatial-send-btn"
            :loading="loading"
            :disabled="!input.trim()"
            @click="handleSend"
          >
            发送 ↵
          </el-button>
        </div>
        <div class="hint-text">
          💡 提示：实时状态由后端查询。预约会先核验并展示草案；只有回复“确认预约”才会提交。Enter
          发送，Shift + Enter 换行。
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { chatApi, chatStreamApi, rebuildKnowledgeIndexApi } from '@/api/ai'
import { useUser } from '@/utils/user'

const { userInfo } = useUser()

function welcomeMessage() {
  return {
    role: 'assistant',
    content:
      '您好，我是实验室助手。可以问我预约规则、实验室介绍和设备说明，也可以查询当前开放标记及设备状态。预约提交后需要管理员审核。'
  }
}

const conversationStorageKey = `lab-ai-thread:${userInfo.value?.id ?? 'unknown'}`

function restoreConversation() {
  try {
    const raw = sessionStorage.getItem(conversationStorageKey)
    if (!raw) return null
    const saved = JSON.parse(raw)
    if (
      typeof saved?.threadId === 'string' &&
      Array.isArray(saved.messages) &&
      saved.messages.every(
        (item) =>
          item &&
          (item.role === 'user' || item.role === 'assistant') &&
          typeof item.content === 'string'
      )
    ) {
      return saved
    }
  } catch {
    // Start with a fresh view when session storage contains invalid data.
  }
  return null
}

const restoredConversation = restoreConversation()

function saveConversation() {
  if (!threadId.value) return
  try {
    sessionStorage.setItem(
      conversationStorageKey,
      JSON.stringify({ threadId: threadId.value, messages: messages.value })
    )
  } catch {
    // The active chat still works in memory if browser storage is unavailable.
  }
}

const messages = ref([welcomeMessage()])
const threadId = ref(restoredConversation?.threadId || null)
if (restoredConversation?.messages?.length) {
  messages.value = restoredConversation.messages
}
const input = ref('')
const loading = ref(false)
const rebuilding = ref(false)
const listRef = ref(null)

function scrollToBottom() {
  nextTick(() => {
    if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
  })
}

function startNewConversation() {
  if (loading.value) return
  threadId.value = null
  try {
    sessionStorage.removeItem(conversationStorageKey)
  } catch {
    // The in-memory conversation still resets.
  }
  messages.value = [welcomeMessage()]
  input.value = ''
  scrollToBottom()
}

async function handleRebuildIndex() {
  if (rebuilding.value) return
  rebuilding.value = true
  try {
    const result = await rebuildKnowledgeIndexApi()
    if (result?.code === 200) {
      ElMessage.success(
        `知识库已更新：${result.data.document_count} 份资料，${result.data.chunk_count} 个文本块`
      )
    } else {
      ElMessage.error(result?.message || '知识库重建失败')
    }
  } catch (error) {
    ElMessage.error(error?.message || '知识库重建失败，请检查 Embedding 配置')
  } finally {
    rebuilding.value = false
  }
}

async function handleSend() {
  const content = input.value.trim()
  if (!content || loading.value) return

  const pendingMessage = [...messages.value]
    .reverse()
    .find((item) => item.role === 'assistant' && item.pending_confirmation)
  if (pendingMessage) pendingMessage.pending_confirmation = false

  messages.value.push({ role: 'user', content })
  saveConversation()
  input.value = ''
  loading.value = true
  scrollToBottom()

  const assistant = reactive({
    role: 'assistant',
    content: '',
    status: '正在思考…',
    steps: [],
    sources: []
  })
  messages.value.push(assistant)

  try {
    await chatStreamApi(
      {
        message: content,
        thread_id: threadId.value || undefined
      },
      (evt) => {
        if (evt?.type === 'meta' && evt.thread_id) {
          threadId.value = evt.thread_id
          assistant.status = '正在思考…'
          return
        }
        if (evt?.type === 'status') {
          assistant.status = evt.message || '正在思考…'
        } else if (evt?.type === 'tool_start') {
          const label = evt.label || evt.name || '工具'
          assistant.status = `正在${label}…`
          assistant.steps.push(`开始：${label}`)
        } else if (evt?.type === 'tool_end') {
          const label = evt.label || evt.name || '工具'
          assistant.status = `${label}完成`
          if (evt.name === 'prepare_reservation') {
            assistant.steps.push(`完成：${label}`)
          } else if (evt.preview) {
            assistant.steps.push(`完成：${label}：${evt.preview}`)
          } else {
            assistant.steps.push(`完成：${label}`)
          }
        } else if (evt?.type === 'confirmation') {
          assistant.status = ''
          assistant.content = evt.message || '请确认预约草案。'
          assistant.pending_confirmation = true
        } else if (evt?.type === 'token') {
          assistant.content += evt.content || ''
          assistant.status = ''
        } else if (evt?.type === 'done') {
          assistant.status = ''
        } else if (evt?.type === 'error') {
          assistant.status = ''
          if (pendingMessage) pendingMessage.pending_confirmation = true
          if (!assistant.content) {
            assistant.content = evt.message || '请求失败'
          }
          ElMessage.error(evt.message || '请求失败')
        }
        scrollToBottom()
      }
    )
  } catch (error) {
    const message = error?.message || '网络异常，请稍后重试。'
    assistant.status = ''
    if (pendingMessage) pendingMessage.pending_confirmation = true
    if (!assistant.content) {
      assistant.content = `本次请求失败：${message}`
    }
    ElMessage.error(message)
  } finally {
    loading.value = false
    assistant.status = ''
    saveConversation()
    scrollToBottom()
  }
}

function sendConfirmation(answer) {
  if (loading.value) return
  input.value = answer
  handleSend()
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.spatial-chat-container {
  max-width: 1100px;
  margin: 0 auto;
  font-family:
    'Inter',
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    Roboto,
    sans-serif;
  color: #0f172a;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px 4px;
}

/* Bento Card 通用现代风格 */
.bento-card {
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 20px;
  padding: 20px 24px;
  box-shadow:
    0 1px 3px rgba(15, 23, 42, 0.03),
    0 4px 12px rgba(15, 23, 42, 0.015);
}

/* 顶部 Header 卡片 */
.chat-header-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  margin-bottom: 6px;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  background: #6366f1;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.chat-title {
  font-size: 22px;
  font-weight: 800;
  color: #0f172a;
  margin: 0;
  letter-spacing: -0.02em;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.spatial-btn-secondary {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #334155;
  border-radius: 10px;
  font-weight: 600;
  padding: 10px 16px;
  transition: all 0.2s ease;
}

.spatial-btn-secondary:hover {
  background: #eef2ff;
  border-color: #c7d2fe;
  color: #4338ca;
}

.spatial-btn-primary {
  background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
  border: none;
  border-radius: 10px;
  font-weight: 600;
  padding: 10px 20px;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
  transition: all 0.2s ease;
}

.spatial-btn-primary:hover {
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35);
  transform: translateY(-1px);
}

/* 聊天工作区 */
.chat-workspace-card {
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.message-list {
  height: min(62vh, 580px);
  min-height: 360px;
  overflow-y: auto;
  padding: 12px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-row {
  align-items: flex-end;
}

.assistant-row {
  align-items: flex-start;
}

.message-bubble {
  max-width: 80%;
  padding: 14px 18px;
  border-radius: 16px;
  background: #ffffff;
  color: #1e293b;
  line-height: 1.6;
  font-size: 14px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.02);
}

.user-bubble {
  background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
  color: #ffffff;
  border: none;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
}

.assistant-status {
  margin-bottom: 6px;
  font-size: 12px;
  color: #6366f1;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

.assistant-steps {
  margin-bottom: 10px;
  padding: 8px 12px;
  background: #f1f5f9;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.5;
  color: #64748b;
  border-left: 3px solid #6366f1;
}

.step-item {
  margin: 2px 0;
}

.step-bullet {
  color: #6366f1;
  font-weight: bold;
}

.confirmation-label {
  margin-bottom: 8px;
  color: #d97706;
  font-size: 13px;
  font-weight: 700;
}

.confirmation-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.sources-tag {
  margin: 4px 12px 0;
  color: #94a3b8;
  font-size: 11px;
}

/* 输入控制台区域 */
.composer-zone {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.composer-box {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 10px 14px;
  transition: all 0.2s ease;
}

.composer-box:focus-within {
  border-color: #6366f1;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

:deep(.spatial-textarea .el-textarea__inner) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  color: #0f172a !important;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
}

.spatial-send-btn {
  background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
  border: none;
  border-radius: 10px;
  font-weight: 600;
  padding: 10px 20px;
  height: 40px;
  flex-shrink: 0;
}

.hint-text {
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.5;
  padding-left: 4px;
}
</style>
