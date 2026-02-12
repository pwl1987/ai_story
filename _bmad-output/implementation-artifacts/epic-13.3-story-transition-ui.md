# Story 13-1.3: 创建转场配置UI面板

> **Epic:** Epic 13 - 转场与导出
> **优先级:** P1
> **预估工作量:** 2天
> **依赖:** 13.1.1, 13.1.2

---

## 📋 需求描述

**用户故事：** 作为内容创作者，我需要一个可视化的转场配置面板，能够设置场景间的转场效果和参数。

**功能说明：**
- 创建转场配置面板组件
- 支持转场类型选择（下拉框）
- 支持转场时长调节（滑块）
- 支持转场预览
- 显示当前场景到下一场景的连接关系

**边界条件：**
- 不包含转场渲染逻辑
- 不包含视频导出
- 只包含 UI 组件

**验收标准：**
- [ ] 转场面板可正常使用
- [ ] 参数调节实时响应
- [ ] 预览功能正常
- [ ] 样式符合 daisyUI 规范

---

## 🔧 技术实现细节

### 转场配置面板组件

```vue
<!-- frontend/src/components/artworks/TransitionConfigPanel.vue -->
<template>
  <div class="transition-config-panel bg-base-100 rounded-lg shadow-md p-6">
    <h3 class="text-lg font-bold mb-4">✨ 转场配置</h3>

    <!-- 场景连接显示 -->
    <div class="mb-4 flex items-center gap-4">
      <div class="flex-1">
        <p class="text-xs text-gray-600 mb-1">源场景</p>
        <div class="bg-base-200 p-3 rounded text-center">
          {{ fromScene?.title || '未选择' }}
        </div>
      </div>

      <div class="text-4xl">→</div>

      <div class="flex-1">
        <p class="text-xs text-gray-600 mb-1">目标场景</p>
        <div class="bg-base-200 p-3 rounded text-center">
          {{ toScene?.title || '未选择' }}
        </div>
      </div>
    </div>

    <!-- 转场类型选择 -->
    <div class="mb-4">
      <label class="label">转场类型</label>
      <select
        v-model="transitionType"
        class="select select-bordered w-full"
        :disabled="!fromScene || !toScene"
      >
        <option value="none">无转场</option>
        <option value="fade">🌅 淡入淡出</option>
        <option value="dissolve">💨 溶解</option>
        <option value="wipe">🧹 擦除</option>
        <option value="slide">➡️ 滑动</option>
        <option value="zoom">🔍 缩放</option>
      </select>
    </div>

    <!-- 转场方向 -->
    <div class="mb-4">
      <label class="label">转场方向</label>
      <div class="flex gap-4">
        <label class="label cursor-pointer">
          <input
            type="radio"
            v-model="direction"
            value="forward"
            class="radio radio-primary"
          />
          正向
        </label>
        <label class="label cursor-pointer">
          <input
            type="radio"
            v-model="direction"
            value="backward"
            class="radio radio-primary"
          />
          反向
        </label>
      </div>
    </div>

    <!-- 转场时长滑块 -->
    <div class="mb-4">
      <div class="flex justify-between mb-2">
        <label class="label">转场时长: {{ duration }}秒</label>
        <span class="text-xs text-gray-600">
          ({{ TRANSITION_DURATION_MIN }} - {{ TRANSITION_DURATION_MAX }}秒)
        </span>
      </div>
      <input
        type="range"
        v-model.number="duration"
        :min="TRANSITION_DURATION_MIN"
        :max="TRANSITION_DURATION_MAX"
        :step="0.1"
        class="range range-primary"
        :disabled="transitionType === 'none'"
      />
      <div class="flex justify-between text-xs text-gray-600 mt-1">
        <span>{{ TRANSITION_DURATION_MIN }}s</span>
        <span>{{ TRANSITION_DURATION_MAX }}s</span>
      </div>
    </div>

    <!-- 自定义参数（根据转场类型动态显示） -->
    <div
      v-if="showCustomParams"
      class="mb-4 bg-base-200 p-4 rounded"
    >
      <h4 class="text-sm font-bold mb-2">高级参数</h4>

      <!-- 擦除方向 -->
      <div v-if="transitionType === 'wipe'" class="mb-2">
        <label class="label">擦除方向</label>
        <select v-model="customParams.wipeDirection" class="select select-bordered">
          <option value="left">从左到右</option>
          <option value="right">从右到左</option>
          <option value="top">从上到下</option>
          <option value="bottom">从下到上</option>
        </select>
      </div>

      <!-- 滑动角度 -->
      <div v-if="transitionType === 'slide'" class="mb-2">
        <label class="label">滑动角度</label>
        <input
          type="range"
          v-model.number="customParams.slideAngle"
          :min="0"
          :max="360"
          class="range range-primary"
        />
        <p class="text-xs text-center mt-1">{{ customParams.slideAngle }}°</p>
      </div>

      <!-- 缩放比例 -->
      <div v-if="transitionType === 'zoom'" class="mb-2">
        <label class="label">缩放比例</label>
        <div class="flex items-center gap-2">
          <input
            type="range"
            v-model.number="customParams.zoomScale"
            :min="0.5"
            :max="2.0"
            :step="0.1"
            class="range range-primary flex-1"
          />
          <span class="text-sm">{{ customParams.zoomScale }}x</span>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="flex gap-2">
      <button
        @click="previewTransition"
        class="btn btn-outline flex-1"
        :disabled="!canPreview"
      >
        👁️ 预览效果
      </button>

      <button
        @click="saveTransition"
        class="btn btn-primary flex-1"
        :disabled="!canSave"
      >
        💾 保存配置
      </button>

      <button
        v-if="existingTransition"
        @click="deleteTransition"
        class="btn btn-error"
      >
        🗑️ 删除
      </button>
    </div>
  </div>
</template>

<script>
import { TRANSITION_TYPES, TRANSITION_DURATION_MIN, TRANSITION_DURATION_MAX } from '@/constants/transition'

export default {
  name: 'TransitionConfigPanel',

  props: {
    fromScene: {
      type: Object,
      default: null
    },
    toScene: {
      type: Object,
      default: null
    },
    existingTransition: {
      type: Object,
      default: null
    }
  },

  data() {
    return {
      TRANSITION_TYPES,
      TRANSITION_DURATION_MIN,
      TRANSITION_DURATION_MAX,

      transitionType: 'fade',
      direction: 'forward',
      duration: 1.0,
      customParams: {},
      showCustomParams: false
    }
  },

  computed: {
    canPreview() {
      return this.fromScene && this.toScene && this.transitionType !== 'none'
    },

    canSave() {
      return this.fromScene && this.toScene
    },

    showCustomParams() {
      return ['wipe', 'slide', 'zoom'].includes(this.transitionType)
    }
  },

  watch: {
    existingTransition: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          // 加载现有配置
          this.transitionType = newVal.transition_type
          this.duration = newVal.duration
          this.direction = newVal.direction
          this.customParams = newVal.custom_params || {}
        }
      }
    },

    transitionType(newVal) {
      // 根据类型重置自定义参数
      if (newVal === 'wipe' && !this.customParams.wipeDirection) {
        this.customParams = { wipeDirection: 'left' }
      } else if (newVal === 'slide' && !this.customParams.slideAngle) {
        this.customParams = { slideAngle: 0 }
      } else if (newVal === 'zoom' && !this.customParams.zoomScale) {
        this.customParams = { zoomScale: 1.0 }
      }
    }
  },

  methods: {
    async saveTransition() {
      const config = {
        from_scene: this.fromScene.id,
        to_scene: this.toScene.id,
        transition_type: this.transitionType,
        duration: this.duration,
        direction: this.direction,
        custom_params: this.customParams
      }

      try {
        await this.$http.post(
          `/artworks/scenes/${this.fromScene.id}/configure-transition/`,
          config
        )
        this.$emit('saved', config)
        this.$toast.success('转场配置已保存')
      } catch (error) {
        this.$toast.error('保存失败：' + error.message)
      }
    },

    async deleteTransition() {
      if (!confirm('确定要删除此转场配置吗？')) return

      try {
        await this.$http.delete(
          `/artworks/transitions/${this.existingTransition.id}/`
        )
        this.$emit('deleted')
        this.$toast.success('转场配置已删除')
      } catch (error) {
        this.$toast.error('删除失败：' + error.message)
      }
    },

    previewTransition() {
      // 打开预览模态框
      this.$emit('preview', {
        type: this.transitionType,
        duration: this.duration,
        params: this.customParams
      })
    }
  }
}
</script>
```

### 转场预览模态框

```vue
<!-- frontend/src/components/artworks/TransitionPreviewModal.vue -->
<template>
  <div class="modal modal-open">
    <div class="modal-box w-11/12 max-w-4xl">
      <div class="modal-body">
        <h3 class="text-lg font-bold mb-4">👁️ 转场效果预览</h3>

        <!-- 预览画布 -->
        <div class="aspect-video bg-base-300 rounded-lg overflow-hidden relative">
          <!-- 源场景 -->
          <div
            class="absolute inset-0 flex items-center justify-center opacity-100"
            :style="{ opacity: sourceOpacity }"
          >
            <p class="text-2xl">源场景</p>
          </div>

          <!-- 转场效果层 -->
          <div
            class="absolute inset-0 flex items-center justify-center bg-gradient-to-r from-transparent to-black"
            :style="{ opacity: transitionOpacity }"
          >
            <p class="text-white text-xl">{{ transitionTypeDisplay }}</p>
          </div>

          <!-- 目标场景 -->
          <div
            class="absolute inset-0 flex items-center justify-center"
            :style="{ opacity: targetOpacity }"
          >
            <p class="text-2xl">目标场景</p>
          </div>
        </div>

        <!-- 播放控制 -->
        <div class="flex justify-center gap-2 mt-4">
          <button
            @click="startPreview"
            class="btn btn-primary"
            :disabled="isPlaying"
          >
            ▶️ 播放预览
          </button>
          <button
            @click="stopPreview"
            class="btn btn-outline"
            :disabled="!isPlaying"
          >
            ⏸️ 停止
          </button>
        </div>
      </div>

      <div class="modal-action">
        <button @click="$emit('close')" class="btn">
          关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TransitionPreviewModal',

  props: {
    type: {
      type: String,
      required: true
    },
    duration: {
      type: Number,
      default: 1.0
    },
    params: {
      type: Object,
      default: () => ({})
    }
  },

  data() {
    return {
      isPlaying: false,
      sourceOpacity: 1,
      transitionOpacity: 0,
      targetOpacity: 0,
      animationFrame: null,
      previewDuration: 2000  // 预览动画时长(ms)
    }
  },

  computed: {
    transitionTypeDisplay() {
      const displays = {
        'fade': '淡入淡出',
        'dissolve': '溶解',
        'wipe': '擦除',
        'slide': '滑动',
        'zoom': '缩放'
      }
      return displays[this.type] || this.type
    }
  },

  methods: {
    startPreview() {
      this.isPlaying = true
      this.animateTransition()
    },

    stopPreview() {
      this.isPlaying = false
      if (this.animationFrame) {
        cancelAnimationFrame(this.animationFrame)
      }
      // 重置状态
      this.sourceOpacity = 1
      this.transitionOpacity = 0
      this.targetOpacity = 0
    },

    animateTransition() {
      const startTime = Date.now()
      const duration = this.previewDuration

      const animate = () => {
        const elapsed = Date.now() - startTime
        const progress = Math.min(elapsed / duration, 1)

        // 根据转场类型计算透明度
        switch (this.type) {
          case 'fade':
            this.sourceOpacity = 1 - progress
            this.targetOpacity = progress
            break
          case 'dissolve':
            this.sourceOpacity = 1 - progress * 0.5
            this.targetOpacity = progress * 0.5
            break
          case 'wipe':
            this.transitionOpacity = Math.sin(progress * Math.PI)
            break
          default:
            this.sourceOpacity = 1 - progress
            this.targetOpacity = progress
        }

        if (progress < 1) {
          this.animationFrame = requestAnimationFrame(animate)
        } else {
          this.isPlaying = false
        }
      }

      this.animationFrame = requestAnimationFrame(animate)
    }
  }
}
</script>
```

---

## 📊 依赖关系

**前置 Story:** 13.1.1, 13.1.2
**阻塞 Story:** 无

---

## 🎯 成功标准

- [ ] 转场配置面板可正常使用
- [ ] 参数调节实时响应
- [ ] 预览功能正常
- [ ] 组件样式符合 daisyUI 规范
