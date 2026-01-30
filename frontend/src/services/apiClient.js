import axios from 'axios';
import store from '@/store';
import router from '@/router';

// 简单的通知函数 (后续可替换为专门的通知组件)
const showMessage = (message, type = 'error') => {
  console[type === 'error' ? 'error' : 'log'](`[${type.toUpperCase()}]`, message);
  // TODO: 实现全局 Toast 通知组件
};

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || '/api/v1',
  timeout: 3000000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 是否正在刷新token
let isRefreshing = false;
// 存储待重试的请求
let failedQueue = [];

// 处理队列
const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 从store获取token
    const token = store.getters['auth/accessToken'];
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  async (error) => {
    const originalRequest = error.config;
    const { response } = error;

    // 处理token过期的情况
    if (response && response.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // 如果正在刷新token,将请求加入队列
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch(err => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = store.getters['auth/refreshToken'];

      if (!refreshToken) {
        // 没有refresh token,直接跳转登录页
        store.dispatch('auth/logout');
        router.push('/login');
        return Promise.reject(error);
      }

      try {
        // 刷新token
        const response = await axios.post(
          `${apiClient.defaults.baseURL}/users/token/refresh/`,
          { refresh: refreshToken }
        );

        const { access } = response.data;

        // 更新store中的token
        store.commit('auth/SET_ACCESS_TOKEN', access);

        // 更新请求头
        originalRequest.headers.Authorization = `Bearer ${access}`;

        // 处理队列中的请求
        processQueue(null, access);

        // 重试原请求
        return apiClient(originalRequest);
      } catch (refreshError) {
        // token刷新失败,清除登录状态并跳转登录页
        processQueue(refreshError, null);
        store.dispatch('auth/logout');
        router.push('/login');
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // 处理其他HTTP错误
    if (response) {
      switch (response.status) {
        case 400:
          showMessage('请求参数错误');
          break;
        case 401:
          showMessage('未授权,请登录');
          break;
        case 403:
          // Epic 8 Story 8.4: 检测强制修改密码
          if (response.data?.error_code === 'MUST_CHANGE_PASSWORD') {
            // 跳转到修改密码页面
            if (router.currentRoute.path !== '/change-password') {
              // 保存原始目标路径，修改密码后跳转回去
              sessionStorage.setItem('redirect_after_password_change', router.currentRoute.fullPath);
              router.push('/change-password');
            }
          } else {
            showMessage('没有权限');
          }
          break;
        case 404:
          showMessage('请求的资源不存在');
          break;
        case 500:
          showMessage('服务器内部错误');
          break;
        default:
          showMessage(response.data?.message || '请求失败');
      }
    } else if (error.request) {
      showMessage('网络错误,请检查网络连接');
    } else {
      showMessage(error.message || '请求失败');
    }

    return Promise.reject(error);
  }
);

export default apiClient;
