/**
 * 用户认证Vuex模块
 * 职责: 管理用户认证状态和token
 */
import * as authAPI from '@/api/auth'

// 从localStorage加载token
const loadTokens = () => {
  try {
    return {
      access: localStorage.getItem('access_token'),
      refresh: localStorage.getItem('refresh_token'),
    }
  } catch (error) {
    console.error('加载token失败:', error)
    return { access: null, refresh: null }
  }
}

// 保存token到localStorage
const saveTokens = (access, refresh) => {
  try {
    if (access) localStorage.setItem('access_token', access)
    if (refresh) localStorage.setItem('refresh_token', refresh)
  } catch (error) {
    console.error('保存token失败:', error)
  }
}

// 清除token
const clearTokens = () => {
  try {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
  } catch (error) {
    console.error('清除token失败:', error)
  }
}

// 从localStorage加载用户信息
const loadUserInfo = () => {
  try {
    const userInfo = localStorage.getItem('user_info')
    return userInfo ? JSON.parse(userInfo) : null
  } catch (error) {
    console.error('加载用户信息失败:', error)
    return null
  }
}

// 保存用户信息到localStorage
const saveUserInfo = (userInfo) => {
  try {
    localStorage.setItem('user_info', JSON.stringify(userInfo))
  } catch (error) {
    console.error('保存用户信息失败:', error)
  }
}

const tokens = loadTokens()

const state = {
  // 访问令牌
  accessToken: tokens.access,
  // 刷新令牌
  refreshToken: tokens.refresh,
  // 用户信息
  user: loadUserInfo(),
  // 登录状态
  isAuthenticated: !!tokens.access,
}

const getters = {
  accessToken: state => state.accessToken,
  refreshToken: state => state.refreshToken,
  user: state => state.user,
  isAuthenticated: state => state.isAuthenticated,
  username: state => state.user?.username || '',
  userEmail: state => state.user?.email || '',
}

const mutations = {
  // 设置访问令牌
  SET_ACCESS_TOKEN(state, token) {
    state.accessToken = token
    saveTokens(token, state.refreshToken)
  },

  // 设置刷新令牌
  SET_REFRESH_TOKEN(state, token) {
    state.refreshToken = token
    saveTokens(state.accessToken, token)
  },

  // 设置tokens
  SET_TOKENS(state, { access, refresh }) {
    state.accessToken = access
    state.refreshToken = refresh
    state.isAuthenticated = true
    saveTokens(access, refresh)
  },

  // 设置用户信息
  SET_USER(state, user) {
    state.user = user
    saveUserInfo(user)
  },

  // 清除认证信息
  CLEAR_AUTH(state) {
    state.accessToken = null
    state.refreshToken = null
    state.user = null
    state.isAuthenticated = false
    clearTokens()
  },
}

const actions = {
  /**
   * 用户登录
   */
  async login({ commit }, credentials) {
    try {
      const response = await authAPI.login(credentials)

      if (response.success) {
        const { user, tokens } = response.data

        // 保存tokens和用户信息
        commit('SET_TOKENS', tokens)
        commit('SET_USER', user)

        return response
      } else {
        throw new Error(response.message || '登录失败')
      }
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  },

  /**
   * 用户注册
   */
  async register({ commit }, userData) {
    try {
      const response = await authAPI.register(userData)

      if (response.success) {
        const { user, tokens } = response.data

        // 保存tokens和用户信息
        commit('SET_TOKENS', tokens)
        commit('SET_USER', user)

        return response
      } else {
        throw new Error(response.message || '注册失败')
      }
    } catch (error) {
      console.error('注册失败:', error)
      throw error
    }
  },

  /**
   * 用户登出
   */
  async logout({ commit, state }) {
    try {
      // 尝试调用后端登出接口
      if (state.refreshToken) {
        await authAPI.logout(state.refreshToken)
      }
    } catch (error) {
      console.error('登出API调用失败:', error)
      // 即使API调用失败,也要清除本地状态
    } finally {
      // 清除本地认证信息
      commit('CLEAR_AUTH')
    }
  },

  /**
   * 刷新访问令牌
   */
  async refreshToken({ commit, state }) {
    try {
      if (!state.refreshToken) {
        throw new Error('没有刷新令牌')
      }

      const response = await authAPI.refreshToken(state.refreshToken)

      if (response.access) {
        commit('SET_ACCESS_TOKEN', response.access)

        // 如果返回了新的refresh token,也更新它
        if (response.refresh) {
          commit('SET_REFRESH_TOKEN', response.refresh)
        }

        return response.access
      } else {
        throw new Error('刷新令牌失败')
      }
    } catch (error) {
      console.error('刷新令牌失败:', error)
      // 刷新失败,清除认证信息
      commit('CLEAR_AUTH')
      throw error
    }
  },

  /**
   * 获取用户信息
   */
  async getUserProfile({ commit }) {
    try {
      const response = await authAPI.getUserProfile()

      if (response.success) {
        commit('SET_USER', response.data)
        return response.data
      } else {
        throw new Error(response.message || '获取用户信息失败')
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  },

  /**
   * 更新用户信息
   */
  async updateUserProfile({ commit }, userData) {
    try {
      const response = await authAPI.updateUserProfile(userData)

      if (response.success) {
        commit('SET_USER', response.data)
        return response.data
      } else {
        throw new Error(response.message || '更新用户信息失败')
      }
    } catch (error) {
      console.error('更新用户信息失败:', error)
      throw error
    }
  },

  /**
   * 修改密码
   *
   * Epic 8 Story 8.4: 支持两种场景
   * 1. 普通修改密码: { old_password, new_password, new_password_confirm }
   * 2. 强制修改密码: { new_password, new_password_confirm }
   */
  async changePassword({ dispatch }, passwordData) {
    try {
      const response = await authAPI.changePassword(passwordData)

      if (response.success || response.status === 'success') {
        // Epic 8 Story 8.4: 修改密码成功后，清除重定向标记并登出
        const redirectPath = sessionStorage.getItem('redirect_after_password_change')

        // 清除重定向标记
        sessionStorage.removeItem('redirect_after_password_change')

        // 修改密码后登出（组件会处理跳转）
        await dispatch('logout')

        return response
      } else {
        throw new Error(response.message || '修改密码失败')
      }
    } catch (error) {
      console.error('修改密码失败:', error)
      throw error
    }
  },

  /**
   * 初始化认证状态(应用启动时调用)
   */
  async initAuth({ commit, state, dispatch }) {
    // 如果有token,尝试获取用户信息
    if (state.accessToken && !state.user) {
      try {
        await dispatch('getUserProfile')
      } catch (error) {
        console.error('初始化认证失败:', error)
        // 获取用户信息失败,清除认证状态
        commit('CLEAR_AUTH')
      }
    }
  },
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions,
}
