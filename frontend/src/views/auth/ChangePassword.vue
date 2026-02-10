<template>
  <div class="min-h-screen bg-base-200 flex items-center justify-center p-4">
    <div class="card w-full max-w-md bg-base-100 shadow-xl">
      <div class="card-body">
        <!-- 警告图标 -->
        <div class="text-center mb-6">
          <div class="text-6xl mb-4">⚠️</div>
          <h2 class="card-title justify-center text-2xl">需要修改密码</h2>
          <p class="text-sm text-base-content/70 mt-2">
            出于安全考虑，您需要修改密码后才能继续使用系统
          </p>
        </div>

        <!-- 修改密码表单 -->
        <form @submit.prevent="handleChangePassword">
          <!-- 原密码（仅在普通修改密码时显示） -->
          <div class="form-control mb-4" v-if="!isForceChange">
            <label class="label">
              <span class="label-text">原密码</span>
            </label>
            <input
              v-model="passwordData.old_password"
              type="password"
              placeholder="请输入原密码"
              class="input input-bordered w-full"
              :class="{ 'input-error': errors.old_password }"
            />
            <label class="label" v-if="errors.old_password">
              <span class="label-text-alt text-error">{{ errors.old_password }}</span>
            </label>
          </div>

          <!-- 新密码 -->
          <div class="form-control mb-4">
            <label class="label">
              <span class="label-text">新密码</span>
            </label>
            <input
              v-model="passwordData.new_password"
              type="password"
              placeholder="请输入新密码"
              class="input input-bordered w-full"
              :class="{ 'input-error': errors.new_password }"
              required
            />
            <label class="label" v-if="errors.new_password">
              <span class="label-text-alt text-error">{{ errors.new_password }}</span>
            </label>
          </div>

          <!-- 确认密码 -->
          <div class="form-control mb-4">
            <label class="label">
              <span class="label-text">确认密码</span>
            </label>
            <input
              v-model="passwordData.confirm_password"
              type="password"
              placeholder="请再次输入新密码"
              class="input input-bordered w-full"
              :class="{ 'input-error': errors.confirm_password }"
              required
            />
            <label class="label" v-if="errors.confirm_password">
              <span class="label-text-alt text-error">{{ errors.confirm_password }}</span>
            </label>
          </div>

          <!-- 密码强度提示 -->
          <div class="alert alert-info text-sm mb-4">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              class="stroke-current shrink-0 w-6 h-6"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>密码至少8位，建议包含大小写字母、数字和特殊字符</span>
          </div>

          <!-- 错误消息 -->
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

          <!-- 提交按钮 -->
          <div class="card-actions justify-end">
            <button
              type="submit"
              class="btn btn-primary w-full"
              :class="{ 'loading': loading }"
              :disabled="loading"
            >
              <span v-if="!loading">修改密码</span>
              <span v-else>处理中...</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';

export default {
  name: 'ChangePassword',

  data() {
    return {
      passwordData: {
        old_password: '',
        new_password: '',
        confirm_password: '',
      },
      errors: {
        old_password: '',
        new_password: '',
        confirm_password: '',
      },
      errorMessage: '',
      loading: false,
      isForceChange: false, // Epic 8 Story 8.4: 是否强制修改密码
    };
  },

  computed: {
    ...mapGetters('auth', ['user']),
  },

  methods: {
    ...mapActions('auth', ['changePassword']),

    /**
     * 验证表单
     */
    validateForm() {
      let isValid = true;
      this.errors = {
        old_password: '',
        new_password: '',
        confirm_password: '',
      };
      this.errorMessage = '';

      // Epic 8 Story 8.4: 如果不是强制修改密码，验证原密码
      if (!this.isForceChange && !this.passwordData.old_password) {
        this.errors.old_password = '请输入原密码';
        isValid = false;
      }

      // 验证新密码
      if (!this.passwordData.new_password) {
        this.errors.new_password = '请输入新密码';
        isValid = false;
      } else if (this.passwordData.new_password.length < 8) {
        this.errors.new_password = '密码至少需要8位';
        isValid = false;
      }

      // 验证确认密码
      if (!this.passwordData.confirm_password) {
        this.errors.confirm_password = '请确认密码';
        isValid = false;
      } else if (
        this.passwordData.new_password !== this.passwordData.confirm_password
      ) {
        this.errors.confirm_password = '两次输入的密码不一致';
        isValid = false;
      }

      return isValid;
    },

    /**
     * 处理修改密码
     */
    async handleChangePassword() {
      // 验证表单
      if (!this.validateForm()) {
        return;
      }

      this.loading = true;
      this.errorMessage = '';

      try {
        // Epic 8 Story 8.4: 构建请求数据
        const requestData = {
          new_password: this.passwordData.new_password,
          new_password_confirm: this.passwordData.confirm_password,
        };

        // 如果不是强制修改密码，添加原密码
        if (!this.isForceChange) {
          requestData.old_password = this.passwordData.old_password;
        }

        // 调用 Vuex action
        await this.changePassword(requestData);

        // 修改密码成功，显示成功消息
        this.$message?.success('密码修改成功，请重新登录') ||
          alert('密码修改成功，请重新登录');

        // Epic 8 Story 8.4: 跳转到登录页
        // changePassword action 已经登出用户，现在跳转到登录页
        this.$router.push('/login');
      } catch (error) {
        console.error('修改密码失败:', error);
        this.errorMessage =
          error.response?.data?.message ||
          error.response?.data?.error ||
          error.message ||
          '修改密码失败，请稍后重试';
      } finally {
        this.loading = false;
      }
    },
  },

  /**
   * Epic 8 Story 8.4: 检查是否强制修改密码场景
   */
  mounted() {
    // 检查用户信息中的must_change_password标志
    if (this.user && this.user.must_change_password) {
      // 强制修改密码场景（管理员重置后）
      this.isForceChange = true
    } else {
      // 普通修改密码场景
      this.isForceChange = false
    }
  },
};
</script>

<style scoped>
/* 添加额外的样式 */
.card {
  border-radius: 1rem;
}

.form-control input:focus {
  outline: none;
  box-shadow: 0 0 0 2px hsl(var(--p));
}
</style>
