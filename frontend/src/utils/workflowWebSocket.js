/**
 * 工作流 WebSocket 客户端
 *
 * 负责：
 * - 连接到 Redis Stream WebSocket 频道
 * - 接收工作流进度事件
 * - 处理连接断开重连
 *
 * Epic: Story 12-6
 * 修改日期：2026-02-12
 */

import { getWebSocketURL } from '@/config/api';

/**
 * WebSocket 客户端
 *
 * 简化版：移除复杂的重连逻辑，专注连接和消息处理
 * 改为依赖注入方式，便于单元测试
 */
export default class WorkflowWebSocket {
  /**
   * 构造函数
   *
   * @param {number} chapterId - 章节 ID
   * @param {Object} callbacks - 回调函数集合
   * @returns {Object} WebSocket 客户端实例
   */
  static create(chapterId, callbacks = {}) {
    const url = getWebSocketURL(chapterId);

    const ws = new WebSocket(url);

    // 绑定事件处理函数到实例，避免 this 问题
    const boundHandleOpen = WorkflowWebSocket.handleOpen.bind({ ws, callbacks });
    const boundHandleMessage = WorkflowWebSocket.handleMessage.bind({ ws, callbacks });
    const boundHandleClose = WorkflowWebSocket.handleClose.bind({ ws, callbacks });
    const boundHandleError = WorkflowWebSocket.handleError.bind({ ws, callbacks });

    ws.onopen = boundHandleOpen;
    ws.onmessage = boundHandleMessage;
    ws.onclose = boundHandleClose;
    ws.onerror = boundHandleError;

    return { ws, disconnect: ws.close.bind(ws) };
  }

  /**
   * 处理 WebSocket 打开事件
   */
  static handleOpen(ws) {
    return (event) => {
      if (event.type === 'open') {
        console.log('WebSocket 已连接');
        ws.isConnected = true;
        if (ws.callbacks.onConnected) {
          ws.callbacks.onConnected();
        }
      }
    };
  }

  /**
   * 处理 WebSocket 消息事件
   */
  static handleMessage(ws) {
    return (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('收到 WebSocket 消息:', data);

        // 验证事件格式
        if (data.type && data.payload) {
          if (ws.callbacks.onEvent) {
            ws.callbacks.onEvent(data.payload);
          }
        }
      } catch (error) {
        console.error('解析 WebSocket 消息失败:', error);
      }
    };
  }

  /**
   * 处理 WebSocket 关闭事件
   */
  static handleClose(ws) {
    return (event) => {
      console.log('WebSocket 已关闭');
      ws.isConnected = false;
      if (ws.callbacks.onDisconnected) {
        ws.callbacks.onDisconnected();
      }
    }
    };

  /**
   * 处理 WebSocket 错误事件
   */
  static handleError(ws) {
    return (error) => {
      console.error('WebSocket 错误:', error);
      if (ws.callbacks.onError) {
        ws.callbacks.onError(error);
      }
    }
  }

  /**
   * 断开连接
   */
  static disconnect(ws) {
    ws.close();
  }
}
