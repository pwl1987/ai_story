<!--
批量操作模态框组件 (Story 11.5.1)

功能:
- 批量删除
- 批量移动
- 批量更新角色造型
- 批量重新生成
- 显示操作进度
- 显示错误报告
-->

<template>
  <div class="modal modal-open">
    <div class="modal-box max-w-2xl">
      <!-- Header -->
      <div class="flex items-center justify-between border-b pb-4">
        <h3 class="font-bold text-lg">批量操作</h3>
        <button class="btn btn-sm btn-circle btn-ghost" @click="$emit('close')">
          ✕
        </button>
      </div>

      <!-- Selected Count -->
      <div class="py-4">
        <div class="alert">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            class="stroke-info shrink-0 w-6 h-6"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            ></path>
          </svg>
          <span>已选择 {{ selectedCount }} 个项目</span>
        </div>
      </div>

      <!-- Operation Tabs -->
      <div role="tablist" class="tabs tabs-lifted tabs-lg mb-4">
        <a
          role="tab"
          class="tab"
          :class="{ 'tab-active': activeTab === 'delete' }"
          @click="activeTab = 'delete'"
        >
          批量删除
        </a>
        <a
          role="tab"
          class="tab"
          :class="{ 'tab-active': activeTab === 'move' }"
          @click="activeTab = 'move'"
        >
          批量移动
        </a>
        <a
          v-if="type === 'shots'"
          role="tab"
          class="tab"
          :class="{ 'tab-active': activeTab === 'character' }"
          @click="activeTab = 'character'"
        >
          更新角色
        </a>
        <a
          v-if="type === 'shots'"
          role="tab"
          class="tab"
          :class="{ 'tab-active': activeTab === 'regenerate' }"
          @click="activeTab = 'regenerate'"
        >
          重新生成
        </a>
      </div>

      <!-- Operation Content -->
      <div class="py-4">
        <!-- 批量删除 -->
        <div v-if="activeTab === 'delete'" class="space-y-4">
          <div class="alert alert-warning">
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
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <span>删除操作不可恢复，请确认是否继续</span>
          </div>
          <div class="flex justify-end gap-2">
            <button class="btn btn-ghost" @click="$emit('close')">取消</button>
            <button
              class="btn btn-error"
              :class="{ loading: loading }"
              :disabled="loading"
              @click="handleDelete"
            >
              确认删除
            </button>
          </div>
        </div>

        <!-- 批量移动 -->
        <div v-if="activeTab === 'move'" class="space-y-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">目标场景</span>
            </label>
            <select v-model="targetSceneId" class="select select-bordered w-full">
              <option value="">请选择目标场景</option>
              <option v-for="scene in availableScenes" :key="scene.id" :value="scene.id">
                {{ scene.chapter_title }} - {{ scene.scene_name }}
              </option>
            </select>
          </div>
          <div class="form-control">
            <label class="label">
              <input type="checkbox" v-model="updateSortOrder" class="checkbox checkbox-primary" />
              <span class="label-text">自动更新排序</span>
            </label>
          </div>
          <div class="flex justify-end gap-2">
            <button class="btn btn-ghost" @click="$emit('close')">取消</button>
            <button
              class="btn btn-primary"
              :class="{ loading: loading }"
              :disabled="loading || !targetSceneId"
              @click="handleMove"
            >
              确认移动
            </button>
          </div>
        </div>

        <!-- 更新角色 -->
        <div v-if="activeTab === 'character'" class="space-y-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">角色造型</span>
            </label>
            <select v-model="characterPoseId" class="select select-bordered w-full">
              <option :value="null">清除造型</option>
              <option v-for="pose in availablePoses" :key="pose.id" :value="pose.id">
                {{ pose.character_name }} - {{ pose.pose_name }}
              </option>
            </select>
          </div>
          <div class="flex justify-end gap-2">
            <button class="btn btn-ghost" @click="$emit('close')">取消</button>
            <button
              class="btn btn-primary"
              :class="{ loading: loading }"
              :disabled="loading"
              @click="handleUpdateCharacter"
            >
              确认更新
            </button>
          </div>
        </div>

        <!-- 重新生成 -->
        <div v-if="activeTab === 'regenerate'" class="space-y-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">重新生成选项</span>
            </label>
            <div class="space-y-2">
              <label class="label cursor-pointer justify-start gap-4">
                <input type="checkbox" v-model="regenerateImage" class="checkbox checkbox-primary" />
                <span class="label-text">重新生成图像</span>
              </label>
              <label class="label cursor-pointer justify-start gap-4">
                <input type="checkbox" v-model="regenerateAudio" class="checkbox checkbox-primary" />
                <span class="label-text">重新生成音频</span>
              </label>
            </div>
          </div>
          <div class="flex justify-end gap-2">
            <button class="btn btn-ghost" @click="$emit('close')">取消</button>
            <button
              class="btn btn-primary"
              :class="{ loading: loading }"
              :disabled="loading || (!regenerateImage && !regenerateAudio)"
              @click="handleRegenerate"
            >
              确认重新生成
            </button>
          </div>
        </div>

        <!-- 操作进度 -->
        <div v-if="operationResult" class="space-y-4">
          <div class="border-t pt-4">
            <h4 class="font-bold mb-2">操作结果</h4>

            <!-- 统计信息 -->
            <div class="stats stats-vertical lg:stats-horizontal shadow mb-4">
              <div class="stat">
                <div class="stat-title">总数</div>
                <div class="stat-value text-primary">{{ operationResult.total_count }}</div>
              </div>
              <div class="stat">
                <div class="stat-title">成功</div>
                <div class="stat-value text-success">{{ operationResult.success_count }}</div>
              </div>
              <div class="stat">
                <div class="stat-title">失败</div>
                <div class="stat-value text-error">{{ operationResult.failed_count }}</div>
              </div>
            </div>

            <!-- 错误列表 -->
            <div v-if="operationResult.errors.length > 0" class="collapse collapse-arrow bg-base-200">
              <input type="checkbox" />
              <div class="collapse-title text-error font-medium">
                错误详情 ({{ operationResult.errors.length }})
              </div>
              <div class="collapse-content">
                <ul class="list-disc list-inside space-y-1">
                  <li v-for="(error, index) in operationResult.errors" :key="index" class="text-sm">
                    <span class="font-mono">ID: {{ error.item_id }}</span>
                    - {{ error.error_message }}
                  </li>
                </ul>
              </div>
            </div>

            <!-- 进度追踪 -->
            <div v-if="operationResult.progress_id" class="alert alert-info mt-4">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                class="stroke-info shrink-0 w-6 h-6"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                ></path>
              </svg>
              <span>操作已启动，可在进度管理中查看</span>
            </div>
          </div>

          <div class="flex justify-end">
            <button class="btn btn-primary" @click="handleDone">完成</button>
          </div>
        </div>

        <!-- 错误提示 -->
        <div v-if="error" class="alert alert-error">
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
          <span>{{ error }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex'

export default {
  name: 'BatchOperationsModal',

  props: {
    type: {
      type: String,
      required: true,
      validator: (value) => ['shots', 'scenes'].includes(value),
    },
    availableScenes: {
      type: Array,
      default: () => [],
    },
    availablePoses: {
      type: Array,
      default: () => [],
    },
  },

  data() {
    return {
      activeTab: 'delete',
      targetSceneId: null,
      updateSortOrder: true,
      characterPoseId: null,
      regenerateImage: true,
      regenerateAudio: true,
    }
  },

  computed: {
    ...mapState('batchOperations', ['loading', 'error', 'operationResult']),
    ...mapGetters('batchOperations', ['selectedCount', 'selectedShots', 'selectedScenes']),

    selectedIds() {
      return this.type === 'shots' ? this.selectedShots : this.selectedScenes
    },
  },

  methods: {
    ...mapActions('batchOperations', [
      'batchDeleteShots',
      'batchDeleteScenes',
      'batchMoveShots',
      'batchUpdateCharacter',
      'batchRegenerateShots',
      'clearAll',
    ]),

    async handleDelete() {
      try {
        if (this.type === 'shots') {
          await this.batchDeleteShots(this.selectedShots)
        } else {
          await this.batchDeleteScenes(this.selectedScenes)
        }
        this.$emit('success')
      } catch (error) {
        console.error('Batch delete failed:', error)
      }
    },

    async handleMove() {
      if (this.type !== 'shots') return

      try {
        await this.batchMoveShots({
          shotIds: this.selectedShots,
          targetSceneId: this.targetSceneId,
          updateSortOrder: this.updateSortOrder,
        })
        this.$emit('success')
      } catch (error) {
        console.error('Batch move failed:', error)
      }
    },

    async handleUpdateCharacter() {
      if (this.type !== 'shots') return

      try {
        await this.batchUpdateCharacter({
          shotIds: this.selectedShots,
          characterPoseId: this.characterPoseId,
        })
        this.$emit('success')
      } catch (error) {
        console.error('Batch update character failed:', error)
      }
    },

    async handleRegenerate() {
      if (this.type !== 'shots') return

      try {
        await this.batchRegenerateShots({
          shotIds: this.selectedShots,
          regenerateImage: this.regenerateImage,
          regenerateAudio: this.regenerateAudio,
        })
        this.$emit('success')
      } catch (error) {
        console.error('Batch regenerate failed:', error)
      }
    },

    handleDone() {
      this.clearAll()
      this.$emit('close')
    },
  },
}
</script>
