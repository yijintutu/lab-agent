<template>
  <div>
    <el-container style="min-height: 100vh">
      <el-header
        style="
          display: flex;
          align-items: center;
          border-bottom: 1px solid #ddd;
          background-color: #fff;
        "
      >
        <div
          style="flex: 1; display: flex; align-items: center; font-size: 24px; font-weight: bold"
        >
          <img style="width: 40px" src="@/assets/imgs/logo.png" alt="" />
          <div style="margin-left: 5px">智能实验室预约系统</div>
        </div>

        <el-dropdown trigger="click" @command="handleCommand">
          <div style="display: flex; align-items: center; cursor: pointer; outline: none">
            <img
              :src="userInfo?.avatar || defaultAvatar"
              alt=""
              style="width: 35px; height: 35px; border-radius: 50%; object-fit: cover"
            />
            <div style="margin-left: 5px">{{ userInfo?.name || '管理员' }}</div>
            <el-icon style="margin-left: 4px; font-size: 14px"><ArrowDown /></el-icon>
          </div>

          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><UserFilled /></el-icon>
                <span style="margin-left: 4px">个人中心</span>
              </el-dropdown-item>

              <el-dropdown-item command="password">
                <el-icon><Lock /></el-icon>
                <span style="margin-left: 4px">修改密码</span>
              </el-dropdown-item>

              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon>
                <span style="margin-left: 4px">退出登录</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-container>
        <el-aside width="220px">
          <el-menu router style="height: 100%" default-active="/manager/home">
            <el-menu-item index="/manager/home">
              <el-icon><icon-menu /></el-icon>
              <span>系统首页</span>
            </el-menu-item>

            <el-menu-item index="/manager/my-reservation" v-if="userInfo?.role === 'student'">
              <el-icon><Tickets /></el-icon>
              <span>我的预约</span>
            </el-menu-item>
            <el-menu-item index="/manager/audit-reservation" v-if="userInfo?.role === 'admin'">
              <el-icon><DocumentChecked /></el-icon>
              <span>预约审核</span>
            </el-menu-item>

            <el-menu-item index="/manager/lablist" v-if="userInfo?.role === 'student'">
              <el-icon><OfficeBuilding /></el-icon>
              <span>实验室列表</span>
            </el-menu-item>

            <el-menu-item v-if="userInfo?.role === 'admin'" index="/manager/lab">
              <el-icon><House /></el-icon>
              <span>实验室管理</span>
            </el-menu-item>
            <el-menu-item v-if="userInfo?.role === 'admin'" index="/manager/equ">
              <el-icon><Setting /></el-icon>
              <span>设备列表管理</span>
            </el-menu-item>
            <el-menu-item v-if="userInfo?.role === 'admin'" index="/manager/user">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="/manager/profile">
              <el-icon><UserFilled /></el-icon>
              <span>个人中心</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { useUser } from '@/utils/user'
import { logout } from '@/utils/auth'
import router from '@/router'
import {
  Menu as IconMenu,
  House,
  Setting,
  User,
  OfficeBuilding,
  Tickets,
  DocumentChecked
} from '@element-plus/icons-vue'

const { userInfo } = useUser()

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/manager/profile')
  } else if (command === 'password') {
    router.push('/manager/password')
  } else if (command === 'logout') {
    logout()
    router.push('/login')
  }
}

// import { ElMessageBox } from 'element-plus'
// import { ArrowDown, SwitchButton, House, Setting, User, UserFilled } from '@element-plus/icons-vue'
// import { useUser } from '@/utils/user'
// import defaultAvatar from '@/assets/imgs/logo.png'
// import { useRouter } from 'vue-router'

// const { userInfo, logout } = useUser()
// const router = useRouter() // 在 setup 中拿到路由实例

// const handleCommand = async (command) => {
//   if (command === 'profile') {
//     router.push('/manager/profile') // 编程式导航：用代码跳转
//     return
//   } else if (command === 'password') {
//     router.push('/manager/password')
//   }
//   if (command !== 'logout') return
//   try {
//     await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
//       confirmButtonText: '确定',
//       cancelButtonText: '取消',
//       type: 'warning'
//     })
//   } catch {
//     return // 用户取消
//   }
//   logout() // 只一行，具体动作都在 composable 里
//   router.push('/login')
// }
</script>
