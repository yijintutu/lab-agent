<template>
  <div class="login-container">
    <div class="login-card">
      <h2 class="title">实验室预约系统</h2>
      <p class="subtitle">基于Agent智能预约系统</p>

      <el-form ref="formRef" :model="form" :rules="rules" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="login"
            @submit.prevent
          />
        </el-form-item>

        <el-button type="primary" class="login-btn" size="large" :loading="loading" @click="login">
          登录
        </el-button>
      </el-form>

      <p class="tip">
        还没有账号？
        <router-link to="/register" class="link">请注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { loginApi } from '@/api/auth'
import { useUser } from '@/utils/user'

const { saveLoginData } = useUser()

const formRef = ref() // 用于表单验证的引用

const form = reactive({
  username: '',
  password: ''
})

const loading = ref(false)

// 表单验证规则
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const login = async () => {
  // 先进行表单验证
  const isValid = await formRef.value.validate().catch(() => false)
  if (!isValid) return

  loading.value = true
  try {
    const res = await loginApi(form)
    if (res.code === 200) {
      saveLoginData(res.data)
      ElMessage.success('登录成功')
      await router.push('/manager/home')
    }
  } catch (err) {
    // 错误提示已由 utils/request.js 的响应拦截器统一弹出，这里不再重复 ElMessage
    console.error('登录失败：', err)
  } finally {
    // 无论成功还是失败，都恢复按钮状态，避免永久 loading
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
}

.login-card {
  width: 380px;
  padding: 40px 36px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.title {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 6px;
}

.subtitle {
  text-align: center;
  font-size: 13px;
  color: #909399;
  margin-bottom: 28px;
}

.login-form {
  margin-top: 8px;
}

.login-btn {
  width: 100%;
}

.tip {
  text-align: center;
  font-size: 13px;
  color: #909399;
  margin-top: 16px;
}

.link {
  color: #409eff;
  text-decoration: none;
}
</style>
