<template>
  <el-card class="chat-card">
    <template #header>
      <div class="card-header">
        <div class="title">AI 智能助手</div>
        <div class="header-actions">
          <el-button :disabled="loading" @click="startNewConversation">新对话</el-button>
          <el-button
            v-if="userInfo?.role === 'admin'"
            :loading="rebuilding"
            @click="handleRebuildIndex"
          >
            重建知识库
          </el-button>
        </div>
      </div>
    </template>

    <div ref="listRef" class="message-list" aria-live="polite">
      <div
        v-for="(item, index) in messages"
        :key="index"
        class="message-row"
        :class="item.role === 'user' ? 'user-row' : 'assistant-row'"
      >
        <div class="message-bubble" :class="item.role === 'user' ? 'user-bubble' : ''">
          <div v-if="item.pending_confirmation" class="confirmation-label">预约待确认</div>
          <div v-if="item.role === 'assistant' && item.status" class="assistant-status">
            {{ item.status }}
          </div>
          <div
            v-if="item.role === 'assistant' && item.steps?.length"
            class="assistant-steps"
          >
            <div v-for="(step, stepIndex) in item.steps" :key="stepIndex">· {{ step }}</div>
          </div>
          {{ item.content }}
          <div v-if="item.role === 'assistant' && item.pending_confirmation" class="confirmation-actions">
            <el-button
              type="primary"
              size="small"
              :disabled="loading"
              @click="sendConfirmation('确认预约')"
            >
              确认预约
            </el-button>
            <el-button
              size="small"
              :disabled="loading"
              @click="sendConfirmation('取消预约')"
            >
              取消预约
            </el-button>
          </div>
        </div>
        <div v-if="item.sources?.length" class="sources">
          参考资料：{{ item.sources.map((source) => source.source).join('、') }}
        </div>
      </div>
    </div>

    <div class="composer">
      <el-input
        v-model="input"
        type="textarea"
        :rows="2"
        maxlength="8000"
        show-word-limit
        placeholder="问问实验室预约规则，或描述预约需求……"
        :disabled="loading"
        @keydown.enter.exact.prevent="handleSend"
        @keydown.enter.shift.stop
      />
      <el-button type="primary" :loading="loading" :disabled="!input.trim()" @click="handleSend">
        发送
      </el-button>
    </div>
    <div class="hint">
      实时状态由后端查询。预约会先核验并展示草案；只有回复“确认预约”才会提交，回复“取消预约”会放弃。提交后仍需管理员审核。Enter 发送，Shift + Enter 换行。
    </div>
  </el-card>
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
.chat-card {
  max-width: 1000px;
}
.title {
  font-size: 16px;
  font-weight: 600;
}
.card-header,
.header-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.message-list {
  height: min(60vh, 560px);
  min-height: 320px;
  overflow-y: auto;
  padding: 12px;
  border-radius: 6px;
  background: #f7f8fa;
}
.message-row {
  display: flex;
  flex-direction: column;
  margin-bottom: 12px;
}
.user-row {
  align-items: flex-end;
}
.assistant-row {
  align-items: flex-start;
}
.message-bubble {
  max-width: 75%;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  box-shadow: 0 1px 3px rgb(0 0 0 / 8%);
}
.user-bubble {
  background: #409eff;
  color: #fff;
}
.assistant-status {
  margin-bottom: 6px;
  font-size: 12px;
  color: #909399;
}
.assistant-steps {
  margin-bottom: 8px;
  font-size: 12px;
  line-height: 1.5;
  color: #909399;
}
.confirmation-label {
  margin-bottom: 6px;
  color: #b88230;
  font-size: 12px;
  font-weight: 600;
}
.confirmation-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.composer {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  margin-top: 12px;
}
.hint {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
  line-height: 1.6;
}
.sources {
  margin: 4px 8px 0;
  color: #909399;
  font-size: 12px;
}
</style>
