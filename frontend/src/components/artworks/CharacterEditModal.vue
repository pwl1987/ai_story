<template>
  <div class="modal modal-open">
    <div class="modal-box max-w-4xl">
      <!-- 标题 -->
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-bold">
          {{ isEdit ? '编辑角色' : '添加角色' }}
        </h2>
        <button class="btn btn-sm btn-circle btn-ghost" @click="$emit('close')">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <!-- 标签页 -->
      <div class="tabs tabs-boxed mb-4">
        <a
          :class="['tab', { 'tab-active': activeTab === 'basic' }]"
          @click="activeTab = 'basic'"
        >
          基本信息
        </a>
        <a
          v-if="isEdit"
          :class="['tab', { 'tab-active': activeTab === 'poses' }]"
          @click="activeTab = 'poses'"
        >
          造型管理
        </a>
        <a
          v-if="isEdit"
          :class="['tab', { 'tab-active': activeTab === 'voice' }]"
          @click="activeTab = 'voice'"
        >
          音色配置
        </a>
      </div>

      <!-- 加载状态 -->
      <loading-container :loading="loading">
        <!-- 基本信息 -->
        <div v-if="activeTab === 'basic'" class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- 作品选择 -->
            <div class="form-control">
              <label class="label">
                <span class="label-text">所属作品 *</span>
              </label>
              <select
                v-model="form.artwork"
                class="select select-bordered"
                :disabled="isEdit"
              >
                <option value="">请选择作品</option>
                <option v-for="artwork in artworks" :key="artwork.id" :value="artwork.id">
                  {{ artwork.title }}
                </option>
              </select>
            </div>

            <!-- 角色名称 -->
            <div class="form-control">
              <label class="label">
                <span class="label-text">角色名称 *</span>
              </label>
              <input
                v-model="form.name"
                type="text"
                placeholder="例如: xiaoming"
                class="input input-bordered"
              />
            </div>

            <!-- 显示名称 -->
            <div class="form-control">
              <label class="label">
                <span class="label-text">显示名称 *</span>
              </label>
              <input
                v-model="form.display_name"
                type="text"
                placeholder="例如: 小明"
                class="input input-bordered"
              />
            </div>

            <!-- 重要性排名 -->
            <div class="form-control">
              <label class="label">
                <span class="label-text">重要性排名</span>
              </label>
              <input
                v-model.number="form.importance_rank"
                type="number"
                min="1"
                placeholder="数字越小越重要"
                class="input input-bordered"
              />
            </div>
          </div>

          <!-- 角色描述 -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">角色描述</span>
            </label>
            <textarea
              v-model="form.description"
              placeholder="描述角色的外貌、性格、背景等"
              class="textarea textarea-bordered"
              rows="3"
            ></textarea>
          </div>

          <!-- 性格特点 -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">性格特点</span>
            </label>
            <textarea
              v-model="form.personality"
              placeholder="例如: 开朗、善良、勇敢"
              class="textarea textarea-bordered"
              rows="2"
            ></textarea>
          </div>

          <!-- 引擎偏好 -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">LLM引擎</span>
              </label>
              <select v-model="form.preferred_llm_engine" class="select select-bordered">
                <option value="ollama">Ollama</option>
                <option value="openai">OpenAI</option>
                <option value="claude">Claude</option>
              </select>
            </div>
            <div class="form-control">
              <label class="label">
                <span class="label-text">TTS引擎</span>
              </label>
              <select v-model="form.preferred_tts_engine" class="select select-bordered">
                <option value="edge">Edge-TTS</option>
                <option value="elevenlabs">ElevenLabs</option>
                <option value="baidu">百度TTS</option>
                <option value="azure">Azure TTS</option>
              </select>
            </div>
            <div class="form-control">
              <label class="label">
                <span class="label-text">图像引擎</span>
              </label>
              <select v-model="form.preferred_image_engine" class="select select-bordered">
                <option value="comfyui">ComfyUI</option>
                <option value="dalle">DALL-E</option>
                <option value="sd">Stable Diffusion</option>
              </select>
            </div>
          </div>

          <!-- 立绘上传 -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">角色立绘</span>
            </label>
            <portrait-preview
              :image="form.default_portrait"
              :name="form.display_name || '角色'"
              :editable="true"
              @upload="handlePortraitUpload"
              @remove="handlePortraitRemove"
            />
          </div>
        </div>

        <!-- 造型管理 -->
        <div v-if="activeTab === 'poses'" class="space-y-4">
          <pose-selector
            :poses="character?.poses || []"
            layout="grid"
            @add="handleAddPose"
            @edit="handleEditPose"
            @delete="handleDeletePose"
            @set-default="handleSetDefaultPose"
          />
        </div>

        <!-- 音色配置 -->
        <div v-if="activeTab === 'voice'" class="space-y-4">
          <voice-player
            :config="voiceConfig"
            @configure="handleConfigureVoice"
            @update:config="handleUpdateVoiceConfig"
            @test="handleTestVoice"
          />
        </div>
      </loading-container>

      <!-- 操作按钮 -->
      <div class="modal-action">
        <button class="btn btn-ghost" @click="$emit('close')">取消</button>
        <button
          class="btn btn-primary"
          :disabled="saving"
          @click="handleSave"
        >
          <span v-if="saving" class="loading loading-spinner loading-sm"></span>
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';
import PortraitPreview from './PortraitPreview.vue';
import PoseSelector from './PoseSelector.vue';
import VoicePlayer from './VoicePlayer.vue';
import LoadingContainer from '@/components/common/LoadingContainer.vue';

export default {
  name: 'CharacterEditModal',

  components: {
    PortraitPreview,
    PoseSelector,
    VoicePlayer,
    LoadingContainer,
  },

  props: {
    characterId: {
      type: String,
      default: null,
    },
  },

  data() {
    return {
      activeTab: 'basic',
      loading: false,
      saving: false,
      character: null,
      voiceConfig: null,
      form: {
        artwork: '',
        name: '',
        display_name: '',
        description: '',
        personality: '',
        importance_rank: 10,
        preferred_llm_engine: 'ollama',
        preferred_tts_engine: 'edge',
        preferred_image_engine: 'comfyui',
        default_portrait: null,
      },
    };
  },

  computed: {
    ...mapState('artworks', ['artworks']),

    isEdit() {
      return !!this.characterId;
    },
  },

  async mounted() {
    await this.loadArtworks();
    if (this.characterId) {
      await this.loadCharacter();
    }
  },

  methods: {
    ...mapActions('artworks', [
      'fetchArtworks',
      'fetchCharacter',
      'createCharacter',
      'updateCharacter',
      'fetchVoiceConfig',
      'updateVoiceConfig',
    ]),

    async loadArtworks() {
      try {
        await this.fetchArtworks({ page_size: 100 });
      } catch (error) {
        this.$message.error('加载作品列表失败: ' + error.message);
      }
    },

    async loadCharacter() {
      this.loading = true;
      try {
        const character = await this.fetchCharacter(this.characterId);
        this.character = character;
        this.form = {
          artwork: character.artwork,
          name: character.name,
          display_name: character.display_name,
          description: character.description || '',
          personality: character.personality || '',
          importance_rank: character.importance_rank,
          preferred_llm_engine: character.preferred_llm_engine,
          preferred_tts_engine: character.preferred_tts_engine,
          preferred_image_engine: character.preferred_image_engine,
          default_portrait: character.default_portrait,
        };

        // 加载音色配置
        if (character.voice_config) {
          this.voiceConfig = character.voice_config;
        }
      } catch (error) {
        this.$message.error('加载角色信息失败: ' + error.message);
      } finally {
        this.loading = false;
      }
    },

    async handleSave() {
      // 验证必填字段
      if (!this.form.artwork) {
        this.$message.warning('请选择所属作品');
        return;
      }
      if (!this.form.name) {
        this.$message.warning('请输入角色名称');
        return;
      }
      if (!this.form.display_name) {
        this.$message.warning('请输入显示名称');
        return;
      }

      this.saving = true;
      try {
        if (this.isEdit) {
          await this.updateCharacter({
            id: this.characterId,
            data: this.form,
          });
          this.$message.success('更新成功');
        } else {
          await this.createCharacter(this.form);
          this.$message.success('创建成功');
        }
        this.$emit('saved');
      } catch (error) {
        this.$message.error('保存失败: ' + error.message);
      } finally {
        this.saving = false;
      }
    },

    handlePortraitUpload(file) {
      this.form.default_portrait = file;
    },

    handlePortraitRemove() {
      this.form.default_portrait = null;
    },

    handleAddPose() {
      // TODO: 打开添加造型对话框
      this.$message.info('添加造型功能待实现');
    },

    handleEditPose(pose) {
      // TODO: 打开编辑造型对话框
      this.$message.info('编辑造型功能待实现');
    },

    async handleDeletePose(pose) {
      const confirmed = await this.$confirm(`确定要删除造型 "${pose.pose_name}" 吗？`);
      if (confirmed) {
        // TODO: 实现删除造型逻辑
        this.$message.info('删除造型功能待实现');
      }
    },

    async handleSetDefaultPose(pose) {
      // TODO: 实现设置默认造型逻辑
      this.$message.info('设置默认造型功能待实现');
    },

    handleConfigureVoice() {
      // 创建音色配置
      this.voiceConfig = {
        tts_engine: this.form.preferred_tts_engine,
        voice_id: '',
        voice_type: '',
        pitch: 'normal',
        speed: 'normal',
        volume: 'normal',
        emotion_mode: '',
        emotion_intensity: 'medium',
        emotion_voices: {},
      };
    },

    async handleUpdateVoiceConfig(config) {
      this.voiceConfig = config;
      if (this.characterId) {
        try {
          await this.updateVoiceConfig({
            characterId: this.characterId,
            data: config,
          });
          this.$message.success('音色配置已更新');
        } catch (error) {
          this.$message.error('更新音色配置失败: ' + error.message);
        }
      }
    },

    handleTestVoice() {
      // TODO: 实现试听功能
      this.$message.info('试听功能待实现');
    },
  },
};
</script>
