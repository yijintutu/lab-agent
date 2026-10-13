//  存储token、存储用户信息、获取token、用户信息，删除token、用户信息这些作用
const TOKEN_KEY = 'token' // 定义 token 在 localStorage 中使用的键名，统一管理避免写错
const USER_KEY = 'userInfo' // 定义用户信息在 localStorage 中使用的键名

export function getToken() {
  // 导出获取 token 的函数，其他文件可以通过 import 使用
  return localStorage.getItem(TOKEN_KEY) // 从 localStorage 读取 token；如果不存在会返回 null
} // getToken 函数结束

export function setToken(token) {
  // 导出设置 token 的函数，参数 token 是调用方传入的 token 值
  localStorage.setItem(TOKEN_KEY, token) // 把 token 写入 localStorage；localStorage 最终会以字符串形式保存
} // setToken 函数结束

export function removeToken() {
  // 导出删除 token 的函数
  localStorage.removeItem(TOKEN_KEY) // 从 localStorage 中删除 token 对应的数据
} // removeToken 函数结束

export function getUserInfo() {
  // 导出获取用户信息的函数
  const str = localStorage.getItem(USER_KEY) // 先读取用户信息的原始字符串；如果不存在会得到 null
  return str ? JSON.parse(str) : null // 如果有字符串，就用 JSON.parse 转成对象；否则返回 null
} // getUserInfo 函数结束

export function setUserInfo(userInfo) {
  // 导出设置用户信息的函数，参数 userInfo 通常是对象
  localStorage.setItem(USER_KEY, JSON.stringify(userInfo)) // 先把对象转成 JSON 字符串，再存入 localStorage
} // setUserInfo 函数结束

export function removeUserInfo() {
  // 导出删除用户信息的函数
  localStorage.removeItem(USER_KEY) // 从 localStorage 中删除用户信息对应的数据
} // removeUserInfo 函数结束

// 登出
export function logout() {
  // 导出登出函数，用来统一清理登录状态
  removeToken() // 调用上面封装好的方法，删除 token
  removeUserInfo() // 调用上面封装好的方法，删除用户信息
} // logout 函数结束
