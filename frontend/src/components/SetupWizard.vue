<template>
  <div class="setup-wizard-modal" v-if="showWizard">
    <div class="modal-overlay" @click="closeWizard"></div>
    <div class="wizard-container">
      <!-- 关闭按钮 -->
      <button class="close-wizard" @click="closeWizard">✕</button>

      <!-- 进度指示器 -->
      <div class="wizard-progress">
        <div
          v-for="(step, index) in steps"
          :key="index"
          class="progress-step"
          :class="{
            'is-active': currentStep === index,
            'is-completed': index < currentStep
          }"
        >
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-label">{{ step.title }}</div>
        </div>
      </div>

      <!-- 步骤内容 -->
      <div class="wizard-content">
        <div class="step-header">
          <h2>{{ steps[currentStep].title }}</h2>
          <p class="step-description">{{ steps[currentStep].description }}</p>
        </div>

        <div class="step-body">
          <!-- Step 0: 欢迎页 -->
          <div v-if="currentStep === 0" class="welcome-step">
            <div class="welcome-icon">🎬</div>
            <h3>欢迎使用 AI Story</h3>
            <p>AI Story 可以将您的文字创意自动转化为视频内容</p>

            <div class="features">
              <div class="feature-item">
                <div class="feature-icon">✨</div>
                <div class="feature-text">
                  <strong>文案改写</strong>
                  <p>AI自动优化您的文字描述</p>
                </div>
              </div>
              <div class="feature-item">
                <div class="feature-icon">🎨</div>
                <div class="feature-text">
                  <strong>AI生图</strong>
                  <p>自动生成分镜图片</p>
                </div>
              </div>
              <div class="feature-item">
                <div class="feature-icon">🎬</div>
                <div class="feature-text">
                  <strong>视频合成</strong>
                  <p>一键生成完整视频</p>
                </div>
              </div>
            </div>

            <div class="quick-options">
              <button class="btn btn-primary" @click="startQuickStart">
                🚀 快速开始（推荐）
              </button>
              <button class="btn btn-secondary" @click="startManualSetup">
                ⚙️ 手动配置
              </button>
            </div>

            <div class="demo-notice">
              <p><strong>💡 提示</strong></p>
              <p>快速开始会使用Mock AI，无需API密钥，可以在1-2分钟内体验完整功能。配置真实AI需要API密钥。</p>
            </div>
          </div>

          <!-- Step 1: 创建项目 -->
          <div v-if="currentStep === 1" class="create-project-step">
            <div class="form-example">
              <h4>示例主题</h4>
              <div class="example-topics">
                <div
                  v-for="(example, index) in exampleTopics"
                  :key="index"
                  class="example-topic"
                  @click="selectTopic(example)"
                >
                  {{ example }}
                </div>
              </div>
            </div>

            <div class="quick-actions">
              <h4>快速操作</h4>
              <button class="action-btn" @click="goToCreateProject">
                ➕ 创建新项目
              </button>
              <button class="action-btn" @click="viewDemoProject">
                👁️ 查看Demo项目
              </button>
            </div>

            <div class="help-box">
              <h4>💡 如何创建项目？</h4>
              <ol>
                <li>点击"创建新项目"按钮</li>
                <li>输入项目名称和主题描述</li>
                <li>选择"Demo完整模板集"</li>
                <li>选择"Demo Mock AI"</li>
                <li>点击"创建"</li>
              </ol>
            </div>
          </div>

          <!-- Step 2: 执行工作流 -->
          <div v-if="currentStep === 2" class="workflow-step">
            <div class="workflow-diagram">
              <h4>AI视频生成流程</h4>
              <div class="workflow-steps">
                <div
                  v-for="(stage, index) in workflowStages"
                  :key="index"
                  class="workflow-stage"
                >
                  <div class="stage-number">{{ index + 1 }}</div>
                  <div class="stage-content">
                    <strong>{{ stage.name }}</strong>
                    <p>{{ stage.description }}</p>
                  </div>
                  <div class="stage-arrow" v-if="index < workflowStages.length - 1">→</div>
                </div>
              </div>
            </div>

            <div class="help-box">
              <h4>📝 如何执行工作流？</h4>
              <ol>
                <li>打开任意项目（如Demo项目）</li>
                <li>点击"执行完整工作流"按钮</li>
                <li>观察5个阶段依次执行</li>
                <li>等待1-2秒（Mock AI）或2-5分钟（真实AI）</li>
                <li>查看生成结果</li>
              </ol>
            </div>

            <div class="notice">
              <p><strong>⚡ 使用Mock AI</strong>时，整个流程只需1-2秒！</p>
            </div>
          </div>

          <!-- Step 3: 配置真实AI -->
          <div v-if="currentStep === 3" class="config-ai-step">
            <div class="config-options">
              <div class="config-card" @click="showMockConfig">
                <div class="card-icon">🎭</div>
                <h4>使用Mock AI</h4>
                <p>快速测试，无需API密钥</p>
                <div class="card-status">✓ 已配置</div>
              </div>

              <div class="config-card" @click="showRealAIConfig">
                <div class="card-icon">🤖</div>
                <h4>配置真实AI</h4>
                <p>需要API密钥，生成真实内容</p>
                <div class="card-status">→ 点击配置</div>
              </div>
            </div>

            <div class="ai-providers">
              <h4>支持的AI服务</h4>
              <div class="provider-list">
                <div class="provider-item">
                  <strong>LLM</strong>
                  <p>OpenAI GPT-4, Claude, 通义千问, 文心一言</p>
                </div>
                <div class="provider-item">
                  <strong>Text2Image</strong>
                  <p>Stable Diffusion, DALL-E, Midjourney</p>
                </div>
                <div class="provider-item">
                  <strong>Image2Video</strong>
                  <p>Runway Gen-2, Pika</p>
                </div>
              </div>
            </div>

            <div class="help-box">
              <h4>🔧 如何配置真实AI？</h4>
              <ol>
                <li>进入"模型管理"页面</li>
                <li>点击"添加提供商"</li>
                <li>选择提供商类型</li>
                <li>填写API密钥和配置</li>
                <li>保存后即可在项目中使用</li>
              </ol>
            </div>
          </div>

          <!-- Step 4: 完成 -->
          <div v-if="currentStep === 4" class="complete-step">
            <div class="complete-icon">🎉</div>
            <h3>设置完成！</h3>
            <p>您已准备好开始使用AI Story</p>

            <div class="next-steps">
              <h4>接下来可以：</h4>
              <ul>
                <li>✅ 查看Demo项目，了解系统功能</li>
                <li>✅ 创建自己的项目，体验AI生成</li>
                <li>✅ 配置真实AI API，生成真实内容</li>
                <li>✅ 自定义提示词模板，优化生成效果</li>
              </ul>
            </div>

            <div class="resources">
              <h4>📚 学习资源</h4>
              <a href="/docs/QUICKSTART.md" target="_blank" class="resource-link">
                📖 快速开始指南
              </a>
              <a href="/docs/FAQ.md" target="_blank" class="resource-link">
                ❓ 常见问题解答
              </a>
            </div>

            <button class="btn btn-primary btn-large" @click="goToProjects">
              🚀 开始使用
            </button>
          </div>
        </div>
      </div>

      <!-- 导航按钮 -->
      <div class="wizard-footer" v-if="currentStep > 0">
        <button
          class="btn btn-secondary"
          @click="previousStep"
          v-if="currentStep > 0 && currentStep < 4"
        >
          ← 上一步
        </button>
        <button
          class="btn btn-primary"
          @click="nextStep"
          v-if="currentStep < 4"
        >
          下一步 →
        </button>
        <button
          class="btn btn-success"
          @click="finishWizard"
          v-if="currentStep === 4"
        >
          ✅ 完成
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SetupWizard',
  data() {
    return {
      showWizard: false,
      currentStep: 0,
      steps: [
        { title: '欢迎', description: '欢迎使用AI Story' },
        { title: '创建项目', description: '创建您的第一个AI视频项目' },
        { title: '执行工作流', description: '了解AI视频生成流程' },
        { title: '配置AI', description: '配置AI服务提供商' },
        { title: '完成', description: '开始您的创作之旅' }
      ],
      exampleTopics: [
        '宁静的小镇，年轻的画家在清晨创作',
        '科幻冒险：宇航员在火星发现外星文明遗迹',
        '童话世界：小兔子在森林里的奇妙冒险'
      ],
      workflowStages: [
        { name: '文案改写', description: 'AI优化您的文字描述' },
        { name: '分镜生成', description: '自动生成分镜脚本' },
        { name: '文生图', description: '根据分镜生成图片' },
        { name: '运镜生成', description: '设计镜头运动效果' },
        { name: '视频生成', description: '合成完整视频' }
      ]
    };
  },
  mounted() {
    // 检查是否首次访问
    const hasSeenWizard = localStorage.getItem('ai_story_wizard_seen');
    const hasProjects = this.$store.state.projects?.items?.length > 0;

    if (!hasSeenWizard && !hasProjects) {
      this.showWizard = true;
    }
  },
  methods: {
    closeWizard() {
      this.showWizard = false;
      localStorage.setItem('ai_story_wizard_seen', 'true');
    },
    startQuickStart() {
      // 跳转到创建项目页面
      this.currentStep = 1;
    },
    startManualSetup() {
      // 跳转到模型管理页面
      this.closeWizard();
      this.$router.push('/models');
    },
    nextStep() {
      if (this.currentStep < this.steps.length - 1) {
        this.currentStep++;
      }
    },
    previousStep() {
      if (this.currentStep > 0) {
        this.currentStep--;
      }
    },
    selectTopic(topic) {
      // 选择主题并跳转到创建项目
      this.$router.push({
        path: '/projects/create',
        query: { topic: topic }
      });
      this.closeWizard();
    },
    goToCreateProject() {
      this.$router.push('/projects/create');
      this.closeWizard();
    },
    viewDemoProject() {
      this.$router.push('/projects');
      this.closeWizard();
    },
    showMockConfig() {
      this.$message.info('Mock AI已自动配置完成！');
    },
    showRealAIConfig() {
      this.$router.push('/models');
      this.closeWizard();
    },
    finishWizard() {
      localStorage.setItem('ai_story_wizard_seen', 'true');
      this.showWizard = false;
      this.goToProjects();
    },
    goToProjects() {
      this.$router.push('/projects');
      this.closeWizard();
    }
  }
};
</script>

<style scoped>
.setup-wizard-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
}

.wizard-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: wizardSlideIn 0.3s ease-out;
}

@keyframes wizardSlideIn {
  from {
    opacity: 0;
    transform: translate(-50%, -45%);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%);
  }
}

.close-wizard {
  position: absolute;
  top: 16px;
  right: 16px;
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  z-index: 1;
  transition: all 0.2s;
}

.close-wizard:hover {
  background: #f0f0f0;
  color: #333;
}

.wizard-progress {
  display: flex;
  justify-content: space-between;
  padding: 32px 48px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
  opacity: 0.5;
  transition: all 0.3s;
}

.progress-step.is-active {
  opacity: 1;
}

.progress-step.is-completed {
  opacity: 0.8;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-bottom: 8px;
}

.progress-step.is-active .step-number {
  background: white;
  color: #667eea;
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.3);
}

.progress-step.is-completed .step-number {
  background: #4ade80;
  color: white;
}

.step-label {
  font-size: 12px;
  text-align: center;
}

.wizard-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px 48px;
}

.step-header {
  margin-bottom: 32px;
}

.step-header h2 {
  margin: 0 0 8px 0;
  font-size: 28px;
  color: #333;
}

.step-description {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.welcome-step {
  text-align: center;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome-step h3 {
  margin: 16px 0;
  font-size: 24px;
  color: #333;
}

.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin: 32px 0;
}

.feature-item {
  padding: 16px;
  background: #f9f9f9;
  border-radius: 8px;
  text-align: left;
}

.feature-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.feature-text strong {
  display: block;
  margin-bottom: 4px;
  color: #333;
}

.feature-text p {
  margin: 0;
  font-size: 13px;
  color: #666;
}

.quick-options {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin: 32px 0;
}

.btn {
  padding: 12px 32px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  background: #d1d5db;
}

.btn-success {
  background: #10b981;
  color: white;
}

.btn-success:hover {
  background: #059669;
}

.btn-large {
  padding: 16px 48px;
  font-size: 16px;
}

.demo-notice {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 16px;
  margin-top: 24px;
  text-align: left;
}

.demo-notice strong {
  color: #92400e;
}

.demo-notice p {
  margin: 8px 0 0 0;
  font-size: 14px;
  color: #78716c;
}

.form-example,
.help-box {
  background: #f9fafb;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.form-example h4,
.help-box h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.example-topics {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.example-topic {
  padding: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.example-topic:hover {
  border-color: #667eea;
  background: #f5f3ff;
}

.quick-actions {
  margin-bottom: 20px;
}

.action-btn {
  width: 100%;
  padding: 12px;
  margin-bottom: 8px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
}

.action-btn:hover {
  border-color: #667eea;
  background: #f5f3ff;
}

.help-box ol {
  margin: 0;
  padding-left: 20px;
}

.help-box li {
  margin-bottom: 8px;
  color: #666;
  line-height: 1.6;
}

.workflow-diagram {
  background: #f9fafb;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.workflow-stages {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.workflow-stage {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stage-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
}

.stage-content {
  flex: 1;
}

.stage-content strong {
  display: block;
  color: #333;
}

.stage-content p {
  margin: 4px 0 0 0;
  font-size: 13px;
  color: #666;
}

.stage-arrow {
  font-size: 20px;
  color: #999;
}

.notice {
  background: #dbeafe;
  border: 1px solid #93c5fd;
  border-radius: 8px;
  padding: 12px;
  margin-top: 16px;
}

.notice p {
  margin: 0;
  color: #1e40af;
  font-size: 14px;
}

.config-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.config-card {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.config-card:hover {
  border-color: #667eea;
  background: #f5f3ff;
}

.card-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.config-card h4 {
  margin: 8px 0;
  color: #333;
}

.config-card p {
  margin: 8px 0;
  font-size: 13px;
  color: #666;
}

.card-status {
  margin-top: 12px;
  font-weight: 500;
  color: #667eea;
}

.ai-providers {
  margin-bottom: 20px;
}

.provider-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.provider-item {
  padding: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.provider-item strong {
  display: block;
  color: #333;
  margin-bottom: 4px;
}

.provider-item p {
  margin: 0;
  font-size: 13px;
  color: #666;
}

.complete-step {
  text-align: center;
}

.complete-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.complete-step h3 {
  margin: 16px 0;
  font-size: 24px;
  color: #333;
}

.next-steps {
  background: #f9fafb;
  border-radius: 8px;
  padding: 20px;
  margin: 24px 0;
  text-align: left;
}

.next-steps h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.next-steps ul {
  margin: 0;
  padding-left: 20px;
}

.next-steps li {
  margin-bottom: 8px;
  color: #666;
}

.resources {
  margin: 24px 0;
}

.resources h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.resource-link {
  display: block;
  padding: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #667eea;
  text-decoration: none;
  margin-bottom: 8px;
  transition: all 0.2s;
}

.resource-link:hover {
  border-color: #667eea;
  background: #f5f3ff;
}

.wizard-footer {
  display: flex;
  justify-content: space-between;
  padding: 24px 48px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}
</style>
