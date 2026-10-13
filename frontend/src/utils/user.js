import { ref } from 'vue' // 从 Vue 导入 ref，用于创建响应式数据
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getUserInfo, setToken, setUserInfo, logout as clearAuth } from './auth' // 从 auth 模块导入读取用户信息、保存 token、保存用户信息的方法

const userInfo = ref(getUserInfo()) // 创建响应式对象 userInfo，初始值来自 localStorage 中读取的用户信息；可以是对象或 null

export function useUser() {
  const router = useRouter() // 必须在 useUser() 内部调用（setup 上下文），不能写在模块顶层

  // 导出 useUser 自定义组合式函数，供组件调用
  function saveLoginData(data) {
    // 定义保存登录数据的函数，参数 data 通常包含 token 和 user
    setToken(data.token) // 把 data.token 保存到 localStorage
    setUserInfo(data.user) // 把 data.user 保存到 localStorage
    userInfo.value = data.user // 同步更新响应式 userInfo，让页面立即感知用户变化
  } // saveLoginData 结束

  function logout() {
    clearAuth() // 清 localStorage（auth.js 的纯工具）
    userInfo.value = null // 重置响应式状态
    ElMessage.success('已退出登录')
    router.push('/login')
  }

  function updateUser(user) {
    // 定义更新用户信息的函数，参数 user 是新的用户对象
    setUserInfo(user) // 把新的用户对象写入 localStorage
    userInfo.value = user // 更新响应式 userInfo
  } // updateUser 结束

  function reloadUser() {
    // 定义重新加载用户信息的函数
    userInfo.value = getUserInfo() // 从 localStorage 重新读取用户信息，并同步到响应式 userInfo
  } // reloadUser 结束
  return {
    // 返回一个对象，暴露给调用方使用
    userInfo, // 响应式用户信息，组件模板中可直接使用
    saveLoginData, // 登录成功后保存数据的方法
    logout, // 登出方法
    updateUser, // 更新用户信息的方法
    reloadUser // 重新从本地存储加载用户信息的方法
  } // return 对象结束
} // useUser 函数结束
