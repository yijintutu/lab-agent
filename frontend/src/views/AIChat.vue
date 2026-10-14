<template>
  <el-card class="chat-card">
    <template #header>
      <div class="title">AI 智能助手</div>
    </template>

    <div ref="listRef" class="message-list" aria-live="polite">
      <div
        v-for="(item, index) in messages"
        :key="index"
        class="message-row"
        :class="item.role === 'user' ? 'user-row' : 'assistant-row'"
      >
        <div class="message-bubble" :class="item.role === 'user' ? 'user-bubble' : ''">
          {{ item.content }}
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
        placeholder="问问实验室预约流程……"
        :disabled="loading"
        @keydown.enter.exact.prevent="handleSend"
        @keydown.enter.shift.stop
      />
      <el-button type="primary" :loading="loading" :disabled="!input.trim()" @click="handleSend">
        发送
      </el-button>
    </div>
    <div class="hint">当前助手不能查询实时实验室、设备和预约状态。Enter 发送，Shift + Enter 换行。</div>
  </el-card>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { chatApi } from '@/api/ai'

const messages = ref([
  {
    role: 'assistant',
    content: '您好，我是实验室助手，可以介绍预约流程。具体实验室和设备信息请查看系统列表。'
  }
])
const history = ref([])
const input = ref('')
const loading = ref(false)
const listRef = ref(null)

function scrollToBottom() {
  nextTick(() => {
    if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
  })
}

async function handleSend() {
  const content = input.value.trim()
  if (!content || loading.value) return

  history.value.push({ role: 'user', content })
  history.value = history.value.slice(-40)
  messages.value.push({ role: 'user', content })
  input.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const result = await chatApi({ messages: history.value })
    if (result?.code === 200 && result.data?.role === 'assistant' && result.data.content) {
      messages.value.push(result.data)
      history.value.push(result.data)
      history.value = history.value.slice(-40)
    } else {
      const message = result?.message || '助手暂时无法回答，请稍后重试。'
      messages.value.push({ role: 'assistant', content: message })
    }
  } catch (error) {
    const message = error?.message || error?.response?.data?.message || '网络异常，请稍后重试。'
    messages.value.push({ role: 'assistant', content: `本次请求失败：${message}` })
  } finally {
    loading.value = false
    scrollToBottom()
  }
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
  margin-bottom: 12px;
}
.user-row {
  justify-content: flex-end;
}
.assistant-row {
  justify-content: flex-start;
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
}
</style>
