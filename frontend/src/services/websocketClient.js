/**
 * WebSocket客户端 - 用于实时接收项目阶段更新
 * 使用原生WebSocket协议连接Django Channels
 */
class WebSocketClient {
  constructor() {
    this.ws = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.projectId = null;
  }

  connect(projectId) {
    if (this.ws) {
      this.disconnect();
    }

    this.projectId = projectId;

    // 构建WebSocket URL
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = process.env.VUE_APP_WS_URL || window.location.host;
    const wsUrl = `${wsProtocol}//${wsHost}/ws/projects/${projectId}/`;

    console.log('[WebSocket] 正在连接:', wsUrl);

    try {
      this.ws = new WebSocket(wsUrl);

      // 连接成功
      this.ws.onopen = () => {
        console.log('[WebSocket] 已连接 - 项目:', projectId);
        this.reconnectAttempts = 0;
        this._triggerEvent('connected', { projectId });
      };

      // 接收消息
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[WebSocket] 收到消息:', data);

          // 根据消息类型触发对应事件
          if (data.type) {
            this._triggerEvent(data.type, data);
          }
          // 兼容通用消息事件
          this._triggerEvent('message', data);
        } catch (error) {
          console.error('[WebSocket] 解析消息失败:', error);
        }
      };

      // 连接关闭
      this.ws.onclose = (event) => {
        console.log('[WebSocket] 已断开:', event.code, event.reason);

        // 尝试重连
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = this.reconnectDelay * this.reconnectAttempts;
          console.log(`[WebSocket] ${delay}ms后尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

          setTimeout(() => {
            this.connect(this.projectId);
          }, delay);
        } else {
          console.error('[WebSocket] 达到最大重连次数，放弃重连');
          this._triggerEvent('disconnect', { code: event.code, reason: event.reason });
        }
      };

      // 连接错误
      this.ws.onerror = (error) => {
        console.error('[WebSocket] 错误:', error);
        this._triggerEvent('error', { error });
      };

    } catch (error) {
      console.error('[WebSocket] 创建连接失败:', error);
    }

    return this;
  }

  disconnect() {
    if (this.ws) {
      console.log('[WebSocket] 主动断开连接');
      this.ws.close();
      this.ws = null;
      this.listeners.clear();
      this.reconnectAttempts = 0;
      this.projectId = null;
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (!this.listeners.has(event)) {
      return;
    }

    const callbacks = this.listeners.get(event);
    const index = callbacks.indexOf(callback);
    if (index > -1) {
      callbacks.splice(index, 1);
    }
  }

  emit(event, data) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[WebSocket] 未连接，无法发送消息');
      return;
    }

    const message = JSON.stringify({ type: event, ...data });
    this.ws.send(message);
  }

  /**
   * 内部方法：触发事件监听器
   */
  _triggerEvent(event, data) {
    if (!this.listeners.has(event)) {
      return;
    }

    const callbacks = this.listeners.get(event);
    callbacks.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`[WebSocket] 事件处理器错误 (${event}):`, error);
      }
    });
  }
}

export default new WebSocketClient();
