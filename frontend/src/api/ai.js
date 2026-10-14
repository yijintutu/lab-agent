import request from '@/utils/request'

export function chatApi(data) {
  return request({
    url: '/api/ai/chat',
    method: 'post',
    data,
    timeout: 60000
  })
}

export function rebuildKnowledgeIndexApi() {
  return request({
    url: '/api/ai/kb/rebuild',
    method: 'post',
    timeout: 120000
  })
}
