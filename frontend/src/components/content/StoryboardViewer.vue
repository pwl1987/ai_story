<template>
  <div class="storyboard-viewer" tabindex="0" @keydown="handleKeydown">
    <!-- 模式切换工具栏 -->
    <div class="flex flex-wrap justify-between items-center gap-4 mb-6 bg-base-100 rounded-lg p-4 border border-base-300">
      <div class="flex items-center gap-3">
        <div class="text-xs text-base-content/60 font-medium uppercase tracking-wide">视图模式</div>
        <div class="btn-group">
          <button
            class="btn btn-sm"
            :class="{ 'btn-active': mode === 'view' }"
            @click="setMode('view')"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            查看模式
          </button>
          <button
            class="btn btn-sm"
            :class="{ 'btn-active': mode === 'edit' }"
            @click="setMode('edit')"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
            编辑模式
          </button>
          <button
            class="btn btn-sm"
            :class="{ 'btn-active': mode === 'quick' }"
            @click="setMode('quick')"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7" />
            </svg>
            快速预览
          </button>
          <button
            class="btn btn-sm"
            :class="{ 'btn-active': mode === 'markdown' }"
            @click="setMode('markdown')"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
            Markdown
          </button>
        </div>
      </div>

      <!-- 右侧操作区 -->
      <div class="flex items-center gap-3">
        <!-- 统计信息 -->
        <div v-if="scenes && scenes.length > 0" class="flex items-center gap-2">
          <div class="badge badge-primary">共 {{ scenes.length }} 个分镜</div>
          <div v-if="hasUnsavedChanges" class="badge badge-warning gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            有未保存更改
          </div>
        </div>

        <!-- 批量操作按钮 (编辑模式下显示) -->
        <template v-if="mode === 'edit' && selectedScenes.size > 0">
          <div class="divider divider-horizontal mx-0"></div>
          <div class="badge badge-info">已选 {{ selectedScenes.size }} 个</div>
          <div class="btn-group btn-group-xs">
            <button class="btn btn-xs" @click="batchUpdateShotType" title="批量修改镜头类型">
              批量修改类型
            </button>
            <button class="btn btn-xs btn-error" @click="batchDelete" title="批量删除">
              批量删除
            </button>
          </div>
          <button class="btn btn-xs btn-ghost" @click="clearSelection" title="取消选择">
            取消选择
          </button>
        </template>

        <!-- 操作按钮 -->
        <div v-if="mode !== 'markdown'" class="divider divider-horizontal mx-0"></div>
        <button
          v-if="mode === 'edit' || mode === 'quick'"
          class="btn btn-sm btn-primary gap-2"
          @click="addBlankCard"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          新增分镜
        </button>
        <button
          v-if="mode === 'edit'"
          class="btn btn-sm btn-ghost gap-2"
          :class="{ 'btn-active': isMultiSelectMode }"
          @click="toggleMultiSelectMode"
          title="多选模式 (M)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012 2h2a2 2 0 012-2m-6 6a2 2 0 012 2h2a2 2 0 012-2m-6 6a2 2 0 012 2h2a2 2 0 012-2" />
          </svg>
          多选
        </button>
        <button
          v-if="mode === 'markdown'"
          class="btn btn-sm btn-ghost gap-2"
          @click="copyMarkdown"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          复制文本
        </button>
      </div>
    </div>

    <!-- 快捷键提示 -->
    <div v-if="mode === 'edit' && showKeyboardHints" class="alert alert-sm bg-base-200 mb-4">
      <div class="flex items-center gap-4 text-xs">
        <span class="font-semibold">快捷键：</span>
        <kbd class="kbd kbd-xs">Ctrl+N</kbd> <span>新增</span>
        <kbd class="kbd kbd-xs">Ctrl+S</kbd> <span>保存</span>
        <kbd class="kbd kbd-xs">Ctrl+A</kbd> <span>全选</span>
        <kbd class="kbd kbd-xs">Esc</kbd> <span>取消选择</span>
        <kbd class="kbd kbd-xs">Delete</kbd> <span>删除选中</span>
        <kbd class="kbd kbd-xs">M</kbd> <span>多选模式</span>
        <button class="btn btn-xs btn-ghost ml-auto" @click="showKeyboardHints = false">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
    <button v-else-if="mode === 'edit'" class="btn btn-xs btn-ghost gap-1 mb-4" @click="showKeyboardHints = true">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      快捷键提示
    </button>

    <!-- 查看模式 - 只读卡片 -->
    <div v-if="mode === 'view'" class="cards-container">
      <div v-if="scenes && scenes.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div
          v-for="(scene, index) in scenes"
          :key="scene.scene_number"
          class="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow"
        >
          <div class="card-body p-4">
            <div class="flex justify-between items-center mb-3">
              <div class="badge badge-lg">场景 {{ scene.scene_number }}</div>
              <div class="badge badge-ghost">{{ scene.shot_type || '标准镜头' }}</div>
            </div>

            <div v-if="scene.urls && scene.urls.length > 0" class="mb-3">
              <img :src="scene.urls[0].url" class="w-full h-32 object-cover rounded-lg" />
            </div>
            <div v-else-if="scene.video_urls && scene.video_urls.length > 0" class="mb-3">
              <video :src="scene.video_urls[0].url" class="w-full h-32 object-cover rounded-lg" preload="metadata"></video>
            </div>

            <div class="space-y-2 text-sm">
              <div class="truncate" :title="scene.narration">
                <span class="font-semibold text-base-content/60">旁白：</span>{{ scene.narration }}
              </div>
              <div class="line-clamp-2 text-base-content/70" :title="scene.visual_prompt">
                {{ scene.visual_prompt }}
              </div>
            </div>

            <div class="card-actions justify-end mt-3">
              <div class="text-xs text-base-content/50">切换到编辑模式进行修改</div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-12">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-base-content/20 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
        </svg>
        <p class="text-base-content/60">暂无分镜数据</p>
        <p class="text-sm text-base-content/40 mt-2">请先生成分镜内容</p>
      </div>
    </div>

    <!-- 编辑模式 - 完整编辑功能 -->
    <div v-else-if="mode === 'edit'" class="cards-container">
      <div v-if="scenes && scenes.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div
          v-for="(scene, index) in scenes"
          :key="scene.scene_number"
          class="card bg-base-100 shadow-xl transition-all duration-300"
          :class="{
            'ring-2 ring-primary ring-offset-2': hasSceneChanges(scene.scene_number),
            'ring-2 ring-accent ring-offset-2': selectedScenes.has(scene.scene_number),
            'cursor-move': isDragging,
            'opacity-50': isDragging && draggedScene === scene.scene_number
          }"
          draggable="true"
          @dragstart="onDragStart($event, scene, index)"
          @dragend="onDragEnd"
          @dragover.prevent
          @drop="onDrop($event, index)"
        >
          <div class="card-body p-4">
            <!-- 多选复选框 -->
            <div v-if="isMultiSelectMode" class="absolute top-3 left-3 z-10">
              <input
                type="checkbox"
                class="checkbox checkbox-xs"
                :checked="selectedScenes.has(scene.scene_number)"
                @change="toggleSceneSelection(scene.scene_number, $event)"
                @click.stop
              />
            </div>

            <!-- 卡片头部 -->
            <div class="flex justify-between items-center mb-3">
              <div class="flex items-center gap-2">
                <div class="badge badge-lg badge-secondary">场景 {{ scene.scene_number }}</div>
                <div v-if="hasSceneChanges(scene.scene_number)" class="badge badge-warning gap-1 animate-pulse">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01" />
                  </svg>
                  未保存
                </div>
              </div>
              <div class="flex items-center gap-2">
                <!-- 拖拽手柄 -->
                <div class="cursor-move text-base-content/40 hover:text-base-content/60" title="拖拽排序">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16" />
                  </svg>
                </div>
                <!-- 镜头类型选择 -->
                <select
                  v-model="scene.shot_type"
                  class="select select-xs select-bordered"
                  @change="markSceneChanged(scene.scene_number)"
                >
                  <option value="标准镜头">标准镜头</option>
                  <option value="特写">特写</option>
                  <option value="中景">中景</option>
                  <option value="远景">远景</option>
                  <option value="全景">全景</option>
                  <option value="俯视">俯视</option>
                  <option value="仰视">仰视</option>
                </select>
                <!-- 操作菜单 -->
                <div class="dropdown dropdown-end">
                  <label tabindex="0" class="btn btn-xs btn-ghost">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                    </svg>
                  </label>
                  <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-40">
                    <li><a @click="insertBlankCard(index, 'before')">在此之前插入</a></li>
                    <li><a @click="insertBlankCard(index, 'after')">在此之后插入</a></li>
                    <li><a @click="duplicateCard(index)">复制此分镜</a></li>
                    <div class="divider my-0"></div>
                    <li v-if="scenes.length > 1"><a class="text-error" @click="removeCard(index)">删除</a></li>
                  </ul>
                </div>
              </div>
            </div>

            <!-- 图片/视频选择器 -->
            <div v-if="scene.urls && scene.urls.length > 0" class="mb-3">
              <div class="text-xs font-semibold text-base-content/60 mb-2">
                生成图片 ({{ getSelectedImageIndex(scene.scene_number) + 1 }}/{{ scene.urls.length }})
              </div>
              <div class="relative rounded-lg overflow-hidden bg-base-200 mb-2">
                <img
                  :src="getSelectedImage(scene.scene_number)"
                  class="w-full h-32 object-cover cursor-pointer hover:opacity-90"
                  @click="openImageModal(scene.scene_number)"
                />
              </div>
              <div v-if="scene.urls.length > 1" class="flex gap-2 overflow-x-auto pb-2">
                <div
                  v-for="(url, idx) in scene.urls"
                  :key="idx"
                  class="flex-shrink-0 cursor-pointer rounded border-2"
                  :class="getSelectedImageIndex(scene.scene_number) === idx ? 'border-primary' : 'border-base-300 hover:border-primary/50'"
                  @click="selectImage(scene.scene_number, idx)"
                >
                  <img :src="url.url" class="w-12 h-12 object-cover rounded" />
                </div>
              </div>
            </div>

            <div v-if="scene.video_urls && scene.video_urls.length > 0" class="mb-3">
              <div class="text-xs font-semibold text-base-content/60 mb-2">生成视频</div>
              <video :src="getSelectedVideo(scene.scene_number)" class="w-full h-32 object-cover rounded-lg" controls preload="metadata"></video>
            </div>

            <!-- 旁白编辑 -->
            <div class="mb-3">
              <div class="text-xs font-semibold text-base-content/60 mb-1">
                旁白文本
                <span v-if="isFieldEditing(scene.scene_number, 'narration')" class="text-primary ml-1">(编辑中)</span>
              </div>
              <textarea
                v-model="scene.narration"
                class="textarea textarea-bordered textarea-xs w-full"
                rows="2"
                placeholder="请输入旁白文本..."
                @focus="setFieldEditing(scene.scene_number, 'narration', true)"
                @blur="handleFieldBlur(scene.scene_number, 'narration')"
              ></textarea>
            </div>

            <!-- 视觉提示词编辑 -->
            <div class="mb-3">
              <div class="text-xs font-semibold text-base-content/60 mb-1">
                视觉提示词
                <span v-if="isFieldEditing(scene.scene_number, 'visual_prompt')" class="text-primary ml-1">(编辑中)</span>
              </div>
              <textarea
                v-model="scene.visual_prompt"
                class="textarea textarea-bordered textarea-xs w-full"
                rows="3"
                placeholder="请输入视觉描述..."
                @focus="setFieldEditing(scene.scene_number, 'visual_prompt', true)"
                @blur="handleFieldBlur(scene.scene_number, 'visual_prompt')"
              ></textarea>
            </div>

            <!-- 运镜描述编辑 -->
            <div class="mb-3">
              <div class="text-xs font-semibold text-base-content/60 mb-1">运镜描述</div>
              <textarea
                v-model="scene.camera_movement"
                class="textarea textarea-bordered textarea-xs w-full"
                rows="2"
                placeholder="请输入运镜描述..."
                @focus="setFieldEditing(scene.scene_number, 'camera_movement', true)"
                @blur="handleFieldBlur(scene.scene_number, 'camera_movement')"
              ></textarea>
            </div>

            <!-- AI生成按钮 -->
            <button
              class="btn btn-xs btn-primary w-full gap-1"
              :class="{ 'loading': executingScenes[scene.scene_number] }"
              :disabled="executingScenes[scene.scene_number] || !projectId"
              @click="executeSceneGeneration(scene.scene_number)"
            >
              <svg v-if="!executingScenes[scene.scene_number]" xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              {{ executingScenes[scene.scene_number] ? '生成中...' : '执行AI生成' }}
            </button>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-12">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-base-content/20 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
        </svg>
        <p class="text-base-content/60">暂无分镜数据</p>
        <button class="btn btn-primary mt-4" @click="addBlankCard">创建第一个分镜</button>
      </div>
    </div>

    <!-- 快速预览模式 -->
    <div v-else-if="mode === 'quick'" class="cards-container">
      <div v-if="scenes && scenes.length > 0" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
        <div
          v-for="(scene, index) in scenes"
          :key="scene.scene_number"
          class="card bg-base-100 shadow hover:shadow-md transition-shadow cursor-pointer"
          @click="quickEditScene(scene)"
        >
          <div class="card-body p-3">
            <div class="flex justify-between items-center mb-2">
              <div class="badge badge-sm">{{ scene.scene_number }}</div>
              <div class="text-xs text-base-content/60">{{ scene.shot_type || '标准' }}</div>
            </div>
            <div class="mb-2">
              <div v-if="scene.urls && scene.urls.length > 0" class="h-20 bg-base-200 rounded overflow-hidden">
                <img :src="scene.urls[0].url" class="w-full h-full object-cover" />
              </div>
              <div v-else class="h-20 bg-base-200 rounded flex items-center justify-center text-base-content/40 text-xs">
                无图片
              </div>
            </div>
            <p class="text-xs line-clamp-2 text-base-content/80">{{ scene.narration }}</p>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-12">
        <p class="text-base-content/60">暂无分镜数据</p>
      </div>
    </div>

    <!-- Markdown模式 -->
    <div v-else-if="mode === 'markdown'" class="markdown-container">
      <div class="mockup-code bg-neutral text-neutral-content">
        <pre class="text-sm whitespace-pre-wrap px-6 py-4"><code>{{ formattedMarkdown }}</code></pre>
      </div>
    </div>

    <!-- 保存状态提示 -->
    <div v-if="showSaveNotification" class="toast toast-top toast-end z-50">
      <div class="alert alert-success shadow-lg">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>已自动保存</span>
      </div>
    </div>

    <!-- 批量修改镜头类型对话框 -->
    <dialog ref="batchUpdateModal" class="modal">
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">批量修改镜头类型</h3>
        <div class="form-control">
          <label class="label">
            <span class="label-text">选择新的镜头类型</span>
          </label>
          <select v-model="batchShotType" class="select select-bordered w-full">
            <option value="标准镜头">标准镜头</option>
            <option value="特写">特写</option>
            <option value="中景">中景</option>
            <option value="远景">远景</option>
            <option value="全景">全景</option>
            <option value="俯视">俯视</option>
            <option value="仰视">仰视</option>
          </select>
        </div>
        <div class="modal-action">
          <button class="btn btn-ghost" @click="closeBatchUpdateModal">取消</button>
          <button class="btn btn-primary" @click="confirmBatchUpdate">确定</button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button>close</button>
      </form>
    </dialog>
  </div>
</template>

<script>
import projectApi from '@/api/projects';
import { createProjectStageSSE, SSE_EVENT_TYPES } from '@/services/sseService';

export default {
  name: 'StoryboardViewer',
  props: {
    // 分镜场景数据 (props 避免与 computed 同名，使用 scenesData)
    scenesData: {
      type: Array,
      default: () => [],
    },
    // 兼容旧版本的 data prop
    data: {
      type: [String, Object, Array],
      default: null,
    },
    // 项目ID
    projectId: {
      type: String,
      default: null,
    },
    // 阶段类型 (如 'storyboard', 'image_generation' 等)
    stageType: {
      type: String,
      default: 'storyboard',
    },
    // 阶段对象 (兼容)
    stage: {
      type: Object,
      default: null,
    },
    // 是否可编辑
    canEdit: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      // 模式: view | edit | quick | markdown
      mode: 'view',

      selectedImages: {},
      selectedVideos: {},
      executingScenes: {},
      localScenes: [],

      // 编辑状态追踪
      editingFields: {},
      changedScenes: new Set(),

      // 多选模式
      isMultiSelectMode: false,
      selectedScenes: new Set(),

      // 拖拽状态
      isDragging: false,
      draggedScene: null,
      draggedIndex: null,

      // UI状态
      showSaveNotification: false,
      saveNotificationTimer: null,
      showKeyboardHints: false,
      debounceTimer: null,

      // 批量操作
      batchShotType: '标准镜头',
    };
  },
  computed: {
    // 显示场景：优先使用本地编辑数据，否则使用 prop 传入的数据
    displayScenes() {
      // 如果有本地编辑数据，返回本地数据
      if (this.localScenes.length > 0) {
        return this.localScenes;
      }

      // 否则，使用 prop 传入的场景数据
      // 支持两种 prop：scenesData (新) 或 data (旧，兼容)
      const sourceData = (this.scenesData && this.scenesData.length > 0) ? this.scenesData : this.data;

      if (!sourceData) return [];

      try {
        let parsedData = sourceData;
        if (typeof sourceData === 'string') {
          parsedData = JSON.parse(sourceData);
        }

        if (Array.isArray(parsedData)) {
          return parsedData;
        } else if (parsedData.scenes && Array.isArray(parsedData.scenes)) {
          return parsedData.scenes;
        } else if (parsedData.storyboards && Array.isArray(parsedData.storyboards)) {
          return parsedData.storyboards;
        }

        return [];
      } catch (error) {
        console.error('解析分镜数据失败:', error);
        return [];
      }
    },

    // 兼容旧代码，使用 displayScenes
    scenes() {
      return this.displayScenes;
    },

    hasUnsavedChanges() {
      return this.changedScenes.size > 0;
    },

    formattedMarkdown() {
      if (!this.displayScenes || this.displayScenes.length === 0) {
        return '暂无分镜数据';
      }

      return this.displayScenes.map((scene) => {
        const sceneNumber = scene.scene_number || '未知';
        const narration = scene.narration || '无';
        const shotType = scene.shot_type || '标准镜头';
        const visualPrompt = scene.visual_prompt || '无';
        const cameraMovement = scene.camera_movement || null;

        let markdown = `场景 ${sceneNumber}\n文案: ${narration}\n镜头类型: ${shotType}\n画面描述: ${visualPrompt}`;

        if (cameraMovement) {
          markdown += `\n运镜描述: ${cameraMovement}`;
        }

        return markdown;
      }).join('\n\n---\n\n');
    },
  },
  watch: {
    data: {
      deep: true,
      handler(newData) {
        console.log('[StoryboardViewer] data prop 更新');
      }
    },
  },
  beforeDestroy() {
    this.disconnectSSE();
    if (this.saveNotificationTimer) {
      clearTimeout(this.saveNotificationTimer);
    }
    // 移除键盘事件监听
    document.removeEventListener('keydown', this.handleKeydown);
  },
  mounted() {
    // 添加键盘事件监听
    document.addEventListener('keydown', this.handleKeydown);
  },
  methods: {
    // ========== 键盘快捷键 ==========
    handleKeydown(event) {
      // 只在编辑模式下响应快捷键
      if (this.mode !== 'edit') return;

      // Ctrl+N - 新增分镜
      if (event.ctrlKey && event.key === 'n') {
        event.preventDefault();
        this.addBlankCard();
        return;
      }

      // Ctrl+S - 保存
      if (event.ctrlKey && event.key === 's') {
        event.preventDefault();
        this.saveChanges();
        this.$message?.success('已保存');
        return;
      }

      // Ctrl+A - 全选
      if (event.ctrlKey && event.key === 'a') {
        event.preventDefault();
        this.selectAll();
        return;
      }

      // Esc - 取消选择或退出多选模式
      if (event.key === 'Escape') {
        if (this.isMultiSelectMode || this.selectedScenes.size > 0) {
          this.clearSelection();
          return;
        }
      }

      // Delete - 删除选中的分镜
      if (event.key === 'Delete' && this.selectedScenes.size > 0) {
        event.preventDefault();
        this.batchDelete();
        return;
      }

      // M - 多选模式
      if (event.key === 'm' && !event.ctrlKey && !event.metaKey) {
        // 检查是否在输入框中
        if (event.target.tagName !== 'TEXTAREA' && event.target.tagName !== 'INPUT') {
          this.toggleMultiSelectMode();
          return;
        }
      }
    },

    // ========== 多选操作 ==========
    toggleMultiSelectMode() {
      this.isMultiSelectMode = !this.isMultiSelectMode;
      if (!this.isMultiSelectMode) {
        this.clearSelection();
      }
      console.log('[StoryboardViewer] 多选模式:', this.isMultiSelectMode);
    },

    toggleSceneSelection(sceneNumber, event) {
      if (event.target.checked) {
        this.selectedScenes.add(sceneNumber);
      } else {
        this.selectedScenes.delete(sceneNumber);
      }
    },

    selectAll() {
      this.isMultiSelectMode = true;
      this.scenes.forEach(scene => {
        this.selectedScenes.add(scene.scene_number);
      });
      this.$message?.info(`已选择 ${this.scenes.length} 个分镜`);
    },

    clearSelection() {
      this.selectedScenes.clear();
      if (!this.isMultiSelectMode) {
        this.isMultiSelectMode = false;
      }
    },

    batchDelete() {
      if (this.selectedScenes.size === 0) return;

      const count = this.selectedScenes.size;
      if (confirm(`确定要删除选中的 ${count} 个分镜吗？`)) {
        // 确保本地数据已初始化
        if (this.localScenes.length === 0 && this.scenes.length > 0) {
          this.localScenes = JSON.parse(JSON.stringify(this.scenes));
        }

        // 过滤掉选中的场景
        this.localScenes = this.localScenes.filter(
          scene => !this.selectedScenes.has(scene.scene_number)
        );

        // 重新编号
        this.reorderSceneNumbers();

        this.clearSelection();
        this.saveChanges();
        this.$message?.success(`已删除 ${count} 个分镜`);
      }
    },

    batchUpdateShotType() {
      if (this.selectedScenes.size === 0) return;

      // 打开批量修改对话框
      this.$refs.batchUpdateModal?.showModal();
    },

    closeBatchUpdateModal() {
      this.$refs.batchUpdateModal?.close();
    },

    confirmBatchUpdate() {
      // 确保本地数据已初始化
      if (this.localScenes.length === 0 && this.scenes.length > 0) {
        this.localScenes = JSON.parse(JSON.stringify(this.scenes));
      }

      // 更新所有选中场景的镜头类型
      this.localScenes.forEach(scene => {
        if (this.selectedScenes.has(scene.scene_number)) {
          scene.shot_type = this.batchShotType;
          this.changedScenes.add(scene.scene_number);
        }
      });

      this.clearSelection();
      this.saveChanges();
      this.closeBatchUpdateModal();
      this.$message?.success(`已批量修改为 ${this.batchShotType}`);
    },

    // ========== 拖拽排序 ==========
    onDragStart(event, scene, index) {
      this.isDragging = true;
      this.draggedScene = scene.scene_number;
      this.draggedIndex = index;
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', index);
    },

    onDragEnd() {
      this.isDragging = false;
      this.draggedScene = null;
      this.draggedIndex = null;
    },

    onDrop(event, dropIndex) {
      event.preventDefault();

      if (this.draggedIndex === null || this.draggedIndex === dropIndex) {
        return;
      }

      // 确保本地数据已初始化
      if (this.localScenes.length === 0 && this.scenes.length > 0) {
        this.localScenes = JSON.parse(JSON.stringify(this.scenes));
      }

      const draggedScene = this.localScenes[this.draggedIndex];

      // 移除拖拽的元素
      this.localScenes.splice(this.draggedIndex, 1);

      // 插入到新位置
      this.localScenes.splice(dropIndex, 0, draggedScene);

      // 重新编号
      this.reorderSceneNumbers();

      this.saveChanges();
      this.$message?.success('排序已更新');
    },

    reorderSceneNumbers() {
      this.localScenes.forEach((scene, index) => {
        scene.scene_number = index + 1;
      });
    },

    // ========== 模式切换 ==========
    setMode(newMode) {
      this.mode = newMode;
      console.log('[StoryboardViewer] 切换模式:', newMode);

      if (newMode === 'edit' && this.localScenes.length === 0 && this.scenes.length > 0) {
        this.localScenes = JSON.parse(JSON.stringify(this.scenes));
      }

      // 退出编辑模式时清除选择状态
      if (newMode !== 'edit') {
        this.clearSelection();
        this.isMultiSelectMode = false;
      }
    },

    // ========== 编辑状态追踪 ==========
    setFieldEditing(sceneNumber, field, isEditing) {
      const key = `${sceneNumber}_${field}`;
      this.$set(this.editingFields, key, isEditing);
    },

    isFieldEditing(sceneNumber, field) {
      const key = `${sceneNumber}_${field}`;
      return this.editingFields[key] === true;
    },

    hasSceneChanges(sceneNumber) {
      return this.changedScenes.has(sceneNumber);
    },

    markSceneChanged(sceneNumber) {
      if (this.localScenes.length === 0 && this.scenes.length > 0) {
        this.localScenes = JSON.parse(JSON.stringify(this.scenes));
      }
      this.changedScenes.add(sceneNumber);
      this.debouncedSave();
    },

    // ========== 自动保存 ==========
    handleFieldBlur(sceneNumber, field) {
      const key = `${sceneNumber}_${field}`;
      this.$set(this.editingFields, key, false);
      this.markSceneChanged(sceneNumber);
    },

    debouncedSave() {
      if (this.debounceTimer) clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.saveChanges();
      }, 500);
    },

    saveChanges() {
      if (this.localScenes.length > 0) {
        console.log('[StoryboardViewer] 自动保存:', this.localScenes.length, '个场景');
        this.$emit('scenes-updated', this.localScenes);
        this.changedScenes.clear();

        this.showSaveNotification = true;
        if (this.saveNotificationTimer) clearTimeout(this.saveNotificationTimer);
        this.saveNotificationTimer = setTimeout(() => {
          this.showSaveNotification = false;
        }, 2000);
      }
    },

    // ========== 卡片操作 ==========
    addBlankCard() {
      this.insertBlankCard(this.scenes.length - 1, 'after');
    },

    insertBlankCard(index, position) {
      if (this.localScenes.length === 0 && this.scenes.length > 0) {
        this.localScenes = JSON.parse(JSON.stringify(this.scenes));
      }

      let insertIndex = position === 'before' ? index : index + 1;

      let newSceneNumber;
      if (this.localScenes.length === 0) {
        newSceneNumber = 1;
      } else if (insertIndex === 0) {
        newSceneNumber = Math.max(1, this.localScenes[0].scene_number - 1);
      } else if (insertIndex >= this.localScenes.length) {
        const maxNum = Math.max(...this.localScenes.map(s => s.scene_number || 0));
        newSceneNumber = maxNum + 1;
      } else {
        newSceneNumber = (this.localScenes[insertIndex - 1].scene_number + this.localScenes[insertIndex].scene_number) / 2;
      }

      const blankCard = {
        scene_number: newSceneNumber,
        narration: '请输入旁白文本...',
        visual_prompt: '请输入视觉提示词...',
        shot_type: '标准镜头',
        camera_movement: '',
        urls: [],
        video_urls: [],
      };

      this.localScenes.splice(insertIndex, 0, blankCard);
      this.changedScenes.add(newSceneNumber);
      this.saveChanges();

      this.$message?.success(`已添加场景 ${newSceneNumber}`);
    },

    duplicateCard(index) {
      if (this.localScenes.length === 0 && this.scenes.length > 0) {
        this.localScenes = JSON.parse(JSON.stringify(this.scenes));
      }

      const scene = this.localScenes[index];
      const newScene = JSON.parse(JSON.stringify(scene));

      const maxNum = Math.max(...this.localScenes.map(s => s.scene_number || 0));
      newScene.scene_number = maxNum + 1;
      newScene.urls = [];
      newScene.video_urls = [];

      this.localScenes.splice(index + 1, 0, newScene);
      this.changedScenes.add(newScene.scene_number);
      this.saveChanges();

      this.$message?.success(`已复制场景 ${scene.scene_number}`);
    },

    removeCard(index) {
      if (this.localScenes.length === 0 && this.scenes.length > 0) {
        this.localScenes = JSON.parse(JSON.stringify(this.scenes));
      }

      if (this.localScenes.length <= 1) {
        this.$message?.warning('至少需要保留一个场景');
        return;
      }

      const scene = this.localScenes[index];
      if (confirm(`确定要删除场景 ${scene.scene_number} 吗？`)) {
        this.localScenes.splice(index, 1);
        this.saveChanges();
        this.$message?.success(`已删除场景 ${scene.scene_number}`);
      }
    },

    quickEditScene(scene) {
      this.setMode('edit');
      this.$nextTick(() => {
        console.log('[StoryboardViewer] 快速编辑场景:', scene.scene_number);
      });
    },

    // ========== 图片/视频选择 ==========
    getSelectedImageIndex(sceneNumber) {
      return this.selectedImages[sceneNumber] !== undefined
        ? this.selectedImages[sceneNumber]
        : 0;
    },

    getSelectedImage(sceneNumber) {
      const scene = this.scenes.find(s => s.scene_number === sceneNumber);
      if (!scene || !scene.urls || scene.urls.length === 0) return '';
      const index = this.getSelectedImageIndex(sceneNumber);
      return scene.urls[index]?.url || scene.urls[0]?.url;
    },

    selectImage(sceneNumber, imageIndex) {
      this.$set(this.selectedImages, sceneNumber, imageIndex);
    },

    getSelectedVideoIndex(sceneNumber) {
      return this.selectedVideos[sceneNumber] !== undefined
        ? this.selectedVideos[sceneNumber]
        : 0;
    },

    getSelectedVideo(sceneNumber) {
      const scene = this.scenes.find(s => s.scene_number === sceneNumber);
      if (!scene || !scene.video_urls || scene.video_urls.length === 0) return '';
      const index = this.getSelectedVideoIndex(sceneNumber);
      return scene.video_urls[index]?.url || scene.video_urls[0]?.url;
    },

    selectVideo(sceneNumber, videoIndex) {
      this.$set(this.selectedVideos, sceneNumber, videoIndex);
    },

    openImageModal(sceneNumber) {
      console.log('[StoryboardViewer] 打开图片查看器:', sceneNumber);
    },

    // ========== AI生成 ==========
    async executeSceneGeneration(sceneNumber) {
      if (!this.projectId) {
        this.$message?.error('缺少项目ID');
        return;
      }

      const scene = this.scenes.find(s => s.scene_number === sceneNumber);
      if (!scene) {
        this.$message?.error(`未找到场景 ${sceneNumber}`);
        return;
      }

      this.$set(this.executingScenes, sceneNumber, true);

      try {
        const inputData = {
          storyboard_ids: [sceneNumber],
          narration: scene.narration,
          visual_prompt: scene.visual_prompt,
          shot_type: scene.shot_type,
          camera_movement: scene.camera_movement,
        };

        this.connectSSE();

        await projectApi.executeStage(
          this.projectId,
          this.stageType,
          inputData
        );

        this.$message?.success(`场景 ${sceneNumber} AI生成已启动`);
      } catch (error) {
        console.error('执行场景生成失败:', error);
        const errorMsg = error.response?.data?.error || error.message || '生成失败';
        this.$message?.error(`场景 ${sceneNumber} 生成失败: ${errorMsg}`);
        this.$set(this.executingScenes, sceneNumber, false);
      }
    },

    // ========== SSE连接 ==========
    connectSSE() {
      this.disconnectSSE();

      this.sseClient = createProjectStageSSE(this.projectId, this.stageType, {
        autoReconnect: false,
      });

      this.sseClient
        .on(SSE_EVENT_TYPES.DONE, (data) => {
          console.log('[StoryboardViewer] 生成完成:', data);
          this.executingScenes = {};
          this.$emit('scene-generated', { sceneNumber: null, response: data });
          this.$message?.success('生成完成！');
        })
        .on(SSE_EVENT_TYPES.ERROR, (data) => {
          console.error('[StoryboardViewer] 生成失败:', data);
          this.executingScenes = {};
          this.$message?.error(data.error || '生成失败');
        });
    },

    disconnectSSE() {
      if (this.sseClient) {
        this.sseClient.disconnect();
        this.sseClient = null;
      }
    },

    // ========== 工具方法 ==========
    async copyMarkdown() {
      try {
        await navigator.clipboard.writeText(this.formattedMarkdown);
        this.$message?.success('已复制到剪贴板');
      } catch (error) {
        this.$message?.error('复制失败');
      }
    },
  },
};
</script>

<style scoped>
.storyboard-viewer {
  width: 100%;
  max-width: 100%;
  outline: none; /* 移除 focus 时默认的轮廓 */
}

.cards-container {
  width: 100%;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 卡片动画 */
.card {
  transition: all 0.2s ease;
}

.card:hover {
  transform: translateY(-2px);
}

/* 编辑模式下的选中效果 */
.ring-2 {
  animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse-ring {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* 拖拽样式 */
.cursor-move {
  cursor: move;
}

.cursor-move:active {
  cursor: grabbing;
}

.opacity-50 {
  opacity: 0.5;
}

/* 文本区域样式 */
.textarea {
  transition: all 0.2s ease;
}

.textarea:focus {
  border-color: hsl(var(--p));
  box-shadow: 0 0 0 3px hsla(var(--p) / 0.1);
}

/* 保存通知动画 */
.toast {
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* kbd 快捷键样式 */
.kbd {
  border-radius: 0.25rem;
  padding: 0.125rem 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}
</style>
