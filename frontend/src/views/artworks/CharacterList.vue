<template>
  <div class="character-list">
    <page-card>
      <template #header>
        <div class="flex justify-between items-center">
          <h2 class="text-2xl font-bold">角色管理</h2>
          <div class="flex gap-2">
            <button
              v-if="selectedCharacters.length > 0"
              class="btn btn-sm btn-error gap-2"
              @click="handleBulkDelete"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              删除选中 ({{ selectedCharacters.length }})
            </button>
            <button class="btn btn-sm btn-primary gap-2" @click="handleCreate">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 4v16m8-8H4"
                />
              </svg>
              添加角色
            </button>
          </div>
        </div>
      </template>

      <!-- 筛选区域 -->
      <div class="flex flex-wrap gap-3 mb-6">
        <!-- 作品选择 -->
        <div class="form-control">
          <select
            v-model="filters.artwork"
            class="select select-bordered select-sm w-48"
            @change="handleFilter"
          >
            <option value="">全部作品</option>
            <option v-for="artwork in artworks" :key="artwork.id" :value="artwork.id">
              {{ artwork.title }}
            </option>
          </select>
        </div>

        <!-- 查看作品详情按钮 (Epic 12 入口) -->
        <button
          v-if="filters.artwork"
          class="btn btn-sm btn-primary"
          @click="goToArtworkDetail"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          作品详情
        </button>

        <!-- 搜索 -->
        <div class="form-control">
          <div class="input-group">
            <input
              v-model="filters.search"
              type="text"
              placeholder="搜索角色名称"
              class="input input-bordered input-sm w-48"
              @keyup.enter="handleFilter"
            />
            <button class="btn btn-square btn-sm" @click="handleFilter">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </button>
          </div>
        </div>

        <!-- 视图切换 -->
        <div class="btn-group btn-group-sm">
          <button
            :class="['btn', viewMode === 'grid' ? 'btn-active' : '']"
            @click="viewMode = 'grid'"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
              />
            </svg>
          </button>
          <button
            :class="['btn', viewMode === 'list' ? 'btn-active' : '']"
            @click="viewMode = 'list'"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- 角色列表 -->
      <loading-container :loading="loading.characters">
        <!-- 空状态 -->
        <div
          v-if="!loading.characters && characters.length === 0"
          class="text-center py-12"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-24 w-24 mx-auto text-base-content/50"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          <p class="mt-4 text-base-content/70">暂无角色数据</p>
          <button class="btn btn-primary mt-4" @click="handleCreate">
            添加第一个角色
          </button>
        </div>

        <!-- 网格视图 -->
        <div v-else-if="viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <character-card
            v-for="character in characters"
            :key="character.id"
            :character="character"
            :selected="selectedCharacters.includes(character.id)"
            @select="toggleSelectCharacter"
            @edit="handleEdit"
            @delete="handleDelete"
          />
        </div>

        <!-- 列表视图 -->
        <div v-else class="overflow-x-auto">
          <table class="table table-zebra w-full">
            <thead>
              <tr>
                <th class="w-12">
                  <input
                    type="checkbox"
                    class="checkbox checkbox-sm"
                    :checked="selectedCharacters.length === characters.length && characters.length > 0"
                    @change="toggleSelectAll"
                  />
                </th>
                <th>角色名称</th>
                <th>描述</th>
                <th>出场次数</th>
                <th>造型数量</th>
                <th>TTS引擎</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="character in characters" :key="character.id">
                <td>
                  <input
                    v-model="selectedCharacters"
                    type="checkbox"
                    class="checkbox checkbox-sm"
                    :value="character.id"
                  />
                </td>
                <td>
                  <div class="flex items-center gap-3">
                    <div class="avatar">
                      <div class="w-12 rounded">
                        <img
                          v-if="character.portrait_url"
                          :src="character.portrait_url"
                          :alt="character.display_name"
                        />
                        <div v-else class="placeholder bg-base-300">
                          <span class="text-2xl">{{ character.display_name[0] }}</span>
                        </div>
                      </div>
                    </div>
                    <div>
                      <div class="font-bold">{{ character.display_name }}</div>
                      <div class="text-xs text-base-content/70">{{ character.name }}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <div class="truncate max-w-xs" :title="character.description">
                    {{ character.description || '-' }}
                  </div>
                </td>
                <td>
                  <div class="badge badge-ghost">{{ character.appearance_count }}</div>
                </td>
                <td>
                  <div class="badge badge-ghost">{{ character.poses?.length || 0 }}</div>
                </td>
                <td>
                  <div class="badge badge-sm">
                    {{ character.preferred_tts_engine_display || '-' }}
                  </div>
                </td>
                <td>
                  <div class="flex gap-2">
                    <button class="btn btn-ghost btn-xs" @click="handleEdit(character.id)">
                      编辑
                    </button>
                    <button
                      class="btn btn-ghost btn-xs text-error"
                      @click="handleDelete(character)"
                    >
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </loading-container>

      <!-- 分页 -->
      <div v-if="pagination.total > pagination.pageSize" class="flex justify-center mt-6">
        <div class="join">
          <button
            class="join-item btn"
            :disabled="pagination.page <= 1"
            @click="changePage(pagination.page - 1)"
          >
            上一页
          </button>
          <button class="join-item btn btn-active">
            第 {{ pagination.page }} / {{ totalPages }} 页
          </button>
          <button
            class="join-item btn"
            :disabled="pagination.page >= totalPages"
            @click="changePage(pagination.page + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </page-card>

    <!-- 角色编辑对话框 -->
    <character-edit-modal
      v-if="showEditModal"
      :character-id="editingCharacterId"
      @close="closeEditModal"
      @saved="handleSaved"
    />
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex';
import CharacterCard from '@/components/artworks/CharacterCard.vue';
import CharacterEditModal from '@/components/artworks/CharacterEditModal.vue';
import LoadingContainer from '@/components/common/LoadingContainer.vue';
import PageCard from '@/components/common/PageCard.vue';

export default {
  name: 'CharacterList',

  components: {
    CharacterCard,
    CharacterEditModal,
    LoadingContainer,
    PageCard,
  },

  data() {
    return {
      viewMode: 'grid', // grid | list
      filters: {
        artwork: '',
        search: '',
      },
      selectedCharacters: [],
      showEditModal: false,
      editingCharacterId: null,
    };
  },

  computed: {
    ...mapState('artworks', ['characters', 'artworks', 'loading', 'pagination']),
    ...mapGetters('artworks', ['totalPages']),

    artworkId() {
      return this.$route.params.artworkId || this.filters.artwork;
    },
  },

  watch: {
    artworkId: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.filters.artwork = newVal;
        }
      },
    },
  },

  mounted() {
    this.loadData();
  },

  methods: {
    ...mapActions('artworks', [
      'fetchArtworks',
      'fetchCharacters',
      'deleteCharacter',
      'bulkDeleteCharacters',
    ]),

    async loadData() {
      try {
        // 加载作品列表
        await this.fetchArtworks({ page_size: 100 });
        // 加载角色列表
        await this.loadCharacters();
      } catch (error) {
        // Epic 11: 处理401未认证错误
        if (error.response?.status === 401) {
          console.warn('未登录，跳转到登录页')
          this.$router.push('/login')
          return
        }
        // 其他错误：显示空列表（默认处理）
        console.error('加载数据失败:', error)
      }
    },

    async loadCharacters() {
      const params = {
        page: this.pagination.page,
        page_size: this.pagination.pageSize,
      };
      if (this.filters.artwork) {
        params.artwork = this.filters.artwork;
      }
      if (this.filters.search) {
        params.search = this.filters.search;
      }
      await this.fetchCharacters(params);
    },

    handleFilter() {
      this.pagination.page = 1;
      this.loadCharacters();
    },

    // Epic 12: 跳转到作品详情页（章节工作室入口）
    goToArtworkDetail() {
      if (this.filters.artwork) {
        this.$router.push(`/artworks/${this.filters.artwork}`);
      }
    },

    changePage(page) {
      this.pagination.page = page;
      this.loadCharacters();
    },

    handleCreate() {
      this.editingCharacterId = null;
      this.showEditModal = true;
    },

    handleEdit(id) {
      this.editingCharacterId = String(id);
      this.showEditModal = true;
    },

    closeEditModal() {
      this.showEditModal = false;
      this.editingCharacterId = null;
    },

    async handleSaved() {
      this.closeEditModal();
      await this.loadCharacters();
    },

    async handleDelete(character) {
      const confirmed = await this.$confirm(
        `确定要删除角色 "${character.display_name}" 吗？此操作不可恢复。`
      );
      if (confirmed) {
        try {
          await this.deleteCharacter(character.id);
          this.$message.success('删除成功');
          await this.loadCharacters();
        } catch (error) {
          this.$message.error('删除失败: ' + error.message);
        }
      }
    },

    toggleSelectCharacter(id) {
      const index = this.selectedCharacters.indexOf(id);
      if (index > -1) {
        this.selectedCharacters.splice(index, 1);
      } else {
        this.selectedCharacters.push(id);
      }
    },

    toggleSelectAll() {
      if (this.selectedCharacters.length === this.characters.length) {
        this.selectedCharacters = [];
      } else {
        this.selectedCharacters = this.characters.map((c) => c.id);
      }
    },

    async handleBulkDelete() {
      const confirmed = await this.$confirm(
        `确定要删除选中的 ${this.selectedCharacters.length} 个角色吗？此操作不可恢复。`
      );
      if (confirmed) {
        try {
          await this.bulkDeleteCharacters(this.selectedCharacters);
          this.$message.success('批量删除成功');
          this.selectedCharacters = [];
          await this.loadCharacters();
        } catch (error) {
          this.$message.error('批量删除失败: ' + error.message);
        }
      }
    },
  },
};
</script>
