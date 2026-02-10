/**
 * 用户认证API服务
 */
import apiClient from '@/services/apiClient'
import axios from 'axios'
import store from '@/store'
import router from '@/router'

// Epic 8 Story 8.4: 登录和注册不应该携带token
// 因为这些请求是用于获取token的，不应该有旧的认证信息
const authClient = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || '/api/v1',
  timeout: 3000000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Epic 8 Story 8.4: authClient响应拦截器 - 处理403错误（强制修改密码）
authClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  async (error) => {
    const { response } = error

    // Epic 8 Story 8.4: 处理强制修改密码的403错误
    if (response && response.status === 403) {
      if (response.data?.error_code === 'MUST_CHANGE_PASSWORD') {
        // 跳转到修改密码页面
        if (router.currentRoute.path !== '/change-password') {
          sessionStorage.setItem('redirect_after_password_change', router.currentRoute.fullPath)
          router.push('/change-password')
        }
      }
    }

    return Promise.reject(error)
  }
)

/**
 * 用户登录
 * @param {Object} credentials - 登录凭证 { username, password }
 * @returns {Promise} 响应数据
 */
export const login = (credentials) => {
  return authClient({
    url: '/users/login/',
    method: 'post',
    data: credentials,
  })
}

/**
 * 用户注册
 * @param {Object} userData - 用户数据
 * @returns {Promise} 响应数据
 */
export const register = (userData) => {
  return authClient({
    url: '/users/register/',
    method: 'post',
    data: userData,
  })
}

/**
 * 用户登出
 * @param {string} refreshToken - 刷新令牌
 * @returns {Promise} 响应数据
 */
export const logout = (refreshToken) => {
  return apiClient({
    url: '/users/logout/',
    method: 'post',
    data: { refresh: refreshToken },
  })
}

/**
 * 刷新访问令牌
 * @param {string} refreshToken - 刷新令牌
 * @returns {Promise} 响应数据
 */
export const refreshToken = (refreshToken) => {
  return apiClient({
    url: '/users/token/refresh/',
    method: 'post',
    data: { refresh: refreshToken },
  })
}

/**
 * 获取当前用户信息
 * @returns {Promise} 响应数据
 */
export const getUserProfile = () => {
  return apiClient({
    url: '/users/profile/',
    method: 'get',
  })
}

/**
 * 更新用户信息
 * @param {Object} userData - 用户数据
 * @returns {Promise} 响应数据
 */
export const updateUserProfile = (userData) => {
  return apiClient({
    url: '/users/profile/',
    method: 'patch',
    data: userData,
  })
}

/**
 * 修改密码
 *
 * Epic 8 Story 8.4: 支持两种场景
 * 1. 普通修改密码: { old_password, new_password, new_password_confirm }
 * 2. 强制修改密码: { new_password, new_password_confirm }
 *
 * @param {Object} passwordData - 密码数据
 * @returns {Promise} 响应数据
 */
export const changePassword = (passwordData) => {
  return apiClient({
    url: '/users/change-password/',
    method: 'post',
    data: passwordData,
  })
}

export default {
  login,
  register,
  logout,
  refreshToken,
  getUserProfile,
  updateUserProfile,
  changePassword
}
