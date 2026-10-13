<template>
  <el-card>
    <div>欢迎您：{{ userInfo?.name }}！</div>
    <div style="margin-top: 8px; color: #909399">角色：{{ userInfo?.role }}</div>
  </el-card>
</template>

<script setup>
import { useUser } from '@/utils/user'
const { userInfo } = useUser()
</script>
