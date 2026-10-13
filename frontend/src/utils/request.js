import axios from 'axios' // 导入 axios 库，用来发送 HTTP 请求
import { getToken, logout } from './auth' // 从 auth 模块导入获取 token 和登出方法
import { ElMessage } from 'element-plus' // 从 Element Plus 导入消息提示组件
import router from '@/router' // 导入 Vue Router 实例，@ 通常表示 src 目录

// 测试连接地址
console.log('测试连接地址：空置', import.meta.env.VITE_API_BASE_URL) // 打印当前环境下的 API 基础 URL，方便调试

const service = axios.create({
  // 创建一个 axios 实例，后续请求都用这个实例
  baseURL: import.meta.env.VITE_API_BASE_URL || '', // 设置请求基础地址，值来自 Vite 环境变量
  timeout: 30000 //30s // 设置请求超时时间，单位毫秒，30000 毫秒等于 30 秒
}) // axios 实例创建结束

// 请求拦截器的配置
service.interceptors.request.use(
  // 注册请求拦截器，请求发出前会先执行这里
  (config) => {
    // 请求成功时的回调，config 是本次请求的配置对象
    const token = getToken() // 从本地存储中获取 token
    if (token) {
      // 如果 token 存在
      config.headers.Authorization = `Bearer ${token}` // 在请求头中加入 Authorization，格式为 Bearer token
    } // if 判断结束
    return config // 返回修改后的请求配置，让请求继续发送
  }, // 请求成功回调结束
  (err) => Promise.reject(err) // 请求配置出错时，直接返回一个失败的 Promise
) // 请求拦截器注册结束

// 返回的拦截器配置
service.interceptors.response.use(
  // 注册响应拦截器，服务器返回响应后会先执行这里
  (res) => {
    // HTTP 响应成功时的回调，res 是 axios 包装后的响应对象
    const data = res.data // 取出后端返回的真正数据体

    // 测试拦截器
    console.log('拦截器测试：', data, 'HTTP 状态码：', res.status, '请求地址：', res.config.url)

    if (data.code !== 200) {
      // 如果业务状态码不是 200，说明业务处理失败
      ElMessage.error(data.message || '请求失败') // 弹出错误提示，优先显示后端返回的 message
      if (data.code === 401) {
        // 如果业务状态码是 401，表示未登录或登录已失效
        logout() // 调用登出方法，清除 token 和用户信息
        router.push('/login') // 跳转到登录页
        return Promise.reject(data) // 返回失败的 Promise，让调用方进入 catch
      } // 401 业务码处理结束
    } // 非 200 业务码处理结束
    return data // 业务码为 200 时，直接返回后端数据；非 401 业务错误也会走到这里
  }, // HTTP 成功响应回调结束
  (err) => {
    // HTTP 响应失败时的回调，比如 4xx、5xx 或网络错误
    if (err.response) {
      // 如果服务器有响应，说明请求到达了服务器
      const httpStatusCode = err.response.status // 获取 HTTP 状态码，比如 401、500
      if (httpStatusCode === 401) {
        // 如果 HTTP 状态码是 401
        ElMessage.error('登录状态已失效，请重新登录') // 提示登录状态失效
        logout() // 清除本地登录状态
        router.push('/login') // 跳转到登录页
      } else {
        // 其他 HTTP 错误，比如 403、500
        ElMessage.error(err.response.data?.message || '请求失败') // 弹出后端 message，没有则用默认提示
      } // HTTP 状态码判断结束
    } else {
      // 没有 response，说明请求没有到达服务器
      // 后端没启动，网络异常了
      ElMessage.error('网络异常，请检查后端服务') // 提示网络异常
    } // 是否有响应判断结束
    return Promise.reject(err) // 继续返回失败的 Promise，交给调用方处理
  } // HTTP 失败响应回调结束
) // 响应拦截器注册结束

export default service // 默认导出 axios 实例，其他文件可以 import service 使用
