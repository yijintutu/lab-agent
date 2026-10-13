import request from '@/utils/request'

export function uploadFileApi(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/api/files/upload',
    method: 'post',
    data: formData
    // 不要手动写 Content-Type，交给浏览器
  })
}
