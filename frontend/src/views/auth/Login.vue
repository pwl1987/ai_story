<template>
  <div class="min-h-screen flex items-center justify-center bg-base-200 py-12 px-4 sm:px-6 lg:px-8">
    <div class="card w-full max-w-md bg-base-100 shadow-xl">
      <div class="card-body">
        <!-- Logo和标题 -->
        <div class="text-center mb-6">
          <h1 class="text-3xl font-bold text-primary">AI Story</h1>
          <p class="text-base-content/70 mt-2">登录您的账户</p>
        </div>

        <!-- 登录表单 -->
        <form @submit.prevent="handleSubmit">
          <!-- 用户名 -->
          <div class="form-control mb-4">
            <label class="label">
              <span class="label-text">用户名</span>
            </label>
            <input
              v-model="form.username"
              type="text"
              placeholder="请输入用户名"
              class="input input-bordered"
              :class="{ 'input-error': errors.username }"
              required
            />
            <label v-if="errors.username" class="label">
              <span class="label-text-alt text-error">{{ errors.username }}</span>
            </label>
          </div>

          <!-- 密码 -->
          <div class="form-control mb-4">
            <label class="label">
              <span class="label-text">密码</span>
            </label>
            <input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              class="input input-bordered"
              :class="{ 'input-error': errors.password }"
              required
            />
            <label v-if="errors.password" class="label">
              <span class="label-text-alt text-error">{{ errors.password }}</span>
            </label>
          </div>

          <!-- 记住我 -->
          <div class="form-control mb-6">
            <label class="label cursor-pointer justify-start gap-2">
              <input
                v-model="form.remember"
                type="checkbox"
                class="checkbox checkbox-primary checkbox-sm"
              />
              <span class="label-text">记住我</span>
            </label>
          </div>

          <!-- 错误提示 -->
          <div v-if="errorMessage" class="alert alert-error mb-4">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="stroke-current shrink-0 h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>{{ errorMessage }}</span>
          </div>

          <!-- 登录按钮 -->
          <button
            type="submit"
            class="btn btn-primary w-full"
            :class="{ 'loading': loading }"
            :disabled="loading"
          >
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>

        <!-- 底部链接 -->
        <div class="divider">或</div>
        <div class="text-center">
          <p class="text-sm text-base-content/70">
            还没有账户？
            <router-link to="/register" class="link link-primary">
              立即注册
            </router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'

export default {
  name: 'Login',
  data() {
    return {
      form: {
        username: '',
        password: '',
        remember: false
      },
      errors: {},
      errorMessage: '',
      loading: false
    }
  },
  mounted() {
    // Epic 8 Story 8.4: 登录页面加载时清除旧的认证信息
    // 避免携带旧token导致登录请求被middleware拦截
    this.$store.dispatch('auth/logout')
  },
  methods: {
    ...mapActions('auth', ['login']),

    async handleSubmit() {
      // 清空错误
      this.errors = {}
      this.errorMessage = ''

      // 表单验证
      if (!this.form.username) {
        this.errors.username = '请输入用户名'
        return
      }
      if (!this.form.password) {
        this.errors.password = '请输入密码'
        return
      }

      this.loading = true

      try {
        const response = await this.login({
          username: this.form.username,
          password: this.form.password
        })

        // Epic 8 Story 8.4: 检查是否需要强制修改密码
        const user = response.data.user
        if (user.must_change_password) {
          // 需要修改密码，跳转到修改密码页面
          // 保存原本想去的路径，修改密码后跳转
          const redirect = this.$route.query.redirect || '/projects'
          this.$router.push({
            path: '/change-password',
            query: { redirect }
          })
        } else {
          // 登录成功，跳转到首页或之前的页面
          const redirect = this.$route.query.redirect || '/'
          this.$router.push(redirect)
        }
      } catch (error) {
        console.error('登录失败:', error)
        this.errorMessage = error.message || '登录失败，请检查用户名和密码'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
/* 额外的样式可以在这里添加 */
</style>
