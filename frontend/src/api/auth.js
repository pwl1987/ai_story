/**
 * 用户认证API服务
 */
import apiClient from '@/services/apiClient'

/**
 * 用户登录
 * @param {Object} credentials - 登录凭证 { username, password }
 * @returns {Promise} 响应数据
 */
export const login = (credentials) => {
  return apiClient({
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
  return apiClient({
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
